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
const { resolveRoot, resolvePython, resolvePipelineRoot } = require('./runtime');
const { createSettingsStore, DEFAULTS } = require('./settings');
const { registerTaskIpc } = require('./task-runner');
const policy = require('./window-policy');
const appMenu = require('./app-menu');
const appPaths = require('./app-paths');
const writableData = require('./writable-data');
const { registerProjectIpc } = require('./ipc-project');
const startup = require('./startup');
const { createWindowManager } = require('./window');

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

let windows = null;
let project = null;
// Запущенная задача живёт здесь: её видит и `task-runner.js`, и выход.
const taskState = { activeTask: null, dossierDir: null, userData: null };
let settingsStore = null;

function settings() {
  if (!settingsStore) {
    settingsStore = createSettingsStore({ dir: app.getPath('userData') });
  }
  return settingsStore;
}

function projectFor(root = ROOT, fileSystem = createNodeFs()) {
  return createProject(fileSystem, root, { dossierDir: dossierPlan().dir });
}

/**
 * Каталог досье и докладка демо-артиста — в `writable-data.js`: в
 * установленной сборке `resources/project` лежит в Program Files, где
 * обычному пользователю писать нельзя.
 */
let dossierPlanCache = null;
function dossierPlan() {
  if (!dossierPlanCache) {
    dossierPlanCache = writableData.prepareDossierStore({
      packaged: app.isPackaged,
      projectRoot: ROOT || path.resolve(__dirname, '..', '..'),
      userData: (() => {
        try {
          return app.getPath('userData');
        } catch {
          return null;
        }
      })(),
    });
  }
  return dossierPlanCache;
}

/** Каталог «Музыка» (Windows 11) либо запасной путь — см. app-paths.js. */
function safeMusicDir() {
  return appPaths.musicDir(app);
}

/** `zsmm:save-copy` вне IPC: окно отчёта не должно зависеть от регистрации. */
function saveTextCopy(args = {}, window = null) {
  const target = window || (windows ? windows.get() : null);
  return beatService.saveTextCopy({ ...args, dialog, getWindow: () => target, musicDir: safeMusicDir });
}

/** Меню: шаблон в `app-menu.js`, сборка в меню Electron — здесь. */
function buildMenu({ isDev = IS_DEV } = {}) {
  const dataDir = dossierPlan().dir;
  return Menu.buildFromTemplate(
    appMenu.menuTemplate({
      isDev,
      openRoot: () => ROOT && shell.openPath(ROOT),
      showAbout,
      // Досье в установленной сборке лежит в каталоге пользователя, а не
      // рядом с программой: путь должен открываться одним пунктом меню.
      openDossier: () => shell.openPath(dataDir),
      // F5 перечитывает данные раздела. Это не перезагрузка страницы:
      // собранный бит при этом не теряется.
      reloadView: () => {
        const window = windows && windows.get();
        if (window && !window.webContents.isDestroyed()) window.webContents.send('zsmm:refresh');
      },
    }),
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
  dialog.showMessageBox((windows && windows.get()) || undefined, {
    type: 'info',
    title: text.title,
    message: text.message,
    detail: text.detail,
    buttons: ['Закрыть'],
  });
}

/** IPC: один канал на раздел. Возвращаем данные либо {error} — без исключений. */
function registerIpc(getProject) {
  // Данные проекта — в ipc-project.js: шесть однотипных загрузчиков не должны
  // занимать место рядом с окном и задачами.
  registerProjectIpc({
    ipcMain,
    getProject,
    root: ROOT,
    // Писать досье в `resources/project` нельзя (Program Files): каналы
    // получают каталог пользователя, а раздел «Диагностика» — причину.
    dataDir: dossierPlan().source === 'user' ? dossierPlan().dir : null,
  });

  // Запуск задач — в `task-runner.js`: там же проверка, что пайплайн на
  // месте (в установщике есть только данные проекта), и одна активная
  // задача на окно.
  // `dossierDir` нужен нативной сводке по досье: в установленной сборке она
  // читает каталог пользователя, а не `resources/project`.
  taskState.dossierDir = dossierPlan().source === 'user' ? dossierPlan().dir : null;
  // Самодиагностике окна нужен каталог настроек: запись туда проверяется
  // на настоящем файле, а не «на глаз».
  try {
    taskState.userData = app.getPath('userData');
  } catch {
    taskState.userData = null;
  }
  registerTaskIpc({
    ipcMain,
    root: ROOT,
    getProject,
    getWindows: () => windows,
    state: taskState,
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
    const pipeline = resolvePipelineRoot({ root: ROOT });
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
        // Где приложение ведёт досье и почему: в установленной сборке
        // `resources/project` только для чтения.
        dossier_dir: dossierPlan().dir,
        dossier_source: dossierPlan().source === 'user'
          ? 'каталог пользователя: каталог установки только для чтения'
          : 'каталог проекта: приложение запущено из репозитория',
        python: python.python,
        python_error: python.error,
        // Пайплайн — отдельная вещь от интерпретатора: «Python есть» не
        // значит «задачи раздела „Запуск“ заработают».
        pipeline_root: pipeline.root,
        pipeline_error: pipeline.error,
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

// Окно и всё, что к нему привязано, — в window.js: main.js остаётся про
// запуск, IPC и меню.
windows = createWindowManager({
  BrowserWindow,
  shell,
  dialog,
  settings,
  dev: IS_DEV,
});

// Замок берётся до `whenReady`: второй процесс не должен успеть подняться.
const HAS_SINGLE_INSTANCE = startup.installSingleInstance({
  app,
  getWindow: () => windows.get(),
});

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
  startup.installAppUserModelId({ app, platform: process.platform });

  if (!ROOT) {
    dialog.showErrorBox('Не удалось найти проект', `${rootInfo.error}\n\nКандидаты:\n${rootInfo.candidates.join('\n')}`);
    app.quit();
    return;
  }
  // Первый запуск установленной сборки: демо-артист и схема копируются в
  // каталог пользователя, иначе раздел «Досье» открылся бы пустым.
  if (dossierPlan().seeded.length) {
    process.stdout.write(`досье: скопировано ${dossierPlan().seeded.length} файл(ов) в каталог пользователя\n`);
  }
  if (dossierPlan().error) process.stdout.write(`${dossierPlan().error}\n`);
  try {
    project = projectFor();
  } catch (err) {
    dialog.showErrorBox('Не удалось открыть проект', `${err.message}\n\nКорень: ${ROOT}`);
    app.quit();
    return;
  }
  registerIpc(() => project);
  windows.create(project);
});

app.on('window-all-closed', () => {
  // Дочерний процесс не должен переживать окно.
  if (taskState.activeTask) taskState.activeTask.stop();
  if (policy.quitsOnAllWindowsClosed(process.platform)) app.quit();
});

app.on('before-quit', () => {
  if (taskState.activeTask) taskState.activeTask.stop();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) windows.create(project);
});

module.exports = {
  projectFor,
  registerIpc,
  buildMenu,
  saveTextCopy,
  settings,
  safeMusicDir,
  resolvePython,
  resolveRoot,
  DEFAULTS,
  ROOT,
  rootInfo,
};
