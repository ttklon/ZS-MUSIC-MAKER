'use strict';
/** Export is an allowlist projection, not a regex promise about arbitrary prose. */
const SOURCES = new Set(['task', 'python', 'python-launch', 'renderer', 'startup', 'preload', 'load']);
const EVENTS = new Set(['start', 'stopping', 'timeout', 'exit', 'error', 'protocol-error', 'cleanup-failed', 'done']);
function safeExport(text) {
  const entries = [], ids = new Map();
  for (const line of String(text).split('\n').slice(-5000)) {
    if (line.length > 16384) continue;
    let record;
    try { record = JSON.parse(line); } catch { continue; }
    if (!record || !SOURCES.has(record.source)) continue;
    let task = null;
    if (typeof record.taskId === 'string' && record.taskId.length <= 80) {
      if (!ids.has(record.taskId)) ids.set(record.taskId, ids.size + 1);
      task = ids.get(record.taskId);
    }
    const row = { source: record.source, task };
    if (record.source === 'task') {
      let value;
      try { value = JSON.parse(record.message); } catch { value = {}; }
      if (!value || typeof value !== 'object' || Array.isArray(value)) value = {};
      row.event = EVENTS.has(value.type) ? value.type : 'error';
      for (const key of ['ok', 'canceled', 'timedOut', 'cleanupConfirmed']) if (typeof value[key] === 'boolean') row[key] = value[key];
      if (Number.isSafeInteger(value.code) && Math.abs(value.code) <= 4294967295) row.code = value.code;
    }
    entries.push(row);
  }
  return { schema: 2, privacy: 'structured-only-no-free-text', entries };
}
module.exports = { safeExport };
