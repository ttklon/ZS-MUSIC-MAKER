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
    stopTask: () => Promise.resolve({ ok: false, error: 'нет задачи' }),
    onTaskEvent: () => () => {},
    onTaskDone: () => () => {},
    revealRoot: () => Promise.resolve({ ok: false, error: 'доступно только в приложении' }),
    openExternal: () => Promise.resolve({ ok: false, error: 'доступно только в приложении' }),
  };
})();`;
}

function createServer(project) {
  return http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const send = (status, body, type) => {
      res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' });
      res.end(body);
    };

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
      body = Buffer.from(
        body.toString('utf8').replace(
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
