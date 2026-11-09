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

test('отменённый рендер показывается как отмена, а не как ошибка', async (t) => {
  // Мост отвечает так же, как главный процесс после отмены: рендер не удался,
  // но по вине пользователя. Окно не должно ругаться красной плашкой.
  const bridge = {
    ...realBridge(),
    renderBeat: async () => ({ ok: false, cancelled: true, error: 'рендер отменён' }),
    cancelBeat: async () => ({ ok: true, data: { cancelled: false } }),
    onBeatProgress: () => () => {},
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

  const render = document.getElementById('beat-render');
  render.dispatch('click');
  await flush();
  await flush();

  const status = document.getElementById('beat-status').textContent;
  assert.match(status, /отменён/i, `состояние после отмены: ${status}`);
  assert.doesNotMatch(status, /не собран/i);
  // Сохранять нечего: отменённый WAV на диск не писался.
  assert.equal(document.getElementById('beat-save').disabled, true);
  // Кнопка рендера снова доступна — иначе окно «залипло» бы после отмены.
  assert.equal(render.disabled, false);
});

test('справка называет отмену рендера и одно окно', async (t) => {
  const { document } = bootWindow({ bridge: realBridge() });
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'help');
  button.dispatch('click');
  await flush();
  await flush();

  const text = document.getElementById('help-body').textContent;
  // Обещания интерфейса должны совпадать с тем, что он умеет.
  assert.match(text, /Отмена рендера/);
  assert.match(text, /Одно окно/);
  // Метаданные EXE теперь заполняются, а подписи кода нет: ограничение
  // названо именно так, иначе раздел обещал бы старую проблему.
  assert.doesNotMatch(text, /Свойства файла EXE/, 'свойства файла больше не ограничение');
  assert.match(text, /Подпись кода/);
  assert.match(text, /SmartScreen/);
  assert.match(text, /Мгновенная отмена/, 'задержка отмены должна быть названа');
});

test('в блоке вокала есть запись с микрофона и честная подпись', async (t) => {
  // Мост с рендером: без него раздел «Бит» честно говорит «вне Electron» и
  // до проверки режима вокала дело не доходит.
  const bridge = realBridge();
  bridge.beatBank = async () => ({
    ok: true,
    data: { status: 'REAL_PASS', total_samples: 32, instruments_with_samples: ['kick'] },
  });
  bridge.loadSettings = async () => ({ ok: true, data: {} });
  bridge.saveSettings = async () => ({ ok: true, data: {} });
  bridge.vocalInput = async () => ({ ok: true, data: { recording: true, available: null } });

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

  // Кнопки записи на месте, режим выбирается.
  const mode = document.getElementById('vocal-mode');
  assert.ok(mode, 'нет выбора режима вокала');
  assert.ok(document.getElementById('vocal-record'), 'нет кнопки «Записать дубль»');
  assert.ok(document.getElementById('vocal-stop'), 'нет кнопки «Остановить запись»');
  // Кнопка «Записать дубль» доступна только в режиме записи: иначе она
  // обещала бы действие, которое никуда не попадёт.
  assert.equal(document.getElementById('vocal-record').disabled, true);
  assert.equal(document.getElementById('vocal-stop').disabled, true, 'стоп без записи не нужен');

  // Без записанного дубля рендер не притворяется, что вокал есть: он
  // называет причину, а не собирает трек молча.
  // В режиме «запись» без дубля окно не собирает трек молча: оно бросает
  // ошибку с просьбой записать дубль — её и показывает подпись.
  mode.value = 'record';
  assert.throws(() => window.ZSMM_UI.vocalOptions(), /запишите дубль/i);

  // Подпись под блоком помнит, что запись — это микрофон, а не имитация.
  const note = document.getElementById('vocal-note');
  assert.ok(note, 'нет подписи под блоком вокала');
});
