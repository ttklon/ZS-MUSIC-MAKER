'use strict';
/**
 * test/agent-bridge.test.js — «Сделать хит» без Electron.
 *
 * Проверяем три вещи, которые ломаются незаметно:
 *  1. мост `zsmm:agent-hit` реально запускает задачу и отдаёт ошибку, а не
 *     молча ничего не делает;
 *  2. путь к мастеру читается из отчёта Python, а не выдумывается окном;
 *  3. аргументы агентика доходят до `main.py` ровно теми флагами, которые
 *     понимает парсер (иначе кнопка «Сделать хит» падает на argparse).
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { registerAgentIpc, parseMasterPath, masterExists } = require('../electron/agent-service');
const { buildCommand, sanitizeOptions, TaskError } = require('../electron/tasks');
const { parseLog, reportText } = require('../src/core/agent-report');
const { parseEvent } = require('../src/core/task-events');
const { refusalOutcome, preservesSnapshot, unchangedSnapshot } = require('../electron/agent-preflight-check');

function harness({ startAgent = null, exists = () => true, openPath = async () => null } = {}) {
  const handlers = new Map();
  const calls = [];
  const ipcMain = { handle: (channel, fn) => handlers.set(channel, fn) };
  registerAgentIpc({
    ipcMain,
    fsApi: { existsSync: (target) => exists(target) },
    openPath,
    startAgent: startAgent || ((options) => {
      calls.push(options);
      return { ok: true, data: { pid: 42, command: ['main.py', '--agent-hit'] } };
    }),
  });
  return { handlers, calls };
}

test('каналы агентика зарегистрированы и запускают задачу', async () => {
  const { handlers, calls } = harness();
  const reply = await handlers.get('zsmm:agent-hit')({}, { mood: 'ночь', voice: 'record' });

  assert.equal(reply.ok, true);
  assert.equal(reply.data.pid, 42);
  assert.deepEqual(calls[0], { mood: 'ночь', voice: 'record' });
});

test('agent-hit привязывает поток событий к вызывающему окну', async () => {
  const sender = { id: 'window-sender' };
  let forwarded = null;
  const { handlers } = harness({ startAgent: (options, actualSender) => {
    forwarded = { options, actualSender };
    return { ok: true, data: { pid: 42, command: ['main.py', '--agent-hit'] } };
  } });

  const reply = await handlers.get('zsmm:agent-hit')({ sender }, { mood: 'ночь' });

  assert.equal(reply.ok, true);
  assert.deepEqual(forwarded, { options: { mood: 'ночь' }, actualSender: sender });
});

test('ошибка запуска отдаётся строкой, а не исключением', async () => {
  const { handlers } = harness({
    startAgent: () => { throw new Error('Python не найден'); },
  });
  const reply = await handlers.get('zsmm:agent-hit')({}, {});
  assert.equal(reply.ok, false);
  assert.match(reply.error, /Python не найден/);
});

test('installed preflight harness accepts an explicit refusal, not a successful render', () => {
  const run = { done: { ok: false, report: {
    result: { succeeded: false, status: 'failed' },
    hardware_preflight: { status: 'blocked', decision: 'refuse', can_attempt: false,
      selected_backend: 'procedural_dsp', inference_verified: false,
      product_profile_accepted: false, reasons: ['ram_available_gib: unknown'] },
  } }, events: [{ type: 'protocol', event: { type: 'progress', message: 'preflight' } }] };
  assert.equal(refusalOutcome(run, 'ram_available_gib').ok, true);
  run.events.push({ type: 'protocol', event: { type: 'progress', message: 'HitFactory: rendering' } });
  assert.equal(refusalOutcome(run, 'ram_available_gib').ok, false);
});

test('hardware denial snapshot allows no writes; retry may add files but preserves prior hashes', () => {
  const before = { 'previous.wav': 'abc', 'note.txt': 'def' };
  assert.equal(unchangedSnapshot(before, { ...before }), true);
  assert.equal(unchangedSnapshot(before, { ...before, 'new.wav': 'ghi' }), false);
  assert.equal(preservesSnapshot(before, { ...before, 'new.wav': 'ghi' }), true);
  assert.equal(preservesSnapshot(before, { ...before, 'previous.wav': 'changed' }), false);
});

test('мастер читается из отчёта Python, а не из последней строки', () => {
  const lines = [
    '[agent-hit] Агент понял: тема=ночь',
    JSON.stringify({ schema: 'zsmm.task', version: 1, task_id: 'test', seq: 1, type: 'done', ok: false, report: { verdict: 'HIT', master_path: 'C:/hits/master.wav', hit_score: 74.2 } }),
    '[agent-hit] Готово за 91 с',
  ];
  const result = parseMasterPath(lines);
  assert.equal(result.masterPath, 'C:/hits/master.wav');
  assert.equal(result.verdict, 'HIT');
});

test('отчёт с verdict=FAILED не выдаёт себя за готовый трек', () => {
  const result = parseMasterPath([JSON.stringify({ schema: 'zsmm.task', version: 1, task_id: 'test', seq: 1, type: 'done', ok: false, report: { verdict: 'FAILED', master_path: null } })]);
  assert.equal(result.masterPath, null);
  assert.equal(result.verdict, 'FAILED');
});

test('инвентаризация и DSP master не обозначаются проверенным inference или принятым профилем', () => {
  const line = JSON.stringify({ schema: 'zsmm.task', version: 1, task_id: 'test', seq: 1,
    type: 'done', ok: false, report: { verdict: 'PARTIAL', master_path: 'C:/hits/master.wav',
      blocked: [{ stage: 'lyrics', reason: 'Ollama unavailable' }],
      hardware_preflight: { status: 'inventory_only', selected_backend: 'procedural_dsp',
        inference_verified: false, product_profile_accepted: false } } });
  const result = parseLog([line], parseEvent);
  const text = reportText(result);
  assert.match(text, /промежуточный мастер-артефакт/);
  assert.match(text, /inventory_only/);
  assert.match(text, /backend procedural_dsp/);
  assert.match(text, /Inference не подтверждён; профиль продукта не принят/);
  assert.match(text, /не подтверждает модельный inference/);
  assert.doesNotMatch(text, /Готовый трек:/);
});

test('preflight refusal is shown explicitly and without a success label', () => {
  const line = JSON.stringify({ schema: 'zsmm.task', version: 1, task_id: 'test', seq: 1,
    type: 'done', ok: false, report: { verdict: 'FAILED', master_path: null,
      blocked: [{ stage: 'hardware_preflight', reason: 'ram_available_gib unknown' }],
      hardware_preflight: { status: 'blocked', decision: 'refuse', selected_backend: 'musicgen',
        inference_verified: false, product_profile_accepted: false } } });
  const text = reportText(parseLog([line], parseEvent));
  assert.match(text, /Мастер-файл не создан/);
  assert.match(text, /hardware_preflight: ram_available_gib unknown/);
  assert.match(text, /backend musicgen/);
  assert.doesNotMatch(text, /Готовый трек|Результат принят/);
});

test('открытие мастера проверяет файл на диске', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-agent-'));
  const file = path.join(dir, 'master.wav');
  fs.writeFileSync(file, 'RIFF');

  const opened = [];
  const { handlers } = harness({
    exists: (target) => fs.existsSync(target),
    openPath: async (target) => { opened.push(target); return null; },
  });
  const ok = await handlers.get('zsmm:agent-open')({}, { masterPath: file });
  assert.equal(ok.ok, true);
  assert.deepEqual(opened, [file]);

  const missing = await handlers.get('zsmm:agent-open')({}, { masterPath: path.join(dir, 'nope.wav') });
  assert.equal(missing.ok, false);
  assert.match(missing.error, /не найден/);
  fs.rmSync(dir, { recursive: true, force: true });
});

test('относительный путь не считается мастером', () => {
  assert.equal(masterExists('output/hits/master.wav', fs), false);
  assert.equal(masterExists('', fs), false);
});

test('аргументы агентика: ровно те флаги, что понимает парсер', () => {
  const argv = buildCommand('agent-hit', {
    mood: 'ночной город', artist: 'ICEGERGERT', refs: 'C:/ref.wav', voice: 'record',
  });
  // Порядок не важен — важен состав: ровно четыре ответа и ни одного лишнего.
  assert.equal(argv[0], '--agent-hit');
  const pairs = {};
  for (let index = 1; index < argv.length; index += 2) pairs[argv[index]] = argv[index + 1];
  assert.deepEqual(pairs, {
    '--agent-mood': 'ночной город',
    '--agent-artist': 'ICEGERGERT',
    '--agent-refs': 'C:/ref.wav',
    '--agent-voice': 'record',
  });
  for (const flag of ['--agent-mood', '--agent-artist', '--agent-refs', '--agent-voice']) {
    assert.ok(argv.includes(flag), flag);
  }
});

test('пустой артист у агентика — это «из трендов», а не ошибка', () => {
  const argv = buildCommand('agent-hit', {});
  assert.deepEqual(argv, ['--agent-hit']);
});

test('досье по-прежнему требует артиста', () => {
  assert.throws(() => buildCommand('dossier-build', {}), TaskError);
});

test('перевод строки в теме не ломает формат отчёта', () => {
  const safeOptions = sanitizeOptions({ mood: 'ночь\nтачки' });
  assert.equal(safeOptions.mood, 'ночь тачки');
  assert.throws(() => sanitizeOptions({ mood: 'x'.repeat(400) }), TaskError);
});

test('кавычки в референсах вычищаются: склейка аргументов невозможна', () => {
  const safeOptions = sanitizeOptions({ refs: '"C:/a.wav" `b`' });
  assert.equal(safeOptions.refs.includes('"'), false);
  assert.equal(safeOptions.refs.includes('`'), false);
});
