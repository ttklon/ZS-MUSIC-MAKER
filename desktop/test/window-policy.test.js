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
const appPaths = require('../electron/app-paths');

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
  // Сам вызов живёт в startup.js, порядок — в main.js: сначала
  // идентификатор панели задач, потом окно.
  const startupSource = fs.readFileSync(path.join(DESKTOP, 'electron', 'startup.js'), 'utf8');
  assert.match(startupSource, /app\.setAppUserModelId\(/, 'без этого вызова иконка в панели задач чужая');

  const setIndex = MAIN_SOURCE.indexOf('startup.installAppUserModelId(');
  const windowIndex = MAIN_SOURCE.indexOf('windows.create(project);');
  assert.ok(setIndex > 0, 'идентификатор ставится из whenReady');
  assert.ok(windowIndex > setIndex, 'идентификатор ставится раньше окна');
});

test('единственный экземпляр: второй запуск выходит, первый показывает окно', () => {
  assert.equal(policy.shouldContinueStartup({ gotLock: true }), true);
  assert.equal(policy.shouldContinueStartup({ gotLock: false }), false);
  // Ссылка на обработчик second-instance есть только в первом процессе.
  const startupSource = fs.readFileSync(path.join(DESKTOP, 'electron', 'startup.js'), 'utf8');
  assert.match(startupSource, /requestSingleInstanceLock\(\)/);
  assert.match(startupSource, /app\.on\('second-instance'/);
  assert.match(startupSource, /policy\.focusExisting\(getWindow\(\)\)/);
  assert.match(MAIN_SOURCE, /startup\.installSingleInstance\(/);
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

test('размер окна запоминается, но не в развёрнутом и не в свёрнутом виде', () => {
  // Развёрнутое окно занимает весь монитор: если запомнить этот размер,
  // после перезапуска окно откроется «во весь экран» без кнопки «развернуть».
  const maximized = {
    getBounds: () => ({ width: 1920, height: 1080 }),
    getNormalBounds: () => ({ width: 1180, height: 760 }),
    isMaximized: () => true,
    isMinimized: () => false,
    isFullScreen: () => false,
  };
  assert.deepEqual(policy.boundsToRemember(maximized), { width: 1180, height: 760 });

  const plain = { getBounds: () => ({ width: 1000.4, height: 700.6 }), isMaximized: () => false };
  assert.deepEqual(policy.boundsToRemember(plain), { width: 1000, height: 701 });

  // Свёрнутое и полноэкранное окно не даёт осмысленного размера.
  assert.equal(policy.boundsToRemember({ ...plain, isMinimized: () => true }), null);
  assert.equal(policy.boundsToRemember({ ...plain, isFullScreen: () => true }), null);
  // Вырожденные размеры и мусор тоже не запоминаем.
  assert.equal(policy.boundsToRemember({ getBounds: () => ({ width: 0, height: 0 }) }), null);
  assert.equal(policy.boundsToRemember({ getBounds: () => ({ width: 'wide', height: 700 }) }), null);
  assert.equal(policy.boundsToRemember({}), null);
  assert.equal(policy.boundsToRemember(null), null);
});

test('сохранённый размер подставляется в окно в пределах минимума', () => {
  const custom = policy.windowOptions({ width: 1500, height: 950 });
  assert.equal(custom.width, 1500);
  assert.equal(custom.height, 950);

  // Меньше минимума Windows 11 не покажет — подгибаем сами.
  const small = policy.windowOptions({ width: 300, height: 200 });
  assert.equal(small.width, 960);
  assert.equal(small.height, 600);

  const broken = policy.windowOptions({ width: 'широко', height: undefined });
  assert.equal(broken.width, 1280);
  assert.equal(broken.height, 820);
});

test('размер окна лежит в настройках между запусками', () => {
  const os = require('node:os');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-bounds-'));
  const { createSettingsStore, DEFAULTS } = require('../electron/settings');
  const store = createSettingsStore({ dir });

  assert.equal(DEFAULTS.windowWidth, 1280);
  assert.equal(store.load().value.windowHeight, 820);

  const saved = store.save({ windowWidth: 1440, windowHeight: 900 });
  assert.equal(saved.error, null);
  assert.equal(store.load().value.windowWidth, 1440);

  // Мусор вместо размера — не повод ронять запуск: берётся умолчание, а
  // причина называется в отчёте о настройках (`invalid` в окне).
  const junk = store.save({ windowWidth: 'широко', windowHeight: 'высоко' });
  assert.deepEqual(junk.invalid.sort(), ['windowHeight', 'windowWidth']);
  assert.equal(store.load().value.windowWidth, 1280);

  // Меньше минимума окно не откроется: настройки такое значение не берут,
  // а окно всё равно подгибает размер, если он пришёл из старого файла.
  const tooSmall = store.save({ windowWidth: 300, windowHeight: 200 });
  assert.deepEqual(tooSmall.invalid.sort(), ['windowHeight', 'windowWidth']);
  const small = policy.windowOptions({ width: 300, height: 200 });
  assert.equal(small.width, 960);
  assert.equal(small.height, 600);
  fs.rmSync(dir, { recursive: true, force: true });
});

test('прогресс рендера показывается на кнопке панели задач', () => {
  // Свёрнутое окно во время рендера иначе выглядит зависшим.
  assert.equal(policy.taskbarProgress({ phase: 'section', percent: 16 }), 0.16);
  assert.equal(policy.taskbarProgress({ phase: 'master', percent: 100 }), 1);
  // До первого процента — бесконечный индикатор, а не пустой.
  assert.equal(policy.taskbarProgress({ phase: 'start', percent: 0 }), 2);
  assert.equal(policy.taskbarProgress({ phase: 'section' }), 2);
  // Завершённые фазы снимают индикатор.
  for (const phase of ['done', 'error', 'cancelled', 'idle']) {
    assert.equal(policy.taskbarProgress({ phase, percent: 100 }), -1, phase);
  }
  assert.equal(policy.taskbarProgress(null), -1);
  // Мусор в процентах не должен давать NaN в системный вызов.
  assert.equal(policy.taskbarProgress({ phase: 'section', percent: 'много' }), 2);
  assert.equal(policy.taskbarProgress({ phase: 'section', percent: 500 }), 1);
});

test('прогресс задачи «Запуск» — бесконечный, пока она идёт', () => {
  // Пайплайн не печатает проценты: выдумывать их нельзя.
  for (const type of ['start', 'stdout', 'stderr']) {
    assert.equal(policy.taskProgress({ type }), 2, type);
  }
  for (const type of ['exit', 'error', 'timeout']) {
    assert.equal(policy.taskProgress({ type }), -1, type);
  }
  assert.equal(policy.taskProgress({ type: 'что-то' }), null);
  assert.equal(policy.taskProgress(null), null);
});

test('каталог «Музыка» на Windows или запасной путь вместо падения', () => {
  assert.equal(
    appPaths.musicDir({ getPath: (name) => (name === 'music' ? 'C:\\Users\\me\\Music' : null) }),
    'C:\\Users\\me\\Music',
  );
  // В урезанном профиле каталога может не быть: приложение не должно писать
  // в C:\ и не должно падать.
  const fallback = appPaths.musicDir({ getPath: () => undefined });
  assert.match(fallback, /zsmm$/);
  assert.match(appPaths.musicDir({ getPath: () => { throw new Error('нет профиля'); } }), /zsmm$/);
  assert.match(appPaths.musicDir(null), /zsmm$/);
});

test('меню умеет открыть каталог досье и перечитать раздел', () => {
  // В установленной сборке досье лежит в каталоге пользователя, а данные
  // раздела нужно перечитывать без перезагрузки страницы: иначе собранный
  // бит пропадал бы по F5.
  const calls = [];
  const template = appMenu.menuTemplate({
    openDossier: () => calls.push('dossier'),
    reloadView: () => calls.push('reload'),
  });
  const items = template.flatMap((item) => item.submenu || []);
  items.find((sub) => sub.label === 'Каталог досье').click();
  const refresh = items.find((sub) => sub.label && sub.label.startsWith('Обновить раздел'));
  assert.ok(refresh, 'нет пункта «Обновить раздел»');
  assert.equal(refresh.accelerator, 'F5');
  refresh.click();
  assert.deepEqual(calls, ['dossier', 'reload']);

  // Без обработчиков пунктов нет: шаблон не должен ссылаться на undefined.
  const bare = appMenu.menuTemplate().flatMap((item) => item.submenu || []);
  assert.ok(!bare.some((sub) => sub.label === 'Каталог досье'));
  assert.ok(!bare.some((sub) => sub.label && sub.label.startsWith('Обновить раздел')));
});
