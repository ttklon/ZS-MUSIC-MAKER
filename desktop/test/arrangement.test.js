'use strict';
/**
 * arrangement.test.js — драматургия: секции, энергия, правило 15 секунд.
 *
 * Ожидаемые значения взяты из Python-версии (`plan_sections` на тех же bpm и
 * длительностях), поэтому тест ловит не «код запускается», а расхождение
 * структуры трека с эталоном.
 */

const test = require('node:test');
const assert = require('node:assert');

const arrangement = require('../src/core/audio/arrangement');

const shape = (plans) => plans.map((plan) => `${plan.name}:${plan.bars}`);

test('план для 140 BPM / 120 с совпадает с Python', () => {
  const plans = arrangement.planSections({ bpm: 140, durationSec: 120 });
  assert.deepStrictEqual(shape(plans), [
    'intro:5', 'verse:9', 'pre_chorus:5', 'hook:9',
    'verse:9', 'pre_chorus:5', 'hook:9', 'bridge:5', 'hook:9', 'outro:5',
  ]);
  assert.strictEqual(plans.reduce((sum, plan) => sum + plan.bars, 0), 70);
});

test('план для 128 BPM / 180 с совпадает с Python', () => {
  const plans = arrangement.planSections({ bpm: 128, durationSec: 180 });
  assert.deepStrictEqual(shape(plans), [
    'intro:6', 'verse:13', 'pre_chorus:6', 'hook:13',
    'verse:13', 'pre_chorus:6', 'hook:14', 'bridge:6', 'hook:13', 'outro:6',
  ]);
});

test('короткий заказ не растягивается: секции ужимаются до двух тактов', () => {
  const plans = arrangement.planSections({ bpm: 174, durationSec: 30 });
  assert.deepStrictEqual(shape(plans), [
    'intro:2', 'verse:3', 'pre_chorus:2', 'hook:3',
    'verse:2', 'pre_chorus:2', 'hook:2', 'bridge:2', 'hook:2', 'outro:2',
  ]);
});

test('энергия и слои: хук богаче куплета, интро несёт мотив хука', () => {
  const plans = arrangement.planSections({ bpm: 140, durationSec: 120 });
  const intro = plans[0];
  const verse = plans[1];
  const hook = plans[3];
  assert.strictEqual(intro.name, 'intro');
  assert.ok(intro.layers.includes('hook_lead'), 'в интро должен звучать мотив хука (правило 15 секунд)');
  assert.ok(!intro.layers.includes('bass'), 'в интро нет баса: сначала узнаётся мотив');
  assert.ok(hook.energy > verse.energy, 'энергия хука должна быть выше куплета');
  assert.deepStrictEqual(hook.layers.slice(0, 6), ['drums', 'bass', 'pad', 'keys', 'melody', 'fx']);
  assert.ok(hook.bassGain > verse.bassGain, 'в хуке низ полный, в куплете подсушен');
});

test('правило TikTok: мотив хука слышен в первые 15 секунд', () => {
  for (const bpm of [90, 120, 140, 174]) {
    for (const durationSec of [30, 60, 120, 180]) {
      const plans = arrangement.planSections({ bpm, durationSec });
      const report = arrangement.structureReport(plans, bpm);
      assert.ok(
        report.hook_motif_start_sec <= 15,
        `${bpm} BPM / ${durationSec} с: мотив хука начинается на ${report.hook_motif_start_sec} с`,
      );
      assert.strictEqual(report.hook_within_15s, true);
    }
  }
});

test('отчёт структуры: контраст дропа и потолок слоёв', () => {
  const plans = arrangement.planSections({ bpm: 140, durationSec: 120 });
  const report = arrangement.structureReport(plans, 140);
  assert.ok(report.drop_contrast >= 0.3, `контраст хука и куплета ${report.drop_contrast}`);
  assert.strictEqual(report.drop_contrast, 0.38);
  assert.strictEqual(report.max_layers, 7);
  assert.strictEqual(report.sections.length, 10);
  const hookInfo = report.sections.find((section) => section.name === 'hook');
  assert.strictEqual(hookInfo.gain_db, 0);
  // В отчёте `gain_db` — производная от энергии (−12·(1−E)), а −4 дБ — это
  // гейн сборки секции в `engine.js::SECTION_GAIN_DB`.
  const verseInfo = report.sections.find((section) => section.name === 'verse');
  assert.strictEqual(verseInfo.gain_db, -4.56);
  assert.strictEqual(require('../src/core/audio/engine').SECTION_GAIN_DB.verse, -4);
});

test('план из аранжировки: цифры в имени отбрасываются, drop становится хуком', () => {
  const plans = arrangement.sectionsFromArrangement([
    { name: 'intro', bars: 4 },
    { name: 'verse2', bars: 8 },
    { name: 'drop1', bars: 8 },
    { name: 'chorus1', bars: 6 },
    { name: 'outro', bars: 4 },
  ], 140);
  assert.deepStrictEqual(plans.map((plan) => plan.name), ['intro', 'verse', 'hook', 'chorus', 'outro']);
  assert.deepStrictEqual(plans.map((plan) => plan.bars), [4, 8, 8, 6, 4]);
  assert.strictEqual(plans[2].energy, 1.0);
  assert.strictEqual(plans[2].sourceName, 'drop1');
});

test('план из аранжировки уважает явную энергию и не выходит за 0…1', () => {
  const plans = arrangement.sectionsFromArrangement([
    { name: 'verse', bars: 4, energy: 1.7 },
    { name: 'hook', bars: 4, energy: -2 },
  ], 120);
  assert.strictEqual(plans[0].energy, 1.0);
  assert.strictEqual(plans[1].energy, 0.0);
});

test('неверный bpm — ошибка с текстом, а не деление на ноль', () => {
  assert.throws(() => arrangement.planSections({ bpm: 0, durationSec: 60 }), /bpm/);
  assert.throws(() => arrangement.sectionsFromArrangement([], 0), /bpm/);
});

test('канонические имена секций не теряют слои и трим низа', () => {
  assert.strictEqual(arrangement.canonicalSectionName('chorus1'), 'chorus');
  assert.strictEqual(arrangement.canonicalSectionName('build'), 'pre_chorus');
  assert.strictEqual(arrangement.canonicalSectionName('break'), 'breakdown');
  assert.strictEqual(arrangement.canonicalSectionName('что-то своё'), 'verse');
  assert.strictEqual(arrangement.energyCurve(['hook', 'verse']).join(','), '1,0.62');
});
