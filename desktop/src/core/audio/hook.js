'use strict';
/**
 * core/audio/hook.js — мотив хука: короткий лид, по которому трек узнаётся.
 *
 * Вынесено из `voices.js`: мотив не зависит ни от банка, ни от RNG, это чистая
 * функция от тональности.
 *
 * Честность названия: раньше здесь был **не мотив, а арпеджио** — та же
 * последовательность нот на каждые четыре доли, без памяти и без повтора
 * внутри такта. Узнаваемость от такого «мотива» не появляется: трек звучит
 * ровной гаммой. Теперь это фраза из 8 шагов (полтакта в 16-й сетке) с ритмом
 * и паузами, а `motifLoopForBar` гарантирует, что в припеве звучит **одна и та
 * же** фраза в тех же нотах.
 */

const { movingAverage } = require('./dsp');
const { rootFreq, isMajor } = require('./tuning');

// Ритм фразы в 16-х: индексы шагов, где звучит нота. Паузы — часть мотива,
// именно они делают фразу «липкой», а не потоком нот.
const MOTIF_RHYTHM = {
  minor: [0, 3, 6, 10, 12],
  major: [0, 2, 6, 8, 12, 14],
};

// Интервалы в полутонах от тоники: ход вниз по минорной пентатонике звучит
// «тревожно», подъём по мажорной — «открыто». Оба укладываются в одну руку.
const MOTIF_STEPS = {
  minor: [0, -2, -5, -7, -5],
  major: [0, 4, 7, 5, 4],
};

/** Частоты мотива: тоника и интервалы лада, а не произвольные множители. */
function hookMotif(key) {
  const root = rootFreq(key);
  const steps = isMajor(key) ? MOTIF_STEPS.major : MOTIF_STEPS.minor;
  return steps.map((semitones) => root * Math.pow(2, semitones / 12));
}

/**
 * Фраза на такт: `{step, freq, lengthSteps}` в 16-й сетке.
 *
 * `bar` — номер такта: нечётные такты играют мотив как есть, чётные —
 * его же, но с последней нотой на октаву выше (вопрос-ответ). Смещения нет:
 * узнаваемость держится на повторе, а не на вариации.
 */
function motifLoopForBar(key, bar = 0) {
  const notes = hookMotif(key);
  const major = isMajor(key);
  const rhythm = MOTIF_RHYTHM[major ? 'major' : 'minor'];
  const bend = Math.trunc(bar) % 2 === 1;
  return rhythm.map((step, index) => {
    const freq = notes[index % notes.length] * (bend && index === rhythm.length - 1 ? 2 : 1);
    const next = rhythm[index + 1];
    return {
      step,
      freq,
      lengthSteps: Math.max(1, (next === undefined ? 16 : next) - step),
    };
  });
}

/** Сглаживающий «воздух» для одной ноты мотива. */
function motifLead(sr, freq, duration) {
  const n = Math.max(16, Math.trunc(sr * duration));
  const out = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const env = Math.exp(-t * 4.0) * (1.0 - Math.exp(-t * 60.0));
    out[i] = (
      0.6 * Math.sin(2 * Math.PI * freq * t)
      + 0.25 * Math.sin(2 * Math.PI * freq * 2 * t)
      + 0.1 * Math.sin(2 * Math.PI * freq * 3 * t)
    ) * env;
  }
  return movingAverage(out, 3);
}

module.exports = { MOTIF_RHYTHM, hookMotif, motifLead, motifLoopForBar };
