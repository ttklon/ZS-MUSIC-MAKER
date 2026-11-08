'use strict';
/**
 * Предпросмотр в браузере (`scripts/preview-server.js`).
 *
 * Сервер нужен только для проверки вёрстки без Electron; но если он отдаёт
 * файлы вне `src/` или подсовывает шим в приложение — это дыра. Проверяем и
 * то, и другое.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const { createServer, shim } = require('../scripts/preview-server');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');

function get(server, pathname) {
  const address = server.address();
  return new Promise((resolve, reject) => {
    const req = http.request(
      { host: '127.0.0.1', port: address.port, path: pathname, method: 'GET' },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () =>
          resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8'), headers: res.headers }),
        );
      },
    );
    req.on('error', reject);
    req.end();
  });
}

async function withServer(t) {
  const project = createProject(createNodeFs(), ROOT);
  const server = createServer(project);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  return server;
}

test('отдаёт index.html и подключает шим только в предпросмотре', async (t) => {
  const server = await withServer(t);

  const page = await get(server, '/');

  assert.equal(page.status, 200);
  assert.match(page.headers['content-type'], /text\/html/);
  assert.match(page.body, /preview-shim\.js/, 'шим обязан быть подключён до app.js');
  assert.ok(
    page.body.indexOf('preview-shim.js') < page.body.indexOf('app.js'),
    'шим должен загружаться первым',
  );
});

test('шим отдаёт настоящие данные проекта и не умеет запускать процессы', async (t) => {
  const server = await withServer(t);

  const response = await get(server, '/preview-shim.js');

  assert.equal(response.status, 200);
  assert.match(response.body, /zsmm/);
  assert.match(response.body, /задачи запускает только приложение Electron/);
  assert.doesNotMatch(response.body, /require\(|child_process/);
});

test('шим содержит версию и жанры из файлов', () => {
  const project = createProject(createNodeFs(), ROOT);
  const code = shim(project);

  const version = project.version().version;
  assert.ok(code.includes(version), 'версия должна попасть в шим');
  assert.match(code, /"genres":\[/);
});

test('выход за пределы src/ невозможен', async (t) => {
  const server = await withServer(t);

  for (const evil of ['/../package.json', '/../../package.json', '/..%2fpackage.json']) {
    const response = await get(server, evil);
    assert.notEqual(response.status, 200, `отдан файл вне src/: ${evil}`);
  }
});

test('неизвестный файл — 404, а не пустая страница', async (t) => {
  const server = await withServer(t);

  const response = await get(server, '/nope.js');

  assert.equal(response.status, 404);
});

test('css отдаётся с правильным типом', async (t) => {
  const server = await withServer(t);

  const response = await get(server, '/styles.css');

  assert.equal(response.status, 200);
  assert.match(response.headers['content-type'], /text\/css/);
});

test('предпросмотр рендерит бит тем же движком, что приложение', async (t) => {
  const project = createProject(createNodeFs(), ROOT);
  const server = createServer(project);
  t.after(() => server.close());
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();

  const post = (payload) => new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const req = http.request(
      { host: '127.0.0.1', port, path: '/beat-render', method: 'POST', headers: { 'Content-Type': 'application/json' } },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))));
      },
    );
    req.on('error', reject);
    req.end(body);
  });

  const ok = await post({ bpm: 120, genre: 'house', seed: 3, durationSec: 2 });
  assert.equal(ok.ok, true, ok.error);
  assert.equal(ok.data.report.bpm, 120);
  assert.equal(ok.data.report.deterministic, true);
  assert.ok(ok.data.wavBase64.length > 1000, 'должен вернуться готовый WAV, а не заглушка');
  assert.equal(Buffer.from(ok.data.wavBase64, 'base64').toString('ascii', 0, 4), 'RIFF');

  const bad = await post({ bpm: 5000 });
  assert.equal(bad.ok, false);
  assert.match(bad.error, /BPM/);
});

test('CSP предпросмотра разрешает свой же сервер, приложение — нет', async (t) => {
  const project = createProject(createNodeFs(), ROOT);
  const server = createServer(project);
  t.after(() => server.close());
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));

  const page = await get(server, '/');
  assert.match(page.body, /connect-src 'self'/, 'предпросмотру нужен свой origin для рендера');
  assert.doesNotMatch(page.body, /connect-src 'none'/);

  const source = fs.readFileSync(path.join(ROOT, 'desktop', 'src', 'index.html'), 'utf8');
  assert.match(source, /connect-src 'none'/, 'в приложении окно не должно ходить даже к себе по HTTP');
});
