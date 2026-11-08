'use strict';
/**
 * main.js — главный процесс Electron. В окне нет ни Python, ни сети.
 *
 * Окно работает на данных, которые этот процесс читает из файлов проекта
 * (жанры, пресеты, снимок inventory/готовности). Логика вынесена в
 * `src/core/*` и `electron/{runtime,pipeline,render-host}.js`, поэтому её
 * проверяет обычный `node --test` без графической среды, а main.js остаётся
 * тонким: окно, IPC, безопасность.
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
const { renderBeatPayload, createBankProvider } = require('./pipeline');
const beatService = require('./beat-service');
const { resolveRoot, resolvePython } = require('./runtime');
const { createSettingsStore, DEFAULTS } = require('./settings');
const tasks = require('./tasks');

const IS_DEV = process.argv.includes('--dev');
// `--smoke` запускает приложение, проверяет, что проект открылся и данные
// читаются, печатает JSON и выходит с кодом 0/1. Нужен CI: упакованную
// сборку надо чем-то проверить, а графической среды на раннере нет.
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
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 600,
    // Окно красится в тон интерфейсу: без этого при старте видна белая вспышка.
    backgroundColor: '#0f1115',
    show: false,
    title: 'ZS Music Maker',
    icon: path.join(__dirname, '..', 'build', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.loadFile(path.join(__dirname, '..', 'src', 'index.html'));

  // Окно не должно превращаться в браузер: внешние ссылки уходят в систему.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) {
      event.preventDefault();
      if (/^https?:\/\//.test(url)) shell.openExternal(url);
    }
  });

  if (IS_DEV) mainWindow.webContents.openDevTools({ mode: 'detach' });
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Меню приложения.
 *
 * В собранной Windows-сборке меню по умолчанию выглядит как меню браузера:
 * «Reload», «Toggle DevTools», «Zoom». Для приложения это лишнее и опасно
 * (перезагрузка сбрасывает собранный бит), поэтому меню своё: только то, что
 * действительно нужно.
 */
function buildMenu({ isDev = IS_DEV } = {}) {
  const template = [
    {
      label: 'Файл',
      submenu: [
        { label: 'Папка проекта', click: () => ROOT && shell.openPath(ROOT) },
        { type: 'separator' },
        { role: 'quit', label: 'Выход' },
      ],
    },
    {
      label: 'Вид',
      submenu: [
        { role: 'resetZoom', label: 'Обычный масштаб' },
        { role: 'zoomIn', label: 'Крупнее' },
        { role: 'zoomOut', label: 'Мельче' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Во весь экран' },
        ...(isDev ? [{ role: 'reload', label: 'Перезагрузить' }, { role: 'toggleDevTools', label: 'Инструменты' }] : []),
      ],
    },
    {
      label: 'Справка',
      submenu: [
        { label: 'О приложении', click: () => showAbout() },
      ],
    },
  ];
  return Menu.buildFromTemplate(template);
}

function showAbout() {
  const version = project ? project.version() : { version: null };
  dialog.showMessageBox(mainWindow || undefined, {
    type: 'info',
    title: 'ZS Music Maker',
    message: `ZS Music Maker ${version.version ? `v${version.version}` : ''}`.trim(),
    detail: [
      'Бит собирается внутри приложения: движок на JavaScript, без Python и сети.',
      ROOT ? `Проект: ${ROOT}` : 'Проект не найден — задайте ZSMM_ROOT.',
      `Electron ${process.versions.electron}, Node ${process.versions.node}, Chromium ${process.versions.chrome}.`,
      `Платформа: ${process.platform} ${process.arch}.`,
    ].join('\n\n'),
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
    if (typeof url !== 'string' || !/^https?:\/\//.test(url)) {
      return { ok: false, error: 'разрешены только http(s)-ссылки' };
    }
    await shell.openExternal(url);
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

app.whenReady().then(() => {
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
  if (process.platform !== 'darwin') app.quit();
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
};
