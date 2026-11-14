'use strict';
/**
 * core/audio/patterns.js — ритмические семейства и velocity-карты.
 *
 * Порт `modules/beat/patterns.py`. Таблицы живут в `pattern-data.js` (шаги
 * строками из 16 символов), здесь — логика: проекция жанра на семейство,
 * пресет слотов, карта акцентов и производные карты из профилей.
 */

const {
  STEPS,
  PATTERN_ROWS,
  VELOCITY_MAPS,
  ACCENT_PROFILES,
  FAMILY_RULES,
  LEGACY_SLOT_PRESET,
} = require('./pattern-data');

const SLOT_NAMES = ['kick', 'snare', 'hat', 'bass', 'melody'];

/** Строка из 16 символов → массив 0/1. */
function parseRow(row) {
  const out = new Array(STEPS).fill(0);
  for (let i = 0; i < Math.min(STEPS, row.length); i += 1) out[i] = row[i] === '1' ? 1 : 0;
  return out;
}

function rowsToPatterns(rows) {
  const out = {};
  for (const slot of SLOT_NAMES) out[slot] = parseRow(rows[slot] || '');
  return out;
}

const LEGACY_PATTERN = rowsToPatterns(LEGACY_SLOT_PRESET);

/** Проекция названия жанра на ритмическое семейство. */
function familyKey(genre) {
  const key = String(genre || '').trim().toLowerCase().replace(/-/g, '_').replace(/ /g, '_');
  for (const [needle, family] of FAMILY_RULES) {
    if (key.includes(needle)) return family;
  }
  return 'phonk';
}

const familyForGenre = familyKey;

/** Пять слотов по 16 шагов для жанра. */
function slotPresetForGenre(genre) {
  return rowsToPatterns(PATTERN_ROWS[familyKey(genre)]);
}

/** Акценты из профиля семейства по сетке 16 шагов. */
function derivedVelocityMap(slot, family = 'phonk') {
  const profile = ACCENT_PROFILES[family] || ACCENT_PROFILES.phonk;
  const [strong, weak, off, hatStrong, hatWeak, hatMid] = profile;
  const values = [];
  for (let step = 0; step < STEPS; step += 1) {
    if (slot === 'hat') {
      if (step % 4 === 0) values.push(hatStrong);
      else if (step % 2) values.push(hatWeak);
      else values.push(hatMid);
    } else if (slot === 'kick' || slot === 'bass') {
      values.push(step % 8 === 0 ? strong : step % 4 === 0 ? off : weak);
    } else {
      values.push(step % 8 === 4 ? strong : step % 4 === 0 ? off : weak);
    }
  }
  return values;
}

/** Ручная карта семейства, иначе производная из профиля акцентов. */
function velocityMapForGenre(genre) {
  const family = familyKey(genre);
  const base = {};
  for (const slot of SLOT_NAMES) base[slot] = derivedVelocityMap(slot, family);
  for (const [slot, values] of Object.entries(VELOCITY_MAPS[family] || {})) {
    if (values.length === STEPS) base[slot] = values.slice();
  }
  return base;
}

function families() {
  return Object.keys(PATTERN_ROWS).sort();
}

/** Сводка для отчётов: плотность слотов и число акцентов. */
function familySummary() {
  return families().map((name) => {
    const density = {};
    for (const [slot, row] of Object.entries(PATTERN_ROWS[name])) {
      density[slot] = row.split('').filter((ch) => ch === '1').length;
    }
    const accents = Object.values(VELOCITY_MAPS[name] || {})
      .flat()
      .filter((value) => value > 1.0).length;
    return { family: name, density, accents };
  });
}

module.exports = {
  STEPS,
  SLOT_NAMES,
  LEGACY_PATTERN,
  familyKey,
  familyForGenre,
  slotPresetForGenre,
  derivedVelocityMap,
  velocityMapForGenre,
  families,
  familySummary,
  parseRow,
};
