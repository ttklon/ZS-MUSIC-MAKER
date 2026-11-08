'use strict';
/**
 * Раздел «Запуск»: окно запускает РЕАЛЬНЫЙ процесс и показывает его вывод.
 *
 * Здесь Electron не нужен — проверяется связка окна с задачами: события
 * приходят из `electron/tasks.js`, вывод попадает в панель, остановка
 * отражается в статусе. Python в этом окружении есть, поэтому запускается
 * настоящий `main.py --readiness`.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { documentFromHtml, bootWindow: bootDocumentWindow } = require('./fake-dom');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');
const { runTask } = require('../electron/tasks');

const SRC = path.resolve(__dirname, '..', 'src');
const ROOT = path.resolve(__dirname, '..', '..');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

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

/** Мост: данные — настоящие, задачи — через реальный runTask. */
function bridge(overrides = {}) {
  const project = createProject(createNodeFs(), ROOT);
  const wrap = (loader) => async () => ({ ok: true, data: loader() });
  const taskListeners = [];
  const doneListeners = [];
  let current = null;

  return {
    version: wrap(() => project.version()),
    genres: wrap(() => project.genres()),
    modules: wrap(() => project.modules()),
    readiness: wrap(() => project.readiness()),
    dossiers: wrap(() => project.dossiers()),
    system: wrap(() => project.systemInfo()),
    listTasks: async () => [
      { key: 'readiness', label: 'Готовность', accepts: [] },
      { key: 'run', label: 'Полный прогон', accepts: ['genre', 'seed'] },
    ],
    startTask: async (key, options) => {
      const interpreter = python();
      if (!interpreter) return { ok: false, error: 'Python не найден' };
      try {
        current = runTask({
          key,
          options,
          python: interpreter,
          root: ROOT,
          onEvent: (event) => taskListeners.forEach((cb) => cb(event)),
        });
      } catch (err) {
        return { ok: false, error: err.message };
      }
      current.done.then((result) => doneListeners.forEach((cb) => cb(result)));
      return { ok: true, data: { pid: current.pid, command: current.command } };
    },
    stopTask: async () => {
      if (!current) return { ok: false, error: 'нет задачи' };
      return { ok: true, data: { stopped: current.stop() } };
    },
    onTaskEvent: (cb) => {
      taskListeners.push(cb);
      return () => {};
    },
    onTaskDone: (cb) => {
      doneListeners.push(cb);
      return () => {};
    },
    revealRoot: async () => ({ ok: true }),
    ...overrides,
  };
}

/** Поднять всё окно (`app.js` + `sections/*.js`) с указанным мостом. */
function bootWindow(api) {
  global.setTimeout = global.setTimeout;
  return bootDocumentWindow({ srcDir: SRC, html: HTML, bridge: api });
}

const flush = () => new Promise((resolve) => setImmediate(resolve));
const waitFor = async (check, timeoutMs = 60_000) => {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (check()) return true;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  return false;
};

test('в разделе «Запуск» есть список задач и кнопки', async (t) => {
  const { document } = bootWindow(bridge());
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  assert.ok(button, 'нет пункта навигации «Запуск»');
  button.dispatch('click');
  await flush();
  await flush();

  const select = document.getElementById('task-select');
  assert.equal(select.children.length, 2);
  assert.equal(document.getElementById('task-start').disabled, false);
  assert.equal(document.getElementById('task-stop').disabled, true);
});

test('нажатие «Запустить» показывает живой вывод и успешное завершение', async (t) => {
  const interpreter = python();
  if (!interpreter) {
    t.skip('Python не найден');
    return;
  }
  const { document } = bootWindow(bridge());
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  document.getElementById('task-select').value = 'readiness';
  document.getElementById('task-start').dispatch('click');

  const finished = await waitFor(
    () => /Завершено/.test(document.getElementById('task-status').textContent),
  );

  assert.ok(finished, `статус: ${document.getElementById('task-status').textContent}`);
  assert.match(document.getElementById('task-status').textContent, /успешно/);
  const output = document.getElementById('task-output').textContent;
  assert.ok(output.length > 0, 'вывод задачи пуст');
  assert.match(output, /percent|готовность|readiness/i);
  assert.equal(document.getElementById('task-start').disabled, false, 'кнопка снова доступна');
});

test('некорректный сид: ошибка видна, задача не стартует', async (t) => {
  const interpreter = python();
  if (!interpreter) {
    t.skip('Python не найден');
    return;
  }
  const { document } = bootWindow(bridge());
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  document.getElementById('task-select').value = 'run';
  document.getElementById('task-seed').value = '-7';
  document.getElementById('task-start').dispatch('click');
  await flush();
  await flush();

  const banner = document.getElementById('error-banner');
  assert.equal(banner.classList.contains('is-hidden'), false);
  assert.match(banner.textContent, /сид/);
  assert.equal(document.getElementById('task-start').disabled, false);
});

test('нет Python — понятное сообщение, а не зависание', async (t) => {
  const api = bridge({
    startTask: async () => ({ ok: false, error: 'Python не найден. Укажите ZSMM_PYTHON' }),
  });
  const { document } = bootWindow(api);
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  document.getElementById('task-start').dispatch('click');
  await flush();
  await flush();

  assert.match(document.getElementById('error-banner').textContent, /ZSMM_PYTHON/);
  assert.equal(document.getElementById('task-status').textContent, 'Не запущено');
});


test('«Собрать досье» передаёт артиста в задачу dossier-build', async (t) => {
  const calls = [];
  const api = bridge({
    listTasks: async () => ({ ok: true, data: [
      { key: 'health', label: 'Проверка окружения', accepts: [] },
      { key: 'dossier-build', label: 'Собрать досье артиста', accepts: ['artist'] },
    ] }),
    startTask: async (key, options) => {
      calls.push({ key, options });
      return { ok: true, data: { command: ['python', 'main.py', '--dossier-build'], pid: 7 } };
    },
  });
  const { document } = bootWindow(api);
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  document.getElementById('task-select').value = 'dossier-build';
  document.getElementById('task-artist').value = 'Demo Artist';
  document.getElementById('task-start').dispatch('click');
  await flush();
  await flush();

  assert.deepEqual(calls, [{ key: 'dossier-build', options: { artist: 'Demo Artist' } }]);
  assert.match(document.getElementById('task-status').textContent, /Запущено/);
});


test('без Python раздел «Запуск» говорит об этом до нажатия', async (t) => {
  const api = bridge({
    environment: async () => ({
      ok: true,
      data: {
        python: null,
        python_error: 'Python не найден: ни .venv, ни PATH',
        user_data: 'C:/u',
        music_dir: 'C:/m',
        root: 'C:/p',
        packaged: true,
      },
    }),
  });
  const { document } = bootWindow(api);
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  const note = document.getElementById('task-python-note').textContent;
  assert.match(note, /не найден/i);
  // Важно, что рядом сказано: остальное окно от Python не зависит.
  assert.match(note, /без него/);
  // И кнопка не спрятана: пользователь должен видеть, что она есть.
  assert.equal(document.getElementById('task-start').disabled, false);
});

test('нативная задача запускается без Python и подпись это говорит', async (t) => {
  const api = bridge({
    // Python «не найден» — а задача всё равно должна работать.
    environment: async () => ({ ok: true, data: { python: null, python_error: 'Python не найден' } }),
    listTasks: async () => ({ ok: true, data: [
      { key: 'native-files', label: 'Проверка файлов проекта (без Python)', accepts: [], native: true },
      { key: 'readiness', label: 'Готовность через Python', accepts: [] },
    ] }),
    startTask: async (key) => ({
      ok: true,
      data: { pid: null, command: ['Проверка файлов проекта (без Python)'], native: true },
    }),
  });
  const { document } = bootWindow(api);
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  // Выбрана нативная задача — про Python не предупреждаем.
  document.getElementById('task-select').value = 'native-files';
  document.getElementById('task-select').dispatch('change');
  assert.match(document.getElementById('task-python-note').textContent, /Python не нужен/);

  document.getElementById('task-start').dispatch('click');
  await flush();
  await flush();
  const status = document.getElementById('task-status').textContent;
  assert.match(status, /Запущено: Проверка файлов проекта/);
  // pid у нативной задачи нет — окно не пишет «(pid null)».
  assert.doesNotMatch(status, /pid/);

  // Переключились на задачу Python — предупреждение вернулось.
  document.getElementById('task-select').value = 'readiness';
  document.getElementById('task-select').dispatch('change');
  assert.match(document.getElementById('task-python-note').textContent, /не найден/i);
});

test('Python есть, а пайплайна нет — раздел не обещает запуск', async (t) => {
  const api = bridge({
    environment: async () => ({
      ok: true,
      data: {
        python: 'C:/Python311/python.exe',
        python_error: null,
        pipeline_root: null,
        pipeline_error: 'Пайплайн на Python в поставку не входит: укажите ZSMM_PIPELINE_ROOT.',
      },
    }),
  });
  const { document } = bootWindow(api);
  t.after(() => {
    delete global.window;
    delete global.document;
  });
  await flush();
  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'run');
  button.dispatch('click');
  await flush();
  await flush();

  const note = document.getElementById('task-python-note').textContent;
  // Главное: окно не говорит «всё хорошо» на основании одного интерпретатора.
  assert.match(note, /Python найден/);
  assert.match(note, /не входит/);
  assert.match(note, /ZSMM_PIPELINE_ROOT/);
});
