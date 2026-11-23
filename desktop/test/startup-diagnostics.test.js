'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createDiagnostics, registerDiagnostics } = require('../electron/startup-diagnostics');
function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-errors-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return { dir, diagnostics: createDiagnostics(dir) };
}
test('persists bounded startup error and rotates locally', t => {
  const { diagnostics } = fixture(t);
  diagnostics.record('startup', new Error('failure'));
  assert.match(fs.readFileSync(diagnostics.file, 'utf8'), /failure/);
  for (let i = 0; i < 300; i++) diagnostics.record('renderer', 'x'.repeat(5000));
  assert.ok(fs.statSync(diagnostics.file).size < 1100000);
  assert.ok(fs.existsSync(diagnostics.file + '.previous'));
});
test('exports only after save dialog and cancellation does not write a file', async t => {
  const { dir, diagnostics } = fixture(t); diagnostics.record('renderer', 'visible error');
  const handlers = {};
  registerDiagnostics({ ipcMain: { handle: (k, fn) => { handlers[k] = fn; } }, diagnostics,
    dialog: { showSaveDialog: async () => ({ filePath: path.join(dir, 'export.log') }) } });
  assert.equal((await handlers['zsmm:export-errors']()).ok, true);
  const exported = JSON.parse(fs.readFileSync(path.join(dir, 'export.log'), 'utf8'));
  assert.equal(exported.schema, 2); assert.equal(exported.entries[0].source, 'renderer');
  assert.doesNotMatch(JSON.stringify(exported), /visible error/);
  assert.equal(handlers['zsmm:report-error'](null, {}).ok, false);
});

test('task lifecycle and renderer errors correlate without raw prompts argv tokens or media', t => {
  const { dir, diagnostics } = fixture(t);
  diagnostics.task('task-id', 'agent-hit', { type: 'start', command: ['secret prompt'] });
  diagnostics.task('task-id', 'agent-hit', { type: 'stdout', line: 'private lyrics and secret' });
  diagnostics.task('task-id', 'agent-hit', { type: 'protocol', event: { type: 'error', message: 'token=abc password="multi word" Bearer xyz https://host/private?key=secret' } });
  diagnostics.record('renderer', 'C:\\Users\\Private\\voice.wav failed api_key=abc', 'task-id');
  const text = fs.readFileSync(diagnostics.file, 'utf8');
  assert.match(text, /task-id/); assert.match(text, /python/); assert.match(text, /renderer/);
  for (const privateValue of ['secret prompt', 'private lyrics', 'token=abc', 'multi word', 'Bearer xyz', 'Private', 'host/private', 'api_key=abc']) assert.ok(!text.includes(privateValue), privateValue);
  assert.deepEqual(fs.readdirSync(dir), ['startup-errors.jsonl']);
});

test('canceling diagnostic export does not create a file', async t => {
  const { dir, diagnostics } = fixture(t); const handlers = {};
  registerDiagnostics({ ipcMain: { handle: (key, fn) => { handlers[key] = fn; } }, diagnostics,
    dialog: { showSaveDialog: async () => ({ canceled: true, filePath: path.join(dir, 'must-not-exist') }) } });
  assert.equal((await handlers['zsmm:export-errors']()).canceled, true);
  assert.equal(fs.existsSync(path.join(dir, 'must-not-exist')), false);
});

test('independent export consumer: unknown private text and task identifiers cannot cross allowlist', t => {
  const { diagnostics } = fixture(t);
  const secret = require('node:crypto').randomBytes(24).toString('hex');
  diagnostics.record('renderer', 'unknown creative text ' + secret, secret);
  diagnostics.record('python', 'unrecognized credential ' + secret, secret);
  diagnostics.task(secret, 'agent-hit', { type: 'exit', code: 2 });
  const out = require('../electron/startup-diagnostics').exportDiagnostics(diagnostics);
  assert.equal(JSON.stringify(out).includes(secret), false);
  assert.equal(out.entries.length, 3);
  assert.ok(out.entries.every(e => e.task === 1));
  for (const entry of out.entries) assert.ok(Object.keys(entry).every(k => ['source', 'task', 'event', 'code', 'ok', 'canceled', 'timedOut', 'cleanupConfirmed'].includes(k)));
});

test('structured export tolerates malformed task messages without exporting their content', () => {
  const { safeExport } = require('../electron/diagnostic-export');
  for (const message of ['null', 'false', '[]', '42', '"private text"', 'invalid json']) {
    const result = safeExport(JSON.stringify({ source: 'task', message }));
    assert.deepEqual(result.entries, [{ source: 'task', task: null, event: 'error' }]);
  }
});
