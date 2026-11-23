'use strict';
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');
const { runAgentFromInstalledUi } = require('./agent-preflight-ui');

function processIsRunning(pid) {
  if (!Number.isSafeInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    if (process.platform === 'linux') {
      try { if (/\) Z /.test(fs.readFileSync(`/proc/${pid}/stat`, 'utf8'))) return false; }
      catch (error) { if (error.code === 'ENOENT') return false; throw error; }
    }
    return true;
  } catch (error) {
    if (['ESRCH', 'ENOENT'].includes(error.code)) return false;
    throw error;
  }
}

async function runInstalledWorkerCancellation({ window, python, markerPath, lockPath, timeoutMs = 90000 }) {
  let settled = false;
  const taskPromise = runAgentFromInstalledUi(window, '').then(
    (run) => { settled = true; return { run }; },
    (error) => { settled = true; return { error: error?.message || String(error) }; },
  );
  const deadline = Date.now() + timeoutMs;
  while (!fs.existsSync(markerPath) && !settled && Date.now() < deadline)
    await new Promise((resolve) => setTimeout(resolve, 25));

  let metadata = null;
  let markerError = null;
  if (fs.existsSync(markerPath)) {
    try { metadata = JSON.parse(fs.readFileSync(markerPath, 'utf8')); }
    catch (error) { markerError = error.message; }
  } else markerError = settled ? 'agent task finished before the isolated stage worker marker appeared' : 'stage worker marker timed out';

  const pid = Number(metadata?.pid);
  const parentPid = Number(metadata?.parent_pid);
  const workerAliveBeforeStop = Number.isSafeInteger(pid) && pid > 0 ? processIsRunning(pid) : false;
  const taskProcessAliveBeforeStop = Number.isSafeInteger(parentPid) && parentPid > 0
    ? processIsRunning(parentPid) : false;
  let stopClick = null;
  try {
    stopClick = await window.webContents.executeJavaScript(`(() => {
      const root = document.getElementById('agent-body');
      const button = [...(root?.querySelectorAll('button') || [])]
        .find(candidate => candidate.textContent.trim() === 'Остановить');
      if (!button || button.disabled) return { clicked: false, reason: 'creation UI stop button unavailable' };
      button.click();
      return { clicked: true, label: button.textContent.trim() };
    })()`);
  } catch (error) { stopClick = { clicked: false, reason: error.message }; }

  // Cleanup fallback is not accepted as proof of cancellation through the UI.
  let bridgeStop = null;
  if (!stopClick?.clicked) {
    try { bridgeStop = await window.webContents.executeJavaScript('window.zsmm.stopTask()'); }
    catch (error) { bridgeStop = { ok: false, error: error.message }; }
  }
  const taskOutcome = await new Promise((resolve) => {
    const timer = setTimeout(() => resolve({ error: 'task completion timed out after stop request' }), 30000);
    taskPromise.then((value) => { clearTimeout(timer); resolve(value); });
  });
  const run = taskOutcome.run || null;
  let workerAlive = null;
  let taskProcessAlive = null;
  let lockProbe = null;
  if (Number.isSafeInteger(pid) && pid > 0) workerAlive = processIsRunning(pid);
  if (Number.isSafeInteger(parentPid) && parentPid > 0) taskProcessAlive = processIsRunning(parentPid);
  if (fs.existsSync(lockPath)) {
    const code = [
      'import os, sys',
      "f = open(sys.argv[1], 'r+b'); f.seek(0)",
      'if os.name == "nt":',
      ' import msvcrt; msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)',
      'else:',
      ' import fcntl; fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)',
      'f.close()',
    ].join('\n');
    const probe = spawnSync(python, ['-I', '-B', '-c', code, lockPath],
      { encoding: 'utf8', timeout: 10000, windowsHide: true });
    lockProbe = { ok: probe.status === 0, status: probe.status, error: probe.error?.message || null,
      stderr: (probe.stderr || '').slice(-1000) };
  } else lockProbe = { ok: false, status: null, error: 'worker lock file missing', stderr: '' };

  const result = {
    scenario: 'installed creation UI stop button → agent-hit IPC/shared task runner → bundled Python → SequentialAIRunner isolated stage worker',
    ok: false,
    markerObserved: Boolean(metadata),
    markerError,
    workerKind: 'test-only blocking stage function; model=None; no model loading or inference',
    workerPid: Number.isSafeInteger(pid) ? pid : null,
    taskProcessPid: Number.isSafeInteger(parentPid) ? parentPid : null,
    workerAliveBeforeStop,
    taskProcessAliveBeforeStop,
    stopButtonClicked: stopClick?.clicked === true,
    stopClickError: stopClick?.reason || null,
    bridgeStopCleanup: bridgeStop,
    taskDone: Boolean(run?.done),
    taskOk: run?.done?.ok === true,
    canceled: run?.done?.canceled === true,
    termination: run?.done?.termination || null,
    cancelEventObserved: Boolean(run?.events?.some((event) => event?.type === 'stopping' && event.reason === 'canceled')),
    exitEventObserved: Boolean(run?.events?.some((event) => event?.type === 'exit')),
    workerAliveAfterStop: workerAlive,
    taskProcessAliveAfterStop: taskProcessAlive,
    lockProbe,
    startCommand: run?.startCommand || null,
    taskId: run?.taskId || null,
    taskError: run?.done?.error || taskOutcome.error || null,
    taskProtocolError: run?.done?.protocolError || null,
    uiStatus: run?.status || null,
  };
  result.ok = result.markerObserved && result.workerPid !== null && result.taskProcessPid !== null
    && result.workerPid !== result.taskProcessPid && result.workerAliveBeforeStop === true
    && result.taskProcessAliveBeforeStop === true && result.stopButtonClicked
    && result.taskDone && result.canceled && result.termination?.confirmed === true
    && result.cancelEventObserved && result.exitEventObserved
    && result.workerAliveAfterStop === false && result.taskProcessAliveAfterStop === false
    && result.lockProbe?.ok === true
    && Array.isArray(result.startCommand) && result.startCommand.includes('--agent-hit');
  return result;
}

module.exports = { runInstalledWorkerCancellation };
