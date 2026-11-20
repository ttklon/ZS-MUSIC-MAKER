'use strict';
/** Real packaged renderer probe, distinct from the headless data smoke check. */
const fs = require('node:fs');
function checkWindow(window, app) {
  if (!process.argv.includes('--window-check')) return;
  let finished = false;
  const errors = [];
  function finish(report) {
    if (finished) return;
    finished = true; clearTimeout(timer);
    const result = { ...report, errors };
    try { fs.writeFileSync(process.env.ZSMM_WINDOW_CHECK_OUT, JSON.stringify(result, null, 2)); }
    catch { app.exit(1); return; }
    app.exit(result.ok ? 0 : 1);
  }
  const timer = setTimeout(() => finish({ ok: false, error: 'Renderer startup timed out' }), 30000);
  window.webContents.on('preload-error', (_event, _file, error) => errors.push(String(error)));
  window.webContents.on('did-finish-load', async () => {
    try {
      const report = await window.webContents.executeJavaScript(`new Promise(resolve => {
        const deadline = Date.now() + 15000;
        const check = () => {
          if ((window.ZSMM_UI?.ready && window.ZSMM_UI.state.loaded.has('agent')) || Date.now() > deadline) {
            const error = document.getElementById('error-text')?.textContent || '';
            resolve({ ok: !!window.zsmm && !!window.ZSMM_UI?.ready && !!window.ZSMM_UI.state.loaded.has('agent') && !error,
              bridge: !!window.zsmm, title: document.getElementById('view-title')?.textContent,
              creationVisible: !document.getElementById('view-agent')?.classList.contains('is-hidden'), error });
          } else setTimeout(check, 50);
        }; check();
      })`);
      finish({ ...report, ok: report.ok && report.creationVisible && errors.length === 0 });
    } catch (error) { finish({ ok: false, error: String(error) }); }
  });
}
module.exports = { checkWindow };
