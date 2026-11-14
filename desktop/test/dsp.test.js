'use strict';
/**
 * dsp.test.js — фильтры, огибающие, нормализация.
 *
 * Главная проверка — не «фильтр что-то делает», а «фильтр совпадает со
 * scipy». Эталонные значения получены из Python-версии проекта
 * (`scipy.signal.sosfreqz` на тех же параметрах) и вписаны числом: если
 * дизайн коэффициентов поедет, тест провалится на конкретной частоте.
 */

const test = require('node:test');
const assert = require('node:assert');

const dsp = require('../src/core/audio/dsp');

/** Импульсная характеристика → АЧХ в дБ на заданных частотах. */
function magnitudeDb(kind, cutoff, sr, order, freqs) {
  const n = 16384;
  const impulse = new Float32Array(n);
  impulse[0] = 1;
  const response = dsp.filter(kind, impulse, cutoff, sr, order);
  return freqs.map((freq) => {
    const w = (2 * Math.PI * freq) / sr;
    let re = 0;
    let im = 0;
    for (let i = 0; i < n; i += 1) {
      re += response[i] * Math.cos(w * i);
      im -= response[i] * Math.sin(w * i);
    }
    return 20 * Math.log10(Math.max(Math.hypot(re, im), 1e-12));
  });
}

const SR = 44100;

test('bandpass 900–3600 Гц совпадает со scipy по АЧХ', () => {
  const freqs = [200, 400, 700, 900, 1200, 1800, 2600, 3600, 5000, 8000];
  // scipy.signal.butter(2, (900, 3600), btype="bandpass", fs=44100, output="sos")
  const expected = [-30.8, -18.2, -7.4, -3.0, -0.4, 0.0, -0.2, -3.0, -9.3, -19.7];
  const actual = magnitudeDb('bandpass', [900, 3600], SR, 2, freqs);
  actual.forEach((value, index) => {
    assert.ok(
      Math.abs(value - expected[index]) < 0.6,
      `на ${freqs[index]} Гц ожидалось ${expected[index]} дБ, получено ${value.toFixed(1)}`,
    );
  });
});

test('highpass 6800 и 8200 Гц совпадают со scipy по АЧХ', () => {
  const freqs = [200, 900, 1200, 2600, 3600, 5000, 8000];
  const expected6800 = [-62.7, -36.5, -31.5, -18.0, -12.4, -7.0, -1.6];
  const expected8200 = [-100.0, -60.8, -53.2, -32.9, -24.1, -15.1, -3.4];
  const actual6800 = magnitudeDb('highpass', 6800, SR, 2, freqs);
  const actual8200 = magnitudeDb('highpass', 8200, SR, 3, freqs);
  actual6800.forEach((value, index) => {
    assert.ok(Math.abs(value - expected6800[index]) < 0.8, `ФВЧ 6800 на ${freqs[index]} Гц: ${value.toFixed(1)} дБ`);
  });
  actual8200.forEach((value, index) => {
    assert.ok(Math.abs(value - expected8200[index]) < 0.8, `ФВЧ 8200 (3-й порядок) на ${freqs[index]} Гц: ${value.toFixed(1)} дБ`);
  });
});

test('lowpass 120 Гц третьего порядка даёт −3 дБ на срезе', () => {
  const [atCutoff] = magnitudeDb('lowpass', 120, SR, 3, [120]);
  assert.ok(Math.abs(atCutoff + 3.0) < 0.5, `на срезе ожидалось −3 дБ, получено ${atCutoff.toFixed(2)}`);
  const [deep] = magnitudeDb('lowpass', 120, SR, 3, [960]);
  assert.ok(deep < -30, `вне полосы пропускания ожидалось сильное подавление, получено ${deep.toFixed(1)} дБ`);
});

test('фильтр не переполняется и не даёт NaN на шуме', () => {
  const noise = new Float32Array(4096);
  for (let i = 0; i < noise.length; i += 1) noise[i] = Math.sin(i * 12.9898) * 0.5;
  const out = dsp.bandpass(noise, 900, 3600, SR, 2);
  assert.ok(out.every((value) => Number.isFinite(value)), 'в выходе фильтра есть NaN/Infinity');
  assert.ok(dsp.peak(out) < 4, 'полосовой фильтр не должен раздувать амплитуду шума');
});

test('неизвестный тип фильтра — понятная ошибка, а не тишина', () => {
  assert.throws(() => dsp.filter('notch', new Float32Array(8), 100, SR, 2), /неизвестный тип/);
});

test('огибающая: пик на атаке, спад к концу', () => {
  const envelope = dsp.env(4410, SR, 0.001, 0.05);
  assert.ok(Math.abs(envelope[0]) < 0.05, 'на нуле огибающая должна быть почти нулевой');
  assert.ok(envelope[44] > envelope[2000], 'огибающая должна спадать');
  assert.ok(dsp.peak(envelope) <= 1.0000001, 'огибающая не должна превышать единицу');
});

test('peakNormalize даёт ровно единицу и не ломает тишину', () => {
  const signal = Float32Array.from([0.1, -0.4, 0.2]);
  const normalized = dsp.peakNormalize(signal);
  assert.strictEqual(dsp.peak(normalized), 1);
  const silence = dsp.peakNormalize(new Float32Array(16));
  assert.strictEqual(dsp.peak(silence), 0);
});

test('softClip сжимает пик и сохраняет знак', () => {
  const signal = Float32Array.from([2.0, -2.0, 0.5]);
  const clipped = dsp.softClip(signal, 1.6);
  // tanh(x·1.6)/tanh(1.6): двойка превращается в ≈1.08, то есть пик
  // сжимается почти вдвое, но строго в единицу не упирается. Это поведение
  // Python-версии (`drums.py::_soft_clip`), и оно сохранено намеренно.
  assert.ok(clipped[0] > 0 && clipped[0] < 1.1, `ожидалось сжатие к ~1.08, получено ${clipped[0]}`);
  assert.ok(clipped[1] < 0 && clipped[1] > -1.1);
  assert.ok(clipped[2] > 0.5 && clipped[2] < 1, 'небольшие значения не режутся, но и не раздуваются до пика');
});

test('fit, mixInto и movingAverage ведут себя предсказуемо', () => {
  const target = new Float32Array(8);
  dsp.mixInto(target, Float32Array.from([1, 1, 1, 1]), 6, 0.5);
  assert.deepStrictEqual(Array.from(target.slice(6)), [0.5, 0.5]);
  const fitted = dsp.fit(Float32Array.from([1, 2, 3]), 5);
  assert.deepStrictEqual(Array.from(fitted), [1, 2, 3, 0, 0]);
  const smoothed = dsp.movingAverage(Float32Array.from([1, 1, 1, 1]), 3);
  assert.ok(dsp.peak(smoothed) <= 1.0001);
});

test('rms и peak считают то, что заявлено', () => {
  assert.strictEqual(dsp.peak(Float32Array.from([0.5, -2, 1])), 2);
  assert.ok(Math.abs(dsp.rms(Float32Array.from([1, -1, 1, -1])) - 1) < 1e-9);
  assert.strictEqual(dsp.rms(new Float32Array(0)), 0);
});
