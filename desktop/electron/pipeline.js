'use strict';
/**
 * pipeline.js — что именно происходит по кнопке «Собрать бит».
 *
 * Одна функция на все хосты: Electron (`electron/main.js`), предпросмотр
 * (`scripts/preview-server.js`), рендер-поток (`electron/render-worker.js`) и
 * тесты. Раньше эта логика была продублирована в двух IPC-обработчиках, и
 * любое изменение (банк, проверка параметров, прогресс) приходилось делать
 * дважды — то есть один раз забывать.
 *
 * Здесь нет ни `electron`, ни сети: только движок, проверка параметров и
 * источник сэмплов.
 */

const { renderBeatInSteps } = require('../src/core/audio/engine');
const { SampleSource } = require('../src/core/audio/bank');
const { sanitizeBeatOptions } = require('../src/core/beat-options');
const { createNodeFs } = require('../src/core/fs-node');

/**
 * Источник сэмплов с кэшем на процесс.
 *
 * Банк держит декодированные one-shot'ы, поэтому повторный рендер не
 * перечитывает 32 файла. `shared` — кэш, который передаёт вызывающая сторона.
 */
function createBankProvider({ rootDir, fileSystem = createNodeFs(), shared = { source: null } } = {}) {
  return {
    shared,
    bank() {
      if (!shared.source) shared.source = new SampleSource({ fileSystem, rootDir });
      return shared.source;
    },
    reset() {
      shared.source = null;
    },
  };
}

/**
 * Собрать бит.
 *
 * @param {object} options         параметры из окна (проверяются здесь)
 * @param {object} context
 * @param {string} context.rootDir корень проекта (для банка сэмплов)
 * @param {Function} [context.bankFor] вернуть готовый SampleSource
 * @param {Function} [context.onProgress] прогресс по секциям
 * @param {object} [context.fileSystem]
 * @returns {Promise<{ok: true, data: {wav: Buffer, report: object}} | {ok: false, error: string}>}
 */
async function renderBeatRequest(options, context = {}) {
  const sanitized = sanitizeBeatOptions(options);
  // `fatal` — ошибка самих параметров: повторять её в главном процессе
  // бессмысленно (результат будет тот же), поэтому render-host её не ловит.
  if (sanitized.error) return { ok: false, error: sanitized.error, fatal: true };

  // Банк открывается лениво: если галочка «банк сэмплов» снята, 32 файла
  // читаться не должны. Кэш живёт в замыкании вызова (или приходит готовым).
  const provider = context.provider || createBankProvider({
    rootDir: context.rootDir,
    fileSystem: context.fileSystem,
    shared: context.bankCache || { source: null },
  });
  const bankFor = typeof context.bankFor === 'function' ? context.bankFor : () => provider.bank();

  try {
    const { wav, report } = await renderBeatInSteps(
      {
        ...sanitized.value,
        bank: sanitized.value.useBank === false ? null : bankFor(),
      },
      {
        onProgress: typeof context.onProgress === 'function' ? context.onProgress : undefined,
        yieldToEventLoop: context.yieldToEventLoop !== false,
        // Отмена приходит из главного процесса (см. render-host.js):
        // движок проверяет её между секциями.
        isCancelled: typeof context.isCancelled === 'function' ? context.isCancelled : undefined,
      },
    );
    return { ok: true, data: { wav, report } };
  } catch (err) {
    if (err && err.name === 'RenderCancelled') {
      return { ok: false, error: 'рендер отменён', cancelled: true };
    }
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
}

/**
 * Бит в том виде, в котором он уходит через IPC: WAV строкой base64.
 *
 * Buffer по structured clone дошёл бы и так, но base64 не зависит от версии
 * Electron и одинаково работает в предпросмотре и в render-потоке.
 */
async function renderBeatPayload(options, context = {}) {
  const result = await renderBeatRequest(options, context);
  if (result.ok !== true) return result;
  return {
    ok: true,
    data: {
      report: result.data.report,
      wavBase64: result.data.wav.toString('base64'),
    },
  };
}

module.exports = {
  createBankProvider,
  renderBeatRequest,
  renderBeatPayload,
};
