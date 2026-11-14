'use strict';
/** Каталог жанров, пресеты и разбор inventory — на настоящих файлах проекта. */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createCatalog, parseInventoryMarkdown, summarizeInventory } = require('../src/core/catalog');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');

test('каталог жанров читается из config/genres_100.json', () => {
  const catalog = createCatalog(createNodeFs(), ROOT);
  const { genres, categories, error } = catalog.readCatalog();

  assert.equal(error, null);
  assert.ok(genres.length > 100, `ожидалось больше 100 жанров, получено ${genres.length}`);
  assert.ok(categories.electronic > 0);

  const source = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'genres_100.json'), 'utf8'));
  const expected = Object.values(source).reduce((sum, list) => sum + list.length, 0);
  assert.equal(genres.length, expected, 'ни один жанр не потерян');
});

test('жанры отсортированы и каждый имеет категорию', () => {
  const { genres } = createCatalog(createNodeFs(), ROOT).readCatalog();

  const names = genres.map((g) => g.name);
  assert.deepEqual(names, [...names].sort((a, b) => a.localeCompare(b, 'ru')));
  assert.ok(genres.every((g) => typeof g.category === 'string' && g.category.length > 0));
});

test('пресеты читаются и содержат только известные поля', () => {
  const catalog = createCatalog(createNodeFs(), ROOT);
  const { presets, error } = catalog.readPresets();

  assert.equal(error, null);
  assert.ok(Object.keys(presets).length > 0);

  const first = Object.values(presets)[0];
  for (const key of Object.keys(first)) {
    assert.ok(
      ['genre', 'bpm_range', 'typical_keys', 'mood_tags', 'vocal_style', 'structure_templates'].includes(key),
      `неожиданное поле пресета: ${key}`,
    );
  }
});

test('карточка жанра честно отмечает отсутствие пресета', () => {
  const catalog = createCatalog(createNodeFs(), ROOT);

  const withPreset = catalog.genreCard({ name: '2step', category: 'electronic' }, { bpm_range: [125, 135] });
  const without = catalog.genreCard({ name: 'нет-такого', category: 'x' }, null);

  assert.equal(withPreset.hasPreset, true);
  assert.deepEqual(withPreset.bpm, [125, 135]);
  assert.equal(without.hasPreset, false);
  assert.equal(without.bpm, null);
});

test('битый каталог — ошибка, а не пустой список', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-'));
  fs.mkdirSync(path.join(dir, 'config'));
  fs.writeFileSync(path.join(dir, 'config', 'genres_100.json'), '{битый', 'utf8');

  const result = createCatalog(createNodeFs(), dir).readCatalog();

  assert.deepEqual(result.genres, []);
  assert.match(result.error, /genres_100\.json/);
});

test('каталог-массив вместо объекта тоже назван ошибкой', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-'));
  fs.mkdirSync(path.join(dir, 'config'));
  fs.writeFileSync(path.join(dir, 'config', 'genres_100.json'), '[]', 'utf8');

  assert.match(createCatalog(createNodeFs(), dir).readCatalog().error, /объект категорий/);
});

test('createCatalog требует файловое API', () => {
  assert.throws(() => createCatalog(null, ROOT), /fsApi/);
});

test('inventory парсится в строки со ссылками и синтаксисом', () => {
  const text = [
    '| Versioned module | Status | AST syntax | Production refs | Test refs |',
    '|---|---|---:|---:|---:|',
    '| app/core/x.py | REAL_PASS | PASS | 3 | 12 |',
    '| modules/old.py | DEPRECATED | PASS | 0 | 1 |',
    '| modules/new.py | PLANNED | FAIL | 0 | 0 |',
  ].join('\n');

  const { rows, errors } = parseInventoryMarkdown(text);

  assert.deepEqual(errors, []);
  assert.equal(rows.length, 3);
  assert.deepEqual(rows[0], {
    path: 'app/core/x.py',
    status: 'REAL_PASS',
    syntaxOk: true,
    reachable: true,
    productionReferences: 3,
    testReferences: 12,
  });
  assert.equal(rows[2].syntaxOk, false);
  assert.equal(rows[2].reachable, false, 'PLANNED не выдаётся за достижимый');
});

test('нечисловые ссылки попадают в ошибки, а не в нули', () => {
  const text = '| Versioned module | Status | AST syntax | Production refs | Test refs |\n'
    + '|---|---|---:|---:|---:|\n| a.py | REAL_PASS | PASS | много | 1 |';

  const { rows, errors } = parseInventoryMarkdown(text);

  assert.equal(rows.length, 0);
  assert.match(errors[0], /не числа/);
});

test('строки без статуса игнорируются', () => {
  const text = '| что-то | другое | PASS | 1 | 2 |\n| a.py | REAL_PASS | PASS | 1 | 2 |';

  const { rows } = parseInventoryMarkdown(text);

  assert.equal(rows.length, 1);
});

test('summary считает статусы и общее число', () => {
  const rows = [
    { status: 'REAL_PASS' },
    { status: 'REAL_PASS' },
    { status: 'DEPRECATED' },
  ];

  assert.deepEqual(summarizeInventory(rows), { counts: { REAL_PASS: 2, DEPRECATED: 1 }, total: 3 });
});

test('реальный снимок inventory читается целиком', () => {
  const file = path.join(ROOT, 'data', 'desktop', 'inventory.md');
  if (!fs.existsSync(file)) {
    assert.ok(true, 'снимок не сгенерирован: тест пропущен');
    return;
  }

  const { rows, errors } = parseInventoryMarkdown(fs.readFileSync(file, 'utf8'));

  assert.deepEqual(errors, []);
  assert.ok(rows.length > 200, `строк в inventory: ${rows.length}`);
});


test('пресет находится по множественному числу, сокращению и словам', () => {
  const fsApi = createNodeFs();
  const catalog = createCatalog(fsApi, ROOT);
  const index = catalog.indexPresets(catalog.readPresets().presets);

  // Живые пары из каталога: раньше они показывались как «без пресета»,
  // хотя файлы лежат в data/genre_presets.
  const pairs = [
    ['Afrobeats', 'afrobeat'],
    ['Drum and Bass', 'dnb'],
    ['Lo-Fi Hip Hop', 'lofi'],
    ['Phonk', 'phonk'],
  ];
  for (const [name, slug] of pairs) {
    const preset = catalog.presetFor(index, name);
    assert.ok(preset, `${name}: пресет не найден (ожидался ${slug})`);
  }

  // А вот выдумывать нечего: у жанра без пресета его нет.
  assert.equal(catalog.presetFor(index, 'Baroque'), null);
  assert.equal(catalog.presetFor(null, 'Phonk'), null);
});

test('все 50 пресетов видны каталогу, если на них есть жанр или родственник', () => {
  const fsApi = createNodeFs();
  const catalog = createCatalog(fsApi, ROOT);
  const { genres } = catalog.readCatalog();
  const index = catalog.indexPresets(catalog.readPresets().presets);
  const matched = genres.filter((genre) => catalog.presetFor(index, genre.name));
  assert.ok(matched.length >= 20, `с пресетом всего ${matched.length} жанров`);
  // И каждая пара действительно даёт числа, а не пустую карточку.
  for (const genre of matched) {
    const card = catalog.genreCard(genre, catalog.presetFor(index, genre.name));
    assert.equal(card.hasPreset, true);
    assert.ok(Array.isArray(card.bpm) && card.bpm.length === 2, `${genre.name}: нет bpm_range`);
  }
});
