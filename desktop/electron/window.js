'use strict';
/**
 * window.js — создание главного окна и всё, что к нему привязано.
 *
 * Вынесено из `main.js`: окно, внешние ссылки, восстановление после падения,
 * запоминание размера и индикатор панели задач — это одна тема, и она не
 * должна тонуть среди IPC-каналов. Сами решения (какие ссылки разрешены,
 * какой размер запоминать, что показывать на кнопке) принимает
 * `window-policy.js`, поэтому их проверяет `node --test` без Electron.
 *
 * Electron приходит аргументами: модуль можно потребовать в тестах, подставив
 * двойники `BrowserWindow`, `shell` и `dialog`.
 */

const path = require('node:path');

const policy = require('./window-policy');

/**
 * @param {object} params
 * @param {object} params.BrowserWindow класс окна из Electron (или двойник)
 * @param {object} params.shell         открытие внешних ссылок
 * @param {object} params.dialog        сообщения о падении окна
 * @param {Function} params.settings    () => хранилище настроек
 * @param {object} [params.screen]      `screen` из Electron: какие экраны подключены
 * @param {boolean} [params.dev]        открыть инструменты разработчика
 * @returns {{create: Function, get: Function, setTaskbar: Function,
 *            showTaskProgress: Function, showTaskbarProgress: Function}}
 */
function createWindowManager({ BrowserWindow, shell, dialog, settings, screen = null, dev = false }) {
  let current = null;

  const setTaskbar = (value) => {
    if (!current || value === null) return;
    try {
      current.setProgressBar(value);
    } catch {
      /* без графической среды панели задач нет */
    }
  };

  /** Сообщение о падении окна: перезагрузка только там, где она поможет. */
  const showCrash = (plan) => {
    const window = current;
    if (!window) return;
    const buttons = plan.reload ? ['Перезагрузить', 'Закрыть'] : ['Понятно'];
    let choice = buttons.length - 1;
    try {
      choice = dialog.showMessageBoxSync(window, {
        type: 'error',
        title: plan.title,
        message: plan.title,
        detail: plan.text,
        buttons,
        defaultId: 0,
        cancelId: buttons.length - 1,
      });
    } catch {
      /* без графической среды диалог не показать; окно всё равно перезагрузим */
    }
    if (plan.reload && choice === 0 && !window.isDestroyed()) window.reload();
  };

  /** Открыть внешнюю ссылку; какие ссылки разрешены — решает window-policy. */
  const openExternal = (url) => {
    const allowed = policy.externalUrl(url);
    if (allowed) shell.openExternal(allowed);
    return allowed;
  };

  /**
   * Создать окно.
   *
   * @param {{version?: string|null}} [project] модель проекта (для заголовка)
   * @returns {object} окно
   */
  const create = (project = null) => {
    // Размер, цвет фона и webPreferences — в window-policy.js.
    const saved = settings().load().value;
    const options = policy.windowOptions({
      iconPath: path.join(__dirname, '..', 'build', 'icon.png'),
      preloadPath: path.join(__dirname, 'preload.js'),
      width: saved.windowWidth,
      height: saved.windowHeight,
    });
    // Позиция из прошлого запуска — только если она видна на подключённом
    // экране: монитор мог отключиться, и окно иначе оказалось бы вне стола.
    let displays = [];
    try {
      displays = screen && typeof screen.getAllDisplays === 'function'
        ? screen.getAllDisplays().map((display) => ({ workArea: display.workArea }))
        : [];
    } catch {
      // Список экранов недоступен — окно откроется там, куда положит Windows.
      displays = [];
    }
    const position = policy.restorePosition({
      x: saved.windowX,
      y: saved.windowY,
      width: saved.windowWidth,
      height: saved.windowHeight,
    }, displays);
    if (position) {
      options.x = position.x;
      options.y = position.y;
    }
    current = new BrowserWindow(options);

    // В заголовке — версия проекта: в списке задач Windows должно быть видно,
    // какая сборка открыта.
    try {
      const version = project ? (project.version() || {}).version : null;
      if (version) current.setTitle(policy.windowTitle({ version }));
    } catch {
      /* без версии остаётся имя приложения */
    }

    current.once('ready-to-show', () => current.show());
    current.loadFile(path.join(__dirname, '..', 'src', 'index.html'));

    // Окно не должно превращаться в браузер: внешние ссылки уходят в систему.
    current.webContents.setWindowOpenHandler(({ url }) => {
      openExternal(url);
      return { action: 'deny' };
    });
    current.webContents.on('will-navigate', (event, url) => {
      if (!url.startsWith('file://')) {
        event.preventDefault();
        openExternal(url);
      }
    });

    // Белое окно без объяснений — худший вид поломки.
    current.webContents.on('render-process-gone', (_event, details) => {
      showCrash(policy.crashRecovery({ name: 'render-process-gone', details }));
    });
    current.on('unresponsive', () => {
      showCrash(policy.crashRecovery({ name: 'unresponsive' }));
    });

    if (dev) current.webContents.openDevTools({ mode: 'detach' });

    // Размер запоминается до закрытия: после `closed` границ уже нет.
    current.on('close', () => {
      const bounds = policy.boundsToRemember(current);
      if (!bounds) return;
      const patch = {
        windowWidth: bounds.width,
        windowHeight: bounds.height,
      };
      // Позиция пишется вместе с размером: по отдельности они разъедутся,
      // и окно откроется со старой шириной в новой точке.
      if (Number.isFinite(bounds.x) && Number.isFinite(bounds.y)) {
        patch.windowX = bounds.x;
        patch.windowY = bounds.y;
      }
      settings().save(patch);
    });
    current.on('closed', () => {
      current = null;
    });

    return current;
  };

  return {
    create,
    get: () => current,
    setTaskbar,
    showTaskbarProgress: (progress) => setTaskbar(policy.taskbarProgress(progress)),
    showTaskProgress: (event) => setTaskbar(policy.taskProgress(event)),
  };
}

module.exports = { createWindowManager };
