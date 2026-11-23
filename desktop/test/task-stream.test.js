'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { PassThrough } = require('node:stream');
const { once } = require('node:events');
const { createTaskStream } = require('../electron/task-stream');
const { parseEvent } = require('../src/core/task-events');
const event = (seq, type, payload = {}) => ({ schema: 'zsmm.task', version: 1, task_id: 'id', seq, type, ...payload });
async function feed(chunks, options = {}) {
  const seen = [], stream = new PassThrough();
  const decoder = createTaskStream({ taskId: 'id', onEvent: e => seen.push(e), ...options });
  decoder.attach(stream, 'stdout');
  const ended = once(stream, 'end');
  for (const chunk of chunks) stream.write(chunk);
  stream.end(); await ended;
  return { seen, ...decoder.result() };
}
test('UTF8 byte splits, CRLF, multiple records, multiline text and trailing EOF', async () => {
  const text = JSON.stringify(event(1, 'progress', { message: 'Ночь\nновая строка' })) + '\r\n' +
    'noise {"master_path":"fake.wav"}\n' + JSON.stringify(event(2, 'done', { ok: false, report: { master_path: 'real.wav' } }));
  const bytes = Buffer.from(text);
  const result = await feed([...bytes].map(b => Buffer.from([b])));
  assert.equal(result.invalid, false);
  assert.equal(result.seen[0].event.message, 'Ночь\nновая строка');
  assert.equal(result.seen[1].type, 'stdout');
  assert.equal(result.terminal.report.master_path, 'real.wav');
});
test('unrelated JSON and log braces never become protocol results', async () => {
  const result = await feed(['{"master_path":"fake.wav"}\n[agent] {"master_path":"fake2.wav"}\n']);
  assert.equal(result.terminal, null);
  assert.equal(parseEvent('{"master_path":"fake.wav"}'), null);
});
for (const mutation of [e => ({ ...e, task_id: 'foreign' }), e => ({ ...e, seq: 3 }), e => ({ ...e, version: 2 })]) {
  test('identity sequence and unknown version fail closed ' + mutation, async () => {
    const result = await feed([JSON.stringify(mutation(event(1, 'done', { ok: true, report: {} }))) + '\n']);
    assert.equal(result.invalid, true);
    assert.equal(result.terminal, null);
  });
}
test('oversized line discarded through newline, recovery remains marked invalid', async () => {
  const result = await feed(['x'.repeat(300), '\n', JSON.stringify(event(1, 'done', { ok: false, report: {} })) + '\n'], { maxLine: 200 });
  assert.equal(result.invalid, true);
  assert.equal(result.terminal.ok, false);
});
test('duplicate terminal is not accepted', async () => {
  const result = await feed([JSON.stringify(event(1, 'done', { ok: true, report: {} })) + '\n' +
    JSON.stringify(event(2, 'done', { ok: true, report: {} })) + '\n']);
  assert.equal(result.invalid, true);
});
