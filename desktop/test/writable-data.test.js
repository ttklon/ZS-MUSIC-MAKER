'use strict';
/**
 * test/writable-data.test.js — куда приложение пишет досье.
 *
 * Главная проверка здесь — та, которую невозможно сделать в песочнице без
 * Windows: в установленной сборке `resources/project` лежит в Program Files,
 * и запись туда запрещена. Значит, окно обязано писать в каталог
 * пользователя, а демо-артиста и схему — докладывать один раз.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const writable = require('../electron/writable-data');
const { createNodeFs } = require('../src/core/fs-node');
const { createProject } = require('../src/core/project');
const dossier = require('../src/core/dossier-edit');
const dossierTracks = require('../src/core/dossier-tracks');
const { registerProjectIpc } = require('../electron/ipc-project');

/** Проект, который «только для чтения»: поставка с демо-артистом. */
function makeProject() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-proj-'));
  const dir = path.join(root, 'data', 'artist_dossier');
  fs.mkdirSync(path.join(dir, 'demo_artist'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'schema.json'), '{"$id":"zsmm.artist-dossier.v1"}');
  fs.writeFileSync(
    path.join(dir, 'demo_artist', 'artist.json'),
    JSON.stringify({ artist: 'Demo Artist', slug: 'demo_artist', tracks: [], dossier: {}, note: 'демо' }),
  );
  return root;
}

// Пути в этих двух тестах строятся от `os.tmpdir()`, а не от «/repo»:
// на Windows `path.join('/repo', …)` даёт `\repo\…`, и проверка падала бы
// только в CI на windows-latest.
test('из репозитория досье пишется в проект', () => {
  const project = path.join(os.tmpdir(), 'zsmm-repo');
  const plan = writable.dossierWriteDir({ packaged: false, projectRoot: project, userData: os.tmpdir() });
  assert.equal(plan.source, 'project');
  assert.equal(plan.dir, path.join(project, 'data', 'artist_dossier'));
});

test('в установленной сборке досье пишется в каталог пользователя', () => {
  const programFiles = path.join(os.tmpdir(), 'Program Files', 'app', 'resources', 'project');
  const userData = path.join(os.tmpdir(), 'zsmm-user');
  const plan = writable.dossierWriteDir({ packaged: true, projectRoot: programFiles, userData });
  assert.equal(plan.source, 'user');
  // Program Files только для чтения: писать туда нельзя.
  assert.equal(plan.dir, path.join(userData, 'artist_dossier'));
  assert.ok(!plan.dir.includes('Program Files'));
});

test('демо-артист и схема докладываются один раз и не перетирают правки', () => {
  const project = makeProject();
  const userData = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-userdata-'));
  const first = writable.prepareDossierStore({ packaged: true, projectRoot: project, userData });

  assert.equal(first.source, 'user');
  // Пути собираются через `path.join`: на Windows разделитель другой, и
  // сравнение со слэшами падало бы только в CI на windows-latest.
  assert.deepEqual(first.seeded.sort(), [path.join('demo_artist', 'artist.json'), 'schema.json'].sort());
  assert.ok(fs.existsSync(path.join(first.dir, 'demo_artist', 'artist.json')));
  assert.ok(fs.existsSync(path.join(first.dir, 'schema.json')));

  // Пользователь удалил демо-артиста — второй запуск не должен его вернуть.
  dossier.removeArtist(createNodeFs(), project, { slug: 'demo_artist' }, { dataDir: first.dir });
  const second = writable.prepareDossierStore({ packaged: true, projectRoot: project, userData });
  assert.deepEqual(second.seeded, [], 'повторный запуск не копирует ничего');
  assert.ok(!fs.existsSync(path.join(first.dir, 'demo_artist')), 'удалённое не возвращается');

  fs.rmSync(project, { recursive: true, force: true });
  fs.rmSync(userData, { recursive: true, force: true });
});

test('свой артист и трек живут в каталоге пользователя, поставка не тронута', () => {
  const project = makeProject();
  const userData = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-userdata-'));
  const plan = writable.prepareDossierStore({ packaged: true, projectRoot: project, userData });
  const fsApi = createNodeFs();

  const added = dossier.addArtist(fsApi, project, { artist: 'Мой Артист' }, { dataDir: plan.dir });
  assert.equal(added.ok, true, added.error);
  const track = dossierTracks.addTrack(
    fsApi, project, { slug: added.data.slug, title: 'Мой трек' }, { dataDir: plan.dir },
  );
  assert.equal(track.ok, true, track.error);

  assert.ok(fs.existsSync(path.join(plan.dir, added.data.slug, 'tracks', `${track.data.track_id}.json`)));
  // В поставке ничего не появилось: она только для чтения.
  const shipped = fs.readdirSync(path.join(project, 'data', 'artist_dossier'));
  assert.deepEqual(shipped.sort(), ['demo_artist', 'schema.json']);

  // Чтение через проект идёт из того же каталога: список видит оба источника.
  const model = createProject(fsApi, project, { dossierDir: plan.dir });
  const names = model.dossiers().artists.map((artist) => artist.artist).sort();
  assert.deepEqual(names, ['Demo Artist', 'Мой Артист']);

  fs.rmSync(project, { recursive: true, force: true });
  fs.rmSync(userData, { recursive: true, force: true });
});

test('IPC пишет досье туда, куда сказал главный процесс', async () => {
  const project = makeProject();
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-userdossier-'));
  const handlers = new Map();
  registerProjectIpc({
    ipcMain: { handle: (channel, fn) => handlers.set(channel, fn) },
    getProject: () => null,
    root: project,
    dataDir,
  });

  const added = await handlers.get('zsmm:dossier-add')({}, { artist: 'Через Канал' });
  assert.equal(added.ok, true, added.error);
  assert.ok(fs.existsSync(path.join(dataDir, 'через_канал', 'artist.json')));
  assert.ok(!fs.existsSync(path.join(project, 'data', 'artist_dossier', 'через_канал')));

  fs.rmSync(project, { recursive: true, force: true });
  fs.rmSync(dataDir, { recursive: true, force: true });
});

test('нечитаемая поставка не роняет окно: пусто и с причиной', () => {
  const userData = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-userdata-'));
  const plan = writable.prepareDossierStore({
    packaged: true,
    projectRoot: path.join(os.tmpdir(), 'zsmm-нет-такого-каталога'),
    userData,
  });
  assert.equal(plan.source, 'user');
  assert.deepEqual(plan.seeded, []);
  fs.rmSync(userData, { recursive: true, force: true });
});
