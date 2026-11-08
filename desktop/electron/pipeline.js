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
const { sanitizeBeatOptions, sanitizeVocalOptions } = require('../src/core/beat-options');
const { createNodeFs } = require('../src/core/fs-node');
const takes = require('../src/core/audio/takes');

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
 * Собрать вокальный дубль по параметрам окна.
 *
 * Окно не присылает аудио: оно присылает режим, текст и (для файла) путь,
 * выбранный в системном диалоге. Файл читается здесь, чтобы рендер-поток и
 * главный процесс считали одно и то же.
 *
 * @param {object} sanitized проверенные параметры бита
 * @param {object} context   `{ vocalOptions, fileSystem, rootDir }`
 * @returns {{take: object|null, gain: number, error?: string}}
 */
function buildVocal(sanitized, context = {}) {
  // `sanitizeBeatOptions` уже вернул `{value: {...}}`: берём вложенное значение.
  // Ошибка здесь была бы тихой — вокал просто не появился бы в миксе.
  const raw = context.vocalOptions || (sanitized.vocal && sanitized.vocal.value) || sanitized.vocal || { mode: 'none' };
  const checked = sanitizeVocalOptions(raw);
  if (checked.error) return { take: null, gain: 0, error: checked.error };
  const options = checked.value;
  if (options.mode === 'none') return { take: null, gain: 0 };

  const seconds = Math.max(2, Number(sanitized.durationSec) || 20);
  const seed = sanitized.seed === null || sanitized.seed === undefined ? 7 : sanitized.seed;
  // Мелодия строится из текста: сколько слогов — столько нот, иначе вокал
  // обрывается на середине строки или тянет пустые ноты.
  const syllables = require('../src/core/audio/vocal').splitSyllables(options.text || '');
  const midi = require('../src/core/audio/vocal').melodyFor({
    key: sanitized.key || 'A minor',
    count: Math.max(1, syllables.length || 8),
    seed,
  });

  if (options.mode === 'test') {
    return {
      take: takes.testTake({ text: options.text, seconds, seed, midiNotes: midi }),
      gain: options.gain,
    };
  }
  if (options.mode === 'synth') {
    return {
      take: takes.synthTake({ text: options.text, seconds, seed, midiNotes: midi }),
      gain: options.gain,
    };
  }

  // Файл: путь пришёл из диалога, но читаем через файловое API проекта,
  // чтобы ошибка была текстом, а не исключением из fs.
  // Читалка вокала может приходить отдельным объектом: у рендер-потока нет
  // доступа к диску пользователя, поэтому главный процесс передаёт сюда
  // минимальный `{exists, readBinary}`.
  const fsApi = context.vocalFileSystem || context.fileSystem || createNodeFs();
  // У `createNodeFs` метод называется `readBinary`; старые имена оставлены
  // для двойников в тестах, но проверяются после него.
  const read = fsApi.readBinary || fsApi.readFileBuffer || fsApi.readFileBinary;
  if (typeof read !== 'function') {
    return { take: null, gain: 0, error: 'файловое API не умеет читать бинарные файлы' };
  }
  if (typeof fsApi.exists === 'function' && !fsApi.exists(options.file)) {
    return { take: null, gain: 0, error: `вокальный файл не найден: ${options.file}` };
  }
  const readResult = read(options.file);
  if (readResult && readResult.error) {
    return { take: null, gain: 0, error: `вокальный файл не прочитан: ${readResult.error}` };
  }
  const buffer = Buffer.isBuffer(readResult) ? readResult : readResult.value;
  try {
    return { take: takes.loadTake(buffer), gain: options.gain };
  } catch (err) {
    return { take: null, gain: 0, error: `вокальный файл не разобран: ${err.message}` };
  }
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
    // Вокал собирается здесь же, из проверенных параметров: окно не присылает
    // аудио, оно просит «синтез», «тестовый дубль» или «файл из этого пути».
    const vocal = buildVocal(sanitized.value, context);
    if (vocal.error) return { ok: false, error: vocal.error, fatal: true };
    const { wav, report } = await renderBeatInSteps(
      {
        ...sanitized.value,
        bank: sanitized.value.useBank === false ? null : bankFor(),
        vocalTake: vocal.take,
        vocalGain: vocal.gain,
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
  buildVocal,
  createBankProvider,
  renderBeatRequest,
  renderBeatPayload,
};
