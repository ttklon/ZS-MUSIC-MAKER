'use strict';
/**
 * Раздел «Треки»: окно ведёт досье артиста само, без Python.
 *
 * Проверяется то, что легко сломать незаметно: список артистов заполняется,
 * трек добавляется с текстом, статус честно «не разобран», а отказ сервиса
 * виден человеку. Всё пишется во временный каталог — репозиторий не трогается.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { documentFromHtml, bootWindow: bootDocumentWindow } = require('./fake-dom');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');
const dossier = require('../src/core/dossier-edit');
const dossierTracks = require('../src/core/dossier-tracks');

const SRC = path.resolve(__dirname, '..', 'src');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

const flush = () => new Promise((resolve) => setImmediate(resolve));

/** Корень с двумя артистами: реальный dossier-edit в temp-каталоге. */
function makeRoot() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-views-tracks-'));
  fs.mkdirSync(path.join(root, 'data', 'artist_dossier'), { recursive: true });
  dossier.addArtist(createNodeFs(), root, { artist: 'Первый Артист' });
  dossier.addArtist(createNodeFs(), root, { artist: 'Второй Артист' });
  dossierTracks.addTrack(createNodeFs(), root, { slug: 'первый_артист', title: 'Уже есть' });
  return root;
}

function bridge(root) {
  const fsApi = createNodeFs();
  const project = createProject(fsApi, root);
  const wrap = (loader) => async () => ({ ok: true, data: loader() });
  return {
    version: wrap(() => project.version()),
    genres: wrap(() => project.genres()),
    modules: wrap(() => project.modules()),
    readiness: wrap(() => project.readiness()),
    dossiers: wrap(() => project.dossiers()),
    system: wrap(() => project.systemInfo()),
    dossierTracks: async (slug) => ({
      ok: true,
      data: { slug, ...dossierTracks.listTracks(fsApi, root, slug) },
    }),
    dossierTrackAdd: async (payload) => dossierTracks.addTrack(fsApi, root, payload),
    dossierAdd: async (payload) => dossier.addArtist(fsApi, root, payload),
    dossierRemove: async (payload) => dossier.removeArtist(fsApi, root, payload),
  };
}

function openTracks(api) {
  const { document } = bootDocumentWindow({ srcDir: SRC, html: HTML, bridge: api });
  return { document, button: [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'tracks') };
}

test('в навигации есть раздел «Треки» и он показывает артистов', async (t) => {
  const root = makeRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { document, button } = openTracks(bridge(root));
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  assert.ok(button, 'нет пункта навигации «Треки»');
  button.dispatch('click');
  await flush();
  await flush();

  const select = document.getElementById('tracks-artist');
  assert.deepEqual(
    select.children.map((option) => option.value),
    ['второй_артист', 'первый_артист'],
  );
  // По умолчанию выбран первый артист списка — у него треков нет, и это
  // сказано текстом, а не пустым списком без объяснения.
  assert.match(document.getElementById('tracks-status').textContent, /треков пока нет/);

  // Переключение артиста перечитывает его треки: у первого они есть.
  document.getElementById('tracks-artist').value = 'первый_артист';
  document.getElementById('tracks-artist').dispatch('change');
  await flush();
  await flush();
  assert.match(document.getElementById('tracks-status').textContent, /Треков: 1/);
  assert.match(document.getElementById('tracks-list').textContent, /Уже есть/);
});

test('трек добавляется из окна: текст сохраняется, статус честный', async (t) => {
  const root = makeRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { document, button } = openTracks(bridge(root));
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  button.dispatch('click');
  await flush();
  await flush();

  document.getElementById('tracks-artist').value = 'второй_артист';
  document.getElementById('tracks-artist').dispatch('change');
  await flush();
  await flush();
  // У второго артиста треков нет — так и написано.
  assert.match(document.getElementById('tracks-status').textContent, /треков пока нет/);

  document.getElementById('tracks-title').value = 'Новый Трек';
  document.getElementById('tracks-url').value = 'https://example.com/t';
  document.getElementById('tracks-lyrics').value = 'строка текста';
  document.getElementById('tracks-add').dispatch('click');
  await flush();
  await flush();

  const stored = JSON.parse(fs.readFileSync(
    path.join(root, 'data', 'artist_dossier', 'второй_артист', 'tracks', `${dossierTracks.trackId('Новый Трек', 'https://example.com/t')}.json`),
    'utf8',
  ));
  assert.equal(stored.title, 'Новый Трек');
  assert.equal(stored.status, 'pending', 'разбор не выполнялся — статус не может быть analyzed');
  assert.equal(stored.lyrics, 'строка текста');
  assert.ok(fs.existsSync(path.join(root, 'data', 'artist_dossier', 'второй_артист', 'lyrics')));

  const list = document.getElementById('tracks-list').textContent;
  assert.match(list, /Новый Трек/);
  assert.match(list, /не разобран/);
  assert.match(document.getElementById('tracks-status').textContent, /Треков: 1/);
  assert.equal(document.getElementById('tracks-title').value, '', 'форма очищена после успеха');
});

test('повтор трека и пустое название дают текст, а не тишину', async (t) => {
  const root = makeRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { document, button } = openTracks(bridge(root));
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  button.dispatch('click');
  await flush();
  await flush();

  document.getElementById('tracks-artist').value = 'первый_артист';
  document.getElementById('tracks-add').dispatch('click');
  await flush();
  await flush();
  assert.match(document.getElementById('error-banner').textContent, /название/i);

  document.getElementById('tracks-title').value = 'Уже есть';
  document.getElementById('tracks-add').dispatch('click');
  await flush();
  await flush();
  assert.match(document.getElementById('error-banner').textContent, /уже есть/);
  // Форма не очищена: человек должен видеть, что именно он ввёл.
  assert.equal(document.getElementById('tracks-title').value, 'Уже есть');
});

test('из «Досье» кнопка «Треки» открывает треки нужного артиста', async (t) => {
  const root = makeRoot();
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const { document } = bootDocumentWindow({ srcDir: SRC, html: HTML, bridge: bridge(root) });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();

  const dossierButton = [...document.querySelectorAll('[data-view]')]
    .find((b) => b.dataset.view === 'dossiers');
  dossierButton.dispatch('click');
  await flush();
  await flush();

  // У каждого артиста две кнопки: «Треки» и «Собрать досье».
  const items = document.getElementById('dossier-list').children;
  assert.ok(items.length >= 2);
  const target = items.find((item) => /Первый Артист/.test(item.textContent));
  assert.ok(target, 'нет строки артиста');
  const tracksButton = target.children.find((child) => child.textContent === 'Треки');
  assert.ok(tracksButton, 'нет кнопки «Треки» у артиста');
  tracksButton.dispatch('click');
  await flush();
  await flush();

  // Открылся раздел «Треки» и выбран именно этот артист.
  assert.equal(document.getElementById('view-title').textContent, 'Треки');
  assert.equal(document.getElementById('tracks-artist').value, 'первый_артист');
  assert.match(document.getElementById('tracks-list').textContent, /Уже есть/);
});
