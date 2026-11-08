'use strict';
/**
 * analysis.test.js — измерение трека: «формульность» и «человечность».
 *
 * Эти числа попадают в отчёт окна, поэтому проверять их нужно числом, а не
 * «функция вернула объект». Эталоны взяты из Python-версии
 * (`modules/beat/variation.py`, `microtime.py`) на одинаковом сигнале.
 */

const test = require('node:test');
const assert = require('node:assert');

const analysis = require('../src/core/audio/analysis');

/** Тот же клик-трек, что в `tests/test_beat_variation.py`. */
function clickTrack({ bars = 16, vary = false, sampleRate = 48000, bpm = 240 } = {}) {
  const bar = Math.round(4 * (60 / bpm) * sampleRate);
  const audio = new Float32Array(bar * bars);
  for (let barIndex = 0; barIndex < bars; barIndex += 1) {
    for (let hit = 0; hit < 4; hit += 1) {
      const start = barIndex * bar + hit * Math.round(bar / 4);
      const amplitude = vary ? 0.7 + 0.1 * ((barIndex + hit) % 5) : 1.0;
      for (let i = 0; i < 800 && start + i < audio.length; i += 1) {
        // Окно Ханна — как `np.hanning` в Python-эталоне: от него зависит
        // спектр и, значит, центроид.
        const window = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / 799);
        audio[start + i] += amplitude * Math.sin(i * 0.3) * window;
      }
    }
  }
  return { audio, sampleRate, bpm };
}

test('БПФ сходится с наивным ДПФ по положению и величине пика', () => {
  const n = 1024;
  const signal = new Float32Array(n);
  for (let i = 0; i < n; i += 1) signal[i] = Math.sin((2 * Math.PI * 64 * i) / n);
  const { magnitudes, size } = analysis.fft(signal);
  assert.strictEqual(size, n);
  let best = 0;
  let bestBin = 0;
  magnitudes.forEach((value, bin) => {
    if (value > best) {
      best = value;
      bestBin = bin;
    }
  });
  assert.strictEqual(bestBin, 64, `пик на бине ${bestBin} вместо 64`);
  // Прямоугольное окно: пик одиночной синусоиды равен n/2.
  assert.ok(Math.abs(best - n / 2) < n / 20, `амплитуда ${best} далека от ${n / 2}`);
});

test('БПФ дополняет нулями до степени двойки и терпит короткий вход', () => {
  const short = new Float32Array(100);
  const { size, magnitudes } = analysis.fft(short);
  assert.strictEqual(size, 128);
  assert.strictEqual(magnitudes.length, 65);
  assert.ok(magnitudes.every((value) => Number.isFinite(value)));
});

test('спектральный центроид совпадает с numpy', () => {
  // Один такт клик-трека: numpy даёт центроид 2291.9 Гц.
  const { audio, sampleRate, bpm } = clickTrack({ bars: 1, sampleRate: 48000 });
  const bar = Math.round(4 * (60 / bpm) * sampleRate);
  const features = analysis.barFeatures(audio.subarray(0, bar), sampleRate);
  const centroidHz = features[1] * 1000;
  assert.ok(Math.abs(centroidHz - 2291.9) < 5, `центроид ${centroidHz.toFixed(1)} Гц`);
  // RMS: numpy на этом же сигнале даёт −19.036 дБ.
  assert.ok(Math.abs(features[0] + 19.036) < 0.01, `RMS ${features[0].toFixed(3)} дБ`);
});

test('одинаковые такты — формульный трек, энтропия 0', () => {
  const { audio, sampleRate, bpm } = clickTrack({ vary: false });
  const report = analysis.repetitionReport(audio, sampleRate, bpm);
  assert.strictEqual(report.bars, 16);
  assert.strictEqual(report.distinct_types, 1);
  assert.strictEqual(report.entropy_normalized, 0);
  assert.strictEqual(report.formulaic, true);
  assert.ok(report.bar_similarity > 0.95, `сходство ${report.bar_similarity}`);
});

test('разные такты — не формульный трек (как в Python: 0.578)', () => {
  const { audio, sampleRate, bpm } = clickTrack({ vary: true });
  const report = analysis.repetitionReport(audio, sampleRate, bpm);
  assert.strictEqual(report.distinct_types, 5);
  assert.ok(Math.abs(report.entropy_normalized - 0.578) < 0.01, `энтропия ${report.entropy_normalized}`);
  assert.strictEqual(report.formulaic, false);
  assert.strictEqual(report.min_entropy, 0.35);
});

test('слишком короткий трек честно помечается, а не «идеальным»', () => {
  const short = new Float32Array(1000);
  const report = analysis.repetitionReport(short, 48000, 120);
  assert.strictEqual(report.bars, 0);
  assert.strictEqual(report.formulaic, true);
  assert.strictEqual(report.reason, 'too few bars to measure');
});

test('реальный бит не формульный: энтропия выше порога', () => {
  const path = require('node:path');
  const { createNodeFs } = require('../src/core/fs-node');
  const { renderBeat } = require('../src/core/audio/engine');
  const { decodeWav } = require('../src/core/audio/wav-decode');

  const root = path.resolve(__dirname, '..', '..');
  const { SampleSource } = require('../src/core/audio/bank');
  const bank = new SampleSource({ fileSystem: createNodeFs(), rootDir: root });
  const { wav, report } = renderBeat({
    bpm: 128, key: 'A minor', genre: 'drift phonk', seed: 5, durationSec: 20, bank,
  });
  const audio = decodeWav(wav);
  const mono = new Float32Array(audio.audio.length);
  // decodeWav уже свёл в моно при записи WAV: здесь один канал стерео-файла.
  mono.set(audio.audio);

  const repetition = report.repetition;
  assert.ok(repetition.bars >= 10, `тактов ${repetition.bars}`);
  assert.strictEqual(repetition.formulaic, false, `энтропия ${repetition.entropy_normalized}`);
  assert.ok(repetition.entropy_normalized >= 0.35);
  // Python на этом же заходе даёт 0.641 — сверяем с точностью до 0.05.
  assert.ok(Math.abs(repetition.entropy_normalized - 0.641) < 0.08, `энтропия ${repetition.entropy_normalized}`);
});

test('«человечность» измеряется: шумовой пол и вариативность уровня', () => {
  const sampleRate = 8000;
  const mono = new Float32Array(sampleRate * 3);
  for (let i = 0; i < mono.length; i += 1) {
    // Тихо в начале, громко во второй половине: вариативность должна быть > 0.
    const gain = i < mono.length / 2 ? 0.01 : 0.3;
    mono[i] = Math.sin((2 * Math.PI * 220 * i) / sampleRate) * gain;
  }
  const report = analysis.humanityReport(mono, sampleRate);
  assert.ok(report.noise_floor_dbfs < -20, `шумовой пол ${report.noise_floor_dbfs}`);
  assert.ok(report.level_variation_db > 0.5, `вариативность ${report.level_variation_db}`);

  // Полная тишина: уровень упирается в нижнюю границу −180 дБ (как в Python),
  // а вариативности нет.
  const silence = analysis.humanityReport(new Float32Array(sampleRate), sampleRate);
  assert.ok(silence.noise_floor_dbfs <= -120, `шумовой пол тишины ${silence.noise_floor_dbfs}`);
  assert.strictEqual(silence.level_variation_db, 0);
  // Пустой вход — отдельный честный ответ, а не деление на ноль.
  assert.deepStrictEqual(analysis.humanityReport(new Float32Array(0), sampleRate), {
    noise_floor_dbfs: -120, level_variation_db: 0,
  });
});
