'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { runTask, TASKS } = require('../electron/tasks');
const { monitorActivity } = require('../electron/process-control');
const { transition } = require('../src/core/creation-state');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const python = process.env.ZSMM_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');

test('state gate refuses zero exit without explicit setup and distinguishes setup from inference', () => {
  let state = transition(undefined, { type: 'prepare' });
  assert.equal(state.phase, 'preparing');
  state = transition(state, { type: 'prepared', result: { ok: true } });
  assert.equal(state.phase, 'blocked');
  assert.equal(transition(state, { type: 'generate' }).phase, 'blocked');
  state = transition(state, { type: 'prepared', result: { ok: true, report: { setup: {
    schema: 1, ok: true, inference_verified: false } } } });
  assert.equal(state.phase, 'ready');
  assert.equal(state.setup.inference_verified, false);
  state = transition(state, { type: 'generate' });
  assert.equal(state.phase, 'running');
  assert.equal(transition(state, { type: 'finished', result: { ok: false, canceled: true } }).phase, 'blocked');
});

test('silence warns but never triggers timeout before the hard deadline; monitor stops cleanly', async () => {
  const events = []; let timeout = false;
  const monitor = monitorActivity({ onEvent: e => events.push(e), hardMs: 150,
    quietMs: 10, intervalMs: 10, onTimeout: () => { timeout = true; } });
  await wait(45);
  assert.ok(events.some(e => e.quiet)); assert.equal(timeout, false);
  monitor.touch(); monitor.close(); const count = events.length;
  await wait(160); assert.equal(timeout, false); assert.equal(events.length, count);
});

for (const mode of ['cancel', 'timeout']) {
  test('real Python child and grandchild are terminated and locked file is reusable: ' + mode, { timeout: 20000 }, async t => {
    const root = await fsp.mkdtemp(path.join(os.tmpdir(), 'zsmm-tree-'));
    t.after(() => fsp.rm(root, { recursive: true, force: true }));
    await fsp.writeFile(path.join(root, 'worker.py'), `import os,time
from pathlib import Path
f=open('lock.bin','w+b'); f.write(b'x'); f.flush(); f.seek(0)
if os.name=='nt':
 import msvcrt
 msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
Path('child.pid').write_text(str(os.getpid()))
time.sleep(90)
`);
    await fsp.writeFile(path.join(root, 'main.py'), `import subprocess,sys,time
subprocess.Popen([sys.executable,'worker.py'])
time.sleep(90)
`);
    const old = TASKS.health.timeoutMs;
    TASKS.health.timeoutMs = mode === 'timeout' ? 5000 : 15000;
    t.after(() => { TASKS.health.timeoutMs = old; });
    const handle = runTask({ key: 'health', root, python });
    t.after(() => handle.stop());
    const deadline = Date.now() + 4500;
    while (!fs.existsSync(path.join(root, 'child.pid')) && Date.now() < deadline) await wait(25);
    assert.ok(fs.existsSync(path.join(root, 'child.pid')), 'grandchild started');
    const pid = Number(await fsp.readFile(path.join(root, 'child.pid'), 'utf8'));
    if (mode === 'cancel') assert.equal(handle.stop(), true);
    const result = await handle.done;
    assert.equal(result.ok, false);
    assert.equal(result.canceled, mode === 'cancel');
    assert.equal(result.timedOut, mode === 'timeout');
    assert.equal(result.termination.confirmed, true);
    let alive = false;
    try {
      process.kill(pid, 0); alive = true;
      if (process.platform === 'linux' && /\) Z /.test(fs.readFileSync(`/proc/${pid}/stat`, 'utf8'))) alive = false;
    } catch (e) { if (e.code !== 'ESRCH' && e.code !== 'ENOENT') throw e; }
    assert.equal(alive, false, 'grandchild no longer executes');
    // On Windows actually reacquire the byte lock released by the terminated worker.
    await fsp.writeFile(path.join(root, 'main.py'), `import os
f=open('lock.bin','r+b')
if os.name=='nt':
 import msvcrt
 msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
f.close()
print('recovery confirmed')
`);
    assert.equal((await runTask({ key: 'health', root, python }).done).ok, true);
  });
}
