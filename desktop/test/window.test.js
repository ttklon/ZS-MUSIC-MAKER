'use strict';
/**
 * window.test.js — главное окно на двойниках Electron.
 *
 * Проверяется поведение, которое иначе видно только руками на Windows:
 * показ окна после отрисовки, запрет навигации в браузер, восстановление
 * после падения процесса отрисовки, запоминание размера и индикатор панели
 * задач. `window-policy` решает «что», этот модуль делает «как».
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createWindowManager } = require('../electron/window');

/** Двойник BrowserWindow: записывает вызовы и отдаёт подписки наружу. */
function fakeBrowserWindow(calls) {
  return class Window {
    constructor(options) {
      this.options = options;
      this.handlers = {};
      this.title = options.title;
      calls.push(['new', options]);
      this.webContents = {
        on: (name, fn) => calls.push(['webContents.on', name, fn]),
        setWindowOpenHandler: (fn) => calls.push(['setWindowOpenHandler', fn]),
        openDevTools: () => calls.push(['openDevTools']),
      };
    }

    once(name, fn) {
      this.handlers[name] = fn;
      calls.push(['once', name]);
    }

    on(name, fn) {
      this.handlers[name] = fn;
      calls.push(['on', name]);
    }

    show() {
      calls.push(['show']);
    }

    loadFile(file) {
      calls.push(['loadFile', file]);
    }

    setTitle(title) {
      this.title = title;
      calls.push(['setTitle', title]);
    }

    setProgressBar(value) {
      calls.push(['setProgressBar', value]);
    }

    isDestroyed() {
      return false;
    }

    reload() {
      calls.push(['reload']);
    }

    getBounds() {
      return { width: 1100, height: 720 };
    }

    isMaximized() {
      return false;
    }
  };
}

/** Хранилище настроек в памяти: файл здесь не нужен. */
function memorySettings(initial = {}) {
  const value = { windowWidth: 1280, windowHeight: 820, ...initial };
  const saved = [];
  return {
    saved,
    value,
    load: () => ({ value, errors: [], error: null }),
    save: (patch) => {
      saved.push(patch);
      Object.assign(value, patch);
      return { value, invalid: [], error: null };
    },
  };
}

function makeManager({ settings = memorySettings(), dev = false } = {}) {
  const calls = [];
  const dialogs = [];
  const manager = createWindowManager({
    BrowserWindow: fakeBrowserWindow(calls),
    shell: { openExternal: (url) => calls.push(['openExternal', url]) },
    dialog: {
      showMessageBoxSync: (_window, options) => {
        dialogs.push(options);
        return dialogs.length === 1 ? 0 : 1;
      },
    },
    settings: () => settings,
    dev,
  });
  return { manager, calls, dialogs, settings };
}

const find = (calls, name) => calls.filter((call) => call[0] === name);

test('окно показывается после отрисовки и открывает страницу из __dirname', () => {
  const { manager, calls } = makeManager();
  const window = manager.create({ version: () => ({ version: '3.4.5' }) });

  const [created] = find(calls, 'new');
  assert.ok(created, 'окно не создано');
  assert.equal(created[1].show, false, 'до ready-to-show окно не показывается');
  assert.equal(created[1].width, 1280);
  assert.match(find(calls, 'loadFile')[0][1], /src[\\/]index\.html$/);

  // Заголовок с версией проекта: в списке задач должно быть видно сборку.
  assert.equal(window.title, 'ZS Music Maker v3.4.5');
  // Показ — только по событию, иначе видна белая вспышка.
  assert.equal(find(calls, 'show').length, 0);
  window.handlers['ready-to-show']();
  assert.equal(find(calls, 'show').length, 1);
  assert.equal(manager.get(), window);
});

test('проект без версии не мешает окну открыться', () => {
  const { manager, calls } = makeManager();
  const broken = {
    version() {
      throw new Error('version.json испорчен');
    },
  };
  const window = manager.create(broken);
  assert.equal(window.title, 'ZS Music Maker');
  assert.equal(find(calls, 'loadFile').length, 1);
});

test('размер из настроек подставляется в окно', () => {
  const { manager, calls } = makeManager({ settings: memorySettings({ windowWidth: 1500, windowHeight: 900 }) });
  manager.create();
  const [created] = find(calls, 'new');
  assert.equal(created[1].width, 1500);
  assert.equal(created[1].height, 900);
});

test('размер запоминается при закрытии окна', () => {
  const { manager, settings } = makeManager();
  const window = manager.create();
  window.handlers.close();
  assert.deepEqual(settings.saved, [{ width: 1100, height: 720 }]);
  // После closed ссылки на окно нет: обработчик второго запуска не должен
  // трогать уничтоженное окно.
  window.handlers.closed();
  assert.equal(manager.get(), null);
});

test('всплывающие окна запрещены, внешние ссылки уходят в систему', () => {
  const { manager, calls } = makeManager();
  const window = manager.create();
  const [handler] = find(calls, 'setWindowOpenHandler').map((call) => call[1]);

  assert.deepEqual(handler({ url: 'https://example.com/docs' }), { action: 'deny' });
  assert.deepEqual(find(calls, 'openExternal'), [['openExternal', 'https://example.com/docs']]);

  // Локальные и «javascript:» ссылки наружу не отдаются.
  handler({ url: 'file:///C:/Windows/System32/calc.exe' });
  handler({ url: 'javascript:alert(1)' });
  assert.equal(find(calls, 'openExternal').length, 1);
});

test('навигация прочь от страницы приложения отменяется', () => {
  const { manager, calls } = makeManager();
  const window = manager.create();
  const navigate = find(calls, 'webContents.on').find((call) => call[1] === 'will-navigate')[2];

  let prevented = false;
  const event = { preventDefault: () => { prevented = true; } };
  navigate(event, 'https://example.com');
  assert.equal(prevented, true);
  assert.deepEqual(find(calls, 'openExternal'), [['openExternal', 'https://example.com']]);

  // Переход внутри своей страницы не блокируется.
  prevented = false;
  navigate(event, 'file:///C:/app/resources/app.asar/src/index.html');
  assert.equal(prevented, false);
});

test('падение окна объясняется, и перезагрузка предлагается не всегда', () => {
  const first = makeManager();
  const window = first.manager.create();
  const rendered = find(first.calls, 'webContents.on')
    .find((call) => call[1] === 'render-process-gone')[2];
  rendered({}, { reason: 'crashed' });

  assert.equal(first.dialogs.length, 1);
  assert.match(first.dialogs[0].message, /закрылось неожиданно/i);
  assert.deepEqual(first.dialogs[0].buttons, ['Перезагрузить', 'Закрыть']);
  // Первый выбор в двойнике — «Перезагрузить».
  assert.equal(find(first.calls, 'reload').length, 1);

  // При нехватке памяти перезапуск повторит ту же ошибку.
  const second = makeManager();
  const window2 = second.manager.create();
  const rendered2 = find(second.calls, 'webContents.on')
    .find((call) => call[1] === 'render-process-gone')[2];
  rendered2({}, { reason: 'oom' });
  assert.match(second.dialogs[0].message, /памяти/i);
  assert.deepEqual(second.dialogs[0].buttons, ['Понятно']);
  assert.equal(find(second.calls, 'reload').length, 0);
  assert.ok(window && window2);
});

test('индикатор панели задач реагирует на рендер и на задачу «Запуск»', () => {
  const { manager, calls } = makeManager();
  manager.create();

  manager.showTaskbarProgress({ phase: 'section', percent: 40 });
  manager.showTaskbarProgress({ phase: 'done', percent: 100 });
  manager.showTaskProgress({ type: 'start' });
  manager.showTaskProgress({ type: 'exit', code: 0 });

  const values = find(calls, 'setProgressBar').map((call) => call[1]);
  assert.deepEqual(values, [0.4, -1, 2, -1]);
});

test('индикатор не падает без окна', () => {
  const { manager, calls } = makeManager();
  // Окна ещё нет: вызовы не должны бросать.
  manager.showTaskbarProgress({ phase: 'section', percent: 10 });
  manager.showTaskProgress({ type: 'start' });
  assert.equal(find(calls, 'setProgressBar').length, 0);
});

test('размер окна читается из настоящего settings.json', () => {
  const { createSettingsStore } = require('../electron/settings');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-window-'));
  const store = createSettingsStore({ dir });
  store.save({ windowWidth: 1400, windowHeight: 880 });

  const calls = [];
  const manager = createWindowManager({
    BrowserWindow: fakeBrowserWindow(calls),
    shell: { openExternal: () => {} },
    dialog: { showMessageBoxSync: () => 1 },
    settings: () => store,
  });
  manager.create();
  const [created] = find(calls, 'new');
  assert.equal(created[1].width, 1400);
  assert.equal(created[1].height, 880);
  fs.rmSync(dir, { recursive: true, force: true });
});
