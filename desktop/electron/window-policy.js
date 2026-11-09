'use strict';
/**
 * window-policy.js — правила окна и жизненного цикла, отдельно от Electron.
 *
 * Зачем отдельным модулем: `AppUserModelId`, единственный экземпляр и
 * поведение при закрытии окна видно только на Windows, а проверить их хочется
 * там, где Electron вообще не запускается. Здесь нет `require('electron')`:
 * всё, что нужно от платформы, приходит аргументами.
 *
 * Три вещи, из-за которых приложение на Windows 11 ведёт себя как чужое:
 * 1. без `AppUserModelId` панель задач показывает чужую иконку и не
 *    группирует окна приложения;
 * 2. второй запуск (двойной клик по ярлыку при открытом окне) поднимает
 *    второй процесс, у которого нет ни проекта, ни настроек;
 * 3. `window-all-closed` на Windows обязан завершать процесс, иначе остаётся
 *    висеть фоновый рендер и его не видно в диспетчере задач.
 */

/** Идентификатор приложения: совпадает с `build.appId` в package.json. */
const APP_USER_MODEL_ID = 'ru.zsmm.musicmaker';

/**
 * Размер окна, который нужно запомнить.
 *
 * Кнопка «развернуть» — это не размер окна для настроек: сохранять надо то,
 * куда пользователь вернётся, если развернёт обратно. Поэтому максимизация
 * заменяется обычными границами окна.
 *
 * @param {{getBounds: Function, isMaximized?: Function, isMinimized?: Function, isFullScreen?: Function}} window
 * @returns {{width: number, height: number}|null}
 */
function boundsToRemember(window) {
  if (!window || typeof window.getBounds !== 'function') return null;
  try {
    if (typeof window.isFullScreen === 'function' && window.isFullScreen()) return null;
    if (typeof window.isMinimized === 'function' && window.isMinimized()) return null;
    const bounds = (typeof window.isMaximized === 'function' && window.isMaximized()
      ? window.getNormalBounds()
      : window.getBounds()) || {};
    const width = Math.round(Number(bounds.width));
    const height = Math.round(Number(bounds.height));
    // Окно, сложенное в угол с нулевым размером, запоминать нечего.
    if (!Number.isFinite(width) || !Number.isFinite(height) || width < 400 || height < 300) {
      return null;
    }
    const x = Math.round(Number(bounds.x));
    const y = Math.round(Number(bounds.y));
    const remembered = { width, height };
    // Позицию запоминаем только если она известна: без неё окно откроется
    // там, куда его положит Windows, — это лучше выдуманных координат.
    if (Number.isFinite(x) && Number.isFinite(y)) {
      remembered.x = x;
      remembered.y = y;
    }
    return remembered;
  } catch {
    return null;
  }
}

/**
 * Стоит ли восстанавливать позицию окна на этом мониторе.
 *
 * Windows 11 меняет конфигурацию мониторов: закрыл окно на втором экране,
 * отключил его — и окно оказалось бы за пределами рабочего стола, то есть
 * «приложение не запускается». Поэтому заголовок окна обязан быть виден
 * хотя бы на одном из экранов, иначе позиция отбрасывается.
 *
 * @param {{x: number, y: number, width: number, height: number}} bounds
 * @param {Array<{x: number, y: number, width: number, height: number}>} displays
 * @returns {boolean}
 */
function isVisibleOnSomeDisplay(bounds, displays) {
  const list = Array.isArray(displays) ? displays.filter(Boolean) : [];
  if (!bounds || !Number.isFinite(bounds.x) || !Number.isFinite(bounds.y)) return false;
  if (!list.length) return false;
  const width = Number.isFinite(bounds.width) ? bounds.width : 0;
  const height = Number.isFinite(bounds.height) ? bounds.height : 0;
  // Заголовок окна — полоса сверху высотой ~40 px и шириной от левого края:
  // именно она должна попадать на экран, иначе окно не за что ухватить.
  const gripHeight = Math.min(48, Math.max(1, height));
  const gripWidth = Math.min(240, Math.max(1, width));
  return list.some((display) => {
    const area = display.workArea || display.bounds || display;
    const dx = Number(area.x) || 0;
    const dy = Number(area.y) || 0;
    const dw = Number(area.width) || 0;
    const dh = Number(area.height) || 0;
    return (
      bounds.x + gripWidth > dx
      && bounds.x < dx + dw
      && bounds.y + gripHeight > dy
      && bounds.y < dy + dh
    );
  });
}

/**
 * Параметры окна с учётом запомненной позиции.
 *
 * @param {{x?: number, y?: number, width?: number, height?: number}} saved
 * @param {Array<object>} displays список экранов (`screen.getAllDisplays()`)
 * @returns {{x: number, y: number}|null}
 */
function restorePosition(saved, displays) {
  if (!saved || typeof saved !== 'object') return null;
  // `Number(null)` — это 0, то есть «окно в левом верхнем углу». Пустое
  // значение обязано отличаться от нулевой координаты.
  const known = (value) => value !== null && value !== undefined && value !== ''
    && Number.isFinite(Number(value));
  if (!known(saved.x) || !known(saved.y)) return null;
  const bounds = {
    x: Math.round(Number(saved.x)),
    y: Math.round(Number(saved.y)),
    width: Math.round(Number(saved.width)),
    height: Math.round(Number(saved.height)),
  };
  if (!Number.isFinite(bounds.x) || !Number.isFinite(bounds.y)) return null;
  if (!isVisibleOnSomeDisplay(bounds, displays)) return null;
  return { x: bounds.x, y: bounds.y };
}

/**
 * Идентификатор для панели задач Windows.
 *
 * В разработке (`electron .`) Windows группирует окна по пути к `electron.exe`,
 * поэтому идентификатор ставим только у собранного приложения: иначе ярлык
 * разрабатываемой копии и установленной смешаются в одну группу.
 *
 * @param {{isPackaged?: boolean, platform?: string}} params
 * @returns {string|null} значение для `app.setAppUserModelId` или null
 */
function appUserModelId({ isPackaged = false, platform = process.platform } = {}) {
  if (platform !== 'win32') return null;
  if (!isPackaged) return null;
  return APP_USER_MODEL_ID;
}

/**
 * Нужно ли продолжать запуск после запроса единственного экземпляра.
 *
 * `app.requestSingleInstanceLock()` возвращает false во втором процессе.
 * Такой процесс обязан выйти сразу: окно уже есть в первом, а второй
 * экземпляр писал бы те же настройки и тот же файл банка.
 *
 * @param {{gotLock: boolean}} params
 * @returns {boolean} true — запускаемся дальше, false — выходим
 */
function shouldContinueStartup({ gotLock }) {
  return Boolean(gotLock);
}

/**
 * Что делать со вторым экземпляром: показать и поднять уже открытое окно.
 *
 * Свёрнутое окно надо развернуть, невидимое — показать, иначе пользователь
 * решит, что приложение не запустилось.
 *
 * @param {object|null} window окно, которое уже открыто
 * @returns {{ok: boolean, action: string}} описание действия
 */
function focusExisting(window) {
  if (!window) return { ok: false, action: 'нет окна' };
  try {
    if (typeof window.isMinimized === 'function' && window.isMinimized()) {
      window.restore();
      return { ok: true, action: 'restore' };
    }
    if (typeof window.isVisible === 'function' && !window.isVisible()) {
      window.show();
      return { ok: true, action: 'show' };
    }
    window.focus();
    return { ok: true, action: 'focus' };
  } catch (err) {
    return { ok: false, action: `ошибка: ${err && err.message ? err.message : String(err)}` };
  }
}

/**
 * Индикатор для задачи «Запуск» (Python-пайплайн) по строкам её вывода.
 *
 * Прогресса в процентах пайплайн не печатает, зато называет этапы. Поэтому
 * индикатор «бесконечный» (2), пока задача идёт, и снимается при выходе —
 * это честнее выдуманных процентов.
 *
 * @param {{type?: string}} event событие задачи из electron/tasks.js
 * @returns {number|null} значение для `setProgressBar` либо null — не менять
 */
function taskProgress(event) {
  const type = event && typeof event.type === 'string' ? event.type : '';
  if (type === 'start' || type === 'stdout' || type === 'stderr') return 2;
  if (type === 'exit' || type === 'error' || type === 'timeout') return -1;
  return null;
}

/**
 * Что показать на кнопке панели задач Windows 11.
 *
 * Долгий рендер без индикатора выглядит как зависшее приложение: окно
 * свёрнуто, а в панели задач ничего не происходит. Electron принимает
 * `setProgressBar(0…1)`, `-1` (убрать) и `2` (бесконечный, пока фаза не
 * известна).
 *
 * @param {{phase?: string, percent?: number}|null} progress
 * @returns {number} значение для `window.setProgressBar`
 */
function taskbarProgress(progress) {
  // Нет данных о рендере — значит, и индикатора быть не должно.
  if (!progress || typeof progress !== 'object') return -1;
  const phase = typeof progress.phase === 'string' ? progress.phase : '';
  if (phase === 'done' || phase === 'error' || phase === 'cancelled' || phase === 'idle') return -1;
  const percent = Number(progress.percent);
  if (!Number.isFinite(percent)) return 2;
  const clamped = Math.min(100, Math.max(0, percent));
  // 0 % отрисовался бы пустым индикатором, то есть «ничего не идёт».
  if (clamped === 0) return 2;
  return clamped / 100;
}

/**
 * Что делать, если окно упало или зависло.
 *
 * На Windows падение процесса отрисовки выглядит как белое окно без
 * объяснений: пользователь думает, что приложение сломалось навсегда.
 * Перезагружать окно можно не всегда — при нехватке памяти (OOM) перезапуск
 * повторит ту же ошибку, и честнее сказать об этом прямо.
 *
 * @param {object} params
 * @param {string} [params.name]    'render-process-gone' | 'unresponsive'
 * @param {object} [params.details] `{reason, exitCode}` от Electron
 * @returns {{reload: boolean, title: string, text: string}}
 */
function crashRecovery({ name = '', details = {} } = {}) {
  if (name === 'unresponsive') {
    return {
      reload: true,
      title: 'Окно не отвечает',
      text: 'Приложение перестало отвечать на запросы. Окно можно перезагрузить — '
        + 'собранный бит при этом не пострадает, он хранится в памяти главного процесса.',
    };
  }
  const reason = details && typeof details.reason === 'string' ? details.reason : '';
  const memory = reason === 'oom' || reason === 'memory-exhausted';
  if (memory) {
    return {
      reload: false,
      title: 'Не хватило памяти',
      text: 'Окно закрылось из-за нехватки памяти. Перезапуск повторит ту же ошибку: '
        + 'закройте другие программы или выберите длительность бита покороче.',
    };
  }
  return {
    reload: true,
    title: 'Окно закрылось неожиданно',
    text: `Процесс отрисовки завершился${reason ? ` (${reason})` : ''}. `
      + 'Окно можно открыть заново; данные проекта не пострадали.',
  };
}

/**
 * Закрывать ли процесс, когда закрылись все окна.
 *
 * На macOS приложение живёт без окон (поведение системы), на Windows и Linux
 * закрытие окна означает выход. Нужна как отдельная функция, потому что
 * иначе это правило проверяется только руками на Windows.
 *
 * @param {string} platform
 * @returns {boolean}
 */
function quitsOnAllWindowsClosed(platform = process.platform) {
  return platform !== 'darwin';
}

/**
 * Параметры главного окна, одинаковые для всех платформ.
 *
 * Здесь только числа и булевы значения: создание `BrowserWindow` требует
 * Electron, а сами размеры хочется держать в одном месте и проверять тестом.
 *
 * @param {{dev?: boolean, iconPath?: string, preloadPath?: string}} params
 * @returns {object}
 */
function windowOptions({ iconPath = null, preloadPath = null, width = 1280, height = 820 } = {}) {
  const options = {
    // Размер из настроек прошлого запуска; границы — ниже, в minWidth.
    width: Math.max(960, Math.round(Number(width)) || 1280),
    height: Math.max(600, Math.round(Number(height)) || 820),
    // На Windows 11 окно не должно уменьшаться до нечитаемого состояния:
    // разделы с таблицами ломаются раньше, чем верстка.
    minWidth: 960,
    minHeight: 600,
    // Окно красится в тон интерфейсу: без этого при старте видна белая вспышка.
    backgroundColor: '#0f1115',
    show: false,
    title: 'ZS Music Maker',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  };
  if (iconPath) options.icon = iconPath;
  if (preloadPath) options.webPreferences.preload = preloadPath;
  return options;
}

/**
 * Адрес внешней ссылки либо null, если открывать её не нужно.
 *
 * Окно не должно превращаться в браузер: `http(s)` уходит в систему,
 * всё остальное (в том числе `file:` и `javascript:`) отбрасывается.
 *
 * @param {unknown} url
 * @returns {string|null}
 */
function externalUrl(url) {
  if (typeof url !== 'string') return null;
  if (!/^https?:\/\//i.test(url)) return null;
  return url;
}

/**
 * Заголовок окна: имя приложения и номер версии проекта.
 *
 * @param {{version?: string|null}} [project]
 * @returns {string}
 */
function windowTitle(project) {
  const version = project && project.version;
  return version ? `ZS Music Maker v${version}` : 'ZS Music Maker';
}

module.exports = {
  APP_USER_MODEL_ID,
  appUserModelId,
  boundsToRemember,
  isVisibleOnSomeDisplay,
  restorePosition,
  taskbarProgress,
  taskProgress,
  crashRecovery,
  shouldContinueStartup,
  focusExisting,
  quitsOnAllWindowsClosed,
  windowOptions,
  externalUrl,
  windowTitle,
};
