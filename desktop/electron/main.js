'use strict';
/**
 * main.js — главный процесс Electron. Ни Python, ни сеть здесь не участвуют.
 *
 * Окно работает на данных, которые читает этот процесс из файлов проекта
 * (жанры, пресеты, снимок inventory/готовности). Логика вынесена в
 * `src/core/*`, поэтому её проверяет обычный `node --test` без графической
 * среды, а main.js остаётся тонким: окно, IPC, безопасность.
 */

const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');
const { createProject } = require('../src/core/project');
const { renderBeatInSteps } = require('../src/core/audio/engine');
const { SampleSource } = require('../src/core/audio/bank');
const { sanitizeBeatOptions, BEAT_LIMITS } = require('../src/core/beat-options');
const tasks = require('./tasks');

const ROOT = path.resolve(__dirname, '..', '..');
const IS_DEV = process.argv.includes('--dev');

let mainWindow = null;
let project = null;
let activeTask = null;

/** Найти Python: переменная окружения → локальное окружение → система. */
function resolvePython({ root = ROOT, env = process.env } = {}) {
  const candidates = [
    env.ZSMM_PYTHON,
    path.join(root, '.venv', 'bin', 'python3'),
    path.join(root, '.venv', 'Scripts', 'python.exe'),
    '/usr/bin/python3',
    '/usr/local/bin/python3',
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      if (require('node:fs').existsSync(candidate)) return { python: candidate };
    } catch {
      /* путь недоступен — пробуем следующий */
    }
  }
  return {
    python: null,
    error: 'Python не найден. Укажите ZSMM_PYTHON=/путь/к/интерпретатору '
      + 'или создайте .venv в корне проекта.',
  };
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
    backgroundColor: '#0f1115',
    show: false,
    title: 'ZS Music Maker',
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

  // Бит считается здесь, в главном процессе: страница не получает ни `fs`,
  // ни доступа к движку. Наружу уходит готовый WAV в base64 и отчёт.
  //
  // Банк сэмплов открывается один раз на процесс и переиспользуется: он
  // держит декодированные one-shot'ы в кэше, и повторный рендер не
  // перечитывает 32 файла с диска.
  let sampleSource = null;
  const bankFor = () => {
    if (!sampleSource) sampleSource = new SampleSource({ fileSystem: createNodeFs(), rootDir: ROOT });
    return sampleSource;
  };

  ipcMain.handle('zsmm:beat-render', async (event, options) => {
    const sanitized = sanitizeBeatOptions(options);
    if (sanitized.error) return { ok: false, error: sanitized.error };
    try {
      // Рендер режется по секциям: окно живо и получает прогресс, а не
      // замирает на десятки секунд. WAV при этом побайтово тот же, что у
      // синхронного пути (проверяется тестом).
      const { wav, report } = await renderBeatInSteps(
        {
          ...sanitized.value,
          bank: sanitized.value.useBank === false ? null : bankFor(),
        },
        {
          onProgress: (progress) => {
            if (event && event.sender && !event.sender.isDestroyed()) {
              event.sender.send('zsmm:beat-progress', progress);
            }
          },
        },
      );
      return { ok: true, data: { report, wavBase64: wav.toString('base64') } };
    } catch (err) {
      return { ok: false, error: err && err.message ? err.message : String(err) };
    }
  });

  ipcMain.handle('zsmm:beat-bank', () => {
    try {
      return { ok: true, data: bankFor().report() };
    } catch (err) {
      return { ok: false, error: err && err.message ? err.message : String(err) };
    }
  });

  ipcMain.handle('zsmm:beat-save', async (_event, wavBase64) => {
    if (typeof wavBase64 !== 'string' || wavBase64.length < 64) {
      return { ok: false, error: 'нет данных для сохранения' };
    }
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow || undefined, {
      title: 'Сохранить бит',
      defaultPath: path.join(ROOT, 'data', 'beats', `beat_${Date.now()}.wav`),
      filters: [{ name: 'WAV', extensions: ['wav'] }],
    });
    if (canceled || !filePath) return { ok: false, error: 'сохранение отменено' };
    try {
      const buffer = Buffer.from(wavBase64, 'base64');
      if (buffer.length < 44 || buffer.toString('ascii', 0, 4) !== 'RIFF') {
        return { ok: false, error: 'это не WAV: сохранять нечего' };
      }
      await require('node:fs/promises').mkdir(path.dirname(filePath), { recursive: true });
      await require('node:fs/promises').writeFile(filePath, buffer);
      return { ok: true, data: { path: filePath, bytes: buffer.length } };
    } catch (err) {
      return { ok: false, error: err && err.message ? err.message : String(err) };
    }
  });

  ipcMain.handle('zsmm:task-start', async (event, { key, options } = {}) => {
    if (activeTask) {
      return { ok: false, error: 'уже выполняется другая задача: сначала остановите её' };
    }
    const { python, error } = resolvePython();
    if (!python) return { ok: false, error };
    try {
      const sender = event.sender;
      activeTask = tasks.runTask({
        key,
        options: options || {},
        python,
        root: ROOT,
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
}

app.whenReady().then(() => {
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

module.exports = { projectFor, registerIpc, resolvePython, sanitizeBeatOptions, BEAT_LIMITS, ROOT };
