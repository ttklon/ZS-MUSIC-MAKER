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
  assert.match(fs.readFileSync(path.join(dir, 'export.log'), 'utf8'), /visible error/);
  assert.equal(handlers['zsmm:report-error'](null, {}).ok, false);
});
