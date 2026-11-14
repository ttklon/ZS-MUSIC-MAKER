'use strict';
/**
 * core/audio/hook.js — мотив хука: короткий лид, по которому трек узнаётся.
 *
 * Вынесено из `voices.js`: мотив не зависит ни от банка, ни от RNG, это чистая
 * функция от тональности. `voices.js` реэкспортирует обе функции.
 */

const { movingAverage } = require('./dsp');
const { rootFreq, isMajor } = require('./tuning');

/** Мотив хука: повторяющийся лид, по которому трек узнаётся. */
function hookMotif(key) {
  const root = rootFreq(key);
  if (isMajor(key)) return [root, (root * 9) / 8, (root * 5) / 4, (root * 4) / 3];
  return [root, root * Math.pow(2, -2 / 12), root * Math.pow(2, -5 / 12), root * Math.pow(2, -7 / 12)];
}

/** Сглаживающий «воздух» для мотива: тот же фильтр, что у пэда. */
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

module.exports = { hookMotif, motifLead };
