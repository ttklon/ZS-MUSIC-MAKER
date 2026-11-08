'use strict';
/**
 * patterns.test.js — ритмические семейства и velocity-карты.
 *
 * Таблица данных сгенерирована из `modules/beat/patterns.py`; здесь
 * проверяется, что логика (проекция жанра на семейство, акценты, ручные
 * карты поверх производных) ведёт себя как Python-версия.
 */

const test = require('node:test');
const assert = require('node:assert');

const patterns = require('../src/core/audio/patterns');

test('каждое семейство — пять слотов по 16 шагов из 0/1', () => {
  const families = patterns.families();
  assert.ok(families.length >= 15, `ожидалось не меньше 15 семейств, найдено ${families.length}`);
  for (const family of families) {
    const preset = patterns.slotPresetForGenre(family);
    assert.deepStrictEqual(Object.keys(preset).sort(), ['bass', 'hat', 'kick', 'melody', 'snare']);
    for (const [slot, row] of Object.entries(preset)) {
      assert.strictEqual(row.length, 16, `${family}/${slot}: длина ${row.length}`);
      assert.ok(row.every((value) => value === 0 || value === 1), `${family}/${slot}: не 0/1`);
    }
  }
});

test('проекция жанра на семейство: правила идут по порядку и покрывают каталог', () => {
  const cases = {
    phonk: 'phonk',
    'memphis rap': 'phonk',
    drift: 'drift',
    'cloud rap': 'lofi',
    plugg: 'lofi',
    drill: 'drill',
    'boom-bap': 'boom_bap',
    'tech house': 'tech_house',
    house: 'house',
    techno: 'house',
    jungle: 'dnb',
    'liquid dnb': 'dnb',
    hyperpop: 'hyperpop',
    dembow: 'reggaeton',
    afrobeat: 'afrobeat',
    amapiano: 'amapiano',
    rawstyle: 'hardstyle',
    rage: 'trap',
    'west coast': 'boom_bap',
    cinematic: 'drift',
  };
  for (const [genre, family] of Object.entries(cases)) {
    assert.strictEqual(patterns.familyForGenre(genre), family, `жанр «${genre}»`);
  }
  // Незнакомый жанр получает осмысленный дефолт, а не пустой паттерн.
  assert.strictEqual(patterns.familyForGenre('совершенно новый жанр'), 'phonk');
  assert.strictEqual(patterns.familyForGenre(null), 'phonk');
});

test('phonk: рисунок совпадает с Python-таблицей', () => {
  const phonk = patterns.slotPresetForGenre('phonk');
  assert.deepStrictEqual(phonk.kick, [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0]);
  assert.deepStrictEqual(phonk.snare, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]);
  assert.deepStrictEqual(phonk.hat, [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1]);
  assert.deepStrictEqual(phonk.bass, [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]);
  assert.deepStrictEqual(phonk.melody, [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]);
});

test('velocity-карта: ручная поверх производной, длина 16, акценты на сильных долях', () => {
  for (const genre of ['phonk', 'trap', 'house', 'drill', 'reggaeton', 'lofi', 'amapiano']) {
    const map = patterns.velocityMapForGenre(genre);
    for (const [slot, values] of Object.entries(map)) {
      assert.strictEqual(values.length, 16, `${genre}/${slot}: длина карты ${values.length}`);
      assert.ok(values.every((value) => value > 0.4 && value < 1.5), `${genre}/${slot}: акцент вне разумного диапазона`);
    }
  }
  // Ручная карта phonk-хэта: сильная доля громче «и».
  const hat = patterns.velocityMapForGenre('phonk').hat;
  assert.ok(hat[0] > hat[1], 'хэт на доле должен быть громче хэта на «и»');
  assert.strictEqual(hat[0], 1.1);
  assert.strictEqual(hat[15], 0.7);
});

test('производная карта без ручной: kick и snare акцентируют разные шаги', () => {
  const kick = patterns.derivedVelocityMap('kick', 'house');
  const snare = patterns.derivedVelocityMap('snare', 'house');
  assert.ok(kick[0] > kick[2], 'кик акцентирует сильную долю');
  assert.ok(snare[4] > snare[2], 'снейр акцентирует четвёртый шаг');
  assert.strictEqual(kick.length, 16);
});

test('legacy-пресет: пустые хэты и мелодия, как в Python', () => {
  const legacy = patterns.LEGACY_PATTERN;
  assert.deepStrictEqual(legacy.kick, [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]);
  assert.deepStrictEqual(legacy.hat, new Array(16).fill(0));
  assert.deepStrictEqual(legacy.melody, new Array(16).fill(0));
});

test('сводка семейств: плотность считается по шагам, акценты — по картам', () => {
  const summary = patterns.familySummary();
  const phonk = summary.find((item) => item.family === 'phonk');
  assert.strictEqual(phonk.density.kick, 4);
  assert.strictEqual(phonk.density.snare, 2);
  assert.strictEqual(phonk.density.hat, 10);
  assert.ok(phonk.accents > 0, 'в ручной карте phonk есть акценты выше 1.0');
});

test('parseRow терпим к коротким строкам и мусору', () => {
  assert.deepStrictEqual(patterns.parseRow('101'), [1, 0, 1, ...new Array(13).fill(0)]);
  assert.deepStrictEqual(patterns.parseRow(''), new Array(16).fill(0));
  assert.strictEqual(patterns.STEPS, 16);
});
