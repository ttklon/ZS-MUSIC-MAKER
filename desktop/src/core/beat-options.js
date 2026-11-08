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

  return {
    value: {
      bpm,
      durationSec,
      genre,
      key,
      seed,
      // 16 бит — формат Python-версии; float32 включается только тестами.
      float32: false,
    },
  };
}

module.exports = { BEAT_LIMITS, DEFAULT_BEAT, sanitizeBeatOptions };
