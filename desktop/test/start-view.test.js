'use strict';
/**
 * Стартовый раздел: запомненный или выбранный человеком.
 *
 * Здесь ловится гонка, которую видно только руками: настройки читаются с
 * диска не мгновенно, и человек успевает нажать раздел сам. Раньше поздний
 * ответ `loadSettings` переключал окно на раздел из прошлого запуска — человек
 * видел, что его нажатие отменили. Теперь выбор, сделанный до конца чтения,
 * главнее запомненного.
 *
 * Мост в тесте держит `loadSettings` на защёлке: без неё гонки не создать.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { bootWindow } = require('./fake-dom');

const SRC = path.resolve(__dirname, '..', 'src');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

const flush = () => new Promise((resolve) => setImmediate(resolve));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function ready(window) {
  for (let i = 0; i < 100; i += 1) {
    await flush();
    await sleep(5);
    if (window.ZSMM_UI && window.ZSMM_UI.ready) return;
  }
  throw new Error('окно не дошло до стартового раздела');
}

function bridge({ view, gate }) {
  const data = (value) => async () => ({ ok: true, data: value });
  return {
    version: data({ version: 'test' }),
    genres: data([]),
    modules: data([]),
    readiness: data({}),
    dossiers: data({ artists: [] }),
    system: data({}),
    saveSettings: async () => ({ ok: true }),
    // Диск отвечает не сразу — как настоящий файл настроек.
    loadSettings: async () => {
      if (gate) await gate;
      return { ok: true, data: { view } };
    },
    listTasks: async () => ({ ok: true, data: [] }),
  };
}

function clean() {
  delete global.window;
  delete global.document;
}

test('запомненный раздел открывается, когда человек ничего не нажимал', async (t) => {
  const { document, window } = bootWindow({
    srcDir: SRC, html: HTML, bridge: bridge({ view: 'tracks' }),
  });
  t.after(clean);
  await ready(window);
  assert.equal(document.getElementById('view-title').textContent, 'Треки');
});

test('выбор человека до конца чтения настроек не откатывается', async (t) => {
  let release = null;
  const gate = new Promise((resolve) => { release = resolve; });
  const { document, window } = bootWindow({
    srcDir: SRC, html: HTML, bridge: bridge({ view: 'tracks', gate }),
  });
  t.after(clean);

  // Настройки ещё читаются, а человек уже нажал «Справку».
  const help = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'help');
  help.dispatch('click');
  await flush();
  await flush();
  assert.equal(document.getElementById('view-title').textContent, 'Справка');

  // Диск ответил «Треки» — но нажатие уже было, окно обязано остаться.
  release();
  await ready(window);
  assert.equal(document.getElementById('view-title').textContent, 'Справка');
  assert.equal(window.ZSMM_UI.state.view, 'help');
  // И в настройки уходит именно выбор человека, а не прошлый раздел.
  assert.equal(window.ZSMM_UI.state.settings.view, 'help');
});

test('стартовое переключение не считается выбором человека', async (t) => {
  const { document, window } = bootWindow({
    srcDir: SRC, html: HTML, bridge: bridge({ view: 'health' }),
  });
  t.after(clean);
  await ready(window);
  // Автоматический старт не закрепляет раздел: следующий выбор работает.
  assert.equal(window.ZSMM_UI.state.pinned, null);
  assert.equal(document.getElementById('view-title').textContent, 'Диагностика');
});
