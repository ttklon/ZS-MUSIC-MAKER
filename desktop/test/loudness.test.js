'use strict';
/**
 * test/loudness.test.js — громкость по BS.1770-4.
 *
 * Тесты держат три вещи: калибровку стандарта (синус полной шкалы даёт
 * около −3 LUFS), согласие с pyloudnorm (им мастерит Python-пайплайн, и
 * расхождение в 0.5 дБ — это уже слышимая разница «тише/громче площадки»)
 * и поведение нормализатора на реальном случае: тихий бит с пиками.
 */
const test = require('node:test');
const assert = require('node:assert');

const {
  integratedLoudness,
  normalizeLoudness,
  kWeighting,
} = require('../src/core/audio/loudness');

const SR = 44100;

function sine(freq, seconds, amplitude = 1, sr = SR) {
  const out = new Float32Array(Math.round(seconds * sr));
  for (let i = 0; i < out.length; i += 1) out[i] = amplitude * Math.sin((2 * Math.PI * freq * i) / sr);
  return out;
}

test('калибровка: моно-синус 1 кГц полной шкалы ≈ −3.0 LUFS', () => {
  const { lufs, blocks } = integratedLoudness([sine(1000, 5)], SR);
  assert.ok(blocks > 0);
  assert.ok(Math.abs(lufs + 3.01) < 0.1, `получено ${lufs}`);
});

test('калибровка: стерео −20 dBFS на канал ≈ −20 LUFS', () => {
  const channel = sine(1000, 5, Math.pow(10, -20 / 20));
  const { lufs } = integratedLoudness([channel, channel.slice()], SR);
  assert.ok(Math.abs(lufs + 20) < 0.15, `получено ${lufs}`);
});

/** Усиление цепи K-взвешивания на синусе, в дБ (по установившейся части). */
function weightingGainDb(freq) {
  const weighted = kWeighting(sine(freq, 2), SR);
  let sum = 0;
  for (let i = SR; i < weighted.length; i += 1) sum += weighted[i] * weighted[i];
  return 10 * Math.log10(sum / (weighted.length - SR) / 0.5);
}

test('K-взвешивание совпадает со стандартом на опорных частотах', () => {
  // pyloudnorm: 100 Гц → −1.17 дБ, 1 кГц → +0.66 дБ, 5 кГц → +3.96 дБ.
  assert.ok(Math.abs(weightingGainDb(100) + 1.17) < 0.15, `100 Гц: ${weightingGainDb(100).toFixed(2)}`);
  assert.ok(Math.abs(weightingGainDb(1000) - 0.66) < 0.15, `1 кГц: ${weightingGainDb(1000).toFixed(2)}`);
  assert.ok(Math.abs(weightingGainDb(5000) - 3.96) < 0.2, `5 кГц: ${weightingGainDb(5000).toFixed(2)}`);
});

test('согласие с pyloudnorm на «музыкальном» сигнале', () => {
  // Аккорд с басом: если ФВЧ окажется первого порядка, именно бас уедет.
  const length = SR * 4;
  const left = new Float32Array(length);
  const right = new Float32Array(length);
  for (let i = 0; i < length; i += 1) {
    const t = i / SR;
    const bass = 0.28 * Math.sin(2 * Math.PI * 55 * t);
    const mid = 0.12 * Math.sin(2 * Math.PI * 440 * t);
    const top = 0.05 * Math.sin(2 * Math.PI * 3000 * t);
    left[i] = bass + mid + top;
    right[i] = bass * 0.9 + mid + top * 1.2;
  }
  // Эталон pyloudnorm для этого же сигнала: −13.36 LUFS.
  const { lufs } = integratedLoudness([left, right], SR);
  assert.ok(Math.abs(lufs + 13.36) < 0.15, `получено ${lufs}, ожидание ≈ −13.36`);
});

test('тишина и слишком короткий трек объясняют отказ, а не выдумывают число', () => {
  const silent = integratedLoudness([new Float32Array(SR)], SR);
  assert.strictEqual(silent.lufs, null);
  assert.match(silent.reason, /тишин/i);

  const short = integratedLoudness([sine(440, 0.2)], SR);
  assert.strictEqual(short.lufs, null);
  assert.match(short.reason, /400/);
});

test('нормализация: громкость к цели по LUFS, истинный пик под потолком', () => {
  const source = sine(1000, 3, 0.1);
  const left = Float32Array.from(source);
  const right = Float32Array.from(source);
  const result = normalizeLoudness(left, right, SR, { targetLufs: -14 });
  assert.strictEqual(result.ok, true);
  assert.ok(result.before < -19, `до ${result.before}`);
  assert.ok(Math.abs(result.after + 14) <= 0.3, `после ${result.after}, цель −14`);
  assert.ok(result.applied_db > 5, `усиление ${result.applied_db}`);
  // Потолок — истинный пик −1 dBTP, как в Python-пайплайне, а не сэмпловый.
  assert.strictEqual(result.ceiling_dbtp, -1);
  assert.ok(result.true_peak_after <= -0.99, `истинный пик ${result.true_peak_after}`);
  assert.strictEqual(result.ceiling_ok, true);
});

test('потолок держится по истинному пику, а не по сэмпловому', () => {
  // Синус на fs/4 со сдвигом 45° — худший случай: сэмплы на −3 dBFS, а
  // между ними полная шкала. Сэмпловый лимитер такой сигнал не видит.
  const n = SR * 3;
  const left = new Float32Array(n);
  const right = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const value = Math.sin((2 * Math.PI * (SR / 4) * i) / SR + Math.PI / 4);
    left[i] = value;
    right[i] = value;
  }
  const result = normalizeLoudness(left, right, SR, { targetLufs: -14 });
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.ceiling_ok, true);
  assert.ok(result.true_peak_after <= -0.99, `истинный пик ${result.true_peak_after} пробил потолок`);
  // Сэмпловый пик при этом заведомо ниже потолка — иначе тест ничего не значит.
  assert.ok(result.sample_peak < 0.71, `сэмпловый пик ${result.sample_peak}`);
});

test('нормализация на тишине честно отказывается', () => {
  const result = normalizeLoudness(new Float32Array(SR), new Float32Array(SR), SR);
  assert.strictEqual(result.ok, false);
  assert.strictEqual(result.after, null);
  assert.match(result.reason, /тишин/i);
});
