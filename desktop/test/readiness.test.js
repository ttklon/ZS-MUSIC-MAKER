'use strict';
/**
 * Расчёт готовности на JS обязан совпадать с эталоном Python.
 *
 * Эталон — вывод `python -m tools.readiness --json` (файл
 * data/desktop/readiness.json, его делает scripts/snapshot-readiness.js).
 * Если формулы разойдутся, падает именно этот тест — иначе окно тихо
 * показывало бы другое число, чем CLI.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { computeReadiness, blockPercent, STATUS_WEIGHT } = require('../src/core/readiness');

const ROOT = path.resolve(__dirname, '..', '..');
const SNAPSHOT = path.join(ROOT, 'data', 'desktop', 'readiness.json');

test('blockPercent считает долю по весам статусов', () => {
  const percent = blockPercent({ a: 'REAL_PASS', b: 'REAL_FAIL' });

  assert.equal(percent, 50);
  assert.equal(STATUS_WEIGHT.REAL_PASS, 1);
  assert.equal(blockPercent({}), 0);
});

test('потолки применяются жёстко', () => {
  const { percent, capsTriggered } = computeReadiness({
    probes: {
      voice_recording: { mic_recording: 'REAL_FAIL' },
      audio_pipeline: { musicgen_runtime: 'BLOCKED', demucs_runtime: 'BLOCKED' },
      architecture: { updater_module: 'REAL_FAIL' },
      core_modules: { m: 'REAL_FAIL' },
      release: { r: 'REAL_FAIL' },
      testing: { t: 'REAL_FAIL' },
    },
    inventory: { tracked_modules: 10, REAL_PASS: 10, REAL_FAIL: 0 },
  });

  // все пробы провалены → 0 %; потолки всё равно называются в ответе
  assert.equal(percent, 0, 'при провале всех проб готовность 0, а не 65');
  // три потолка: микрофон, тяжёлые движки и updater — все названы
  assert.deepEqual(capsTriggered.map(([v]) => v), [80, 65, 85]);
  assert.match(capsTriggered[1][1], /musicgen_runtime/);
});

test('без потолков берётся расчётная доля', () => {
  const passes = {
    architecture: { updater_module: 'REAL_PASS' },
    core_modules: { m: 'REAL_PASS' },
    audio_pipeline: { musicgen_runtime: 'REAL_PASS', demucs_runtime: 'REAL_PASS' },
    voice_recording: { mic_recording: 'REAL_PASS' },
    release: {},
    testing: {},
  };
  const { percent, capsTriggered } = computeReadiness({
    probes: passes,
    inventory: { tracked_modules: 4, REAL_PASS: 4, REAL_FAIL: 0 },
  });

  assert.deepEqual(capsTriggered, []);
  // все проверяемые блоки на 100 %: 10+25+25+20 = 80 из 100 веса,
  // release и testing пусты → 0 баллов
  assert.equal(percent, 80);
});

test('мёртвый код снижает core_modules', () => {
  const probes = {
    architecture: { updater_module: 'REAL_PASS' },
    core_modules: { m: 'REAL_PASS' },
    release: {},
    testing: {},
    audio_pipeline: { musicgen_runtime: 'REAL_PASS', demucs_runtime: 'REAL_PASS' },
    voice_recording: { mic_recording: 'REAL_PASS' },
    release: {},
    testing: {},
  };
  const full = computeReadiness({ probes, inventory: { tracked_modules: 4, REAL_PASS: 4, REAL_FAIL: 0 } });
  const half = computeReadiness({
    probes,
    inventory: { tracked_modules: 4, REAL_PASS: 2, REAL_FAIL: 0 },
  });

  assert.equal(full.moduleReachabilityShare, 1);
  assert.equal(half.moduleReachabilityShare, 0.5);
  assert.ok(half.percent < full.percent);
});

test('снимок готовности совпадает с пересчётом JS', (t) => {
  if (!fs.existsSync(SNAPSHOT)) {
    t.skip('снимок не сгенерирован: node scripts/snapshot-readiness.js');
    return;
  }
  const snapshot = JSON.parse(fs.readFileSync(SNAPSHOT, 'utf8'));

  const recomputed = computeReadiness({
    probes: snapshot.raw_probes,
    inventory: snapshot.module_inventory,
  });

  assert.equal(
    recomputed.percent,
    snapshot.percent,
    `JS=${recomputed.percent}%, эталон Python=${snapshot.percent}%`,
  );
  assert.deepEqual(recomputed.capsTriggered, snapshot.caps_triggered);
  for (const [block, value] of Object.entries(snapshot.block_scores)) {
    assert.equal(
      recomputed.blockScores[block],
      value,
      `блок ${block}: JS=${recomputed.blockScores[block]}, Python=${value}`,
    );
  }
});

test('снимок помечен датой и потолками', (t) => {
  if (!fs.existsSync(SNAPSHOT)) {
    t.skip('снимок не сгенерирован');
    return;
  }
  const snapshot = JSON.parse(fs.readFileSync(SNAPSHOT, 'utf8'));

  assert.ok(snapshot.generated_at, 'без даты окно не сможет сказать, что данные устарели');
  assert.ok(Array.isArray(snapshot.caps_triggered));
  assert.ok(snapshot.module_inventory.tracked_modules > 0);
});
