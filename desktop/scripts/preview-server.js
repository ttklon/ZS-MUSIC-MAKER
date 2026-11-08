'use strict';
/**
 * scripts/preview-server.js — посмотреть окно в браузере без Electron.
 *
 * Это НЕ приложение: статический сервер для единственного `src/` и небольшой
 * шим `window.zsmm`, который отдаёт те же данные через `src/core/*`. Нужен,
 * чтобы увидеть вёрстку, когда в окружении нет графической среды (Electron
 * без Xvfb не стартует). Шим не попадает в сборку: он подаётся только этим
 * сервером, а в приложении мост даёт preload.
 */

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');
const { createProject } = require('../src/core/project');
const { createBankProvider, renderBeatPayload } = require('../electron/pipeline');

const DESKTOP = path.resolve(__dirname, '..');
const ROOT = path.resolve(DESKTOP, '..');
const PORT = Number(process.env.ZSMM_PREVIEW_PORT || 4173);
const HOST = '0.0.0.0';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
};

function shim(project) {
  const sections = {
    version: () => project.version(),
    genres: () => project.genres(),
    modules: () => project.modules(),
    readiness: () => project.readiness(),
    dossiers: () => project.dossiers(),
    system: () => project.systemInfo(),
  };
  const payload = {};
  for (const [name, loader] of Object.entries(sections)) payload[name] = loader();

  return `(() => {
  const data = ${JSON.stringify(payload)};
  const reply = (name) => ({ ok: true, data: data[name] });
  window.zsmm = {
    ${Object.keys(payload).map((name) => `${name}: () => Promise.resolve(reply('${name}')),`).join('\n    ')}
    listTasks: () => Promise.resolve([
      { key: 'readiness', label: 'Готовность (в браузере не запускается)', accepts: [] },
    ]),
    startTask: () => Promise.resolve({
      ok: false,
      error: 'предпросмотр в браузере: задачи запускает только приложение Electron',
    }),
    // Рендер идёт на сервере предпросмотра (POST /beat-render): странице
    // не нужен ни движок, ни Buffer. Это тот же код, что в Electron.
    renderBeat: async (options) => {
      const response = await fetch('/beat-render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options || {}),
      });
      return response.json();
    },
    onBeatProgress: (callback) => {
      // Поллинг вместо событий: у шима нет IPC, а держать SSE ради одной
      // кнопки — лишний код. Возвращаем функцию отписки, как в preload.
      if (typeof callback !== 'function') return () => {};
      let stopped = false;
      let last = '';
      const tick = async () => {
        if (stopped) return;
        try {
          const reply = await (await fetch('/beat-progress')).json();
          const key = JSON.stringify(reply.data);
          if (reply.ok && key !== last) {
            last = key;
            callback(reply.data);
          }
        } catch {
          /* предпросмотр закрылся — тихо выходим */
        }
        if (!stopped) setTimeout(tick, 300);
      };
      tick();
      return () => { stopped = true; };
    },
    beatBank: async () => {
      const response = await fetch('/beat-bank');
      return response.json();
    },
    // В браузере диалога сохранения нет — но данные отчёта скачиваются,
    // чтобы проверять его было чем-то, кроме глаз.
    saveBeat: () => Promise.resolve({
      ok: false,
      error: 'в браузере файл не сохраняется: откройте приложение Electron',
    }),
    saveReport: async (name, text) => {
      const blob = new Blob([text], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = String(name || 'report.json');
      link.click();
      URL.revokeObjectURL(url);
      return { ok: true, data: { path: link.download } };
    },
    // В предпросмотре настроек нет: каждый запуск — чистый лист.
    loadSettings: () => Promise.resolve({ ok: true, data: {} }),
    saveSettings: () => Promise.resolve({ ok: true, data: {} }),
    stopTask: () => Promise.resolve({ ok: false, error: 'нет задачи' }),
    onTaskEvent: () => () => {},
    onTaskDone: () => () => {},
    revealRoot: () => Promise.resolve({ ok: false, error: 'доступно только в приложении' }),
    openExternal: () => Promise.resolve({ ok: false, error: 'доступно только в приложении' }),
  };
})();`;
}

function createServer(project, options = {}) {
  // Последний известный прогресс рендера: предпросмотр отдаёт его по запросу.
  let lastProgress = { phase: 'idle', percent: 0 };
  // Один источник сэмплов на сервер: он кэширует декодированные one-shot'ы.
  const bankProvider = createBankProvider({
    rootDir: ROOT,
    fileSystem: createNodeFs(),
    shared: options.sampleSource ? { source: options.sampleSource } : { source: options.bank === false ? null : undefined },
  });
  return http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const send = (status, body, type) => {
      res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' });
      res.end(body);
    };

    if (url.pathname === '/beat-render' && req.method === 'POST') {
      // Те же границы, что в Electron: окно не диктует главному процессу,
      // что рендерить.
      const chunks = [];
      req.on('data', (chunk) => chunks.push(chunk));
      req.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
        } catch {
          send(400, JSON.stringify({ ok: false, error: 'тело запроса — не JSON' }), MIME['.json']);
          return;
        }
        // В предпросмотре прогресс приходит не событиями, а поллингом
        // `/beat-progress`: держать SSE ради одной кнопки — лишний код.
        lastProgress = { phase: 'start', percent: 0 };
        // Тот же конвейер, что в Electron: проверка параметров, банк и
        // прогресс не дублируются, поэтому предпросмотр не «врёт» про окно.
        renderBeatPayload(parsed, {
          rootDir: ROOT,
          bankFor: () => bankProvider.bank(),
          onProgress: (progress) => { lastProgress = progress; },
        }).then((reply) => {
          lastProgress = reply.ok === true
            ? { phase: 'done', percent: 100 }
            : { phase: 'error', percent: 0, error: reply.error };
          send(200, JSON.stringify(reply), MIME['.json']);
        });
      });
      return;
    }

    if (url.pathname === '/beat-progress') {
      send(200, JSON.stringify({ ok: true, data: lastProgress }), MIME['.json']);
      return;
    }

    if (url.pathname === '/beat-bank') {
      try {
        const report = options.bank === false
          ? { status: 'FALLBACK', warnings: ['банк отключён'] }
          : bankProvider.bank().report();
        send(200, JSON.stringify({ ok: true, data: report }), MIME['.json']);
      } catch (err) {
        send(200, JSON.stringify({ ok: false, error: err.message }), MIME['.json']);
      }
      return;
    }

    if (url.pathname === '/preview-shim.js') {
      send(200, shim(project), MIME['.js']);
      return;
    }

    const requested = url.pathname === '/' ? '/index.html' : url.pathname;
    const target = path.join(DESKTOP, 'src', path.normalize(requested).replace(/^(\.\.[/\\])+/, ''));
    if (!target.startsWith(path.join(DESKTOP, 'src')) || !fs.existsSync(target) || !fs.statSync(target).isFile()) {
      send(404, 'не найдено', MIME['.html']);
      return;
    }
    let body = fs.readFileSync(target);
    if (requested === '/index.html') {
      // В разработке шим подключается до ПЕРВОГО скрипта окна (сейчас это
      // app.js, за ним идут sections/*.js); CSP остаётся прежней
      // (скрипт отдаётся с этого же origin, поэтому 'self' его разрешает).
      // В предпросмотре рендер бита идёт на этот же сервер, поэтому
      // `connect-src` расширяется до 'self' — и только здесь. В приложении
      // CSP остаётся `connect-src 'none'`.
      body = Buffer.from(
        body.toString('utf8')
          .replace("connect-src 'none'", "connect-src 'self'")
          .replace(
            '<script src="app.js"></script>',
            '<script src="preview-shim.js"></script>\n    <script src="app.js"></script>',
          ),
        'utf8',
      );
    }
    send(200, body, MIME[path.extname(target)] || 'application/octet-stream');
  });
}

if (require.main === module) {
  const project = createProject(createNodeFs(), ROOT);
  createServer(project).listen(PORT, HOST, () => {
    console.log(`предпросмотр окна: http://localhost:${PORT} (данные из ${ROOT})`);
  });
}

module.exports = { createServer, shim };
