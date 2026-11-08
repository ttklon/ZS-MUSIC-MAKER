'use strict';
/**
 * core/catalog.js — каталог жанров, пресеты и inventory, прочитанные из
 * файлов проекта.
 *
 * Всё считается здесь, в JS: никакого Python-процесса, никакого HTTP. Хост
 * (Electron) передаёт файловое API в аргументах, поэтому модуль проверяется
 * обычным `node --test` на настоящих файлах репозитория.
 *
 * Правило честности: если файла нет или он битый — это `error` в результате,
 * а не пустой список. «Нет данных» и «прочитать не удалось» — разные вещи.
 */

const path = require('node:path');

const PRESET_FIELDS = [
  'genre',
  'bpm_range',
  'typical_keys',
  'mood_tags',
  'vocal_style',
  'structure_templates',
];

/**
 * @param {object} fsApi  { listDir, readJson, readText, exists }
 * @param {string} root   корень репозитория
 */
function createCatalog(fsApi, root) {
  if (!fsApi || typeof fsApi.listDir !== 'function') {
    throw new Error('createCatalog: нужен fsApi.listDir');
  }
  const rootPath = path.resolve(root);
  const rel = (p) => path.relative(rootPath, p) || '.';

  function readCatalog() {
    const file = path.join(rootPath, 'config', 'genres_100.json');
    const data = fsApi.readJson(file);
    if (data.error) return { genres: [], categories: {}, error: `config/genres_100.json: ${data.error}` };
    if (!data.value || typeof data.value !== 'object' || Array.isArray(data.value)) {
      return { genres: [], categories: {}, error: 'config/genres_100.json: ожидался объект категорий' };
    }
    const genres = [];
    const categories = {};
    for (const [category, names] of Object.entries(data.value)) {
      if (!Array.isArray(names)) {
        return { genres: [], categories: {}, error: `категория ${category} не список` };
      }
      categories[category] = names.length;
      for (const name of names) genres.push({ name: String(name), category });
    }
    genres.sort((a, b) => a.name.localeCompare(b.name, 'ru'));
    return { genres, categories, error: null };
  }

  function readPresets() {
    const dir = path.join(rootPath, 'data', 'genre_presets');
    const listing = fsApi.listDir(dir);
    if (listing.error) return { presets: {}, error: `data/genre_presets: ${listing.error}` };
    const presets = {};
    const errors = [];
    for (const name of listing.entries) {
      if (!name.endsWith('.json')) continue;
      const file = path.join(dir, name);
      const data = fsApi.readJson(file);
      if (data.error) {
        errors.push(`${name}: ${data.error}`);
        continue;
      }
      const value = data.value && typeof data.value === 'object' ? data.value : {};
      const key = path.basename(name, '.json');
      const slim = {};
      for (const field of PRESET_FIELDS) {
        if (value[field] !== undefined) slim[field] = value[field];
      }
      presets[key] = slim;
    }
    return {
      presets,
      count: Object.keys(presets).length,
      error: errors.length ? errors.join('; ') : null,
    };
  }

  /**
   * Найти пресет жанра. Имена не совпадают буквально: в каталоге
   * «drum and bass», в файле «drum_and_bass.json». Поэтому сравнение идёт по
   * нормализованному ключу (нижний регистр, `_`/`-`/пробелы — одно и то же).
   * Без этого сопоставления окно показывало бы «пресетов нет» почти для всех
   * жанров, хотя файлы лежат.
   */
  function normalizeKey(name) {
    return String(name || '')
      .toLowerCase()
      .replace(/[_-]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function indexPresets(presets) {
    const byKey = new Map();
    for (const [fileKey, preset] of Object.entries(presets)) {
      byKey.set(normalizeKey(fileKey), preset);
      if (preset && preset.genre) byKey.set(normalizeKey(preset.genre), preset);
    }
    return byKey;
  }

  /** Жанр из каталога + пресет, если он есть: одна карточка для окна. */
  function genreCard(genre, preset) {
    const card = {
      name: genre.name,
      category: genre.category,
      hasPreset: Boolean(preset),
      bpm: preset && preset.bpm_range ? preset.bpm_range : null,
      keys: preset && preset.typical_keys ? preset.typical_keys : [],
      mood: preset && preset.mood_tags ? preset.mood_tags : [],
      vocal: preset && preset.vocal_style ? preset.vocal_style : null,
      structures: preset && preset.structure_templates ? preset.structure_templates : [],
    };
    return card;
  }

  return { readCatalog, readPresets, indexPresets, normalizeKey, genreCard, rootPath, rel };
}

/**
 * Разбор inventory, сгенерированного `python -m tools.readiness
 * --inventory-markdown`. Реальный формат — пять колонок:
 *
 *   | Versioned module | Status | AST syntax | Production refs | Test refs |
 *
 * Достижимость отдельной колонкой не выводится: по контракту инвентаря
 * `REAL_PASS` и означает «достижим и на него ссылаются». Поэтому она
 * вычисляется из статуса, а не выдумывается.
 */
const INVENTORY_STATUSES = new Set(['REAL_PASS', 'REAL_FAIL', 'PLANNED', 'DEPRECATED']);

function parseInventoryMarkdown(text) {
  const lines = String(text || '').split(/\r?\n/);
  const rows = [];
  const errors = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith('|')) continue;
    const cells = trimmed.replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());
    if (cells.length !== 5) continue;
    const [modulePath, status, syntax, productionRefs, testRefs] = cells;
    if (!INVENTORY_STATUSES.has(status)) continue;
    const production = Number.parseInt(productionRefs, 10);
    const tests = Number.parseInt(testRefs, 10);
    if (Number.isNaN(production) || Number.isNaN(tests)) {
      errors.push(`${modulePath}: ссылки не числа (${productionRefs}/${testRefs})`);
      continue;
    }
    rows.push({
      path: modulePath,
      status,
      syntaxOk: syntax.toUpperCase() === 'PASS',
      reachable: status === 'REAL_PASS',
      productionReferences: production,
      testReferences: tests,
    });
  }
  return { rows, errors };
}

function summarizeInventory(rows) {
  const counts = {};
  for (const row of rows) counts[row.status] = (counts[row.status] || 0) + 1;
  return { counts, total: rows.length };
}

module.exports = { createCatalog, parseInventoryMarkdown, summarizeInventory, PRESET_FIELDS };
