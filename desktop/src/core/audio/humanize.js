'use strict';
/**
 * core/audio/humanize.js — «человечность»: микротайминг, velocity, варианты.
 *
 * Порт `modules/beat/humanize.py`. Машина слышна из-за ровной сетки, ровной
 * громкости и одинакового удара на каждом шаге — здесь три поправки к этому.
 * Вся случайность приходит извне (`rng`), поэтому seed определяет результат.
 */

// (min_ms, max_ms) — характер инструмента относительно сетки
const PART_FEEL_MS = {
  kick: [-1.2, 1.4],
  snare: [2.0, 7.0],
  clap: [3.0, 9.0],
  hat: [-3.0, 2.4],
  bass: [0.4, 3.6],
  melody: [1.0, 6.0],
};

const ACCENT_STEPS = new Set([0, 4, 8, 12]);
const GHOST_VELOCITY = 0.28;

/** Смещение удара в миллисекундах (может быть отрицательным — «раньше сетки»). */
function timingOffsetMs(rng, part, step, bar, swing = 0.0, stepMs = 117.0) {
  const [low, high] = PART_FEEL_MS[part] || [-2.0, 2.0];
  let offset = rng.uniform(low, high);
  // Свинг двигает только нечётные шестнадцатые: это и есть «качание».
  if (swing && step % 2 === 1) offset += Math.abs(swing) * stepMs * 0.5;
  // Раз в 4 такта инструмент «дышит» на пол-миллисекунды сильнее.
  if (bar % 4 === 3) offset += rng.uniform(-0.5, 0.5);
  return offset;
}

/** Громкость удара: акцент на сильной доле, ±12 % джиттера, ghost ≤ 30 %. */
function velocityGain(rng, part, step, bar, ghost = false) {
  if (ghost) return GHOST_VELOCITY * rng.uniform(0.85, 1.15);
  let gain = rng.uniform(0.88, 1.12);
  if (ACCENT_STEPS.has(step)) gain *= 1.09;
  if ((part === 'hat' || part === 'snare') && rng.next() < 0.06) {
    // редкий «недобор» — человеческая неровность, а не ошибка паттерна
    gain *= 0.72;
  }
  if (bar % 8 === 7 && part === 'snare') gain *= 0.94;
  return gain;
}

/**
 * Ghost-нота на слабой доле: тихий удар, который «оживляет» грув.
 *
 * `part` принимается ради совпадения с Python-сигнатурой, но на решение не
 * влияет: там он тоже не используется.
 */
function ghostNote(rng, part, step, probability = 0.18, steps = [3, 6, 11, 14]) {
  if (!steps.includes(step)) return false;
  return rng.next() < probability;
}

/** Round-robin выбор варианта сэмпла/тембра. */
function variantIndex(rng, count) {
  if (count <= 1) return 0;
  return Math.min(count - 1, Math.trunc(rng.next() * count));
}

/** Последний такт фразы — место для сбивки. */
function isFillBar(bar, every = 8) {
  return every > 0 && bar % every === every - 1;
}

/** Шаги сбивки в конце фразы (малый барабан 32-ми): только на fill-такте. */
function ghostRollSteps(isFill, humanize = true) {
  if (!isFill || !humanize) return [];
  return [13, 14, 15];
}

module.exports = {
  PART_FEEL_MS,
  ACCENT_STEPS,
  GHOST_VELOCITY,
  timingOffsetMs,
  velocityGain,
  ghostNote,
  variantIndex,
  isFillBar,
  ghostRollSteps,
};
