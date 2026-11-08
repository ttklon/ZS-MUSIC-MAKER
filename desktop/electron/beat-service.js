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
function registerBeatIpc({ ipcMain, dialog, rootDir, getWindow, musicDir, onProgressSender }) {
  // Банк один на процесс: декодированные one-shot'ы кэшируются, повторный
  // рендер не перечитывает 32 файла.
  const bankProvider = createBankProvider({ rootDir });

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
        result = await renderInWorker({
          options,
          rootDir,
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

    'zsmm:beat-save': async (_event, wavBase64) => saveBeat({ dialog, getWindow, musicDir, wavBase64 }),

    'zsmm:save-copy': async (_event, { name, text } = {}) => saveTextCopy({ dialog, getWindow, musicDir, name, text }),
  };

  for (const [channel, handler] of Object.entries(handlers)) ipcMain.handle(channel, handler);

  return { bankProvider, handlers };
}

/** Сохранить WAV через диалог. base64 проверяется до записи. */
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
  registerBeatIpc,
  saveBeat,
  saveTextCopy,
  defaultBeatPath,
};
