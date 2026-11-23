'use strict';
/** Local bounded error log. No network transfer, task stdout, or settings dump. */
const fs = require('node:fs');
const path = require('node:path');
const { redact, validTaskId } = require('./diagnostic-redaction');
const LIMIT = 1024 * 1024;
function createDiagnostics(dir) {
  const file = path.join(dir, 'startup-errors.jsonl');
  function record(source, error, taskId = null) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      if (fs.existsSync(file) && fs.lstatSync(file).isSymbolicLink()) return;
      if (fs.existsSync(file) && fs.statSync(file).size >= LIMIT) {
        fs.rmSync(file + '.previous', { force: true }); fs.renameSync(file, file + '.previous');
      }
      const message = redact(error?.stack || error?.message || error || 'Unknown error');
      fs.appendFileSync(file, JSON.stringify({ time: new Date().toISOString(), source: redact(source).slice(0, 80), taskId: validTaskId(taskId), message }) + '\n');
    } catch { /* diagnostics must never prevent the application from starting */ }
  }
  function task(taskId, key, event) {
    if (event.type === 'protocol' && event.event?.type === 'error') {
      record('python', event.event.message, taskId); return;
    }
    if (event.type === 'error' || event.type === 'protocol-error') record('python-launch', event.error, taskId);
    if (!['start', 'stopping', 'timeout', 'exit', 'error', 'protocol-error', 'cleanup-failed'].includes(event.type) && !('ok' in event)) return;
    // No argv, prompt, stdout, stderr, settings, media or raw report.
    record('task', JSON.stringify({ key, type: event.type || 'done', ok: event.ok,
      code: event.code, canceled: event.canceled, timedOut: event.timedOut,
      cleanupConfirmed: event.termination?.confirmed }), taskId);
  }
  return { file, record, task };
}
function exportDiagnostics(diagnostics) {
  const text = [diagnostics.file + '.previous', diagnostics.file]
    .filter(f => fs.existsSync(f) && !fs.lstatSync(f).isSymbolicLink())
    .map(f => fs.readFileSync(f, 'utf8').slice(-1100000)).join('\n');
  return require('./diagnostic-export').safeExport(text);
}
function registerDiagnostics({ ipcMain, diagnostics, dialog }) {
  ipcMain.handle('zsmm:report-error', (_event, message) => {
    const text = typeof message === 'string' ? message : message?.message;
    if (typeof text !== 'string') return { ok: false };
    diagnostics.record('renderer', text, message?.taskId); return { ok: true };
  });
  ipcMain.handle('zsmm:export-errors', async () => {
    try {
      const choice = await dialog.showSaveDialog({ title: 'Сохранить коды диагностики (без текстов ошибок и путей)', defaultPath: 'ZS-Music-Maker-diagnostics.json' });
      if (choice.canceled || !choice.filePath) return { ok: true, canceled: true };
      fs.writeFileSync(choice.filePath, JSON.stringify(exportDiagnostics(diagnostics), null, 2));
      return { ok: true };
    } catch (err) { return { ok: false, error: err.message }; }
  });
}
module.exports = { createDiagnostics, registerDiagnostics, exportDiagnostics };
