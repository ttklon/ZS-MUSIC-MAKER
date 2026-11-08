'use strict';
/**
 * test/native-tasks.test.js — задачи «Запуска», которые окно считает само.
 *
 * Проверяется не «функция отработала», а честность вывода: каждая проверка
 * либо подтверждает файл, либо называет проблему. Отдельно — что при
 * сломанном файле задача говорит «ПРОБЛЕМА», а не «всё хорошо».
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const native = require('../electron/native-tasks');
const { taskList } = require('../electron/tasks');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');
const dossier = require('../src/core/dossier-edit');
const dossierTracks = require('../src/core/dossier-tracks');

const ROOT = path.resolve(__dirname, '..', '..');

test('нативные задачи есть в общем списке и помечены', () => {
  const list = taskList();
  const natives = list.filter((task) => task.native);
  assert.equal(natives.length, 3);
  for (const key of ['native-files', 'native-readiness', 'native-dossier']) {
    assert.ok(list.some((task) => task.key === key), `нет задачи ${key}`);
  }
  // Задачи Python остаются и не помечены нативными: окно не притворяется,
  // что заменило весь пайплайн.
  assert.ok(list.some((task) => task.key === 'run' && task.native === false));
});

test('проверка файлов на настоящем проекте: проблем нет', () => {
  const project = createProject(createNodeFs(), ROOT);
  const result = native.runNativeTask({ key: 'native-files', project, root: ROOT });
  assert.equal(result.ok, true, result.lines.join('\n'));
  assert.ok(result.lines.some((line) => /^OK версия/.test(line)));
  assert.ok(result.lines.some((line) => /^OK манифест сэмплов/.test(line)));
  assert.match(result.lines.at(-1), /проблем нет/);
});

test('проверка файлов называет проблему, а не молчит', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-native-'));
  fs.mkdirSync(path.join(root, 'config'), { recursive: true });
  fs.writeFileSync(path.join(root, 'version.json'), '{"version":"1.0.0"}');
  fs.writeFileSync(path.join(root, 'config', 'genres_100.json'), '{"one":["A"]}');
  const project = createProject(createNodeFs(), root);
  const events = [];

  const result = native.runNativeTask({
    key: 'native-files',
    project,
    root,
    onEvent: (event) => events.push(event),
  });

  assert.equal(result.ok, false);
  assert.ok(result.lines.some((line) => /^ПРОБЛЕМА каталог жанров: .*жанров 1/.test(line)), result.lines.join('\n'));
  assert.ok(result.lines.some((line) => /^ПРОБЛЕМА снимок модулей: нет/.test(line)));
  // Каждая строка вывода доходит до окна событием — так же, как у Python-задач.
  assert.equal(events.length, result.lines.length);
  assert.ok(events.every((event) => event.type === 'stdout'));
  fs.rmSync(root, { recursive: true, force: true });
});

test('готовность: снимок и пересчёт сверяются, расхождение видно', () => {
  const project = createProject(createNodeFs(), ROOT);
  const ok = native.runNativeTask({ key: 'native-readiness', project, root: ROOT });
  assert.equal(ok.ok, true);
  assert.match(ok.lines.join('\n'), /снимок и пересчёт совпадают/);

  // Подменённый снимок: числа обязаны разойтись, а не «пройти молча».
  const fake = {
    readiness: () => ({
      percent: 99,
      recomputedPercent: 65,
      blockScores: {},
      capsTriggered: [],
      generatedAt: null,
      stale: false,
      mismatch: true,
      error: null,
    }),
  };
  const broken = native.runNativeTask({ key: 'native-readiness', project: fake, root: ROOT });
  assert.equal(broken.ok, false);
  assert.match(broken.lines.join('\n'), /числа расходятся/);
});

test('сводка по досье считает треки и не падает на пустом tracks/', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-native-dossier-'));
  fs.mkdirSync(path.join(root, 'data', 'artist_dossier'), { recursive: true });
  dossier.addArtist(createNodeFs(), root, { artist: 'Сводка' });
  dossierTracks.addTrack(createNodeFs(), root, { slug: 'сводка', title: 'Ждёт разбора' });

  const project = createProject(createNodeFs(), root);
  const result = native.runNativeTask({ key: 'native-dossier', project, root });

  assert.equal(result.ok, true, result.lines.join('\n'));
  const text = result.lines.join('\n');
  assert.match(text, /Сводка: треков 1, не разобрано 1/);
  assert.match(text, /ждут разбора 1/);
  assert.match(text, /артистов 1/);
  fs.rmSync(root, { recursive: true, force: true });
});

test('неизвестная нативная задача — отказ текстом', () => {
  const project = createProject(createNodeFs(), ROOT);
  const result = native.runNativeTask({ key: 'native-nothing', project, root: ROOT });
  assert.equal(result.ok, false);
  assert.match(result.error, /неизвестная задача/);
});

test('нативная задача не запускает процессов', () => {
  // Правило проекта: процессы — только через `tasks.js` (белый список).
  const source = fs.readFileSync(path.join(__dirname, '..', 'electron', 'native-tasks.js'), 'utf8');
  assert.doesNotMatch(source, /child_process|spawn\(|exec\(/);
});
