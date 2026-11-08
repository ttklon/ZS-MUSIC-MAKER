'use strict';
/**
 * core/audio/instruments.js — синтез ударных и баса.
 *
 * Порт `modules/beat/drums.py`. Это тот же рецепт, а не «что-то похожее»:
 * питч-конверт кика, две моды корпуса снейра, четыре хлопка клэпа,
 * металлический кластер хэта, 808 с глиссандо. Смысл — чтобы окно могло
 * собрать бит без Python; числа взяты из Python-версии.
 *
 * Отличие, о котором нужно помнить: генератор шума здесь mulberry32
 * (`rng.js`), а в Python — numpy PCG64. Поэтому шумовые компоненты не будут
 * бит-в-бит равны Python-рендеру; тон, ритм, огибающие и уровни — совпадают
 * по построению (проверяется тестами на свойства, а не на равенство сэмплов).
 */

const {
  bandpass,
  highpass,
  peakNormalize,
  softClip,
  env,
  mul,
  zeros,
  mixInto,
  peak,
} = require('./dsp');

function synthKick(sr, rng, { tune = 1.0, decay = 0.24, punch = 0.42, startHz = 165.0, endHz = 49.0 } = {}) {
  const n = Math.trunc(sr * Math.min(0.8, decay * 2.4));
  if (n < 16) return zeros(Math.max(n, 1));
  const fEnd = endHz * tune;
  const fStart = startHz * tune;

  // питч-конверт: f = fEnd + (fStart - fEnd) * exp(-t / 0.028)
  const pitch = new Float32Array(n);
  for (let i = 0; i < n; i += 1) pitch[i] = fEnd + (fStart - fEnd) * Math.exp(-i / sr / 0.028);

  // фаза = 2π * cumsum(pitch) / sr
  const body = new Float32Array(n);
  let phase = 0;
  for (let i = 0; i < n; i += 1) {
    phase += (2 * Math.PI * pitch[i]) / sr;
    body[i] = Math.sin(phase);
  }
  const bodyEnv = env(n, sr, 0.0015, decay);
  for (let i = 0; i < n; i += 1) body[i] *= bodyEnv[i];

  // вторая гармоника идёт по той же накопленной фазе (sin(2·phase)), поэтому
  // вторую фазу не храним, а накапливаем ещё раз тем же шагом
  const secondEnv = env(n, sr, 0.002, decay * 0.45);
  let phase2 = 0;
  for (let i = 0; i < n; i += 1) {
    phase2 += (2 * Math.PI * pitch[i]) / sr;
    body[i] += 0.13 * Math.sin(2 * phase2) * secondEnv[i];
  }

  const clickN = Math.min(n, Math.trunc(sr * 0.012));
  const click = mul(highpass(rng.noise(clickN), 2200.0, sr), env(clickN, sr, 1e-4, 0.0016));
  const beater = new Float32Array(clickN);
  const beaterEnv = env(clickN, sr, 1e-4, 0.0035);
  for (let i = 0; i < clickN; i += 1) {
    const t = i / sr;
    beater[i] = Math.sin(2 * Math.PI * 1180.0 * t) * beaterEnv[i];
  }
  for (let i = 0; i < clickN; i += 1) {
    body[i] += (click[i] * 0.62 + beater[i] * 0.34) * punch;
  }
  return peakNormalize(softClip(body, 1.5));
}

function synthSnare(sr, rng, { tune = 1.0, decay = 0.16, toneMix = 0.45, bright = 1.0 } = {}) {
  const n = Math.trunc(sr * Math.max(0.18, decay * 2.2));
  const t = (i) => i / sr;
  const body = new Float32Array(n);
  const envA = env(n, sr, 0.001, 0.055);
  const envB = env(n, sr, 0.001, 0.038);
  for (let i = 0; i < n; i += 1) {
    body[i] =
      0.62 * Math.sin(2 * Math.PI * 185.0 * tune * t(i)) * envA[i]
      + 0.38 * Math.sin(2 * Math.PI * 330.0 * tune * t(i)) * envB[i];
  }
  const noiseBand = bandpass(rng.noise(n), 1400.0, Math.min(11000.0 * bright, sr / 2 - 200.0), sr, 2);
  const noise = mul(noiseBand, env(n, sr, 0.0008, decay));

  const mix = new Float32Array(n);
  const bodyNorm = peakNormalize(body);
  const noiseNorm = peakNormalize(noise);
  for (let i = 0; i < n; i += 1) {
    mix[i] = toneMix * bodyNorm[i] + (1 - toneMix) * noiseNorm[i];
  }

  const clickN = Math.min(n, Math.trunc(sr * 0.008));
  const clickBand = bandpass(rng.noise(clickN), 3000.0, Math.min(12000.0, sr / 2 - 200.0), sr);
  const click = mul(clickBand, env(clickN, sr, 1e-4, 0.0012));
  for (let i = 0; i < clickN; i += 1) mix[i] += click[i] * 0.35;

  return peakNormalize(softClip(mix, 1.3));
}

function synthClap(sr, rng, { decay = 0.13 } = {}) {
  const n = Math.trunc(sr * Math.max(0.22, decay * 2.4));
  const out = zeros(n);
  const base = bandpass(rng.noise(n), 900.0, 3600.0, sr, 2);
  const offsets = [0.0, 7.0, 14.0, 22.0];
  offsets.forEach((offsetMs, index) => {
    const start = Math.trunc((sr * offsetMs) / 1000.0);
    if (start >= n) return;
    const segLen = n - start;
    const burstEnv = env(segLen, sr, 2e-4, index < 3 ? 0.006 : 0.012);
    const gain = index < 3 ? 0.9 : 0.7;
    for (let i = 0; i < segLen; i += 1) out[start + i] += base[i] * burstEnv[i] * gain;
  });
  const tail = mul(base, env(n, sr, 0.002, decay));
  for (let i = 0; i < n; i += 1) out[i] += tail[i] * 0.55;
  return peakNormalize(out);
}

function synthHat(sr, rng, { openHat = false, tune = 1.0, metallic = 0.72 } = {}) {
  const tau = openHat ? 0.235 : 0.042;
  const n = Math.trunc(sr * (tau * 5.0 + 0.01));
  const ratios = [205.3, 304.4, 369.6, 522.7, 540.0, 800.0];
  const metal = new Float32Array(n);
  for (const ratio of ratios) {
    for (let i = 0; i < n; i += 1) {
      metal[i] += Math.sign(Math.sin((2 * Math.PI * ratio * tune * i) / sr));
    }
  }
  // в Python: metal / len(ratios), затем ФВЧ 3-го порядка
  for (let i = 0; i < n; i += 1) metal[i] /= ratios.length;
  const metalFiltered = highpass(metal, 6800.0, sr, 3);
  const air = highpass(rng.noise(n), 8200.0, sr, 3);

  const mix = new Float32Array(n);
  const metalNorm = peakNormalize(metalFiltered);
  const airNorm = peakNormalize(air);
  for (let i = 0; i < n; i += 1) mix[i] = metallic * metalNorm[i] + (1 - metallic) * airNorm[i];
  return peakNormalize(mul(mix, env(n, sr, 3e-4, tau)));
}

function synth808(sr, freq, duration, { glide = 0.03, drive = 1.9 } = {}) {
  const n = Math.max(16, Math.trunc(sr * duration));
  const startF = freq * 1.6;
  const body = new Float32Array(n);
  let phase = 0;
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const pitch = freq + (startF - freq) * Math.exp(-t / Math.max(glide, 1e-3));
    phase += (2 * Math.PI * pitch) / sr;
    const attack = Math.min(1, Math.max(0, t / 0.006));
    const release = Math.min(1, Math.max(0, (duration - t) / 0.045));
    const glideEnv = 0.82 + 0.18 * Math.exp(-t / 0.25);
    body[i] = (Math.sin(phase) + 0.16 * Math.sin(2 * phase)) * attack * release * glideEnv;
  }
  return peakNormalize(softClip(body, drive));
}

function synthSubImpact(sr, rng, { duration = 1.1 } = {}) {
  const n = Math.max(16, Math.trunc(sr * duration));
  const body = new Float32Array(n);
  let phase = 0;
  const decayEnv = env(n, sr, 0.003, duration * 0.42);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const pitch = 36.0 + 74.0 * Math.exp(-t / 0.09);
    phase += (2 * Math.PI * pitch) / sr;
    body[i] = Math.sin(phase) * decayEnv[i];
  }
  const thumpN = Math.min(n, Math.trunc(sr * 0.05));
  const thump = mul(highpass(rng.noise(thumpN), 1600.0, sr), env(thumpN, sr, 2e-4, 0.012));
  mixInto(body, thump, 0, 0.5);
  return peakNormalize(softClip(body, 1.2));
}

// Баланс микса FALLBACK-синтеза — значения из `modules/beat/drums.py`.
const INSTRUMENT_GAIN = {
  kick: 0.54,
  snare: 0.44,
  clap: 0.30,
  hat: 0.26,
  bass808: 0.32,
  impact: 0.38,
};

const BANK_GAIN = {
  kick: 0.7,
  snare: 1.45,
  clap: 1.4,
  hat: 3.0,
  open_hat: 2.6,
  '808': 1.0,
};

const CAPABILITIES = {
  engine: 'procedural_drum_synth_js',
  status: 'FALLBACK',
  reason: 'sample bank is not used by the JS engine; synthesised one-shots are used',
  instruments: ['kick', 'snare', 'clap', 'hat', 'bass808', 'impact'],
};

module.exports = {
  synthKick,
  synthSnare,
  synthClap,
  synthHat,
  synth808,
  synthSubImpact,
  INSTRUMENT_GAIN,
  BANK_GAIN,
  CAPABILITIES,
  peak,
};
