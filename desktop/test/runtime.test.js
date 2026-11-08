'use strict';
/**
 * runtime.test.js — где окно ищет проект и Python.
 *
 * В репозитории эти пути очевидны, а в установленном приложении — нет:
 * `resources/app.asar` лежит отдельно от `resources/project`. Ошибка здесь
 * видна только на чужой машине, поэтому проверяем на синтетических деревьях.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { resolveRoot, resolvePython, hasMarkers, rootCandidates } = require('../electron/runtime');

const REPO_ROOT = path.resolve(__dirname, '..', '..');

function tempTree(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-runtime-'));
  for (const [relative, contents] of Object.entries(files)) {
    const target = path.join(dir, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, contents);
  }
  return dir;
}

test('в репозитории корень находится от каталога приложения', () => {
  const info = resolveRoot({ appPath: path.join(REPO_ROOT, 'desktop'), env: {} });

  assert.equal(info.root, REPO_ROOT);
  assert.equal(info.error, null);
});

test('в упакованной сборке корень берётся из resources/project', () => {
  const base = tempTree({ 'resources/project/version.json': '{"version":"1.0.0"}' });
  const info = resolveRoot({ appPath: path.join(base, 'resources', 'app.asar'), resourcesPath: path.join(base, 'resources'), env: {} });

  assert.equal(info.root, path.join(base, 'resources', 'project'));
});

test('ZSMM_ROOT важнее автопоиска', () => {
  const override = tempTree({ 'version.json': '{"version":"9.9.9"}' });
  const info = resolveRoot({ appPath: path.join(REPO_ROOT, 'desktop'), env: { ZSMM_ROOT: override } });

  assert.equal(info.root, override);
});

test('пустой каталог не выдаётся за проект: возвращается причина и список', () => {
  const empty = tempTree({ 'readme.txt': 'ничего' });
  const info = resolveRoot({ appPath: path.join(empty, 'app'), env: {} });

  assert.equal(info.root, null);
  assert.match(info.error, /Корень проекта не найден/);
  assert.ok(info.candidates.length > 0, 'кандидаты должны быть перечислены для сообщения об ошибке');
});

test('маркером считается и config/genres_100.json, и version.json', () => {
  const onlyGenres = tempTree({ 'config/genres_100.json': '{"phonk":["phonk"]}' });

  assert.equal(hasMarkers(onlyGenres), true);
  assert.equal(hasMarkers(tempTree({})), false);
});

test('кандидаты не содержат дублей после нормализации', () => {
  const base = path.resolve(path.sep, 'app');
  const candidates = rootCandidates({ appPath: path.join(base, 'desktop'), resourcesPath: base, env: {} });
  const normalized = candidates.map((item) => path.resolve(item));

  assert.equal(new Set(normalized).size, normalized.length);
});

test('Python ищется сначала в .venv Windows, потом в PATH', () => {
  const root = path.resolve(path.sep, 'project');

  const windows = resolvePython({ root, platform: 'win32', env: {}, exists: (p) => p === path.join(root, '.venv', 'Scripts', 'python.exe') });
  assert.equal(windows.python, path.join(root, '.venv', 'Scripts', 'python.exe'));

  const pathOnly = resolvePython({ root, platform: 'win32', env: {}, exists: () => false });
  assert.equal(pathOnly.python, 'python.exe', 'без .venv остаётся системный python из PATH');
});

test('без Python возвращается текст с объяснением, а не пустота', () => {
  // `platform: 'win32'` нарочно не используется: на Windows-раннере короткие
  // имена `python.exe`/`py.exe` считаются найденными в PATH, и проверка
  // «Python нет» зависела бы от того, что установлено на машине.
  const result = resolvePython({ root: path.resolve(path.sep, 'project'), platform: 'linux', env: {}, exists: () => false });

  assert.equal(result.python, null);
  assert.match(result.error, /рендер бита\s+работает/);
  assert.match(result.error, /ZSMM_PYTHON/);
});
