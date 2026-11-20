'use strict';
/** Local bounded error log. No network transfer, task stdout, or settings dump. */
const fs = require('node:fs');
const path = require('node:path');
const LIMIT = 1024 * 1024;
function createDiagnostics(dir) {
  const file = path.join(dir, 'startup-errors.jsonl');
  function record(source, error) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      if (fs.existsSync(file) && fs.statSync(file).size >= LIMIT) {
        fs.rmSync(file + '.previous', { force: true }); fs.renameSync(file, file + '.previous');
      }
      const message = String(error?.stack || error?.message || error || 'Unknown error').slice(0, 4000);
      fs.appendFileSync(file, JSON.stringify({ time: new Date().toISOString(), source: String(source).slice(0, 80), message }) + '\n');
    } catch { /* diagnostics must never prevent the application from starting */ }
  }
  return { file, record };
}
function registerDiagnostics({ ipcMain, diagnostics, dialog }) {
  ipcMain.handle('zsmm:report-error', (_event, message) => {
    if (typeof message !== 'string') return { ok: false };
    diagnostics.record('renderer', message.slice(0, 4000)); return { ok: true };
  });
  ipcMain.handle('zsmm:export-errors', async () => {
    try {
      const choice = await dialog.showSaveDialog({ title: 'Сохранить ошибки запуска (могут содержать локальные пути)', defaultPath: 'ZS-Music-Maker-errors.log' });
      if (choice.canceled || !choice.filePath) return { ok: true, canceled: true };
      const text = [diagnostics.file + '.previous', diagnostics.file]
        .filter(f => fs.existsSync(f)).map(f => fs.readFileSync(f, 'utf8')).join('');
      fs.writeFileSync(choice.filePath, text || 'Ошибки пока не зарегистрированы.\n');
      return { ok: true };
    } catch (err) { return { ok: false, error: err.message }; }
  });
}
module.exports = { createDiagnostics, registerDiagnostics };
