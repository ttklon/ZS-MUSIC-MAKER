'use strict';
/**
 * test/dossier-edit.test.js — досье можно вести из окна, без Python.
 *
 * Проверяются оба направления: созданный артист лежит там, где его ждёт
 * Python-менеджер (`data/artist_dossier/<slug>/artist.json`), а удаление
 * не выходит за пределы каталога досье.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');
const dossier = require('../src/core/dossier-edit');
const { registerProjectIpc } = require('../electron/ipc-project');

function makeRoot() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-dossier-'));
  fs.mkdirSync(path.join(root, 'data', 'artist_dossier'), { recursive: true });
  return root;
}

test('slug совпадает по правилам с Python-менеджером', () => {
  assert.equal(dossier.slugify('Demo Artist'), 'demo_artist');
  assert.equal(dossier.slugify('  МС Тест  '), 'мс_тест');
  assert.equal(dossier.slugify('A/B:C'), 'a_b_c');
  assert.equal(dossier.slugify(''), '');
});

test('пустой каталог — не ошибка, а понятное состояние', () => {
  const root = makeRoot();
  const list = dossier.dossiers(createNodeFs(), root);
  assert.deepEqual(list.artists, []);
  assert.equal(list.error, null);
  fs.rmSync(root, { recursive: true, force: true });
});

test('артист добавляется в формате Python-менеджера', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  const added = dossier.addArtist(fsApi, root, { artist: 'Тест Артист', note: 'из окна' });
  assert.equal(added.ok, true, added.error);

  const file = path.join(root, 'data', 'artist_dossier', 'тест_артист', 'artist.json');
  assert.ok(fs.existsSync(file), 'artist.json не создан');
  const stored = JSON.parse(fs.readFileSync(file, 'utf8'));
  for (const key of ['artist', 'slug', 'added_at', 'updated_at', 'tracks', 'dossier']) {
    assert.ok(key in stored, `в записи нет поля ${key}`);
  }
  assert.equal(stored.artist, 'Тест Артист');
  assert.deepEqual(stored.tracks, []);

  const list = dossier.dossiers(fsApi, root);
  assert.equal(list.artists.length, 1);
  assert.equal(list.artists[0].artist, 'Тест Артист');
  assert.equal(list.artists[0].tracks, 0);
  assert.equal(list.artists[0].hasDossier, false);
  assert.equal(list.artists[0].note, 'из окна');
  fs.rmSync(root, { recursive: true, force: true });
});

test('окно создаёт ту же структуру каталога, что ждёт Python', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  const added = dossier.addArtist(fsApi, root, { artist: 'Структура' });
  assert.equal(added.ok, true, added.error);
  const dir = path.join(root, 'data', 'artist_dossier', 'структура');
  for (const sub of ['tracks', 'lyrics']) {
    assert.ok(fs.existsSync(path.join(dir, sub)), `нет каталога ${sub}/: Python-менеджер его ждёт`);
  }
  fs.rmSync(root, { recursive: true, force: true });
});

test('запись из окна читается правилами Python-формата', () => {
  // Файл пишет окно, а читает его и окно, и Python. Здесь проверяется
  // формальная сторона: только известные поля записи и `note` строкой, иначе
  // Python-менеджер (`ArtistEntry(**payload)`) не прочитает артиста.
  const root = makeRoot();
  const fsApi = createNodeFs();
  dossier.addArtist(fsApi, root, { artist: 'Формат', note: 'из окна' });
  const stored = JSON.parse(
    fs.readFileSync(path.join(root, 'data', 'artist_dossier', 'формат', 'artist.json'), 'utf8'),
  );
  for (const key of Object.keys(stored)) {
    assert.ok(
      ['artist', 'slug', 'added_at', 'updated_at', 'tracks', 'dossier', 'note'].includes(key),
      `лишнее поле в artist.json: ${key}`,
    );
  }
  assert.equal(typeof stored.note, 'string');
  assert.equal(typeof stored.added_at, 'number');
  fs.rmSync(root, { recursive: true, force: true });
});

test('повтор и слишком короткое имя отклоняются с текстом, а не молча', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  dossier.addArtist(fsApi, root, { artist: 'Демо' });
  const again = dossier.addArtist(fsApi, root, { artist: 'Демо' });
  assert.equal(again.ok, false);
  assert.match(again.error, /уже есть/);
  const short = dossier.addArtist(fsApi, root, { artist: 'Я' });
  assert.equal(short.ok, false);
  assert.match(short.error, /короче/);
  fs.rmSync(root, { recursive: true, force: true });
});

test('удаление убирает каталог артиста, но не схему', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  fs.writeFileSync(path.join(root, 'data', 'artist_dossier', 'schema.json'), '{}');
  dossier.addArtist(fsApi, root, { artist: 'Удаляемый' });
  const removed = dossier.removeArtist(fsApi, root, { slug: 'удаляемый' });
  assert.equal(removed.ok, true, removed.error);
  assert.ok(!fs.existsSync(path.join(root, 'data', 'artist_dossier', 'удаляемый')));
  assert.ok(fs.existsSync(path.join(root, 'data', 'artist_dossier', 'schema.json')), 'схема удалена');
  fs.rmSync(root, { recursive: true, force: true });
});

test('удаление не выходит за каталог досье', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  for (const slug of ['../..', 'a/b', '', 'схема.json']) {
    const result = dossier.removeArtist(fsApi, root, { slug });
    assert.equal(result.ok, false, `путь «${slug}» не должен удаляться`);
  }
  const outside = dossier.removeArtist(fsApi, root, { slug: path.resolve(root) });
  assert.equal(outside.ok, false);
  fs.rmSync(root, { recursive: true, force: true });
});

test('IPC досье отвечает {ok} и не бросает исключений', async () => {
  const root = makeRoot();
  const handlers = new Map();
  const ipcMain = { handle: (channel, fn) => handlers.set(channel, fn) };
  const registered = registerProjectIpc({
    ipcMain,
    getProject: () => null,
    root,
    fileSystem: createNodeFs(),
  });
  assert.ok(registered.includes('zsmm:dossier-add'));
  assert.ok(registered.includes('zsmm:dossier-remove'));

  const added = await handlers.get('zsmm:dossier-add')({}, { artist: 'Через IPC' });
  assert.equal(added.ok, true, added.error);
  const list = dossier.dossiers(createNodeFs(), root);
  assert.equal(list.artists[0].artist, 'Через IPC');

  const bad = await handlers.get('zsmm:dossier-add')({}, null);
  assert.equal(bad.ok, false, 'null-полезная нагрузка должна давать отказ');

  const removed = await handlers.get('zsmm:dossier-remove')({}, { slug: 'через_ipc' });
  assert.equal(removed.ok, true, removed.error);
  fs.rmSync(root, { recursive: true, force: true });
});

test('демо-артист из поставки читается и не мешает', () => {
  // В репозитории лежит data/artist_dossier/demo_artist — чтобы раздел не был
  // пустым на первом запуске. Тест держит формат этого файла.
  const root = path.resolve(__dirname, '..', '..');
  const list = dossier.dossiers(createNodeFs(), root);
  assert.ok(Array.isArray(list.artists));
  const demo = list.artists.find((artist) => artist.slug === 'demo_artist');
  assert.ok(demo, 'демо-артист пропал из поставки');
  assert.equal(demo.artist, 'Demo Artist');
  assert.equal(demo.demo, true, 'демо-артист должен быть помечен, а не выглядеть как настоящий');
  assert.ok(demo.note && demo.note.length > 0, 'у демо-артиста нет пояснения');
});
