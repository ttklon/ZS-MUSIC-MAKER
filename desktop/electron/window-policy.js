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
function windowOptions({ iconPath = null, preloadPath = null } = {}) {
  const options = {
    width: 1280,
    height: 820,
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
  shouldContinueStartup,
  focusExisting,
  quitsOnAllWindowsClosed,
  windowOptions,
  externalUrl,
  windowTitle,
};
