'use strict';
/**
 * core/audio/tuning.js — таблица частот первой октавы.
 *
 * Один источник правды: раньше `ROOT_FREQS` лежал в `voices.js`, а `hook.js`
 * нужен был тот же объект. Дублировать числа нельзя — расхождение в центах
 * слышно как фальшь, но не ловится тестом.
 */

const ROOT_FREQS = {
  C: 261.63,
  'C#': 277.18,
  D: 293.66,
  'D#': 311.13,
  E: 329.63,
  F: 349.23,
  'F#': 369.99,
  G: 392.0,
  'G#': 415.3,
  A: 440.0,
  'A#': 466.16,
  B: 493.88,
};


/** Частота тоники по названию тональности: «A minor» → 440. */
function rootFreq(key) {
  const text = String(key || 'A minor');
  const root = text.includes(' ') ? text.split(' ')[0] : 'A';
  return ROOT_FREQS[root] === undefined ? 440.0 : ROOT_FREQS[root];
}

/** Мажор или нет — по слову в названии тональности. */
function isMajor(key) {
  const text = String(key || 'A minor');
  if (!text.includes(' ')) return false;
  return text.split(' ').pop().toLowerCase().startsWith('maj');
}

module.exports = { ROOT_FREQS, rootFreq, isMajor };

