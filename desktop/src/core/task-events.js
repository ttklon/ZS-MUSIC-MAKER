'use strict';
/** Strict line-level NDJSON contract shared by Electron and renderer. */
(function () {
  function parseEvent(line) {
    if (typeof line !== 'string' || line.length > 1024 * 1024) return null;
    let e;
    try { e = JSON.parse(line); } catch { return null; }
    if (!e || e.schema !== 'zsmm.task' || e.version !== 1 ||
        typeof e.task_id !== 'string' || !e.task_id ||
        !Number.isSafeInteger(e.seq) || e.seq < 1) return null;
    if (e.type === 'progress' || e.type === 'error') return typeof e.message === 'string' ? e : null;
    if (e.type === 'artifact') return typeof e.path === 'string' && typeof e.role === 'string' ? e : null;
    if (e.type === 'done') return typeof e.ok === 'boolean' && e.report &&
      typeof e.report === 'object' && !Array.isArray(e.report) ? e : null;
    return null;
  }
  const api = { parseEvent };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (typeof window === 'object') window.ZSMM_TASK_EVENTS = api;
})();
