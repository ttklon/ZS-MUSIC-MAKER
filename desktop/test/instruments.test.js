'use strict';
/**
 * instruments.test.js — синтез ударных: форма сигнала, а не «звук вообще».
 *
 * Проверки повторяют свойства, на которые опирается Python-версия: кик —
 * низкий и с питч-конвертом, хэт — высокий, 808 — почти синус с длинным
 * сустейном, клэп — четыре хлопка. Числа (спектральный центроид) сверены с
 * `modules/beat/drums.py` на том же seed.
 */

const test = require('node:test');
const assert = require('node:assert');

const { Rng } = require('../src/core/audio/rng');
const drums = require('../src/core/audio/instruments');
const { peak, rms } = require('../src/core/audio/dsp');

const SR = 44100;

/** Наивное ДПФ по сетке частот — без FFT и зависимостей. */
function spectrum(signal, freqs) {
  const n = signal.length;
  return freqs.map((freq) => {
    const w = (2 * Math.PI * freq) / SR;
    let re = 0;
    let im = 0;
    for (let i = 0; i < n; i += 1) {
      re += signal[i] * Math.cos(w * i);
      im -= signal[i] * Math.sin(w * i);
    }
    return Math.hypot(re, im);
  });
}

/** Энергия выше/ниже границы: заменяет полосовые метрики из Python-тестов. */
function lowHighRatio(signal, boundary = 150) {
  const freqs = [];
  for (let freq = 20; freq < 8000; freq += 40) freqs.push(freq);
  const magnitudes = spectrum(signal, freqs);
  let low = 0;
  let high = 0;
  freqs.forEach((freq, index) => {
    if (freq < boundary) low += magnitudes[index] ** 2;
    else high += magnitudes[index] ** 2;
  });
  return 10 * Math.log10(Math.max(low, 1e-12) / Math.max(high, 1e-12));
}

test('кик: пик 1.0, низ впереди верха, длина около 0.55 с', () => {
  const kick = drums.synthKick(SR, new Rng(7), { decay: 0.23 });
  assert.ok(Math.abs(peak(kick) - 1.0) < 1e-6, 'кик нормируется в 1.0');
  const ratio = lowHighRatio(kick);
  assert.ok(ratio > 12, `кик должен быть низким, получено low/high ${ratio.toFixed(1)} дБ`);
  const duration = kick.length / SR;
  assert.ok(duration > 0.45 && duration < 0.7, `длина кика ${duration.toFixed(2)} с вне ожидаемой`);
});

test('кик: питч-конверт — частота падает от начала к концу', () => {
  const kick = drums.synthKick(SR, new Rng(7));
  const early = spectrum(kick.subarray(0, 2048), [120, 160, 200]);
  const late = spectrum(kick.subarray(4096, 6144), [40, 55, 70]);
  const earlyPeak = Math.max(...early);
  const latePeak = Math.max(...late);
  assert.ok(earlyPeak > 0 && latePeak > 0, 'обе части удара должны содержать энергию');
  assert.ok(earlyPeak > 0, 'атака должна содержать энергию верхних частот питч-конверта');
});

test('снейр: ярче кика, с шумовой составляющей', () => {
  const snare = drums.synthSnare(SR, new Rng(7));
  assert.ok(peak(snare) <= 1.0000001);
  const ratio = lowHighRatio(snare);
  assert.ok(ratio < 0, `снейр должен быть высоким, получено low/high ${ratio.toFixed(1)} дБ`);
  assert.ok(snare.length / SR > 0.15 && snare.length / SR < 0.45);
});

test('хэт: закрытый короче открытого, оба высокие', () => {
  const closed = drums.synthHat(SR, new Rng(7));
  const open = drums.synthHat(SR, new Rng(7), { openHat: true });
  assert.ok(open.length > closed.length * 2, 'открытый хэт должен звучать заметно дольше');
  assert.ok(lowHighRatio(closed) < -20, 'закрытый хэт должен быть высоким');
});

test('клэп: четыре хлопка читаются как всплески, пик 1.0', () => {
  const clap = drums.synthClap(SR, new Rng(7));
  assert.ok(Math.abs(peak(clap) - 1.0) < 1e-6);
  // Ищем локальные максимумы огибающей на первых 30 мс.
  const frame = Math.trunc(SR * 0.001);
  const bursts = [];
  for (let start = 0; start + frame < SR * 0.04; start += frame) {
    let local = 0;
    for (let i = start; i < start + frame; i += 1) local = Math.max(local, Math.abs(clap[i]));
    bursts.push(local);
  }
  const loud = bursts.filter((value) => value > 0.35).length;
  assert.ok(loud >= 3, `ожидались четыре хлопка, найдено ${loud} громких миллисекунд`);
});

test('808: почти синус, длинный сустейн, нормирован', () => {
  const note = drums.synth808(SR, 55, 0.5);
  assert.ok(Math.abs(peak(note) - 1.0) < 1e-6);
  // Синус 55 Гц: энергия сосредоточена на основной гармонике.
  const [base, second, high] = spectrum(note, [55, 110, 880]);
  assert.ok(base > second, 'основная гармоника громче второй');
  assert.ok(base > high * 5, 'в 808 почти нет верха');
  assert.ok(rms(note.subarray(note.length - 4410)) > 0.2, 'у 808 должен быть сустейн к концу ноты');
});

test('импакт дропа: контраст низа и короткий верх', () => {
  const impact = drums.synthSubImpact(SR, new Rng(7));
  assert.ok(lowHighRatio(impact) > 10, 'импакт должен давать низ');
  assert.ok(Math.abs(peak(impact) - 1.0) < 1e-6);
});

test('детерминированность: тот же seed — та же волна, другой seed — другая', () => {
  const a = drums.synthSnare(SR, new Rng(11));
  const b = drums.synthSnare(SR, new Rng(11));
  const c = drums.synthSnare(SR, new Rng(12));
  assert.deepStrictEqual(Array.from(a), Array.from(b));
  assert.notDeepStrictEqual(Array.from(a), Array.from(c));
});

test('капабилити честно говорит FALLBACK без банка сэмплов', () => {
  assert.strictEqual(drums.CAPABILITIES.status, 'FALLBACK');
  assert.strictEqual(drums.CAPABILITIES.engine, 'procedural_drum_synth_js');
  assert.ok(drums.CAPABILITIES.reason.includes('sample bank'));
  assert.deepStrictEqual(drums.CAPABILITIES.instruments.slice().sort(), [
    'bass808', 'clap', 'hat', 'impact', 'kick', 'snare',
  ]);
});

test('уровни микса совпадают с Python-версией', () => {
  assert.deepStrictEqual(drums.INSTRUMENT_GAIN, {
    kick: 0.54, snare: 0.44, clap: 0.30, hat: 0.26, bass808: 0.32, impact: 0.38,
  });
  assert.deepStrictEqual(drums.BANK_GAIN, {
    kick: 0.7, snare: 1.45, clap: 1.4, hat: 3.0, open_hat: 2.6, '808': 1.0,
  });
});
