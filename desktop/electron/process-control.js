'use strict';
const { spawn } = require('node:child_process');
const path = require('node:path');
/** Isolated process groups on POSIX; Windows taskkill /T /F includes pip/workers.
 * Acknowledging a request is NOT completion. Caller waits for close and this result.
 */
function terminateTree(pid, platform = process.platform) {
  if (!Number.isSafeInteger(pid) || pid <= 0) return Promise.resolve({ confirmed: false, error: 'No child PID' });
  if (platform !== 'win32') {
    try { process.kill(-pid, 'SIGKILL'); return Promise.resolve({ confirmed: true, method: 'process-group-SIGKILL' }); }
    catch (e) { return Promise.resolve({ confirmed: e.code === 'ESRCH', error: e.code === 'ESRCH' ? null : e.message }); }
  }
  return new Promise(resolve => {
    const killer = spawn(path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'taskkill.exe'), ['/PID', String(pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    let settled = false;
    const finish = result => { if (!settled) { settled = true; clearTimeout(timer); resolve(result); } };
    const timer = setTimeout(() => { killer.kill(); finish({ confirmed: false, error: 'taskkill timed out' }); }, 15000);
    killer.on('error', e => finish({ confirmed: false, error: e.message }));
    killer.on('close', code => finish({ confirmed: code === 0, method: 'taskkill-/T-/F', code }));
  });
}
function monitorActivity({ onEvent, hardMs, onTimeout, intervalMs = 5000, quietMs = 60000, now = Date.now }) {
  const started = now(); let last = started;
  const heartbeat = setInterval(() => {
    const elapsedMs = now() - started, silenceMs = now() - last;
    onEvent({ type: 'heartbeat', elapsedMs, silenceMs, quiet: silenceMs >= quietMs,
      message: silenceMs >= quietMs ? 'Нет нового вывода. Процесс ещё запущен; это не доказательство зависания.' : 'Процесс запущен; heartbeat не является процентом готовности.' });
  }, intervalMs);
  const hard = setTimeout(onTimeout, hardMs);
  return { touch: () => { last = now(); }, close: () => { clearInterval(heartbeat); clearTimeout(hard); } };
}
module.exports = { terminateTree, monitorActivity };
