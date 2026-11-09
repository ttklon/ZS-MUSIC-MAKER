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
// Разделы (`sections/*.js`) в браузере делят с этим файлом одну глобальную
// область, поэтому наружу каждый отдаёт ровно одно имя — сюда. Так видно,
// какие разделы действительно загрузились: если файл упал с ошибкой, его
// инициализатора тут не будет, и окно скажет об этом, а не покажет пустоту.
window.ZSMM_SECTIONS = {};

const state = {
  view: 'overview',
  genres: [],
  loaded: new Set(),
  tasks: [],
  taskRunning: false,
  taskLines: [],
  beat: null,
  // `blob:`-адрес готового WAV: нужен, чтобы освобождать его перед следующим
  // рендером. `data:`-адрес здесь не годится — его блокирует CSP окна.
  beatUrl: null,
  beatReport: null,
  settingsTimer: null,
};
W.state = state;

const $ = (id) => document.getElementById(id);
W.$ = $;

function showError(message) {
  const banner = $('error-banner');
  // Текст отдельным узлом: в баннере теперь ещё и кнопка закрытия, и
  // `textContent` на весь баннер стёр бы её.
  const text = $('error-text');
  text.textContent = message;
  banner.classList.remove('is-hidden');
  window.clearTimeout(showError._timer);
  showError._timer = window.setTimeout(() => hideError(), 9000);
}

function hideError() {
  window.clearTimeout(showError._timer);
  $('error-banner').classList.add('is-hidden');
}

W.hideError = hideError;
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
 *
 * Вызывающий код при этом ждёт `{ok, data|error}` — как у `window.zsmm.*`:
 * у `ask` ошибка летит исключением, а у правки данных вызывающему нужен и
 * текст ошибки, и признаки вроде `cancelled`. Смешивать два вида ответа в
 * одном помощнике — значит получить тихую ошибку в каждом втором месте.
 */
async function askWith(section, payload) {
  if (!window.zsmm || typeof window.zsmm[section] !== 'function') {
    setStatus(false, 'мост не подключён');
    throw new Error(BRIDGE_MISSING);
  }
  return window.zsmm[section](payload);
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

/**
 * Base64 → `Blob` для проигрывания.
 *
 * `data:audio/wav;base64,…` в адресе плеера **не работает в собранном
 * приложении**: CSP окна (`default-src 'self'`) блокирует такие источники, и
 * кнопка «Слушать» молча ничего не играла — это видел только настоящий
 * браузер, DOM-двойник CSP не применяет. `blob:` разрешён отдельной
 * директивой `media-src`, а сеть остаётся закрытой: `connect-src 'none'`.
 *
 * @param {string} base64
 * @param {string} mime
 * @returns {string} адрес для `audio.src`
 */
function blobUrl(base64, mime = 'audio/wav') {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return URL.createObjectURL(new Blob([bytes], { type: mime }));
}

/**
 * Запустить разделы: один сломанный файл не должен ронять остальные.
 *
 * `init` каждого раздела регистрирует свои загрузчики в `W`. Если скрипт
 * упал при разборе, инициализатора не будет — и это лучше видно причиной,
 * чем пустой панелью.
 */
function bootSections() {
  const sections = window.ZSMM_SECTIONS || {};
  const missing = [];
  for (const [name, init] of Object.entries(sections)) {
    try {
      init();
    } catch (err) {
      missing.push(`${name}: ${(err && err.message) || 'ошибка'}`);
    }
  }
  return missing;
}

const LOADERS = {
  overview: () => W.loadOverview(),
  modules: () => W.loadModules(),
  genres: () => W.loadGenres(),
  beat: () => W.loadBeat(),
  dossiers: () => W.loadDossiers(),
  tracks: () => W.loadTracks(),
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
  tracks: 'Треки',
  run: 'Запуск',
  health: 'Диагностика',
  help: 'Справка',
};

/**
 * Запомнить раздел.
 *
 * `saveSettings` в главном процессе сливает переданное с тем, что уже лежит
 * на диске, поэтому частичная запись не затирает жанр, темп и размер окна.
 * Пишется без ожидания: смена раздела не должна ждать диск, а об ошибке
 * сообщать нечего — при следующем запуске просто откроется «Обзор».
 */
function rememberView(view) {
  if (state.settings) state.settings.view = view;
  if (window.zsmm && typeof window.zsmm.saveSettings === 'function') {
    window.zsmm.saveSettings({ view }).catch(() => {});
  }
}

async function switchView(view, { force = false } = {}) {
  if (!LOADERS[view]) return;
  state.view = view;
  rememberView(view);
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

// Раздел «Бит» должен быть доступен из других разделов (жанр → бит), поэтому
// переключение отдаётся через общий объект, как и остальные помощники.
W.switchView = switchView;
W.blobUrl = blobUrl;

function wire() {
  for (const button of document.querySelectorAll('.nav-item')) {
    button.addEventListener('click', () => switchView(button.dataset.view));
  }
  $('refresh').addEventListener('click', async () => {
    state.loaded.clear();
    await switchView(state.view, { force: true });
  });
  // Сообщение об ошибке можно закрыть рукой, не дожидаясь таймера.
  $('error-close').addEventListener('click', () => hideError());
  $('genre-filter').addEventListener('input', () => W.renderGenres && W.renderGenres());
  // Фильтр модулей перерисовывает уже загруженный список: каждый символ не
  // должен заново читать inventory.md (300 строк) с диска.
  $('module-filter').addEventListener('input', () => {
    if (state.loaded.has('modules') && typeof W.renderModules === 'function') W.renderModules();
  });
  // F5 из меню: перечитать данные текущего раздела, не теряя собранный бит.
  if (window.zsmm && typeof window.zsmm.onRefresh === 'function') {
    window.zsmm.onRefresh(async () => {
      state.loaded.clear();
      await switchView(state.view, { force: true });
    });
  }
  $('reveal').addEventListener('click', async () => {
    const result = await window.zsmm.revealRoot();
    if (!result || result.ok !== true) showError(`Не удалось открыть папку: ${result && result.error}`);
  });
}

/**
 * С какого раздела начать: сохранённый, иначе «Обзор».
 *
 * Файл настроек читается один раз, поэтому при смене разделов в первые
 * секунды после старта запись не затирает ещё не прочитанное.
 */
async function startView() {
  if (state.settings || (window.zsmm && typeof window.zsmm.loadSettings === 'function')) {
    if (!state.settings) {
      try {
        const reply = await window.zsmm.loadSettings();
        if (reply && reply.ok === true && reply.data) state.settings = reply.data;
      } catch {
        // Настройки недоступны — открываем «Обзор»: окно не должно не открыться.
      }
    }
    if (state.settings && LOADERS[state.settings.view]) return state.settings.view;
  }
  return 'overview';
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    wire();
    // Разделы инициализируются после разбора всех скриптов и до первого
    // переключения: иначе `switchView` позвал бы ещё не зарегистрированный
    // загрузчик и показал бы «загрузчик отсутствует» вместо раздела.
    const failed = bootSections();
    if (failed.length) showError(`Раздел не загрузился: ${failed.join('; ')}`);
    // Настройки читаются ДО первого переключения, иначе `saveSettings` мог бы
    // записать «Обзор» поверх запомненного раздела.
    startView().then((view) => switchView(view));
  });
}

if (typeof module !== 'undefined' && module.exports) {
  // Для тестов: состояние, названия разделов и переход между ними.
  module.exports = { state, TITLES, LOADERS, switchView, startView, bootSections, W };
}
