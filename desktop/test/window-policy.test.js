'use strict';
/**
 * window-policy.test.js — поведение, которое видно только на Windows 11.
 *
 * Идентификатор для панели задач, единственный экземпляр, закрытие окна и
 * параметры окна проверяются без запуска Electron: `window-policy.js` не
 * требует `electron`. Иначе эти правила подтверждались бы только руками на
 * Windows, то есть никак.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const policy = require('../electron/window-policy');
const appMenu = require('../electron/app-menu');

const DESKTOP = path.resolve(__dirname, '..');
const MAIN_SOURCE = fs.readFileSync(path.join(DESKTOP, 'electron', 'main.js'), 'utf8');
const pkg = JSON.parse(fs.readFileSync(path.join(DESKTOP, 'package.json'), 'utf8'));

test('идентификатор приложения совпадает с appId сборки', () => {
  // Разные значения дают две группы на панели задач: ярлык и окно.
  assert.equal(policy.APP_USER_MODEL_ID, pkg.build.appId);
  assert.equal(policy.appUserModelId({ isPackaged: true, platform: 'win32' }), 'ru.zsmm.musicmaker');
});

test('идентификатор ставится только у собранного Windows-приложения', () => {
  // В разработке Windows группирует окна по пути к electron.exe.
  assert.equal(policy.appUserModelId({ isPackaged: false, platform: 'win32' }), null);
  assert.equal(policy.appUserModelId({ isPackaged: true, platform: 'linux' }), null);
  assert.equal(policy.appUserModelId({ isPackaged: true, platform: 'darwin' }), null);
});

test('main.js ставит AppUserModelId до создания окна', () => {
  assert.match(MAIN_SOURCE, /app\.setAppUserModelId\(/, 'без этого вызова иконка в панели задач чужая');
  const setIndex = MAIN_SOURCE.indexOf('installAppUserModelId();');
  const windowIndex = MAIN_SOURCE.indexOf('createWindow();');
  assert.ok(setIndex > 0, 'setAppUserModelId должен вызываться из whenReady');
  assert.ok(windowIndex > setIndex, 'идентификатор ставится раньше окна');
});

test('единственный экземпляр: второй запуск выходит, первый показывает окно', () => {
  assert.equal(policy.shouldContinueStartup({ gotLock: true }), true);
  assert.equal(policy.shouldContinueStartup({ gotLock: false }), false);
  // Ссылка на обработчик second-instance есть только в первом процессе.
  assert.match(MAIN_SOURCE, /requestSingleInstanceLock\(\)/);
  assert.match(MAIN_SOURCE, /app\.on\('second-instance'/);
  assert.match(MAIN_SOURCE, /policy\.focusExisting\(mainWindow\)/);
});

test('второй экземпляр поднимает свёрнутое окно, а не просто фокусируется', () => {
  const calls = [];
  const minimized = {
    isMinimized: () => true,
    isVisible: () => true,
    restore: () => calls.push('restore'),
    show: () => calls.push('show'),
    focus: () => calls.push('focus'),
  };
  assert.deepEqual(policy.focusExisting(minimized), { ok: true, action: 'restore' });
  assert.deepEqual(calls, ['restore']);

  calls.length = 0;
  const hidden = { isMinimized: () => false, isVisible: () => false, show: () => calls.push('show'), focus: () => calls.push('focus') };
  assert.deepEqual(policy.focusExisting(hidden), { ok: true, action: 'show' });

  calls.length = 0;
  const visible = { isMinimized: () => false, isVisible: () => true, focus: () => calls.push('focus') };
  assert.deepEqual(policy.focusExisting(visible), { ok: true, action: 'focus' });
});

test('сломанное окно не роняет обработчик второго запуска', () => {
  const result = policy.focusExisting({
    isMinimized() {
      throw new Error('окно уже уничтожено');
    },
  });
  assert.equal(result.ok, false);
  assert.match(result.action, /уже уничтожено/);
  assert.equal(policy.focusExisting(null).ok, false);
});

test('на Windows закрытие окна завершает процесс', () => {
  assert.equal(policy.quitsOnAllWindowsClosed('win32'), true);
  assert.equal(policy.quitsOnAllWindowsClosed('linux'), true);
  // macOS живёт без окон — это правило системы, а не наше.
  assert.equal(policy.quitsOnAllWindowsClosed('darwin'), false);
});

test('окно защищено от nodeIntegration и меньше 960x600 не открывается', () => {
  const options = policy.windowOptions({ iconPath: 'build/icon.png', preloadPath: 'electron/preload.js' });
  assert.equal(options.width, 1280);
  assert.equal(options.height, 820);
  assert.ok(options.minWidth >= 960, 'таблицы разделов ломаются раньше');
  assert.ok(options.minHeight >= 600);
  assert.equal(options.show, false, 'окно показывается только по ready-to-show');
  assert.equal(options.backgroundColor, '#0f1115', 'иначе при старте белая вспышка');
  assert.equal(options.webPreferences.contextIsolation, true);
  assert.equal(options.webPreferences.nodeIntegration, false);
  assert.equal(options.webPreferences.preload, 'electron/preload.js');
  assert.equal(options.icon, 'build/icon.png');
});

test('внешние ссылки открываются, всё остальное отбрасывается', () => {
  assert.equal(policy.externalUrl('https://example.com/a'), 'https://example.com/a');
  assert.equal(policy.externalUrl('http://example.com'), 'http://example.com');
  assert.equal(policy.externalUrl('file:///etc/passwd'), null);
  assert.equal(policy.externalUrl('javascript:alert(1)'), null);
  assert.equal(policy.externalUrl(''), null);
  assert.equal(policy.externalUrl(null), null);
  assert.equal(policy.externalUrl({ href: 'https://example.com' }), null);
});

test('заголовок окна показывает версию проекта', () => {
  assert.equal(policy.windowTitle({ version: '3.4.5' }), 'ZS Music Maker v3.4.5');
  assert.equal(policy.windowTitle({ version: null }), 'ZS Music Maker');
  assert.equal(policy.windowTitle(null), 'ZS Music Maker');
});

test('меню в сборке не даёт перезагрузить окно и открыть инструменты', () => {
  const labels = (template) => template.flatMap((item) => (item.submenu || []).map((sub) => sub.label || sub.role));
  const release = labels(appMenu.menuTemplate());
  const dev = labels(appMenu.menuTemplate({ isDev: true }));

  assert.ok(!release.includes('Перезагрузить'), 'перезагрузка сбрасывает собранный бит');
  assert.ok(!release.includes('toggleDevTools'));
  assert.ok(dev.includes('Перезагрузить') && dev.includes('Инструменты'), 'в разработке они нужны');
  assert.ok(release.includes('Выход') && release.includes('О приложении'));
});

test('меню вызывает переданные обработчики, а не глобальные функции', () => {
  const calls = [];
  const template = appMenu.menuTemplate({
    openRoot: () => calls.push('root'),
    showAbout: () => calls.push('about'),
  });
  const find = (label) =>
    template.flatMap((item) => item.submenu || []).find((sub) => sub.label === label);
  find('Папка проекта').click();
  find('О приложении').click();
  assert.deepEqual(calls, ['root', 'about']);
});

test('окно «О приложении» называет версию, корень и версии движка', () => {
  const text = appMenu.aboutText({
    version: '1.2.3',
    root: 'C:\\Users\\me\\AppData\\Local\\ZS Music Maker',
    electron: '33.0.0',
    node: '20.0.0',
    chrome: '130.0.0',
    platform: 'win32',
    arch: 'x64',
  });
  assert.equal(text.message, 'ZS Music Maker v1.2.3');
  assert.match(text.detail, /Проект: C:\\Users/);
  assert.match(text.detail, /Electron 33\.0\.0/);
  assert.match(text.detail, /Платформа: win32 x64/);
  assert.match(text.detail, /без Python и сети/);

  // Без корня пользователь должен увидеть, что делать, а не пустую строку.
  const broken = appMenu.aboutText({ root: null });
  assert.match(broken.detail, /ZSMM_ROOT/);
  assert.equal(broken.message, 'ZS Music Maker');
});
