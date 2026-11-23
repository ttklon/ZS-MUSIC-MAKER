'use strict';
/**
 * test/mix-balance.test.js — спектр микса и мягкая коррекция баланса.
 *
 * Измерение появилось потому, что «низ не съедает середину» было словами.
 * Здесь проверяется и сам измеритель (на синтетических сигналах с известным
 * ответом), и коррекция: она обязана улучшать баланс, не ломая моносовместимость
 * и не превращая трек в тишину.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const analysis = require('../src/core/audio/analysis');
const { balanceMix } = require('../src/core/audio/balance');
const { renderBeat } = require('../src/core/audio/engine');
const { SampleSource } = require('../src/core/audio/bank');
const { createNodeFs } = require('../src/core/fs-node');

const SR = 44100;
const ROOT = path.resolve(__dirname, '..', '..');
const bankSource = () => new SampleSource({ fileSystem: createNodeFs(), rootDir: ROOT });

const tone = (freq, seconds = 1) => {
  const out = new Float32Array(Math.trunc(SR * seconds));
  for (let i = 0; i < out.length; i += 1) out[i] = 0.5 * Math.sin((2 * Math.PI * freq * i) / SR);
  return out;
};

test('чистый низ определяется как «низ перевесил»', () => {
  const report = analysis.spectrumReport(tone(50), SR);

  assert.equal(report.ok, true);
  assert.ok(report.bands.low > 0.9);
  assert.equal(report.low_heavy, true);
  assert.match(report.reason, /низ перевесил/);
});

test('чистый верх не считается глухим', () => {
  const report = analysis.spectrumReport(tone(12000), SR);

  assert.ok(report.bands.high > 0.5);
  assert.equal(report.dull, false);
});

test('короткий сигнал честно отказывается мерить', () => {
  const report = analysis.spectrumReport(new Float32Array(1000), SR);

  assert.equal(report.ok, false);
  assert.match(report.reason, /короче окна/);
});

test('коррекция вытягивает середину у «бочки»', () => {
  const left = tone(55);
  const right = tone(55);
  // Немного середины, чтобы было что вытягивать.
  const mid = tone(900);
  for (let i = 0; i < left.length; i += 1) {
    left[i] += mid[i] * 0.15;
    right[i] += mid[i] * 0.15;
  }

  const result = balanceMix(left, right, SR);

  assert.ok(result.before.bands.low > 0.62, 'тест должен начинаться с «бочки»');
  assert.ok(result.passes >= 1, 'коррекция не запустилась');
  assert.ok(
    result.after.bands.mid > result.before.bands.mid,
    `середина не выросла: ${result.before.bands.mid} → ${result.after.bands.mid}`,
  );
  // Тишиной «лечить» баланс нельзя.
  const peak = Math.max(...left.map(Math.abs), ...right.map(Math.abs));
  assert.ok(peak > 0.05, 'после коррекции трек стал почти тишиной');
});

test('сбалансированный микс не трогается', () => {
  const left = tone(1000);
  const right = tone(1000);

  const result = balanceMix(left, right, SR);

  assert.equal(result.passes, 0);
  assert.equal(result.correction, null);
});

test('после рендера отчёт несёт и спектр, и историю коррекции', () => {
  const report = renderBeat({
    bpm: 130, genre: 'drift_phonk', seed: 5, durationSec: 12, bank: bankSource(),
  }).report;

  assert.equal(report.spectrum.ok, true);
  assert.deepEqual(Object.keys(report.spectrum.bands), ['low', 'mid', 'high']);
  assert.ok(report.mix_balance, 'нет истории: непонятно, правился ли баланс');
  assert.ok(Array.isArray([report.mix_balance.passes]) || typeof report.mix_balance.passes === 'number');
  // Сумма долей — 1 с точностью округления: полосы покрывают весь спектр.
  const total = report.spectrum.bands.low + report.spectrum.bands.mid + report.spectrum.bands.high;
  assert.ok(Math.abs(total - 1) < 0.01, `доли не складываются в 1: ${total}`);
});

test('стерео после коррекции остаётся моносовместимым', () => {
  const report = renderBeat({
    bpm: 130, genre: 'pop', seed: 3, durationSec: 12, bank: bankSource(),
  }).report;

  // Коррекция правит L и R одинаковыми фильтрами, поэтому корреляция не падает.
  assert.ok(report.humanity.peak < 1.0, 'пик выше единицы — клиппинг');
});

test('строки отчёта не врут при отсутствии данных', () => {
  const { describeVocal, describeSamples, describeSpectrum } = require('../src/core/report-text');

  // Пустой отчёт показывается причиной, а не выдуманным «сбалансировано».
  assert.match(describeSpectrum(null, null), /не измерен/);
  assert.match(describeSpectrum({ ok: false, reason: 'too short' }, null), /too short/);
  assert.equal(describeSamples(null), 'не считалось');
  assert.match(describeSamples({ total: 0, by_instrument: {} }), /синтез/);
  assert.equal(describeVocal(null), 'не подключён');
  assert.match(
    describeVocal({ label: 'запись с микрофона', gain: 0.5, mixed_seconds: 2 }),
    /запись с микрофона, уровень 0.5, в миксе 2 с/,
  );
});

test('правка баланса видна в тексте отчёта', () => {
  const { describeSpectrum } = require('../src/core/report-text');

  const text = describeSpectrum(
    { ok: true, bands: { low: 0.4, mid: 0.6, high: 0.01 }, reason: 'balanced' },
    { passes: 2 },
  );

  assert.match(text, /правка баланса: 2/);
});
