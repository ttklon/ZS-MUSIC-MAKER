'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { prepareWorkspace } = require('../electron/pipeline-workspace');
async function fixture(t) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'zsmm-workspace-'));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  const source = path.join(dir, 'installed'), target = path.join(dir, 'user');
  for (const tree of ['app', 'config', 'data', '.python', 'models', 'output']) await fs.mkdir(path.join(source, tree), { recursive: true });
  await fs.writeFile(path.join(source, 'main.py'), 'print("v1")');
  await fs.writeFile(path.join(source, 'app', 'core.py'), 'VERSION = 1');
  await fs.writeFile(path.join(source, 'config', 'settings.py'), 'SETTINGS = {}');
  await fs.writeFile(path.join(source, 'config', 'defaults.json'), '{"default":true}');
  await fs.writeFile(path.join(source, '.python', 'python.exe'), 'do not copy');
  return { source, target };
}
test('prepares writable code/config without copying bundled Python or model trees', async t => {
  const { source, target } = await fixture(t);
  assert.equal(await prepareWorkspace(source, target), target);
  assert.equal(await fs.readFile(path.join(target, 'config', 'settings.py'), 'utf8'), 'SETTINGS = {}');
  for (const name of ['.python', 'models', 'output']) await assert.rejects(fs.stat(path.join(target, name)), { code: 'ENOENT' });
  await fs.mkdir(path.join(target, 'output')); await fs.writeFile(path.join(target, 'output', 'result.wav'), 'result');
  assert.equal(await fs.readFile(path.join(source, 'main.py'), 'utf8'), 'print("v1")');
});
test('upgrade refreshes code and preserves user models, outputs and settings', async t => {
  const { source, target } = await fixture(t);
  await prepareWorkspace(source, target);
  await fs.mkdir(path.join(target, 'models')); await fs.mkdir(path.join(target, 'output'));
  await fs.writeFile(path.join(target, 'models', 'voice.pt'), 'model');
  await fs.writeFile(path.join(target, 'output', 'master.wav'), 'audio');
  await fs.writeFile(path.join(target, 'config', 'defaults.json'), '{"mine":true}');
  await fs.writeFile(path.join(source, 'app', 'core.py'), 'VERSION = 2');
  await prepareWorkspace(source, target);
  assert.equal(await fs.readFile(path.join(target, 'app', 'core.py'), 'utf8'), 'VERSION = 2');
  assert.equal(await fs.readFile(path.join(target, 'models', 'voice.pt'), 'utf8'), 'model');
  assert.equal(await fs.readFile(path.join(target, 'output', 'master.wav'), 'utf8'), 'audio');
  assert.equal(await fs.readFile(path.join(target, 'config', 'defaults.json'), 'utf8'), '{"mine":true}');
});
test('rejects accidental nested workspace and retries cleanly after missing main', async t => {
  const { source, target } = await fixture(t);
  await assert.rejects(prepareWorkspace(source, path.join(source, 'user')), /outside/);
  await fs.unlink(path.join(source, 'main.py'));
  await assert.rejects(prepareWorkspace(source, target));
  await fs.writeFile(path.join(source, 'main.py'), 'repaired');
  await prepareWorkspace(source, target);
  assert.equal(await fs.readFile(path.join(target, 'main.py'), 'utf8'), 'repaired');
});

test('task runner executes in workspace, not the installed project', async t => {
  const { source, target } = await fixture(t);
  // This fixture's fake exe tests copying, not execution: Windows must not select it.
  await fs.rm(path.join(source, '.python'), { recursive: true, force: true });
  await fs.writeFile(path.join(source, 'main.py'),
    'from pathlib import Path\nPath("output").mkdir(exist_ok=True)\nPath("output/probe.txt").write_text(str(Path.cwd()))\n');
  const { registerTaskIpc } = require('../electron/task-runner');
  const state = { activeTask: null };
  const runner = registerTaskIpc({ ipcMain: { handle() {} }, root: source, workspaceRoot: target, state });
  const reply = await runner.start('health');
  assert.equal(reply.ok, true, reply.error);
  const result = await state.activeTask.done;
  assert.equal(result.ok, true);
  assert.equal(await fs.realpath((await fs.readFile(path.join(target, 'output/probe.txt'), 'utf8')).trim()), await fs.realpath(target));
  await assert.rejects(fs.stat(path.join(source, 'output/probe.txt')), { code: 'ENOENT' });
});
