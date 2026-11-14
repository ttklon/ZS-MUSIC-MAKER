'use strict';
/**
 * Задачи из окна: белый список команд, проверка аргументов и реальный запуск.
 *
 * Здесь важен не «красивый» вывод, а отсутствие дыр: окно не должно уметь
 * выполнить произвольный процесс, а каждая задача обязана показывать свой
 * вывод построчно.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const {
  TASKS,
  TaskError,
  buildCommand,
  sanitizeOptions,
  taskList,
  runTask,
} = require('../electron/tasks');

const ROOT = path.resolve(__dirname, '..', '..');

/**
 * Интерпретатор для настоящего запуска задачи.
 *
 * Windows — тоже целевая платформа: набор тестов оболочки идёт и в CI на
 * `windows-latest`. Поэтому кандидаты платформенные: без `python.exe` тесты
 * не «пропускались», а падали на `path.existsSync('/usr/bin/python3')`.
 */
function python() {
  const candidates = process.platform === 'win32'
    ? [process.env.ZSMM_PYTHON, 'python', 'py', 'python3']
    : [process.env.ZSMM_PYTHON, '/tmp/v/bin/python', '/usr/bin/python3', 'python3'];
  for (const candidate of candidates) {
    if (!candidate) continue;
    if (path.isAbsolute(candidate)) {
      if (fs.existsSync(candidate)) return candidate;
      continue;
    }
    // Имя без пути ищется в PATH — как это сделал бы пользователь.
    const dirs = (process.env.PATH || '').split(path.delimiter);
    for (const dir of dirs) {
      if (!dir) continue;
      for (const name of process.platform === 'win32' ? [`${candidate}.exe`, candidate] : [candidate]) {
        const full = path.join(dir, name);
        if (fs.existsSync(full)) return full;
      }
    }
  }
  return null;
}

test('белый список задач не пуст и каждая принимает только известные флаги', () => {
  const list = taskList();
  assert.ok(list.length >= 5);

  for (const task of list) {
    // Нативные задачи описаны в `native-tasks.js`: окно считает их само и
    // Python для них не нужен, поэтому в белом списке процессов их нет.
    if (task.native) {
      assert.equal(TASKS[task.key], undefined, `${task.key} не должна запускать процесс`);
      continue;
    }
    assert.ok(TASKS[task.key], `нет описания для ${task.key}`);
    for (const accepted of task.accepts) {
      assert.ok(['genre', 'theme', 'seed', 'artist'].includes(accepted), `неизвестный параметр ${accepted}`);
    }
  }
});

test('buildCommand собирает аргументы без оболочки', () => {
  assert.deepEqual(buildCommand('dry-run'), ['--run', '--dry-run']);
  assert.deepEqual(buildCommand('dry-run', { genre: 'drift_phonk' }), [
    '--run', '--dry-run', '--genre', 'drift_phonk',
  ]);
  assert.deepEqual(buildCommand('run', { seed: 7 }), ['--run', '--seed', '7']);
});

test('флаги, которых задача не принимает, не добавляются', () => {
  assert.deepEqual(buildCommand('health', { genre: 'techno' }), ['--health']);
  assert.deepEqual(buildCommand('readiness', { seed: 3 }), ['--readiness']);
});

test('инъекция в аргументы отвергается', () => {
  for (const bad of ['a; rm -rf /', 'a$(whoami)', 'a`id`', 'a\nb', 'a|b', 'a&b']) {
    assert.throws(() => buildCommand('run', { genre: bad }), TaskError, `пропущено: ${bad}`);
  }
});

test('некорректный сид отвергается', () => {
  for (const bad of [-1, 1.5, 'abc', '1e5']) {
    assert.throws(() => buildCommand('run', { seed: bad }), TaskError, `пропущен: ${bad}`);
  }
  assert.equal(sanitizeOptions({ seed: '0' }).seed, 0);
  assert.equal(sanitizeOptions({}).seed, null);
});

test('неизвестная задача — ошибка, а не «молча ничего»', () => {
  assert.throws(() => buildCommand('rm-rf'), TaskError);
});

test('runTask без интерпретатора не запускается', () => {
  assert.throws(() => runTask({ key: 'health', root: ROOT, options: {} }), TaskError);
});

test('задача запускается и отдаёт вывод построчно', async (t) => {
  const interpreter = python();
  if (!interpreter) {
    t.skip('Python не найден');
    return;
  }
  const events = [];
  const handle = runTask({
    key: 'readiness',
    python: interpreter,
    root: ROOT,
    options: {},
    onEvent: (event) => events.push(event),
  });
  const result = await handle.done;

  assert.ok(handle.pid > 0);
  assert.deepEqual(handle.command, ['main.py', '--readiness']);
  assert.equal(result.timedOut, false);
  assert.equal(result.ok, true, `код ${result.code}`);

  const types = events.map((event) => event.type);
  assert.ok(types.includes('start'));
  assert.ok(types.includes('exit'));
  const lines = events.filter((event) => event.type === 'stdout').map((event) => event.line);
  assert.ok(lines.length > 0, 'задача не напечатала ни строки');
  // `--readiness` печатает JSON-отчёт: проверяем именно его, а не заголовок
  assert.ok(
    lines.some((line) => line.includes('percent')),
    `в выводе нет отчёта: ${lines.slice(0, 8).join(' | ')}`,
  );
});

test('stop() останавливает долгую задачу', async (t) => {
  const interpreter = python();
  if (!interpreter) {
    t.skip('Python не найден');
    return;
  }
  const handle = runTask({
    key: 'run',
    python: interpreter,
    root: ROOT,
    options: { genre: 'drift_phonk' },
  });
  const stopped = handle.stop();
  const result = await handle.done;

  assert.equal(stopped, true);
  assert.equal(result.ok, false, 'остановленная задача не может считаться успешной');
  assert.equal(handle.stop(), false, 'повторная остановка — не ошибка, но и не действие');
});

test('таймаут помечается честно', async (t) => {
  const interpreter = python();
  if (!interpreter) {
    t.skip('Python не найден');
    return;
  }
  // подменяем лимит через прямое изменение таблицы задач — это тест поведения
  const original = TASKS.run.timeoutMs;
  TASKS.run.timeoutMs = 50;
  try {
    const events = [];
    const handle = runTask({
      key: 'run',
      python: interpreter,
      root: ROOT,
      options: {},
      onEvent: (event) => events.push(event),
    });
    const result = await handle.done;

    assert.equal(result.timedOut, true);
    assert.equal(result.ok, false);
    assert.ok(events.some((event) => event.type === 'timeout'));
  } finally {
    TASKS.run.timeoutMs = original;
  }
});


test('сборка досье запускает тот же CLI, что терминал', () => {
  assert.deepEqual(
    buildCommand('dossier-build', { artist: 'Demo Artist' }),
    ['--dossier-build', '--dossier-artist', 'Demo Artist'],
  );
  // Без артиста задача не имеет смысла: отказ до запуска процесса.
  assert.throws(() => buildCommand('dossier-build', {}), /нужно имя артиста/);
  // Имя уходит аргументом в Python: путь и кавычки запрещены.
  for (const bad of ['../../etc', 'a; rm -rf /', 'x', '']) {
    assert.throws(() => buildCommand('dossier-build', { artist: bad }), /артиста/);
  }
  // Кириллица разрешена: артистов зовут не только латиницей.
  assert.deepEqual(
    buildCommand('dossier-build', { artist: 'МС Тест' }),
    ['--dossier-build', '--dossier-artist', 'МС Тест'],
  );
});
