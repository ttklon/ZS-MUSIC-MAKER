'use strict';
/**
 * app.js — точка входа окна: состояние, общие помощники, навигация.
 *
 * Разделы вынесены в `sections/*.js`: каждый — одна функция загрузки. Так
 * файл остаётся читаемым, а раздел можно менять, не читая остальные.
 *
 * Порядок подключения важен: `sections/*.js` используют `W.$`, `W.el`,
 * `W.ask` из этого файла, а `app.js` зовёт их загрузчики уже в конце.
 *
 * Данные приходят из preload (`window.zsmm.*`), который спрашивает главный
 * процесс. Никаких сетевых запросов и никакого Python. Если раздела нет или
 * файл не прочитан — показывается причина из `error`, а не пустой экран.
 */

/** Пространство имён окна: сюда пишут все скрипты, отсюда читают. */
const W = (window.ZSMM_UI = window.ZSMM_UI || {});

const state = {
  view: 'overview',
  genres: [],
  loaded: new Set(),
  tasks: [],
  taskRunning: false,
  taskLines: [],
  beat: null,
  beatReport: null,
  settingsTimer: null,
};
W.state = state;

const $ = (id) => document.getElementById(id);
W.$ = $;

function showError(message) {
  const banner = $('error-banner');
  banner.textContent = message;
  banner.classList.remove('is-hidden');
  window.clearTimeout(showError._timer);
  showError._timer = window.setTimeout(() => banner.classList.add('is-hidden'), 9000);
}
W.showError = showError;

function setStatus(ok, label) {
  const dot = $('backend-dot');
  dot.classList.toggle('is-ok', ok === true);
  dot.classList.toggle('is-bad', ok === false);
  $('backend-state').textContent = label;
}
W.setStatus = setStatus;

const BRIDGE_MISSING = 'window.zsmm недоступен: окно открыто вне Electron';

/** Единая обёртка: успех → data, ошибка → исключение с текстом причины. */
async function ask(section) {
  if (!window.zsmm || typeof window.zsmm[section] !== 'function') {
    setStatus(false, 'мост не подключён');
    throw new Error(BRIDGE_MISSING);
  }
  const reply = await window.zsmm[section]();
  if (!reply || reply.ok !== true) {
    setStatus(false, 'ошибка');
    throw new Error((reply && reply.error) || 'нет ответа');
  }
  setStatus(true, 'проект открыт');
  return reply.data;
}
W.ask = ask;

/**
 * Как `ask`, но с аргументом: каналы, которые что-то меняют (добавить
 * артиста, удалить), принимают объект и отвечают `{ok, data|error}`.
 */
async function askWith(section, payload) {
  if (!window.zsmm || typeof window.zsmm[section] !== 'function') {
    setStatus(false, 'мост не подключён');
    throw new Error(BRIDGE_MISSING);
  }
  const reply = await window.zsmm[section](payload);
  if (!reply || reply.ok !== true) throw new Error((reply && reply.error) || 'нет ответа');
  return reply.data;
}
W.askWith = askWith;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}
W.el = el;

function card(label, value, hint) {
  const box = el('div', 'card');
  box.append(el('div', 'card-label', label), el('div', 'card-value', value), el('div', 'card-hint', hint));
  return box;
}
W.card = card;

function statusTag(status) {
  const kind =
    status === 'REAL_PASS' ? 'ok' : status === 'DEPRECATED' || status === 'PLANNED' ? 'warn' : 'bad';
  return el('span', `tag ${kind}`, status);
}
W.statusTag = statusTag;

// ----------------------------------------------------------- навигация
// Загрузчики берутся из разделов: `sections/*.js` уже выполнились, потому
// что подключены раньше этого файла.

const LOADERS = {
  overview: () => W.loadOverview(),
  modules: () => W.loadModules(),
  genres: () => W.loadGenres(),
  beat: () => W.loadBeat(),
  dossiers: () => W.loadDossiers(),
  run: () => W.loadRun(),
  health: () => W.loadHealth(),
  help: () => W.loadHelp(),
};

const TITLES = {
  overview: 'Обзор',
  modules: 'Модули',
  genres: 'Жанры',
  beat: 'Бит',
  dossiers: 'Досье',
  run: 'Запуск',
  health: 'Диагностика',
  help: 'Справка',
};

async function switchView(view, { force = false } = {}) {
  if (!LOADERS[view]) return;
  state.view = view;
  $('view-title').textContent = TITLES[view];
  for (const button of document.querySelectorAll('.nav-item')) {
    button.classList.toggle('is-active', button.dataset.view === view);
  }
  for (const name of Object.keys(LOADERS)) {
    $(`view-${name}`).classList.toggle('is-hidden', name !== view);
  }
  if (force || !state.loaded.has(view)) {
    try {
      await LOADERS[view]();
      state.loaded.add(view);
    } catch (err) {
      showError(`${TITLES[view]}: ${err.message}`);
    }
  }
}

function wire() {
  for (const button of document.querySelectorAll('.nav-item')) {
    button.addEventListener('click', () => switchView(button.dataset.view));
  }
  $('refresh').addEventListener('click', async () => {
    state.loaded.clear();
    await switchView(state.view, { force: true });
  });
  $('genre-filter').addEventListener('input', () => W.renderGenres && W.renderGenres());
  $('module-filter').addEventListener('input', () => {
    if (state.loaded.has('modules')) {
      W.loadModules().catch((err) => showError(err.message));
    }
  });
  $('reveal').addEventListener('click', async () => {
    const result = await window.zsmm.revealRoot();
    if (!result || result.ok !== true) showError(`Не удалось открыть папку: ${result && result.error}`);
  });
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    wire();
    switchView('overview');
  });
}

if (typeof module !== 'undefined' && module.exports) {
  // Для тестов: состояние, названия разделов и переход между ними.
  module.exports = { state, TITLES, LOADERS, switchView, W };
}
