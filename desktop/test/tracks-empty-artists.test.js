'use strict';
/**
 * Раздел «Треки» на свежей установке: артистов ещё нет, а кнопки уже живые.
 *
 * Дефект: `loadTracks` выходил по `return`, если список артистов пуст, — и
 * навешивание обработчиков оставалось ниже этой строки. На чистой установке
 * человек видел предупреждение «Артистов нет», но кнопка «Добавить» не
 * реагировала ни на что до тех пор, пока он не заводил артиста в «Досье» и не
 * перезапускал раздел. Кнопка, которая молчит без причины, читается как
 * «программа сломалась», хотя причина рядом.
 *
 * Проверяется: обработчик навешен при пустом списке, отказ объяснён причиной
 * и форма не очищается, а после появления артиста добавление работает.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { bootWindow } = require('./fake-dom');

const SRC = path.resolve(__dirname, '..', 'src');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

/** Мост раздела «Треки»: управляемый список артистов и журнал добавлений. */
function bridge({ artists = [], added = [] } = {}) {
  return {
    added,
    artists,
    loadSettings: async () => ({ ok: true, data: {} }),
    saveSettings: async () => ({ ok: true, data: {} }),
    dossiers: async () => ({ ok: true, data: { artists: artists.slice(), error: null } }),
    dossierTracks: async (slug) => ({ ok: true, data: { slug, tracks: [], errors: [] } }),
    dossierTrackAdd: async (payload) => {
      added.push(payload);
      return { ok: true, data: { slug: payload.slug, title: payload.title } };
    },
  };
}

async function bootTracks(options) {
  const built = bridge(options);
  const { document, window } = bootWindow({ srcDir: SRC, html: HTML, bridge: built });
  await window.ZSMM_UI.switchView('tracks');
  await new Promise((resolve) => { setTimeout(resolve, 60); });
  return { document, window, bridge: built };
}

async function press(document, id) {
  const node = document.getElementById(id);
  assert.ok(node, `в разметке нет #${id}`);
  const listeners = node.listeners.get('click') || [];
  for (const listener of listeners) await listener({ target: node });
  return listeners.length;
}

test('при пустом списке артистов «Добавить» отвечает причиной, а не молчит', async () => {
  const { document, bridge: built } = await bootTracks({ artists: [] });

  // Раздел честно говорит, что заводить артиста негде.
  assert.match(document.getElementById('tracks-status').textContent, /Артистов нет/);

  const listeners = document.getElementById('tracks-add').listeners.get('click') || [];
  assert.ok(listeners.length > 0, 'кнопка «Добавить» должна быть подключена даже без артистов');

  document.getElementById('tracks-title').value = 'Проба';
  await press(document, 'tracks-add');

  assert.equal(built.added.length, 0, 'без артиста трек не уходит в главный процесс');
  assert.match(
    document.getElementById('error-text').textContent,
    /выберите артиста|Артистов нет/i,
    'отказ назван причиной',
  );
  // Форму не чистим: человек не должен заново печатать название.
  assert.equal(document.getElementById('tracks-title').value, 'Проба');
});

test('пустое название не отправляется, а объясняется', async () => {
  const { document, bridge: built } = await bootTracks({
    artists: [{ slug: 'demo', artist: 'Демо' }],
  });

  await press(document, 'tracks-add');
  assert.equal(built.added.length, 0);
  assert.match(document.getElementById('error-text').textContent, /название/i);
});

test('когда артист есть, трек добавляется и форма очищается', async () => {
  const { document, bridge: built } = await bootTracks({
    artists: [{ slug: 'demo', artist: 'Демо' }],
  });

  document.getElementById('tracks-title').value = 'Проверочный трек';
  document.getElementById('tracks-lyrics').value = 'первая строка\nвторая строка';
  await press(document, 'tracks-add');

  assert.equal(built.added.length, 1, 'трек ушёл в главный процесс');
  assert.equal(built.added[0].title, 'Проверочный трек');
  assert.match(built.added[0].lyrics, /первая строка/);
  assert.equal(document.getElementById('tracks-title').value, '', 'после успеха поле очищено');
});

test('обработчики навешиваются один раз, даже если раздел открывали дважды', async () => {
  const { document, window, bridge: built } = await bootTracks({
    artists: [{ slug: 'demo', artist: 'Демо' }],
  });
  await window.ZSMM_UI.switchView('tracks', { force: true });
  await new Promise((resolve) => { setTimeout(resolve, 60); });

  document.getElementById('tracks-title').value = 'Один раз';
  await press(document, 'tracks-add');

  assert.equal(built.added.length, 1, 'одно нажатие — одно добавление');
});
