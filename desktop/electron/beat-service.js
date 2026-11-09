'use strict';
/**
 * beat-service.js — IPC вокруг бита: рендер, банк, сохранение.
 *
 * Вынесено из `main.js`, потому что это самая быстрорастущая часть: рендер,
 * прогресс, банк, два сохранения. Зависимости приходят аргументами, поэтому
 * всё проверяется `node --test` без Electron.
 */

const path = require('node:path');
const fsp = require('node:fs/promises');
const { existsSync, readFileSync } = require('node:fs');
const os = require('node:os');

/** Минимальное файловое API для чтения вокального WAV. */
function readBinary(target) {
  try {
    return { value: readFileSync(target) };
  } catch (err) {
    return { error: `${err.code || 'ERR'}: ${err.message}` };
  }
}

const vocalService = require('./vocal-service');
const { renderBeatPayload, createBankProvider } = require('./pipeline');
const { renderInWorker, createCancelSignal } = require('./render-host');

/**
 * @param {object} params
 * @param {object} params.ipcMain     electron ipcMain (или двойник в тестах)
 * @param {object} params.dialog      electron dialog
 * @param {string} params.rootDir     где лежит `data/samples`
 * @param {Function} params.getWindow вернуть окно (для диалогов)
 * @param {Function} params.musicDir  каталог для сохранений по умолчанию
 * @param {Function} [params.python]  для сообщений о разделе «Запуск»
 * @returns {{bankProvider: object, handlers: object}}
 */
function registerBeatIpc({
  ipcMain, dialog, rootDir, getWindow, musicDir, onProgressSender,
  openPath = null, tempDir = require('node:os').tmpdir(),
}) {
  // Банк один на процесс: декодированные one-shot'ы кэшируются, повторный
  // рендер не перечитывает 32 файла.
  const bankProvider = createBankProvider({ rootDir });
  // Минимальное файловое API для вокального WAV: главный процесс умеет
  // читать диск, рендер-поток — нет.
  const vocalFileSystem = {
    exists: (target) => existsSync(target),
    readBinary: (target) => readBinary(target),
  };

  // Отмена живёт на уровне сервиса: одновременно идёт один рендер, и
  // «Отменить» относится именно к нему. Сигнала нет — рендера нет.
  let activeRender = null;

  const handlers = {
    'zsmm:beat-render': async (event, options) => {
      const send = (progress) => {
        if (onProgressSender) onProgressSender(event, progress);
        else if (event && event.sender && !event.sender.isDestroyed()) {
          event.sender.send('zsmm:beat-progress', progress);
        }
      };
      // Основной путь — отдельный поток. Если он недоступен, тот же код
      // считается в главном процессе: пользователь получает бит в любом
      // случае, а отчёт говорит, каким путём (`renderer`).
      const signal = createCancelSignal();
      activeRender = signal;
      let result;
      try {
        // Файл вокала читается в главном процессе через файловое API проекта:
        // рендер-поток не должен сам ходить по произвольным путям.
        result = await renderInWorker({
          options,
          rootDir,
          // Вокальный файл читается здесь: в рендер-поток уходит уже готовый
          // дубль, а не путь по диску пользователя.
          vocalFileSystem,
          onProgress: send,
          signal,
          renderInMain: (opts, ctx) => renderBeatPayload(opts, { ...ctx, bankFor: () => bankProvider.bank() }),
        });
      } finally {
        if (activeRender === signal) activeRender = null;
      }
      if (result.ok !== true) {
        return { ok: false, error: result.error, cancelled: result.cancelled === true };
      }
      return {
        ok: true,
        data: { ...result.data, report: { ...result.data.report, renderer: result.renderer } },
      };
    },

    // «Остановить» во время рендера. Возвращает, было что отменять, — окно
    // не должно показывать «отменено» там, где ничего не шло.
    'zsmm:beat-cancel': () => {
      if (!activeRender) return { ok: true, data: { cancelled: false } };
      const cancelled = activeRender.abort();
      return { ok: true, data: { cancelled } };
    },

    'zsmm:beat-bank': () => {
      try {
        return { ok: true, data: bankProvider.bank().report() };
      } catch (err) {
        return { ok: false, error: err && err.message ? err.message : String(err) };
      }
    },

    // Выбор вокального WAV. Путь выбирает системный диалог: страница не
    // может подсунуть произвольный путь, поэтому чтение файла безопасно.
    'zsmm:vocal-pick': async () => pickVocalFile({ dialog, getWindow }),

    // Готовность входа: есть ли в системе устройства записи. Окно показывает
    // это честно, а не притворяется, что пишет с микрофона.
    'zsmm:vocal-input': async () => ({ ok: true, data: vocalService.describeInput() }),

    // «Открыть в плеере»: готовый WAV пишется во временный файл и отдаётся
    // системе — в окне нет аудиоплеера, который умел бы всё (m4a, flac и т. п.).
    'zsmm:beat-open-external': async (_event, wavBase64) => openInPlayer({
      getWindow, wavBase64, openPath, tmpDir: tempDir,
    }),

    // Дубль, записанный с микрофона в окне: окно присылает те же байты WAV,
    // что держит в памяти. Главный процесс проверяет размер и формат, а не
    // верит на слово: иначе «записью» можно назвать что угодно.
    'zsmm:vocal-save-recording': async (_event, payload) => vocalService.saveRecording({
      dialog, getWindow, musicDir, payload,
    }),

    // Тестовый дубль как файл: пользователь может послушать его отдельно и
    // убедиться, что это именно сгенерированная дорожка, а не «микрофон».
    'zsmm:vocal-export': async (_event, payload) => exportVocalTake({
      dialog, getWindow, musicDir, payload,
    }),

    'zsmm:beat-save': async (_event, wavBase64) => saveBeat({ dialog, getWindow, musicDir, wavBase64 }),

    'zsmm:save-copy': async (_event, { name, text } = {}) => saveTextCopy({ dialog, getWindow, musicDir, name, text }),
  };

  for (const [channel, handler] of Object.entries(handlers)) ipcMain.handle(channel, handler);

  // Идёт ли рендер прямо сейчас. Нужно главному процессу: закрытие окна
  // посреди сборки молча выбрасывало десятки секунд работы.
  const isRendering = () => Boolean(activeRender);
  // Отмена для закрытия: тот же сигнал, что у кнопки «Отменить».
  const cancelRender = () => (activeRender ? activeRender.abort() : false);

  return { bankProvider, handlers, isRendering, cancelRender };
}

/** Диалог выбора WAV для вокального дубля. */
async function pickVocalFile({ dialog, getWindow }) {
  try {
    const { canceled, filePaths } = await dialog.showOpenDialog(getWindow() || undefined, {
      title: 'Выбрать WAV с вокалом',
      properties: ['openFile'],
      filters: [{ name: 'WAV', extensions: ['wav'] }],
    });
    if (canceled || !filePaths || !filePaths.length) return { ok: true, data: { path: null } };
    return { ok: true, data: { path: filePaths[0] } };
  } catch (err) {
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
}

/**
 * Открыть WAV в системном плеере.
 *
 * Возвращаем не «ок», а путь: пользователь должен видеть, какой файл открыт.
 * Временный файл с уникальным именем — чтобы два рендера подряд не
 * перезаписывали друг другу прослушивание.
 */
async function openInPlayer({ getWindow, wavBase64, openPath, tmpDir = os.tmpdir() }) {
  if (typeof wavBase64 !== 'string' || wavBase64.length < 64) {
    return { ok: false, error: 'нет данных для воспроизведения' };
  }
  if (typeof openPath !== 'function') {
    return { ok: false, error: 'системное открытие файлов недоступно' };
  }
  const buffer = Buffer.from(wavBase64, 'base64');
  if (buffer.length < 44 || buffer.subarray(0, 4).toString('ascii') !== 'RIFF') {
    return { ok: false, error: 'это не WAV: воспроизведение отменено' };
  }
  const file = path.join(tmpDir, `zsmm-${Date.now()}-${process.pid}.wav`);
  try {
    await fsp.writeFile(file, buffer);
  } catch (err) {
    return { ok: false, error: `временный файл не записан: ${err.message}` };
  }
  const error = await openPath(file);
  if (error) return { ok: false, error: `плеер не открылся: ${error}` };
  return { ok: true, data: { path: file, seconds: Math.round((buffer.length / 176400) * 10) / 10 } };
}

/**
 * Сохранить тестовый/синтезированный дубль в WAV через диалог.
 *
 * Окно присылает уже готовый WAV в base64 (его собрал движок): главный
 * процесс не синтезирует заново, иначе файл мог бы отличаться от того, что
 * играл в миксе.
 */
async function exportVocalTake({ dialog, getWindow, musicDir, payload = {} }) {
  const { wavBase64, name } = payload;
  if (typeof wavBase64 !== 'string' || wavBase64.length < 64) {
    return { ok: false, error: 'нет данных дубля' };
  }
  const base = String(name || 'vocal-take').replace(/[^\w.-]+/g, '_').slice(0, 80) || 'vocal-take';
  const suggestion = path.join(typeof musicDir === 'function' ? musicDir() : musicDir, `${base}.wav`);
  const { canceled, filePath } = await dialog.showSaveDialog(getWindow() || undefined, {
    title: 'Сохранить вокальный дубль',
    defaultPath: suggestion,
    filters: [{ name: 'WAV', extensions: ['wav'] }],
  });
  if (canceled || !filePath) return { ok: true, data: { path: null, cancelled: true } };
  try {
    await fsp.writeFile(filePath, Buffer.from(wavBase64, 'base64'));
    return { ok: true, data: { path: filePath } };
  } catch (err) {
    return { ok: false, error: `файл не записан: ${err.message}` };
  }
}

async function saveBeat({ dialog, getWindow, musicDir, wavBase64 }) {
  if (typeof wavBase64 !== 'string' || wavBase64.length < 64) {
    return { ok: false, error: 'нет данных для сохранения' };
  }
  const { canceled, filePath } = await dialog.showSaveDialog(getWindow() || undefined, {
    title: 'Сохранить бит',
    defaultPath: defaultBeatPath(musicDir),
    filters: [{ name: 'WAV', extensions: ['wav'] }],
  });
  if (canceled || !filePath) return { ok: false, error: 'сохранение отменено' };
  try {
    const buffer = Buffer.from(wavBase64, 'base64');
    if (buffer.length < 44 || buffer.toString('ascii', 0, 4) !== 'RIFF') {
      return { ok: false, error: 'это не WAV: сохранять нечего' };
    }
    await fsp.mkdir(path.dirname(filePath), { recursive: true });
    await fsp.writeFile(filePath, buffer);
    return { ok: true, data: { path: filePath, bytes: buffer.length } };
  } catch (err) {
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
}

/**
 * Сохранить текстовый отчёт рядом с готовым битом.
 *
 * `name` — только имя файла: окно не должно уметь писать куда угодно.
 */
async function saveTextCopy({ dialog, getWindow, musicDir, name, text }) {
  if (typeof text !== 'string' || !text.trim()) return { ok: false, error: 'отчёт пуст' };
  const safeName = String(name || 'report.json').replace(/[\\/:*?"<>|]/g, '_');
  const { canceled, filePath } = await dialog.showSaveDialog(getWindow() || undefined, {
    title: 'Сохранить отчёт',
    defaultPath: path.join(musicDir(), safeName),
    filters: [
      { name: 'JSON', extensions: ['json'] },
      { name: 'Markdown', extensions: ['md'] },
      { name: 'Текст', extensions: ['txt'] },
    ],
  });
  if (canceled || !filePath) return { ok: false, error: 'сохранение отменено' };
  try {
    await fsp.mkdir(path.dirname(filePath), { recursive: true });
    await fsp.writeFile(filePath, text, 'utf8');
    return { ok: true, data: { path: filePath, bytes: Buffer.byteLength(text, 'utf8') } };
  } catch (err) {
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
}

/**
 * Куда сохранять бит по умолчанию.
 *
 * В установленном приложении корень проекта только для чтения (внутри
 * `resources/`), поэтому по умолчанию берём пользовательский каталог музыки.
 */
function defaultBeatPath(musicDir = () => path.join(require('node:os').tmpdir(), 'zsmm')) {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  return path.join(musicDir(), `beat_${stamp}.wav`);
}

module.exports = {
  openInPlayer,
  exportVocalTake,
  pickVocalFile,
  // Вокальный вход живёт в `vocal-service.js`; имена оставлены здесь, чтобы
  // не ломать тех, кто уже обращается к сервису бита.
  describeInput: vocalService.describeInput,
  recordingToWav: vocalService.recordingToWav,
  saveRecording: vocalService.saveRecording,
  registerBeatIpc,
  saveBeat,
  saveTextCopy,
  defaultBeatPath,
};
