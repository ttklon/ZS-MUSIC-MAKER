'use strict';
/**
 * test/samples-usage.test.js — отчёт «сколько сэмплов реально прозвучало».
 *
 * `drum_engine.status = REAL_PASS` с текстом «drums come from the licensed
 * sample bank» — утверждение. Подтверждать его должно число: раньше в отчёте
 * не было ни одного счётчика, и проверить утверждение было нечем.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { renderBeat } = require('../src/core/audio/engine');
const { SampleSource } = require('../src/core/audio/bank');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');
const bankSource = () => new SampleSource({ fileSystem: createNodeFs(), rootDir: ROOT });

test('с банком: счётчик подтверждает REAL_PASS', () => {
  const report = renderBeat({
    bpm: 140, genre: 'drift_phonk', seed: 5, durationSec: 12, bank: bankSource(),
  }).report;

  assert.equal(report.drum_engine.status, 'REAL_PASS');
  assert.ok(report.samples_used, 'в отчёте нет счётчика сэмплов');
  assert.ok(report.samples_used.total > 0, 'REAL_PASS без единого сэмпла — ложь');
  assert.ok(report.samples_used.by_source.bank > 0);
  for (const instrument of ['kick', 'hat', 'snare']) {
    assert.ok(report.samples_used.by_instrument[instrument] > 0, instrument);
  }
});

test('без банка: FALLBACK и нули, а не выдуманные числа', () => {
  const report = renderBeat({ bpm: 140, genre: 'phonk', seed: 5, durationSec: 8 }).report;

  assert.equal(report.drum_engine.status, 'FALLBACK');
  assert.equal(report.samples_used.total, 0);
  assert.deepEqual(report.samples_used.by_source, {});
});

test('`available` отделён от «прозвучало»', () => {
  const report = renderBeat({
    bpm: 140, genre: 'drift_phonk', seed: 5, durationSec: 8, bank: bankSource(),
  }).report;

  const { available } = report.samples_used;
  assert.ok(available && typeof available === 'object');
  // Сэмплы переданы через банк, а не через `samples=`: пользовательских файлов нет.
  assert.deepEqual(Object.values(available), [0, 0, 0, 0, 0, 0, 0, 0]);
});

test('счётчики детерминированы по seed', () => {
  const first = renderBeat({
    bpm: 140, genre: 'drift_phonk', seed: 9, durationSec: 8, bank: bankSource(),
  }).report.samples_used;
  const second = renderBeat({
    bpm: 140, genre: 'drift_phonk', seed: 9, durationSec: 8, bank: bankSource(),
  }).report.samples_used;

  assert.deepEqual(first, second);
});
