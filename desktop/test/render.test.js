'use strict';
/**
 * Проверка, что окно действительно рисует данные: `app.js` исполняется в
 * DOM-двойнике с мостом, который отдаёт НАСТОЯЩИЕ данные проекта.
 *
 * Это не замена ручному запуску Electron (его в этом окружении нет — нет
 * графических библиотек), но именно здесь ловятся ошибки вроде «обращение к
 * null» или «раздел остался пустым». Ограничение записано честно.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { documentFromHtml, windowScripts } = require('./fake-dom');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const SRC = path.resolve(__dirname, '..', 'src');
const ROOT = path.resolve(__dirname, '..', '..');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

/** Загрузить app.js в поддельный документ с указанным мостом. */
function bootWindow({ bridge }) {
  const document = documentFromHtml(HTML);
  const window = document.createElement('window');
  window.zsmm = bridge;

  const timers = [];
  global.window = window;
  global.document = document;
  global.setTimeout = (fn, ms) => {
    timers.push({ fn, ms });
    return timers.length;
  };
  global.clearTimeout = () => {};
  window.setTimeout = global.setTimeout;
  window.clearTimeout = global.clearTimeout;

  // Скрипты окна — классические: исполняем их по порядку, как браузер.
  for (const script of windowScripts(SRC)) {
    // eslint-disable-next-line no-new-func
    new Function('window', 'document', 'setTimeout', 'clearTimeout', script.source)(
      window,
      document,
      global.setTimeout,
      global.clearTimeout,
    );
  }
  document.dispatch('DOMContentLoaded');
  return { document, window };
}

function realBridge() {
  const project = createProject(createNodeFs(), ROOT);
  const wrap = (loader) => async () => {
    try {
      return { ok: true, data: loader() };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  };
  return {
    version: wrap(() => project.version()),
    genres: wrap(() => project.genres()),
    modules: wrap(() => project.modules()),
    readiness: wrap(() => project.readiness()),
    dossiers: wrap(() => project.dossiers()),
    system: wrap(() => project.systemInfo()),
    revealRoot: async () => ({ ok: true }),
  };
}

const flush = () => new Promise((resolve) => setImmediate(resolve));

test('окно рисует обзор из настоящих данных проекта', async (t) => {
  const { document } = bootWindow({ bridge: realBridge() });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  await flush();

  assert.equal(document.getElementById('version').textContent.startsWith('v'), true);
  const cards = document.getElementById('overview-cards').children;
  assert.equal(cards.length, 4, 'четыре карточки обзора');

  const readinessNote = document.getElementById('readiness-note').textContent;
  assert.match(readinessNote, /потолк|Потолков|устарел|снимок/i);

  const caps = document.getElementById('caps').children;
  const readiness = createProject(createNodeFs(), ROOT).readiness();
  assert.equal(caps.length, (readiness.capsTriggered || []).length);
});

test('переключение на «Модули» заполняет таблицу', async (t) => {
  const { document } = bootWindow({ bridge: realBridge() });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'modules');
  button.dispatch('click');
  await flush();
  await flush();

  const rows = document.getElementById('modules-body').children;
  const expected = createProject(createNodeFs(), ROOT).modules();
  assert.equal(rows.length, expected.rows.length);
  assert.match(document.getElementById('modules-summary').textContent, /модул/);
});

test('ошибка моста показывается, а не прячется', async (t) => {
  const bridge = realBridge();
  bridge.readiness = async () => ({ ok: false, error: 'снимок не найден' });
  const { document } = bootWindow({ bridge });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  await flush();

  const banner = document.getElementById('error-banner');
  assert.equal(banner.classList.contains('is-hidden'), false, 'баннер обязан быть виден');
  assert.match(banner.textContent, /снимок не найден/);
  // панель обзора грузится параллельно: причина обязана быть либо в ней,
  // либо в баннере — но не исчезнуть совсем
  const note = document.getElementById('readiness-note').textContent;
  assert.ok(/снимок не найден/.test(note) || /снимок не найден/.test(banner.textContent));
});

test('без моста окно говорит об этом прямо', async (t) => {
  const { document } = bootWindow({ bridge: {} });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  await flush();

  const banner = document.getElementById('error-banner');
  assert.match(banner.textContent, /window\.zsmm недоступен/);
  assert.match(document.getElementById('backend-state').textContent, /не подключён/);
});

test('фильтр жанров работает без повторной загрузки', async (t) => {
  const { document } = bootWindow({ bridge: realBridge() });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'genres');
  button.dispatch('click');
  await flush();
  await flush();

  const before = document.getElementById('genre-list').children.length;
  assert.ok(before > 100);

  const filter = document.getElementById('genre-filter');
  filter.value = 'phonk';
  filter.dispatch('input');

  const after = document.getElementById('genre-list').children.length;
  assert.ok(after < before && after > 0, `фильтр не сузил список: ${before} → ${after}`);
});

test('справка перечисляет и возможности, и ограничения', async (t) => {
  const { document } = bootWindow({ bridge: realBridge() });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'help');
  assert.ok(button, 'нет пункта навигации «Справка»');
  button.dispatch('click');
  await flush();
  await flush();

  const text = document.getElementById('help-body').textContent;
  assert.match(text, /Что действительно работает/);
  assert.match(text, /Чего здесь нет/);
  // Обещание, которое нельзя проверить, в справке — это ложь интерфейса.
  assert.match(text, /Подпись кода/, 'ограничение SmartScreen должно быть названо');
});

test('кнопка «Отменить» доступна только во время рендера', async (t) => {
  let cancelledCalls = 0;
  const bridge = {
    ...realBridge(),
    cancelBeat: async () => {
      cancelledCalls += 1;
      return { ok: true, data: { cancelled: true } };
    },
  };
  const { document } = bootWindow({ bridge });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'beat');
  button.dispatch('click');
  await flush();
  await flush();

  const cancel = document.getElementById('beat-cancel');
  assert.equal(cancel.disabled, true, 'до рендера отменять нечего');

  // Клик по заблокированной кнопке ничего не отправляет: иначе окно
  // показывало бы «отменяю» там, где рендер даже не начинался.
  cancel.dispatch('click');
  await flush();
  assert.equal(cancelledCalls, 0);
});
