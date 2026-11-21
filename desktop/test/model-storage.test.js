'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { scanDirectory, modelStorage } = require('../electron/model-storage');
test('model inventory reports real size, partial files and absence without importing models', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zs-models-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(dir, 'voice.pt'), '12345');
  fs.writeFileSync(path.join(dir, 'download.incomplete'), '12');
  fs.writeFileSync(path.join(dir, 'notes.txt'), 'not weights');
  const r = scanDirectory(dir);
  assert.deepEqual(r.files.map(f => f.bytes).sort(), [2, 5]);
  assert.equal(scanDirectory(path.join(dir, 'missing')).files.length, 0);
  assert.equal(scanDirectory(dir, 1).truncated, true);
});
test('model locations include workspace and explicit cache environment', () => {
  const locations = modelStorage({ root: null, home: '/no-such-zs-home', pipelineRoot: null, userData: null,
    env: { HF_HUB_CACHE: '/no-such-zs-hf', TORCH_HOME: '/no-such-zs-torch' } });
  assert.deepEqual(locations.map(l => l.directory), ['/no-such-zs-hf', '/no-such-zs-torch']);
});
test('registered environment IPC includes packaged workspace models', () => {
  const handlers = new Map();
  require('../electron/shell-service').registerShellIpc({
    ipcMain: { handle: (name, fn) => handlers.set(name, fn) },
    root: null, rootInfo: { candidates: [], error: null }, shell: {}, policy: {},
    settings: () => ({}), safeMusicDir: () => 'music', dossierPlan: () => ({ dir: 'dossiers' }),
    resolvePython: () => ({ python: 'python', error: null }),
    resolvePipelineRoot: () => ({ root: null, error: null }),
    getUserData: () => path.join(os.tmpdir(), 'zs-workspace-inventory'), isPackaged: true,
  });
  const report = handlers.get('zsmm:environment')().data;
  assert.equal(report.packaged, true);
  assert.ok(report.model_storage.some(l => l.directory === path.join(report.user_data, 'workspace', 'models')));
});
