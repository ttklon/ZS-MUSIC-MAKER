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
const { renderBeat } = require('../src/core/audio/engine');
const { SampleSource } = require('../src/core/audio/bank');
const { sanitizeBeatOptions } = require('../src/core/beat-options');

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
    beatBank: async () => {
      const response = await fetch('/beat-bank');
      return response.json();
    },
    saveBeat: () => Promise.resolve({
      ok: false,
      error: 'в браузере файл не сохраняется: откройте приложение Electron',
    }),
    stopTask: () => Promise.resolve({ ok: false, error: 'нет задачи' }),
    onTaskEvent: () => () => {},
    onTaskDone: () => () => {},
    revealRoot: () => Promise.resolve({ ok: false, error: 'доступно только в приложении' }),
    openExternal: () => Promise.resolve({ ok: false, error: 'доступно только в приложении' }),
  };
})();`;
}

function createServer(project, options = {}) {
  // Один источник сэмплов на сервер: он кэширует декодированные one-shot'ы.
  const sampleSource = options.sampleSource
    || (options.bank === false ? null : new SampleSource({ fileSystem: createNodeFs(), rootDir: ROOT }));
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
        const sanitized = sanitizeBeatOptions(parsed);
        if (sanitized.error) {
          send(200, JSON.stringify({ ok: false, error: sanitized.error }), MIME['.json']);
          return;
        }
        try {
          const { wav, report } = renderBeat({
            ...sanitized.value,
            bank: sanitized.value.useBank === false ? null : sampleSource,
          });
          send(200, JSON.stringify({ ok: true, data: { report, wavBase64: wav.toString('base64') } }), MIME['.json']);
        } catch (err) {
          send(200, JSON.stringify({ ok: false, error: err.message }), MIME['.json']);
        }
      });
      return;
    }

    if (url.pathname === '/beat-bank') {
      try {
        const report = sampleSource ? sampleSource.report() : { status: 'FALLBACK', warnings: ['банк отключён'] };
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
      // В разработке шим подключается до app.js; CSP остаётся прежней
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
