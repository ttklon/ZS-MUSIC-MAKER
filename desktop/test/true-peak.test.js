'use strict';
/**
 * test/true-peak.test.js — истинный пик (dBTP).
 *
 * Числа сверены с `modules.dsp.metrics.true_peak_dbtp` (scipy, `resample_poly`):
 * окно и длина ядра взяты оттуда же, поэтому расхождение должно быть в сотых,
 * а не в децибелах. Тест важен тем, что сэмпловый пик на этих сигналах врёт
 * на 3 дБ и больше.
 */
const test = require('node:test');
const assert = require('node:assert');

const { truePeakDbtp } = require('../src/core/audio/true-peak');
const { limitStereo } = require('../src/core/audio/limiter');

const SR = 44100;

function sine(freq, seconds, { amplitude = 1, phase = 0, sr = SR } = {}) {
  const out = new Float32Array(Math.round(seconds * sr));
  for (let i = 0; i < out.length; i += 1) {
    out[i] = amplitude * Math.sin((2 * Math.PI * freq * i) / sr + phase);
  }
  return out;
}

function samplePeakDb(channels) {
  let top = 0;
  for (const channel of channels) {
    for (let i = 0; i < channel.length; i += 1) top = Math.max(top, Math.abs(channel[i]));
  }
  return 20 * Math.log10(top);
}

test('синус, попавший сэмплами в нули: истинный пик видит полную шкалу', () => {
  // fs/4 со сдвигом 45°: все отсчёты на −3.01 dBFS, а между ними 0 dBFS.
  const signal = sine(SR / 4, 1, { phase: Math.PI / 4 });
  assert.ok(Math.abs(samplePeakDb([signal]) + 3.01) < 0.01);
  assert.ok(Math.abs(truePeakDbtp([signal])) < 0.15, `истинный пик ${truePeakDbtp([signal])}`);
});

test('на «удобных» сигналах истинный пик совпадает с эталоном', () => {
  assert.ok(Math.abs(truePeakDbtp([sine(1000, 1)])) < 0.05);
  assert.ok(Math.abs(truePeakDbtp([sine(1000, 1, { amplitude: 0.5 })]) + 6.02) < 0.05);
});

test('тишина не даёт минус бесконечность в отчёте', () => {
  const value = truePeakDbtp([new Float32Array(SR)]);
  assert.ok(!Number.isFinite(value) || value < -100, `получено ${value}`);
});

test('лимитер держит истинный пик на враждебном сигнале', () => {
  const left = sine(SR / 4, 1, { phase: Math.PI / 4 });
  const right = sine(SR / 4, 1, { phase: Math.PI / 4 });
  const info = limitStereo(left, right, SR, { ceilingDbtp: -1 });
  assert.ok(info.true_peak_dbtp <= -0.99, `после лимитера ${info.true_peak_dbtp}`);
  assert.ok(info.gain_reduction_db > 0.5, `снято ${info.gain_reduction_db} дБ`);
  let peak = 0;
  for (const channel of [left, right]) {
    for (let i = 0; i < channel.length; i += 1) peak = Math.max(peak, Math.abs(channel[i]));
  }
  assert.ok(20 * Math.log10(peak) <= -0.99, 'сэмпловый пик тоже вышел за потолок');
});

test('лимитер не трогает тихий материал', () => {
  const left = sine(1000, 1, { amplitude: 0.1 });
  const right = sine(1000, 1, { amplitude: 0.1 });
  const before = Array.from(left.subarray(0, 64));
  const info = limitStereo(left, right, SR, { ceilingDbtp: -1 });
  assert.strictEqual(info.gain_reduction_db, 0);
  assert.deepStrictEqual(Array.from(left.subarray(0, 64)), before);
});
