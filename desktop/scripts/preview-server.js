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
const { createCancelSignal } = require('../electron/render-host');

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
  // Снимок строится при каждом запросе шима: после правки досье окно
  // перезагружает раздел и должно увидеть новый список, а не старый.
  const payload = {};
  for (const [name, loader] of Object.entries(sections)) payload[name] = loader();

  return `(() => {
  const data = ${JSON.stringify(payload)};
  const reply = (name) => ({ ok: true, data: data[name] });
  window.zsmm = {
    ${Object.keys(payload).map((name) => `${name}: () => Promise.resolve(reply('${name}')),`).join('\n    ')}
    listTasks: () => Promise.resolve([
      { key: 'native-files', label: 'Проверка файлов проекта (без Python)', accepts: [], native: true },
      { key: 'native-readiness', label: 'Готовность: снимок против пересчёта (без Python)', accepts: [], native: true },
      { key: 'native-dossier', label: 'Сводка по досье (без Python)', accepts: [], native: true },
      { key: 'readiness', label: 'Готовность через Python (только в приложении)', accepts: [] },
    ]),
    startTask: async (key) => {
      // Нативные задачи считает тот же модуль, что в приложении: предпросмотр
      // не должен показывать мёртвую кнопку там, где окно работает.
      if (String(key || '').startsWith('native-')) {
        const response = await fetch('/native-task', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key }),
        });
        return response.json();
      }
      return {
        ok: false,
        error: 'предпросмотр в браузере: задачи Python запускает только приложение Electron',
      };
    },
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
    // В предпросмотре рендер идёт на этом же сервере, поэтому отмена —
    // отдельный POST, как и в Electron.
    cancelBeat: async () => {
      const response = await fetch('/beat-cancel', { method: 'POST' });
      return response.json();
    },
    beatBank: async () => {
      const response = await fetch('/beat-bank');
      return response.json();
    },
    // Досье в предпросмотре правится по-настоящему: тот же dossier-edit и тот
    // же корень проекта, что в приложении. Иначе кнопки «Добавить/Удалить»
    // выглядели бы рабочими, но ничего не делали.
    dossierAdd: async (payload) => {
      const response = await fetch('/dossier-add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {}),
      });
      return response.json();
    },
    dossierRemove: async (payload) => {
      const response = await fetch('/dossier-remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {}),
      });
      return response.json();
    },
    // Треки досье — те же правила, что в приложении: формат один.
    dossierTracks: async (slug) => {
      const response = await fetch('/dossier-tracks?slug=' + encodeURIComponent(slug || ''));
      return response.json();
    },
    dossierTrackAdd: async (payload) => {
      const response = await fetch('/dossier-track-add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {}),
      });
      return response.json();
    },
    // Входа записи в браузере нет — и предпросмотр так и говорит.
    vocalInput: () => Promise.resolve({
      ok: true,
      data: {
        recording: false,
        label: 'захват с микрофона не встроен',
        reason: 'в предпросмотре нет доступа к устройствам записи',
        simulatedAvailable: true,
      },
    }),
    pickVocalFile: () => Promise.resolve({
      ok: false,
      error: 'выбор файла с диска доступен только в приложении Electron',
    }),
    openBeatExternal: () => Promise.resolve({
      ok: false,
      error: 'системный плеер доступен только в приложении Electron',
    }),
    // Дубль в браузере скачивается как файл — без диалога сохранения.
    exportVocalTake: (payload) => {
      const base64 = (payload && payload.wavBase64) || '';
      if (base64.length < 64) return Promise.resolve({ ok: false, error: 'нет данных дубля' });
      const name = String((payload && payload.name) || 'vocal-take').replace(/[^\w.-]+/g, '_');
      const bytes = Uint8Array.from(atob(base64), (ch) => ch.charCodeAt(0));
      const url = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = name + '.wav';
      link.click();
      URL.revokeObjectURL(url);
      return Promise.resolve({ ok: true, data: { path: link.download } });
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
  // Отмена идёт тем же сигналом, что и в Electron (render-host.createCancelSignal).
  let activeRender = null;
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
        const signal = createCancelSignal();
        activeRender = signal;
        renderBeatPayload(parsed, {
          rootDir: ROOT,
          bankFor: () => bankProvider.bank(),
          onProgress: (progress) => { lastProgress = progress; },
          isCancelled: () => signal.aborted,
        }).then((reply) => {
          if (activeRender === signal) activeRender = null;
          if (reply.cancelled === true) lastProgress = { phase: 'cancelled', percent: 0 };
          else {
            lastProgress = reply.ok === true
              ? { phase: 'done', percent: 100 }
              : { phase: 'error', percent: 0, error: reply.error };
          }
          send(200, JSON.stringify(reply), MIME['.json']);
        });
      });
      return;
    }

    if (url.pathname === '/beat-cancel' && req.method === 'POST') {
      const cancelled = activeRender ? activeRender.abort() : false;
      lastProgress = cancelled
        ? { phase: 'cancelled', percent: 0 }
        : lastProgress;
      send(200, JSON.stringify({ ok: true, data: { cancelled } }), MIME['.json']);
      return;
    }

    if (url.pathname === '/beat-progress') {
      send(200, JSON.stringify({ ok: true, data: lastProgress }), MIME['.json']);
      return;
    }

    if ((url.pathname === '/dossier-add' || url.pathname === '/dossier-remove') && req.method === 'POST') {
      const chunks = [];
      req.on('data', (chunk) => chunks.push(chunk));
      req.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
        } catch {
          send(200, JSON.stringify({ ok: false, error: 'тело запроса — не JSON' }), MIME['.json']);
          return;
        }
        const dossier = require('../src/core/dossier-edit');
        const fsApi = createNodeFs();
        const reply = url.pathname === '/dossier-add'
          ? dossier.addArtist(fsApi, ROOT, parsed)
          : dossier.removeArtist(fsApi, ROOT, parsed);
        send(200, JSON.stringify(reply), MIME['.json']);
      });
      return;
    }

    if (url.pathname === '/native-task' && req.method === 'POST') {
      const chunks = [];
      req.on('data', (chunk) => chunks.push(chunk));
      req.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
        } catch {
          send(200, JSON.stringify({ ok: false, error: 'тело запроса — не JSON' }), MIME['.json']);
          return;
        }
        const nativeTasks = require('../electron/native-tasks');
        const task = nativeTasks.NATIVE_TASKS[parsed.key];
        if (!task) {
          send(200, JSON.stringify({ ok: false, error: 'неизвестная задача' }), MIME['.json']);
          return;
        }
        const lines = [];
        const result = nativeTasks.runNativeTask({
          key: parsed.key,
          project,
          root: ROOT,
          onEvent: (event) => lines.push(event.line),
        });
        send(200, JSON.stringify({
          ok: true,
          data: { pid: null, command: [task.label], native: true, result: { ok: result.ok, lines } },
        }), MIME['.json']);
      });
      return;
    }

    if (url.pathname === '/dossier-tracks' && req.method === 'GET') {
      const dossierTracks = require('../src/core/dossier-tracks');
      const slug = String(url.searchParams.get('slug') || '').trim();
      if (!slug) {
        send(200, JSON.stringify({ ok: false, error: 'не указан артист' }), MIME['.json']);
        return;
      }
      const list = dossierTracks.listTracks(createNodeFs(), ROOT, slug);
      send(200, JSON.stringify({ ok: true, data: { slug, tracks: list.tracks, errors: list.errors } }), MIME['.json']);
      return;
    }

    if (url.pathname === '/dossier-track-add' && req.method === 'POST') {
      const chunks = [];
      req.on('data', (chunk) => chunks.push(chunk));
      req.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
        } catch {
          send(200, JSON.stringify({ ok: false, error: 'тело запроса — не JSON' }), MIME['.json']);
          return;
        }
        const dossierTracks = require('../src/core/dossier-tracks');
        send(200, JSON.stringify(dossierTracks.addTrack(createNodeFs(), ROOT, parsed)), MIME['.json']);
      });
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
