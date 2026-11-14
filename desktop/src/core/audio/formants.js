'use strict';
/**
 * core/audio/formants.js — артикуляция: гласные, согласные, перевод букв.
 *
 * Таблицы вынесены из `vocal.js` отдельным модулем по двум причинам:
 *  - это данные, а не алгоритм: их правят (и сверяют с измерениями) отдельно
 *    от синтеза;
 *  - `vocal.js` перешагнул предел в 400 строк, который проверяется тестом.
 *
 * Значения формант — усреднённые певческие (мужской голос, близкий к
 * «нейтральному»). Проверяются не «на слух», а измерением передаточной
 * функции фильтра: `test/vocal-measure.test.js`.
 */

/**
 * Гласные: форманты в герцах и относительная громкость.
 *
 * Значения — усреднённые певческие форманты (мужской голос, близко к
 * «нейтральному»): F1 отвечает за «открытость», F2 — за ряд (у/и/а), F3 —
 * за индивидуальность тембра.
 */
const VOWELS = {
  a: { f: [800, 1150, 2900], gain: 1.0 },
  o: { f: [500, 900, 2600], gain: 0.95 },
  u: { f: [350, 700, 2500], gain: 0.85 },
  e: { f: [500, 1800, 2700], gain: 0.95 },
  i: { f: [320, 2200, 3000], gain: 0.9 },
  y: { f: [380, 1500, 2600], gain: 0.85 },
  ɑ: { f: [800, 1150, 2900], gain: 1.0 },
  æ: { f: [700, 1700, 2800], gain: 0.95 },
};

/** Согласные: тип шума и его длина в секундах. */
const CONSONANTS = {
  s: { kind: 'fricative', center: 6500, bw: 3000, dur: 0.09, gain: 0.35 },
  sh: { kind: 'fricative', center: 3200, bw: 1800, dur: 0.1, gain: 0.32 },
  f: { kind: 'fricative', center: 4500, bw: 4000, dur: 0.07, gain: 0.25 },
  h: { kind: 'aspirate', center: 1800, bw: 2500, dur: 0.06, gain: 0.22 },
  t: { kind: 'stop', center: 4000, bw: 2500, dur: 0.03, gain: 0.4 },
  k: { kind: 'stop', center: 2500, bw: 1800, dur: 0.03, gain: 0.4 },
  p: { kind: 'stop', center: 1200, bw: 1200, dur: 0.03, gain: 0.35 },
  b: { kind: 'voiced_stop', center: 900, bw: 900, dur: 0.04, gain: 0.3 },
  d: { kind: 'voiced_stop', center: 2500, bw: 1500, dur: 0.04, gain: 0.3 },
  g: { kind: 'voiced_stop', center: 1800, bw: 1200, dur: 0.04, gain: 0.3 },
  m: { kind: 'nasal', center: 250, bw: 200, dur: 0.06, gain: 0.35 },
  n: { kind: 'nasal', center: 300, bw: 220, dur: 0.06, gain: 0.35 },
  l: { kind: 'liquid', center: 900, bw: 600, dur: 0.05, gain: 0.3 },
  r: { kind: 'liquid', center: 1300, bw: 700, dur: 0.05, gain: 0.32 },
  v: { kind: 'voiced_fricative', center: 2000, bw: 1500, dur: 0.05, gain: 0.22 },
  z: { kind: 'voiced_fricative', center: 5000, bw: 2500, dur: 0.07, gain: 0.25 },
  zh: { kind: 'voiced_fricative', center: 3000, bw: 1500, dur: 0.08, gain: 0.26 },
  ch: { kind: 'fricative', center: 3500, bw: 1500, dur: 0.08, gain: 0.32 },
  ts: { kind: 'fricative', center: 5000, bw: 2000, dur: 0.08, gain: 0.3 },
  kh: { kind: 'fricative', center: 2200, bw: 1200, dur: 0.07, gain: 0.26 },
};

// Русские буквы → гласная или согласный. Й и ь/ъ не несут слога.
const RU_VOWELS = { а: 'a', о: 'o', у: 'u', э: 'e', е: 'e', и: 'i', ы: 'y', ё: 'o', ю: 'u', я: 'a' };
const RU_CONSONANTS = {
  б: 'b', в: 'v', г: 'g', д: 'd', ж: 'zh', з: 'z', й: 'l', к: 'k', л: 'l', м: 'm',
  н: 'n', п: 'p', р: 'r', с: 's', т: 't', ф: 'f', х: 'kh', ц: 'ts', ч: 'ch', ш: 'sh', щ: 'sh',
};


module.exports = { VOWELS, CONSONANTS, RU_VOWELS, RU_CONSONANTS };
