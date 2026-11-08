'use strict';
/**
 * main.js — главный процесс Electron. В окне нет ни Python, ни сети.
 *
 * Окно работает на данных, которые этот процесс читает из файлов проекта.
 * Логика вынесена в `src/core/*` и `electron/*`, поэтому её проверяет обычный
 * `node --test` без графической среды, а main.js остаётся тонким: окно, IPC.
 *
 * Где лежит проект и есть ли Python — решает `runtime.js`, потому что в
 * установленном приложении (`resources/app.asar`) относительные пути
 * репозитория не существуют.
 */

const { app, BrowserWindow, ipcMain, shell, dialog, Menu, nativeTheme } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const fsp = require('node:fs/promises');

const { createNodeFs } = require('../src/core/fs-node');
const { createProject } = require('../src/core/project');
const beatService = require('./beat-service');
const smoke = require('./smoke');
const { resolveRoot, resolvePython } = require('./runtime');
const { createSettingsStore, DEFAULTS } = require('./settings');
const tasks = require('./tasks');
const policy = require('./window-policy');
const appMenu = require('./app-menu');

const IS_DEV = process.argv.includes('--dev');
// `--smoke`: запустить приложение, проверить данные, напечатать JSON и выйти
// с кодом 0/1. Нужен CI: упакованную сборку надо чем-то проверить, а
// графической среды на раннере нет.
const IS_SMOKE = process.argv.includes('--smoke');

// Корень проекта: в репозитории — на два уровня выше `desktop/`, в
// установленном приложении — `resources/project` (см. `resolveRoot`).
const rootInfo = resolveRoot({
  appPath: app.getAppPath(),
  resourcesPath: process.resourcesPath,
  env: process.env,
});
const ROOT = rootInfo.root;
// Откуда читать сэмпловый банк. В установленной сборке `data/samples/` лежит
// в `resources/project` рядом с `version.json`, как и в репозитории; если
// такого каталога нет — берём корень, где нашлись маркеры.
const SAMPLE_ROOT = ROOT;

let mainWindow = null;
let project = null;
let activeTask = null;
let settingsStore = null;

function settings() {
  if (!settingsStore) {
    settingsStore = createSettingsStore({ dir: app.getPath('userData') });
  }
  return settingsStore;
}

function projectFor(root = ROOT, fileSystem = createNodeFs()) {
  return createProject(fileSystem, root);
}

function createWindow() {
  // Размеры, цвет фона и настройки webPreferences — в window-policy.js:
  // их проверяет тест, которому Electron не нужен.
  mainWindow = new BrowserWindow(
    policy.windowOptions({
      iconPath: path.join(__dirname, '..', 'build', 'icon.png'),
      preloadPath: path.join(__dirname, 'preload.js'),
    }),
  );

  // В заголовке окна — версия проекта: в Windows 11 заголовок виден в
  // списке задач и должен отличать сборку от соседней папки.
  try {
    const version = project ? (project.version() || {}).version : null;
    if (version) mainWindow.setTitle(policy.windowTitle({ version }));
  } catch {
    /* без версии остаётся имя приложения */
  }

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.loadFile(path.join(__dirname, '..', 'src', 'index.html'));

  // Окно не должно превращаться в браузер: внешние ссылки уходят в систему.
  // Какие ссылки разрешены, решает policy.externalUrl — там же и тест.
  const openExternal = (url) => {
    const allowed = policy.externalUrl(url);
    if (allowed) shell.openExternal(allowed);
    return allowed;
  };
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    openExternal(url);
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) {
      event.preventDefault();
      openExternal(url);
    }
  });

  if (IS_DEV) mainWindow.webContents.openDevTools({ mode: 'detach' });
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/** Меню: шаблон в `app-menu.js`, здесь только сборка в меню Electron. */
function buildMenu({ isDev = IS_DEV } = {}) {
  return Menu.buildFromTemplate(
    appMenu.menuTemplate({ isDev, openRoot: () => ROOT && shell.openPath(ROOT), showAbout }),
  );
}

function showAbout() {
  const version = project ? project.version() : { version: null };
  const text = appMenu.aboutText({
    version: version.version,
    root: ROOT,
    electron: process.versions.electron,
    node: process.versions.node,
    chrome: process.versions.chrome,
    platform: process.platform,
    arch: process.arch,
  });
  dialog.showMessageBox(mainWindow || undefined, {
    type: 'info',
    title: text.title,
    message: text.message,
    detail: text.detail,
    buttons: ['Закрыть'],
  });
}

/** IPC: один канал на раздел. Возвращаем данные либо {error} — без исключений. */
function registerIpc(getProject) {
  const sections = {
    version: (p) => p.version(),
    genres: (p) => p.genres(),
    modules: (p) => p.modules(),
    readiness: (p) => p.readiness(),
    dossiers: (p) => p.dossiers(),
    system: (p) => p.systemInfo(),
  };

  for (const [name, loader] of Object.entries(sections)) {
    ipcMain.handle(`zsmm:${name}`, () => {
      const active = getProject();
      if (!active) return { error: 'проект не открыт' };
      try {
        return { data: loader(active) };
      } catch (err) {
        return { error: err && err.message ? err.message : String(err) };
      }
    });
  }

  ipcMain.handle('zsmm:tasks', () => ({ ok: true, data: tasks.taskList() }));

  // Рендер, банк и сохранения бита живут в beat-service.js. Отсюда передаём
  // только то, что умеет Electron: диалоги и путь к каталогу музыки.
  beatService.registerBeatIpc({
    ipcMain,
    dialog,
    rootDir: SAMPLE_ROOT || path.resolve(__dirname, '..', '..'),
    getWindow: () => mainWindow,
    musicDir: safeMusicDir,
  });

  ipcMain.handle('zsmm:task-start', async (event, { key, options } = {}) => {
    if (activeTask) {
      return { ok: false, error: 'уже выполняется другая задача: сначала остановите её' };
    }
    const { python, error } = resolvePython({ root: ROOT, env: process.env });
    if (!python) return { ok: false, error };
    try {
      const sender = event.sender;
      activeTask = tasks.runTask({
        key,
        options: options || {},
        python,
        root: ROOT || path.resolve(__dirname, '..', '..'),
        onEvent: (payload) => {
          if (!sender.isDestroyed()) sender.send('zsmm:task-event', payload);
        },
      });
      activeTask.done.then((result) => {
        activeTask = null;
        if (!sender.isDestroyed()) sender.send('zsmm:task-done', result);
      });
      return { ok: true, data: { pid: activeTask.pid, command: activeTask.command } };
    } catch (err) {
      activeTask = null;
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle('zsmm:task-stop', () => {
    if (!activeTask) return { ok: false, error: 'нет запущенной задачи' };
    return { ok: true, data: { stopped: activeTask.stop() } };
  });

  ipcMain.handle('zsmm:reveal-root', async () => {
    if (!ROOT) return { ok: false, error: rootInfo.error };
    const error = await shell.openPath(ROOT);
    return { ok: error === '', error: error || null, root: ROOT };
  });

  ipcMain.handle('zsmm:open-external', async (_event, url) => {
    const allowed = policy.externalUrl(url);
    if (!allowed) return { ok: false, error: 'разрешены только http(s)-ссылки' };
    await shell.openExternal(allowed);
    return { ok: true };
  });

  ipcMain.handle('zsmm:settings-load', () => {
    const { value, error, errors } = settings().load();
    return { ok: true, data: { ...value, error, invalid: errors } };
  });

  ipcMain.handle('zsmm:settings-save', (_event, patch) => {
    const { value, error } = settings().save(patch);
    return { ok: error === null, data: value, error };
  });

  // Всё, что отличает «работает в репозитории» от «работает на Windows
  // после установки»: пути, наличие Python, каталог настроек.
  ipcMain.handle('zsmm:environment', () => {
    const python = resolvePython({ root: ROOT, env: process.env });
    return {
      ok: true,
      data: {
        version: app.getVersion(),
        packaged: app.isPackaged,
        root: ROOT,
        rootCandidates: rootInfo.candidates,
        rootError: rootInfo.error,
        user_data: (() => {
          try {
            return app.getPath('userData');
          } catch {
            return null;
          }
        })(),
        music_dir: safeMusicDir(),
        python: python.python,
        python_error: python.error,
        platform: process.platform,
        arch: process.arch,
        electron: process.versions.electron || null,
        node: process.versions.node,
        chrome: process.versions.chrome || null,
        worker_render: true,
      },
    };
  });
}

/** Каталог для сохранений по умолчанию (Windows 11: «Музыка» пользователя). */
function safeMusicDir() {
  try {
    const dir = app.getPath('music');
    if (dir) return dir;
  } catch {
    /* без графической среды пути может не быть */
  }
  return path.join(require('node:os').tmpdir(), 'zsmm');
}

function defaultBeatPath() {
  return beatService.defaultBeatPath(safeMusicDir);
}

function saveTextCopy(args = {}, window = mainWindow) {
  return beatService.saveTextCopy({ ...args, dialog, getWindow: () => window, musicDir: safeMusicDir });
}

/** `--smoke`: проверка без окна. Логика — в `electron/smoke.js`. */
async function runSmoke() {
  const report = await smoke.runSmoke({
    root: ROOT,
    rootError: rootInfo.error,
    createProject: () => projectFor(),
    packaged: app.isPackaged,
    electron: process.versions.electron,
  });
  smoke.writeReport(report, { env: process.env, writeFile: fs.writeFileSync, out: process.stdout });
  app.exit(report.ok ? 0 : 1);
}

/**
 * Второй запуск открывает уже существующее окно.
 *
 * Без этого двойной клик по ярлыку при открытом приложении поднимал второй
 * процесс, который писал те же настройки и тот же файл банка.
 */
function installSingleInstance() {
  const gotLock = app.requestSingleInstanceLock();
  if (!policy.shouldContinueStartup({ gotLock })) {
    // Окно живёт в первом процессе: этому остаётся только выйти.
    app.quit();
    return false;
  }
  app.on('second-instance', () => {
    policy.focusExisting(mainWindow);
  });
  return true;
}

/**
 * Идентификатор для панели задач Windows 11.
 *
 * Ставится только у собранного приложения: в разработке `electron.exe`
 * группируется по своему пути, и смешивать их не надо.
 */
function installAppUserModelId() {
  const id = policy.appUserModelId({ isPackaged: app.isPackaged, platform: process.platform });
  if (!id) return null;
  try {
    app.setAppUserModelId(id);
    return id;
  } catch {
    return null;
  }
}

// Замок берётся до `whenReady`: второй процесс не должен успеть подняться.
const HAS_SINGLE_INSTANCE = installSingleInstance();

app.whenReady().then(() => {
  if (!HAS_SINGLE_INSTANCE) return;
  if (IS_SMOKE) {
    runSmoke().catch((err) => {
      process.stdout.write(`${JSON.stringify({ ok: false, error: err.message })}\n`);
      app.exit(1);
    });
    return;
  }

  // Тёмная тема — не украшение: белые поля в диалогах на тёмном окне
  // выглядят как ошибка отрисовки.
  try {
    nativeTheme.themeSource = 'dark';
  } catch {
    /* старая версия Electron — тема не критична */
  }
  Menu.setApplicationMenu(buildMenu());
  installAppUserModelId();

  if (!ROOT) {
    dialog.showErrorBox('Не удалось найти проект', `${rootInfo.error}\n\nКандидаты:\n${rootInfo.candidates.join('\n')}`);
    app.quit();
    return;
  }
  try {
    project = projectFor();
  } catch (err) {
    dialog.showErrorBox('Не удалось открыть проект', `${err.message}\n\nКорень: ${ROOT}`);
    app.quit();
    return;
  }
  registerIpc(() => project);
  createWindow();
});

app.on('window-all-closed', () => {
  // Дочерний процесс не должен переживать окно.
  if (activeTask) activeTask.stop();
  if (policy.quitsOnAllWindowsClosed(process.platform)) app.quit();
});

app.on('before-quit', () => {
  if (activeTask) activeTask.stop();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

module.exports = {
  projectFor,
  registerIpc,
  buildMenu,
  defaultBeatPath,
  saveTextCopy,
  settings,
  safeMusicDir,
  resolvePython,
  resolveRoot,
  DEFAULTS,
  ROOT,
  rootInfo,
  installSingleInstance,
  installAppUserModelId,
};
