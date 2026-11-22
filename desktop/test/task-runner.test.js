'use strict';
/**
 * test/task-runner.test.js — каналы запуска задач без Electron.
 *
 * Самое важное здесь — не «канал зарегистрирован», а условия, при которых
 * задача вообще может стартовать. В установленной сборке есть данные проекта,
 * но нет ни `main.py`, ни `app/`: если проверять только интерпретатор, окно
 * покажет «Python найден» и будет падать на каждом запуске.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { registerTaskIpc } = require('../electron/task-runner');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');

/** Двойник ipcMain и окна: события складываются в массив. */
function harness({ root = ROOT, cwd = { cwd: ROOT }, project = null } = {}) {
  const handlers = new Map();
  const events = [];
  const sends = [];
  const ipcMain = { handle: (channel, fn) => handlers.set(channel, fn) };
  const sender = {
    isDestroyed: () => false,
    send: (channel, payload) => {
      sends.push({ channel, payload });
      if (channel === 'zsmm:task-event') events.push(payload);
    },
  };
  const state = { activeTask: null, dossierDir: null };
  registerTaskIpc({
    ipcMain,
    root,
    getProject: () => project || createProject(createNodeFs(), root),
    getWindows: () => null,
    state,
  });
  return { handlers, events, sends, state, sender, cwd };
}

test('список задач отдаётся с пометкой «без Python»', async () => {
  const { handlers } = harness();
  const reply = await handlers.get('zsmm:tasks')({}, {});
  assert.equal(reply.ok, true);
  const keys = reply.data.map((task) => task.key);
  for (const key of ['native-files', 'run', 'dossier-build']) assert.ok(keys.includes(key), key);
  assert.equal(reply.data.find((task) => task.key === 'native-files').native, true);
  assert.equal(reply.data.find((task) => task.key === 'run').native, false);
});

test('нативная задача выполняется и отдаёт построчный вывод', async () => {
  const { handlers, events, sender } = harness();
  const reply = await handlers.get('zsmm:task-start')({ sender }, { key: 'native-files' });

  assert.equal(reply.ok, true, reply.error);
  assert.equal(reply.data.native, true);
  assert.equal(reply.data.pid, null);
  const stdout = events.filter((event) => event.type === 'stdout').map((event) => event.line);
  assert.ok(stdout.some((line) => /^OK версия/.test(line)), stdout.join('\n'));
  assert.equal(events[0].type, 'start');
});

test('интерпретатор найден, но пайплайна нет — отказ с причиной', async (t) => {
  // Установщик: данные проекта на месте, main.py отсутствует.
  const dataOnly = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-runner-'));
  fs.writeFileSync(path.join(dataOnly, 'version.json'), '{"version":"1.0.0"}');
  fs.mkdirSync(path.join(dataOnly, 'config'), { recursive: true });
  fs.writeFileSync(path.join(dataOnly, 'config', 'genres_100.json'), '{}');
  t.after(() => fs.rmSync(dataOnly, { recursive: true, force: true }));

  const saved = process.env.ZSMM_PYTHON;
  process.env.ZSMM_PYTHON = process.execPath; // «Python найден» — как на машине с Python
  t.after(() => {
    if (saved === undefined) delete process.env.ZSMM_PYTHON;
    else process.env.ZSMM_PYTHON = saved;
  });

  const { handlers, sender, state } = harness({ root: dataOnly });
  const reply = await handlers.get('zsmm:task-start')({ sender }, { key: 'readiness' });

  assert.equal(reply.ok, false);
  assert.match(reply.error, /main\.py|ZSMM_PIPELINE_ROOT/);
  // Задача не осталась «висящей»: повторный запуск снова даёт отказ по делу,
  // а не «уже выполняется другая задача».
  assert.equal(state.activeTask, null);
});

test('неизвестная нативная задача не запускает процесс', async () => {
  const { handlers, sender } = harness();
  const reply = await handlers.get('zsmm:task-start')({ sender }, { key: 'native-nothing' });
  // Ключа нет в белом списке — это путь обычной задачи, и он честно требует
  // пайплайн/интерпретатор, а не выдаёт «ok».
  assert.equal(reply.ok, false);
  assert.ok(reply.error);
});

test('остановка без задачи — отказ, а не тихий успех', async () => {
  const { handlers } = harness();
  const reply = await handlers.get('zsmm:task-stop')({}, {});
  assert.equal(reply.ok, false);
  assert.match(reply.error, /нет запущенной/);
});

test('нативная задача ставит и снимает индикатор панели задач', async () => {
  // Индикатор — единственный признак, что окно занято, когда оно свёрнуто.
  // Нативные задачи раньше его не трогали вовсе.
  const handlers = new Map();
  const progress = [];
  const ipcMain = { handle: (channel, fn) => handlers.set(channel, fn) };
  const sender = { isDestroyed: () => false, send: () => {} };
  registerTaskIpc({
    ipcMain,
    root: ROOT,
    getProject: () => createProject(createNodeFs(), ROOT),
    getWindows: () => ({ showTaskProgress: (event) => progress.push(event.type) }),
    state: { activeTask: null, dossierDir: null },
  });

  const reply = await handlers.get('zsmm:task-start')({ sender }, { key: 'native-files' });
  assert.equal(reply.ok, true, reply.error);
  assert.deepEqual(progress, ['start', 'exit']);
});

test('shared single slot rejects a second registration while preparation is awaiting and releases on failure', async t => {
  const workspace = require('../electron/pipeline-workspace');
  const original = workspace.prepareWorkspace;
  let fail;
  workspace.prepareWorkspace = () => new Promise((_resolve, reject) => { fail = reject; });
  t.after(() => { workspace.prepareWorkspace = original; });
  const state = { activeTask: null };
  const setup = () => registerTaskIpc({ ipcMain: { handle() {} }, root: ROOT,
    workspaceRoot: 'unused-test-workspace', state, getProject: () => ({}) });
  const first = setup(), second = setup();
  const starting = first.start('bootstrap');
  await new Promise(resolve => setImmediate(resolve));
  assert.ok(state.taskSlot?.taskId);
  const rejected = await second.start('bootstrap');
  assert.equal(rejected.ok, false);
  assert.equal(rejected.taskId, state.taskSlot.taskId);
  fail(new Error('fixture preparation failed'));
  assert.match((await starting).error, /fixture preparation failed/);
  assert.equal(state.taskSlot, null);
  const retry = second.start('bootstrap');
  await new Promise(resolve => setImmediate(resolve));
  fail(new Error('retry failure'));
  assert.match((await retry).error, /retry failure/);
  assert.equal(state.taskSlot, null);
});

test('native task events and completion carry the same unique ID', async () => {
  const f = harness();
  const first = await f.handlers.get('zsmm:task-start')({ sender: f.sender }, { key: 'native-files' });
  const second = await f.handlers.get('zsmm:task-start')({ sender: f.sender }, { key: 'native-files' });
  assert.notEqual(first.data.taskId, second.data.taskId);
  assert.ok(f.sends.every(s => s.payload.taskId && s.payload.eventVersion === 1));
});

test('stop during workspace preparation aborts copying and never starts Python', async t => {
  const workspace = require('../electron/pipeline-workspace'), tasks = require('../electron/tasks');
  const original = workspace.prepareWorkspace, originalRun = tasks.runTask;
  let signal, release, launched = false;
  workspace.prepareWorkspace = (_source, target, options) => { signal = options.signal; return new Promise(resolve => { release = () => resolve(target); }); };
  tasks.runTask = () => { launched = true; throw new Error('must not spawn'); };
  t.after(() => { workspace.prepareWorkspace = original; tasks.runTask = originalRun; });
  const handlers = new Map(), state = { activeTask: null };
  const runner = registerTaskIpc({ ipcMain: { handle: (key, fn) => handlers.set(key, fn) }, root: ROOT,
    workspaceRoot: 'unused-test-workspace', state });
  const pending = runner.start('bootstrap');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(handlers.get('zsmm:task-stop')().data.pending, true);
  assert.equal(signal.aborted, true); assert.ok(state.taskSlot, 'slot stays held until preparation settles');
  release(); assert.equal((await pending).ok, false);
  assert.equal(launched, false); assert.equal(state.taskSlot, null);
});
