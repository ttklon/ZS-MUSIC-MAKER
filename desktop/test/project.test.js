'use strict';
/**
 * «Модель проекта» окна: версия, жанры, модули, досье, готовность.
 * Всё проверяется на настоящих файлах репозитория и на временных копиях.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');

function tempProject() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-project-'));
  return { dir, project: createProject(createNodeFs(), dir) };
}

test('версия читается из version.json репозитория', () => {
  const project = createProject(createNodeFs(), ROOT);

  const info = project.version();

  assert.equal(info.error, null);
  assert.match(info.version, /^\d+\.\d+/);
});

test('отсутствующий version.json назван, а не выдан за «0.0.0»', () => {
  const { project } = tempProject();

  const info = project.version();

  assert.equal(info.version, null);
  assert.match(info.error, /version\.json/);
});

test('жанры и пресеты приходят вместе с числом пресетов', () => {
  const project = createProject(createNodeFs(), ROOT);

  const data = project.genres();

  assert.ok(data.genres.length > 100);
  assert.ok(data.presetCount > 0);
  assert.deepEqual(data.errors, []);
  const withPreset = data.genres.filter((g) => g.hasPreset);
  assert.ok(withPreset.length > 0, 'хотя бы часть жанров должна иметь пресет');
});

test('модули без снимка отвечают ошибкой с инструкцией', () => {
  const { project } = tempProject();

  const data = project.modules();

  assert.equal(data.total, 0);
  assert.match(data.error, /snapshot-readiness/);
});

test('модули из снимка репозитория читаются и группируются', () => {
  const project = createProject(createNodeFs(), ROOT);

  const data = project.modules();

  if (data.total === 0) return; // снимок не сгенерирован
  assert.equal(data.error, null);
  assert.equal(
    Object.values(data.counts).reduce((a, b) => a + b, 0),
    data.total,
    'счётчики статусов обязаны сходиться с числом строк',
  );
});

test('готовность из снимка не расходится с пересчётом', () => {
  const project = createProject(createNodeFs(), ROOT);

  const data = project.readiness();

  if (data.percent === null) return; // снимок не сгенерирован
  assert.equal(data.mismatch, false, data.error || '');
  assert.equal(data.percent, data.recomputedPercent);
});

test('старый снимок помечается как устаревший', () => {
  const { dir, project } = tempProject();
  fs.mkdirSync(path.join(dir, 'data', 'desktop'), { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'data', 'desktop', 'readiness.json'),
    JSON.stringify({
      percent: 0,
      generated_at: new Date(Date.now() - 400 * 86_400_000).toISOString(),
      raw_probes: {},
      block_scores: {},
      caps_triggered: [],
      module_inventory: { tracked_modules: 1, REAL_PASS: 0, REAL_FAIL: 0 },
    }),
    'utf8',
  );

  const data = project.readiness();

  assert.equal(data.stale, true);
  assert.ok(data.ageDays > 300);
});

test('расхождение снимка с пересчётом — ошибка, а не «нюанс»', () => {
  const { dir, project } = tempProject();
  fs.mkdirSync(path.join(dir, 'data', 'desktop'), { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'data', 'desktop', 'readiness.json'),
    JSON.stringify({
      percent: 99,
      generated_at: new Date().toISOString(),
      raw_probes: {},
      block_scores: {},
      caps_triggered: [],
      module_inventory: { tracked_modules: 1, REAL_PASS: 0, REAL_FAIL: 0 },
    }),
    'utf8',
  );

  const data = project.readiness();

  assert.equal(data.mismatch, true);
  assert.match(data.error, /перегенерируйте/);
});

test('досье читаются из настоящего каталога или честно пусты', () => {
  const project = createProject(createNodeFs(), ROOT);

  const data = project.dossiers();

  assert.ok(Array.isArray(data.artists));
  for (const artist of data.artists) {
    assert.equal(typeof artist.tracks, 'number');
    assert.equal(typeof artist.hasDossier, 'boolean');
    assert.ok(artist.artist);
  }
});

test('битый artist.json попадает в ошибки, остальные читаются', () => {
  const { dir, project } = tempProject();
  const base = path.join(dir, 'data', 'artist_dossier');
  fs.mkdirSync(path.join(base, 'good'), { recursive: true });
  fs.mkdirSync(path.join(base, 'bad'), { recursive: true });
  fs.writeFileSync(
    path.join(base, 'good', 'artist.json'),
    JSON.stringify({ artist: 'Good', slug: 'good', tracks: ['a', 'b'], dossier: { bio: 'есть' } }),
    'utf8',
  );
  fs.writeFileSync(path.join(base, 'bad', 'artist.json'), '{битый', 'utf8');

  const data = project.dossiers();

  assert.equal(data.artists.length, 1);
  assert.deepEqual(data.artists[0], {
    artist: 'Good',
    slug: 'good',
    tracks: 2,
    hasDossier: true,
    deferred: false,
    // Обычный артист не демо: флаг нужен окну, чтобы подписать поставку.
    demo: false,
    note: null,
  });
  assert.match(data.error, /bad/);
});

test('отложенное досье не выдаётся за собранное', () => {
  const { dir, project } = tempProject();
  const base = path.join(dir, 'data', 'artist_dossier', 'later');
  fs.mkdirSync(base, { recursive: true });
  fs.writeFileSync(
    path.join(base, 'artist.json'),
    JSON.stringify({
      artist: 'Later',
      slug: 'later',
      tracks: [],
      dossier: { note: 'analysis_llm unavailable - dossier deferred' },
    }),
    'utf8',
  );

  const artist = project.dossiers().artists[0];

  assert.equal(artist.hasDossier, false);
  assert.equal(artist.deferred, true);
  assert.match(artist.note, /deferred/);
});

test('systemInfo отдаёт корень и версии без Electron', () => {
  const info = createProject(createNodeFs(), ROOT).systemInfo();

  assert.equal(info.root, ROOT);
  assert.ok(info.platform);
  assert.ok(info.node);
});
