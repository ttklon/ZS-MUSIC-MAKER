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

const { app, BrowserWindow, ipcMain, shell, dialog, Menu, nativeTheme, screen } = require('electron');
const path = require('node:path');
const { createDiagnostics, registerDiagnostics } = require('./startup-diagnostics');
const diagnostics = createDiagnostics(path.join(app.getPath('userData'), 'logs'));
const fs = require('node:fs');
const fsp = require('node:fs/promises');

const { createNodeFs } = require('../src/core/fs-node');
const { createProject } = require('../src/core/project');
const beatService = require('./beat-service');
const smoke = require('./smoke');
const { resolveRoot, resolvePython, resolvePipelineRoot } = require('./runtime');
const { createSettingsStore, DEFAULTS } = require('./settings');
const { registerTaskIpc } = require('./task-runner');
const agentService = require('./agent-service');
const shellService = require('./shell-service');
const { registerUpdaterIpc } = require('./updater-service');
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
// Сервис бита: нужен, чтобы знать, идёт ли рендер, когда окно закрывают.
let beatIpc = null;
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

/**
 * Рендер, банк сэмплов, сохранения бита и вокальный вход — в `beat-service.js`.
 *
 * Здесь остаётся только то, что умеет Electron: диалоги, выход в системный
 * плеер и каталог «Музыка». Вынесено отдельной функцией, потому что блок
 * вырос и main.js перевалил за лимит 400 строк (тест `ui-contract`).
 *
 * Это место однажды уже потерялось при разборе main.js на модули:
 * `registerBeatIpc` остался в модуле, но его перестали звать, и все каналы
 * бита (`zsmm:beat-*`, `zsmm:vocal-*`) оказались не зарегистрированы —
 * «Собрать бит» в собранном приложении не работал бы вовсе. Структурный тест
 * `ui-contract` теперь сверяет preload с регистрацией каналов.
 */
function wireBeatIpc() {
  return beatService.registerBeatIpc({
    ipcMain,
    dialog,
    // Python нужен индексации записи в голосовое хранилище: путь ищется той
    // же функцией, что и для задач, чтобы окно не угадывало интерпретатор.
    python: resolvePython,
    pipelineRoot: resolvePipelineRoot,
    rootDir: SAMPLE_ROOT || path.resolve(__dirname, '..', '..'),
    getWindow: () => (windows ? windows.get() : null),
    musicDir: safeMusicDir,
    // Открытие готового WAV в системном плеере: `shell.openPath` — то же,
    // что двойной щелчок по файлу в проводнике Windows.
    openPath: async (file) => {
      const error = await shell.openPath(file);
      return error || null;
    },
    // Прогресс рендера виден и в панели задач: свёрнутое окно иначе выглядит
    // зависшим. Значение считает window-policy (там же и тест).
    onProgressSender: (event, progress) => {
      if (windows) windows.showTaskbarProgress(progress);
      if (event && event.sender && !event.sender.isDestroyed()) {
        event.sender.send('zsmm:beat-progress', progress);
      }
    },
  });
}

/**
 * Агентик: запуск через общий белый список задач и открытие мастера.
 *
 * Вынесено из `registerIpc`, чтобы главный файл не превращался в свалку
 * каналов: правило проекта — файл окна не длиннее 400 строк (тест
 * `ui-contract`).
 */
function wireAgentIpc(taskIpc) {
  const shellOpen = async (file) => (await shell.openPath(file)) || null;
  return agentService.registerAgentIpc({
    ipcMain,
    fsApi: fs,
    audioRoots: [ROOT && path.join(ROOT, 'output', 'hits'),
      app.isPackaged && path.join(app.getPath('userData'), 'workspace', 'output', 'hits')].filter(Boolean),
    startAgent: (options) => taskIpc.start('agent-hit', options),
    openPath: shellOpen,
  });
}

/** IPC: один канал на раздел. Возвращаем данные либо {error} — без исключений. */
function registerIpc(getProject) {
  registerDiagnostics({ ipcMain, diagnostics, dialog });
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
  // Регистратор задач отдаётся наружу: агентику нужен тот же путь запуска
  // (`zsmm:task-start`), а не второй процесс-лаунчер. «Сделать хит» —
  // единственная кнопка, которая обязана вернуть файл, поэтому её канал
  // (`zsmm:agent-hit` + открытие мастера) регистрируется сразу за задачами.
  wireAgentIpc(registerTaskIpc({
    pythonUserBase: path.join(app.getPath('userData'), 'python-packages'),
    workspaceRoot: app.isPackaged ? path.join(app.getPath('userData'), 'workspace') : null,
    ipcMain,
    root: ROOT,
    getProject,
    getWindows: () => windows,
    // Галочка сети в окне — единственный источник согласия пользователя:
    // без этого моста Python-задачи видели `network disabled` при включённой
    // в приложении сети.
    getSettings: () => settings().load().value,
    state: taskState,
  }));

  // Обновления в один клик: кнопка в приложении скачивает релиз с GitHub и ставит поверх
  try {
    registerUpdaterIpc({ ipcMain, root: ROOT, settingsStore: settings(), app, shell,
      confirmInstall: async installerPath => {
        const { response } = await dialog.showMessageBox({
          type: 'warning', buttons: ['Отмена', 'Установить'], defaultId: 0, cancelId: 0,
          title: 'Установка обновления',
          message: 'Запустить установщик и закрыть приложение?',
          detail: `Сохраните работу. Файлы приложения будут заменены.\n${installerPath}`,
        });
        return response === 1;
      },
    });
  } catch (e) {
    console.error('updater ipc failed', e);
  }

  beatIpc = wireBeatIpc();

  // «О системе»-каналы (корень, ссылки, настройки, окружение) — в
  // `shell-service.js`: registerIpc остаётся списком вызовов.
  shellService.registerShellIpc({
    ipcMain,
    root: ROOT,
    rootInfo,
    shell,
    policy,
    settings,
    safeMusicDir,
    dossierPlan,
    resolvePython,
    resolvePipelineRoot,
    versions: process.versions, getUserData: () => app.getPath('userData'), isPackaged: app.isPackaged,
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
  // Позиция окна восстанавливается только на подключённом экране: монитор
  // могли отключить между запусками.
  screen,
  dev: IS_DEV,
  // Рендер идёт в главном процессе: только он знает, что окно закрывают
  // посреди сборки.
  isRendering: () => Boolean(beatIpc && beatIpc.isRendering && beatIpc.isRendering()),
  cancelRender: () => (beatIpc && beatIpc.cancelRender ? beatIpc.cancelRender() : false),
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
  const mainWindow = windows.create(project);
  require('./window-startup-check').checkWindow(mainWindow, app);
  mainWindow.webContents.on('preload-error', (_e, _file, error) => diagnostics.record('preload', error));
  mainWindow.webContents.on('did-fail-load', (_e, code, description) => diagnostics.record('load', `${code}: ${description}`));
}).catch(err => {
  diagnostics.record('startup', err);
  dialog.showErrorBox('Не удалось запустить приложение', String(err.message || err) + '\nЖурнал: ' + diagnostics.file);
  app.quit();
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
