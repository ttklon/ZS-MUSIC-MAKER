'use strict';
/**
 * core/audio/harmony.js — гармонический слой: пэд, стабы, голосоведение.
 *
 * Порт `modules/beat/harmony.py`. Барабаны и бас — ещё не трек: трек узнаётся
 * по аккордовой последовательности, плавному голосоведению и «воздуху» пэда.
 *
 * Всё возвращает `Float32Array` моно: панораму задаёт аранжировка.
 */

const { movingAverage, peak } = require('./dsp');

const MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10];
const MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11];

// Прогрессии заданы ступенями лада (0 = тоника).
const PROGRESSIONS = {
  phonk: [[0, 5, 2, 6], [0, 5, 6, 4]],
  trap: [[0, 5, 2, 6], [0, 3, 5, 4]],
  house: [[0, 4, 5, 3], [0, 5, 3, 4]],
  pop: [[0, 4, 5, 3], [0, 5, 6, 4]],
  default: [[0, 5, 2, 6], [0, 4, 5, 3]],
};

const PAD_HARMONICS = 8;
const KEYS_HARMONICS = 4;

const scaleFor = (minor) => (minor ? MINOR_SCALE : MAJOR_SCALE);

/** Частоты трезвучия (или септаккорда) на ступени лада. */
function chordFreqs(rootHz, degree, minor = true, seventh = false) {
  const scale = scaleFor(minor);
  const tones = seventh ? [0, 2, 4, 6] : [0, 2, 4];
  const freqs = [];
  for (const tone of tones) {
    const index = degree + tone;
    const octave = Math.floor(index / 7);
    const semitones = scale[((index % 7) + 7) % 7] + 12 * octave;
    freqs.push(rootHz * Math.pow(2, semitones / 12));
  }
  return freqs;
}

/** Прогрессия ступеней для жанра; seed выбирает вариант. */
function progressionFor(genre, seed = null) {
  const key = String(genre || '').toLowerCase();
  let family = 'default';
  if (key.includes('phonk') || key.includes('drift')) family = 'phonk';
  else if (key.includes('house') || key.includes('techno') || key.includes('trance')) family = 'house';
  else if (key.includes('trap') || key.includes('hip') || key.includes('rap')) family = 'trap';
  else if (key.includes('pop') || key.includes('chanson') || key.includes('ballad')) family = 'pop';
  const options = PROGRESSIONS[family];
  const index = seed === null || seed === undefined ? 0 : Math.abs(Math.trunc(seed)) % options.length;
  return options[index].slice();
}

/**
 * Приводит аккорд к ближайшей инверсии относительно предыдущего.
 *
 * Голоса двигаются максимум на кварту: это то, что отличает живую
 * аранжировку от «аккорды в примарной позиции на каждом такте».
 */
function voiceLead(chord, previous) {
  if (!previous || !previous.length) return chord.slice().sort((a, b) => a - b);
  const targets = previous.slice().sort((a, b) => a - b);
  const led = [];
  for (const [index, freq] of chord.slice().sort((a, b) => a - b).entries()) {
    const target = targets[Math.min(index, targets.length - 1)];
    let shift = Math.round(Math.log2(Math.max(target, 1e-6) / Math.max(freq, 1e-6)));
    shift = Math.max(-2, Math.min(2, shift));
    let value = freq * Math.pow(2, shift);
    // Ниже 60 Гц живёт 808-бас: гармония туда не заходит, иначе низ «мылится».
    while (value < 60.0) value *= 2.0;
    led.push(value);
  }
  return led.sort((a, b) => a - b);
}

function detunedAdditive(freqs, sr, n, detuneCents) {
  const out = new Float64Array(n);
  for (const freq of freqs) {
    for (const offset of [-detuneCents, detuneCents]) {
      const f = freq * Math.pow(2, offset / 1200);
      for (let harmonic = 1; harmonic <= PAD_HARMONICS; harmonic += 1) {
        if (f * harmonic > sr / 2 - 500) break;
        const weight = 1 / Math.pow(harmonic, 1.6);
        const ratio = (2 * Math.PI * f * harmonic) / sr;
        for (let i = 0; i < n; i += 1) out[i] += Math.sin(ratio * i) * weight;
      }
    }
  }
  return out;
}

/** Мягкий пэд с детюном и вибрато: моно-сигнал, нормированный в 0.9. */
function synthPad(sr, freqs, duration, { attack = 0.12, release = 0.18, brightness = 0.6 } = {}) {
  const n = Math.max(16, Math.trunc(sr * duration));
  let body = detunedAdditive(freqs, sr, n, 4.0);

  // вибрато: ±5 центов, 5.2 Гц
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    body[i] *= 1.0 + (5.0 / 1200.0) * Math.sin(2 * Math.PI * 5.2 * t);
  }

  // Фильтр «яркости»: скользящее среднее вместо дорогого БИХ на длинном сигнале.
  const window = Math.max(1, Math.trunc(sr * (0.0004 + 0.0016 * (1.0 - brightness))));
  if (window > 1) body = movingAverage(body, window);

  const safeAttack = Math.max(attack, 1e-3);
  const safeRelease = Math.max(release, 1e-3);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const rise = Math.pow(Math.min(1, Math.max(0, t / safeAttack)), 1.4);
    const fall = Math.min(1, Math.max(0, (duration - t) / safeRelease));
    out[i] = body[i] * rise * fall;
  }
  const top = peak(out) || 1.0;
  for (let i = 0; i < n; i += 1) out[i] = (out[i] * 0.9) / top;
  return out;
}

/** FM-плак для аккордовых стабов: короткая атака, «стеклянный» хвост. */
function synthKeys(sr, freqs, duration, { decay = 0.28, fmDepth = 1.15 } = {}) {
  const n = Math.max(16, Math.trunc(sr * duration));
  const out = new Float64Array(n);
  for (const freq of freqs) {
    const carrier = (2 * Math.PI * freq) / sr;
    for (let i = 0; i < n; i += 1) {
      const t = i / sr;
      const phase = carrier * i;
      const modulator = fmDepth * Math.exp(-t * 7.0) * Math.sin(phase * 2.0);
      let voice = Math.sin(phase + modulator) + 0.22 * Math.sin(phase * 3.0);
      for (let harmonic = 2; harmonic <= KEYS_HARMONICS; harmonic += 1) {
        voice += (0.12 / harmonic) * Math.sin(phase * harmonic);
      }
      out[i] += voice;
    }
  }
  const signal = new Float32Array(n);
  const safeDecay = Math.max(decay, 1e-3);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    signal[i] = out[i] * Math.exp(-t / safeDecay) * Math.min(1, Math.max(0, t / 0.004));
  }
  const top = peak(signal) || 1.0;
  for (let i = 0; i < n; i += 1) signal[i] = (signal[i] * 0.9) / top;
  return signal;
}

module.exports = {
  MINOR_SCALE,
  MAJOR_SCALE,
  PROGRESSIONS,
  chordFreqs,
  progressionFor,
  voiceLead,
  synthPad,
  synthKeys,
};
