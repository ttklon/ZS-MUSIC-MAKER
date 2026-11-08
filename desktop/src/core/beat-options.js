'use strict';
/**
 * core/beat-options.js — границы рендера бита и проверка параметров из окна.
 *
 * Живёт отдельно от `electron/main.js`, потому что это чистая логика: её
 * проверяет `node --test` без Electron. Принцип тот же, что у `sanitizeOptions`
 * в `electron/tasks.js`: страница не диктует главному процессу, что делать.
 * Без границ окно может попросить три часа 32-битного стерео и занять всю
 * память процесса.
 */

/** Режимы вокала: без голоса, синтез движком, тестовый дубль, файл. */
const VOCAL_MODES = ['none', 'synth', 'test', 'file'];

const VOCAL_LIMITS = {
  maxTextLength: 600,
  minGain: 0,
  maxGain: 1,
};

const BEAT_LIMITS = {
  minBpm: 40,
  maxBpm: 220,
  minDuration: 2,
  maxDuration: 600,
  maxGenreLength: 64,
  maxKeyLength: 32,
};

const DEFAULT_BEAT = { bpm: 140, durationSec: 20, genre: 'phonk', key: 'A minor' };

/**
 * Проверить параметры рендера.
 *
 * @returns {{value?: object, error?: string}} `error` — текст для окна
 */
function sanitizeBeatOptions(options = {}, limits = BEAT_LIMITS) {
  const source = options && typeof options === 'object' ? options : {};
  const bpm = Number(source.bpm === undefined || source.bpm === null || source.bpm === ''
    ? DEFAULT_BEAT.bpm
    : source.bpm);
  const durationSec = Number(
    source.durationSec === undefined || source.durationSec === null || source.durationSec === ''
      ? DEFAULT_BEAT.durationSec
      : source.durationSec,
  );

  if (!Number.isFinite(bpm) || bpm < limits.minBpm || bpm > limits.maxBpm) {
    return { error: `BPM должен быть от ${limits.minBpm} до ${limits.maxBpm}` };
  }
  if (
    !Number.isFinite(durationSec)
    || durationSec < limits.minDuration
    || durationSec > limits.maxDuration
  ) {
    return {
      error: `длительность должна быть от ${limits.minDuration} до ${limits.maxDuration} секунд`,
    };
  }

  const genre = typeof source.genre === 'string' && source.genre.trim()
    ? source.genre.trim().slice(0, limits.maxGenreLength)
    : DEFAULT_BEAT.genre;
  const key = typeof source.key === 'string' && source.key.trim()
    ? source.key.trim().slice(0, limits.maxKeyLength)
    : DEFAULT_BEAT.key;

  let seed = null;
  if (source.seed !== null && source.seed !== undefined && source.seed !== '') {
    const parsed = Number(source.seed);
    if (!Number.isFinite(parsed)) return { error: 'сид должен быть числом' };
    seed = Math.trunc(parsed);
  }

  // Вокал проверяется вместе с битом: он часть запроса на рендер.
  const vocal = sanitizeVocalOptions(source.vocal);
  if (vocal.error) return { error: vocal.error };

  return {
    value: {
      bpm,
      durationSec,
      genre,
      key,
      seed,
      // 16 бит — формат Python-версии; float32 включается только тестами.
      float32: false,
      // Банк сэмплов включён по умолчанию: живой one-shot лучше синтеза.
      useBank: source.useBank !== false,
      // Вокал едет в том же объекте: рендер получает всё одним запросом.
      vocal,
      vocalFile: vocal.value.file,
    },
  };
}

/**
 * Проверить параметры вокала.
 *
 * Вокал — часть запроса, поэтому его границы проверяются вместе с битом:
 * текст ограничен по длине (иначе строка на 10 000 слогов займёт минуты),
 * уровень — 0…1, режим — из белого списка.
 *
 * @param {object} source
 * @returns {{value: object, error?: string}}
 */
function sanitizeVocalOptions(source = {}) {
  const input = source && typeof source === 'object' ? source : {};
  const mode = typeof input.mode === 'string' ? input.mode.trim() : 'none';
  if (!VOCAL_MODES.includes(mode)) {
    return { error: `режим вокала должен быть один из: ${VOCAL_MODES.join(', ')}` };
  }
  if (mode === 'none') return { value: { mode: 'none', text: '', gain: 0, file: null } };

  const text = typeof input.text === 'string'
    ? input.text.replace(/\s+/g, ' ').trim().slice(0, VOCAL_LIMITS.maxTextLength)
    : '';
  const rawGain = input.gain === undefined || input.gain === null || input.gain === '' ? 0.5 : Number(input.gain);
  const gain = Number.isFinite(rawGain)
    ? Math.min(VOCAL_LIMITS.maxGain, Math.max(VOCAL_LIMITS.minGain, rawGain))
    : 0.5;

  let file = null;
  if (mode === 'file') {
    if (typeof input.file !== 'string' || !input.file.trim()) {
      return { error: 'для режима «файл» нужен путь к WAV' };
    }
    // Путь выбирает диалог, а не страница: принимаем только .wav и только
    // абсолютный путь без переходов вверх.
    file = input.file.trim();
    if (!/\.wav$/i.test(file) || file.split(/[\\/]+/).includes('..')) {
      return { error: 'нужен путь к файлу .wav (без «..»)' };
    }
  }

  return {
    value: {
      mode,
      text: text || 'я читаю твой трек наизусть',
      gain,
      file,
    },
  };
}

module.exports = {
  BEAT_LIMITS,
  DEFAULT_BEAT,
  VOCAL_MODES,
  VOCAL_LIMITS,
  sanitizeBeatOptions,
  sanitizeVocalOptions,
};
