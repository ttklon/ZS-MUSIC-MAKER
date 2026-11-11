'use strict';
/**
 * Фокус после переключения раздела.
 *
 * Фокус остаётся на кнопке в боковой панели, а прокрутка клавишами идёт от
 * фокуса: в настоящем Chromium `PageDown` не двигал справку вовсе (0 px при
 * высоте содержимого 1526 px). Тест держит поведение, которое это лечит:
 * после переключения активный элемент — заголовок раздела, и он не попадает
 * в обход Tab (`tabindex="-1"`).
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { bootWindow } = require('./fake-dom');

const SRC = path.resolve(__dirname, '..', 'src');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

const flush = () => new Promise((resolve) => setImmediate(resolve));

/** Подождать, пока стартовое переключение окна закончится. */
async function ready(window) {
  for (let i = 0; i < 50; i += 1) {
    await flush();
    await new Promise((resolve) => setTimeout(resolve, 5));
    if (window.W && window.W.ready) return;
  }
}

/** Мост-заглушка: разделы рисуются, но данные пустые — важен только фокус. */
function bridge() {
  const data = (value) => async () => ({ ok: true, data: value });
  return {
    version: data({ version: 'test' }),
    genres: data([]),
    modules: data([]),
    readiness: data({}),
    dossiers: data({ artists: [] }),
    system: data({}),
    saveSettings: async () => ({ ok: true }),
    loadSettings: async () => ({ ok: true, data: { view: 'overview' } }),
    listTasks: async () => ({ ok: true, data: [] }),
  };
}

async function open() {
  const { document, window } = bootWindow({ srcDir: SRC, html: HTML, bridge: bridge() });
  await ready(window);
  return { document, window };
}

test('после переключения раздела фокус уходит из меню в заголовок', async (t) => {
  const { document } = await open();
  t.after(() => {
    delete global.window;
    delete global.document;
  });

  const nav = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'modules');
  nav.dispatch('click');
  await flush();

  const title = document.getElementById('view-title');
  assert.equal(document.activeElement, title, 'фокус остался в меню — PageDown не прокрутит раздел');
  assert.equal(title.textContent, 'Модули');
});

test('фокус переносится при каждом переключении, а не только при первом', async (t) => {
  const { document } = await open();
  t.after(() => {
    delete global.window;
    delete global.document;
  });

  const buttons = [...document.querySelectorAll('[data-view]')];
  const help = buttons.find((b) => b.dataset.view === 'help');
  help.dispatch('click');
  await flush();
  await flush();
  assert.equal(document.activeElement, document.getElementById('view-title'));
  assert.equal(document.getElementById('view-title').textContent, 'Справка');

  // Переключение из раздела в раздел по-прежнему возвращает фокус заголовку:
  // в длинной справке человек оказывается в её начале, а не там, где стоял.
  buttons.find((b) => b.dataset.view === 'genres').dispatch('click');
  await flush();
  assert.equal(document.activeElement, document.getElementById('view-title'));
  assert.equal(document.getElementById('view-title').textContent, 'Жанры');
});

test('заголовок принимает фокус, но не попадает в обход Tab', async () => {
  const { document } = await open();
  try {
    const title = document.getElementById('view-title');
    // `-1` — фокус только программный: иначе Tab после переключения встал бы
    // на заголовок и человек не дошёл бы до полей раздела.
    assert.equal(title.getAttribute('tabindex'), '-1');
    assert.equal(title.tabIndex, -1);
  } finally {
    delete global.window;
    delete global.document;
  }
});
