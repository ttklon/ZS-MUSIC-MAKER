'use strict';
/**
 * test/hook-motif.test.js — мотив хука: повтор, ритм, попадание в лад.
 *
 * Раньше «мотивом» было арпеджио из четырёх нот подряд без пауз и без
 * повтора: трек звучал ровной гаммой, и узнаваемости (hook_repeatability)
 * взяться было неоткуда. Здесь проверяется именно то, что делает мотив
 * мотивом: фраза с паузами, точный повтор в припеве и интервалы лада.
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const { hookMotif, motifLoopForBar, MOTIF_RHYTHM } = require('../src/core/audio/hook');
const { rootFreq, isMajor } = require('../src/core/audio/tuning');

test('мотив — фраза с паузами, а не сплошной поток', () => {
  const phrase = motifLoopForBar('A minor', 0);

  assert.ok(phrase.length >= 4, 'фраза слишком короткая, чтобы запомниться');
  const steps = phrase.map((note) => note.step);
  assert.deepEqual(steps, MOTIF_RHYTHM.minor);
  // Паузы: между нотами есть шаги, где ничего не звучит.
  assert.ok(steps[steps.length - 1] < 16, 'фраза должна оставлять воздух в такте');
  assert.ok(phrase.every((note) => note.lengthSteps >= 1));
});

test('в припеве повторяется та же фраза, а то и та же высота', () => {
  const bars = [0, 2, 4, 6].map((bar) => motifLoopForBar('A minor', bar));

  for (const phrase of bars) {
    assert.deepEqual(phrase, bars[0], 'каждый чётный такт — точный повтор (узнаваемость)');
  }
  // Нечётный такт — ответ на фразу: последняя нота на октаву выше.
  const answer = motifLoopForBar('A minor', 1);
  const last = answer[answer.length - 1];
  const base = bars[0][bars[0].length - 1];
  assert.ok(Math.abs(last.freq - base.freq * 2) < 0.01);
  assert.deepEqual(answer.map((n) => n.step), bars[0].map((n) => n.step), 'ритм не меняется');
});

test('интервалы мотива попадают в лад тональности', () => {
  const root = rootFreq('A minor');
  const scale = [0, 2, 3, 5, 7, 8, 10]; // натуральный минор

  for (const freq of hookMotif('A minor')) {
    const semitones = Math.round(12 * Math.log2(freq / root));
    const normalized = ((semitones % 12) + 12) % 12;
    assert.ok(scale.includes(normalized), `нота ${freq.toFixed(1)} Гц вне лада (${normalized} полутонов)`);
  }
  assert.equal(isMajor('A minor'), false);
});

test('мажор даёт мажорный мотив и свой ритм', () => {
  const major = motifLoopForBar('C major', 0);

  assert.equal(isMajor('C major'), true);
  assert.deepEqual(major.map((n) => n.step), MOTIF_RHYTHM.major);
  const root = rootFreq('C major');
  for (const freq of hookMotif('C major')) {
    const semitones = Math.round(12 * Math.log2(freq / root));
    const normalized = ((semitones % 12) + 12) % 12;
    assert.ok([0, 2, 4, 5, 7, 9, 11].includes(normalized), 'мажорная нота вне лада');
  }
});

test('мотив звучит в готовом треке и повторяется', () => {
  const { renderBeat } = require('../src/core/audio/engine');
  const report = renderBeat({ bpm: 140, genre: 'drift_phonk', seed: 11, durationSec: 24 }).report;

  const hooks = (report.sections || []).filter((s) => s.layers.includes('hook_lead'));
  assert.ok(hooks.length >= 2, 'мотив должен звучать минимум в двух секциях');
  assert.ok(report.repetition !== undefined, 'отчёт должен нести метрику повтора');
});
