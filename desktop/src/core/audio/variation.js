'use strict';
/**
 * core/audio/variation.js — микро-вариативность такта.
 *
 * Порт `bar_variant()` из `modules/beat/variation.py`: один и тот же такт,
 * повторённый восемь раз, слышится как машина, даже если каждый удар чуть
 * «человечен». Здесь меняется сам рисунок: пропущенный хэт, добавленный
 * офф-бит, тихая ghost-нота малого, «дыхание» громкости такта.
 *
 * Сильные доли (0, 4, 8, 12) не трогаются никогда — иначе поедет грув.
 * Метрика `repetitionReport` из Python-версии сюда не портирована: она нужна
 * для отчёта и требует FFT-признаков; честно помечено в README.
 */

const ANCHOR_STEPS = new Set([0, 4, 8, 12]);
const HAT_STEPS = [2, 6, 10, 14, 3, 7, 11, 15];
const GHOST_SNARE_STEPS = [7, 9, 15];

/**
 * Изменения рисунка для конкретного такта (детерминированно).
 *
 * Возвращает `skipHatSteps`, `extraHatSteps`, `ghostSnareSteps`,
 * `barGainDb` и короткую `signature` для отладки.
 */
function barVariant(rng, bar, section, strength = 1.0) {
  const amount = Math.max(0, Number(strength) || 0);
  let skip = [];
  let extra = [];
  let ghost = [];
  let gainDb = 0.0;

  // Вариация включается не в каждом такте: рисунок должен «дышать», а не
  // сыпаться. Вероятность тем выше, чем сильнее запрос.
  if (rng.next() < 0.55 * amount) {
    const candidates = HAT_STEPS.filter((step) => !ANCHOR_STEPS.has(step));
    skip = [candidates[Math.trunc(rng.next() * candidates.length)]];
  }

  if (rng.next() < 0.35 * amount) {
    const pool = [7, 15].filter((step) => !skip.includes(step));
    if (pool.length) extra = [pool[Math.trunc(rng.next() * pool.length)]];
  }

  if (['verse', 'hook', 'chorus', 'pre_chorus'].includes(section) && rng.next() < 0.22 * amount) {
    const pool = GHOST_SNARE_STEPS.filter((step) => !skip.includes(step));
    if (pool.length) ghost = [pool[Math.trunc(rng.next() * pool.length)]];
  }

  // Каждый четвёртый такт фразы — чуть тише или чуть громче (дыхание фразы).
  if (bar % 8 === 7) {
    gainDb = rng.uniform(-0.35, 0.15);
  } else if (rng.next() < 0.5) {
    gainDb = rng.uniform(-0.15, 0.15);
  }

  return {
    skipHatSteps: skip,
    extraHatSteps: extra,
    ghostSnareSteps: ghost,
    barGainDb: Math.round(gainDb * 100) / 100,
    signature: `b${bar}:${skip.length ? 's' : '-'}${extra.length ? 'x' : '-'}${ghost.length ? 'g' : '-'}`,
  };
}

module.exports = { ANCHOR_STEPS, HAT_STEPS, GHOST_SNARE_STEPS, barVariant };
