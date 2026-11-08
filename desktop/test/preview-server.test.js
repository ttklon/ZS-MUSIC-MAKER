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

/** POST JSON на сервер предпросмотра; возвращает разобранный ответ. */
function postTo(server, pathname, payload) {
  const address = server.address();
  return new Promise((resolve, reject) => {
    const req = http.request(
      { host: '127.0.0.1', port: address.port, path: pathname, method: 'POST', headers: { 'Content-Type': 'application/json' } },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))));
      },
    );
    req.on('error', reject);
    req.end(JSON.stringify(payload || {}));
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
  // Ищем именно теги скриптов: имена файлов встречаются и в комментариях.
  const shimTag = page.body.indexOf('<script src="preview-shim.js"');
  const firstWindowScript = page.body.indexOf('<script src="app.js"');
  assert.ok(shimTag > -1 && firstWindowScript > -1, 'нет тегов шима и app.js');
  assert.ok(shimTag < firstWindowScript, 'шим должен загружаться первым');
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

  // Банк сэмплов подключён и в предпросмотре: статус не «на словах», а по факту.
  const bankReply = await get(server, '/beat-bank');
  const bankData = JSON.parse(bankReply.body);
  assert.equal(bankData.ok, true, bankData.error);
  assert.equal(bankData.data.status, 'REAL_PASS');
  assert.ok(bankData.data.total_samples >= 32);
  assert.equal(ok.data.report.drum_engine.status, 'REAL_PASS');

  const withoutBank = await post({ bpm: 120, genre: 'house', seed: 3, durationSec: 2, useBank: false });
  assert.equal(withoutBank.data.report.drum_engine.status, 'FALLBACK');
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

test('прогресс рендера отдаётся поллингом, а шим подписывается без IPC', async (t) => {
  const server = await withServer(t);
  const address = server.address();

  const idle = JSON.parse((await get(server, '/beat-progress')).body);
  assert.equal(idle.ok, true);
  assert.equal(idle.data.phase, 'idle');

  const body = JSON.stringify({ bpm: 120, genre: 'house', seed: 3, durationSec: 2 });
  const rendered = await new Promise((resolve, reject) => {
    const req = http.request(
      { host: '127.0.0.1', port: address.port, path: '/beat-render', method: 'POST', headers: { 'Content-Type': 'application/json' } },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))));
      },
    );
    req.on('error', reject);
    req.end(body);
  });
  assert.equal(rendered.ok, true, rendered.error);

  const done = JSON.parse((await get(server, '/beat-progress')).body);
  assert.equal(done.data.phase, 'done');
  assert.equal(done.data.percent, 100);

  // Шим обязан отдать функцию отписки — app.js вызывает её в `finally`.
  const project = createProject(createNodeFs(), ROOT);
  assert.match(shim(project), /onBeatProgress/);
});

test('отмена рендера в предпросмотре отвечает и не ломает прогресс', async (t) => {
  const server = await withServer(t);
  const address = server.address();

  const idle = await postTo(server, '/beat-cancel', {});
  assert.equal(idle.ok, true);
  assert.equal(idle.data.cancelled, false);

  // Длинный рендер и отмена почти сразу.
  const rendering = postTo(server, '/beat-render', { bpm: 128, genre: 'drift phonk', seed: 5, durationSec: 120 });
  const cancelled = await postTo(server, '/beat-cancel', {});
  const result = await rendering;

  assert.equal(cancelled.data.cancelled, true);
  assert.equal(result.ok, false);
  assert.match(result.error, /отменён/);

  const progress = JSON.parse((await get(server, '/beat-progress')).body);
  assert.equal(progress.data.phase, 'cancelled');
  assert.ok(address.port > 0);
});


test('предпросмотр правит досье тем же кодом, что приложение', async (t) => {
  const server = await withServer(t);
  const listing = await get(server, '/preview-shim.js');
  for (const method of ['dossierAdd', 'dossierRemove', 'vocalInput', 'pickVocalFile', 'exportVocalTake', 'openBeatExternal']) {
    assert.match(listing.body, new RegExp(method), `в шиме нет ${method}`);
  }

  // Добавляем и удаляем настоящего артиста: сервер пишет в корень проекта.
  const dir = path.join(ROOT, 'data', 'artist_dossier', 'тест_предпросмотра');
  fs.rmSync(dir, { recursive: true, force: true });
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const added = await postTo(server, '/dossier-add', { artist: 'Тест Предпросмотра', note: 'из теста' });
  assert.equal(added.ok, true, added.error);
  assert.ok(fs.existsSync(path.join(dir, 'artist.json')));

  const duplicate = await postTo(server, '/dossier-add', { artist: 'Тест Предпросмотра' });
  assert.equal(duplicate.ok, false);
  assert.match(duplicate.error, /уже есть/);

  // Выход за каталог досье запрещён и здесь, а не только в приложении.
  const escape = await postTo(server, '/dossier-remove', { slug: '../..' });
  assert.equal(escape.ok, false);

  const removed = await postTo(server, '/dossier-remove', { slug: 'тест_предпросмотра' });
  assert.equal(removed.ok, true, removed.error);
  assert.ok(!fs.existsSync(dir));
});

test('предпросмотр прикладывает дубль к рендеру и честно говорит про микрофон', async (t) => {
  const server = await withServer(t);
  const reply = await postTo(server, '/beat-render', { bpm: 120, durationSec: 2, vocal: { mode: 'test' } });
  assert.equal(reply.ok, true, reply.error);
  assert.equal(reply.data.report.vocal.source, 'test');
  assert.equal(reply.data.report.vocal.simulated, true);
  const bytes = Buffer.from(reply.data.vocalWavBase64, 'base64');
  assert.equal(bytes.subarray(0, 4).toString('ascii'), 'RIFF');
  assert.match(reply.data.vocalName, /^vocal-test-2s-/);
});
