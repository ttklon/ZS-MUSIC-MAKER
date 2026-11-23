'use strict';
/** Real packaged renderer probe, distinct from the headless data smoke check. */
const fs = require('node:fs');
const path = require('node:path');
const { checkGuiInputs } = require('./gui-input-check');
const { checkGuiBeat } = require('./gui-beat-check');
const { verifyProductHelp } = require('./product-help-check');
const { checkResultContract } = require('./result-contract-check');
const { checkLiveInstrumental } = require('./live-result-check');
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
  const timer = setTimeout(() => finish({ ok: false, error: 'Renderer check timed out' }),
    process.env.ZSMM_GUI_BEAT_CHECK === '1' ? 180000 : 30000);
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
      if (report.ok) {
        report.navigation = await window.webContents.executeJavaScript(`(async () => {
          const results = [];
          const guide = document.getElementById('creation-next-action');
          const guideLink = guide?.querySelector('button');
          guideLink?.click();
          results.push({ view: 'journey-guide', ok: !!guideLink && window.ZSMM_UI.state.view === 'settings' });
          for (const view of ['models', 'settings', 'help', 'agent']) {
            document.querySelector('[data-view="' + view + '"]').click();
            const deadline = Date.now() + 5000;
            while (!window.ZSMM_UI.state.loaded.has(view) && Date.now() < deadline)
              await new Promise(r => setTimeout(r, 50));
            const section = document.getElementById('view-' + view);
            results.push({ view, ...(view === 'help' ? { product: { contract: window.ZSMM_PRODUCT,
              intro: document.getElementById('product-contract')?.textContent,
              scenarios: document.getElementById('product-scenarios')?.textContent } } : {}), ok: !section.classList.contains('is-hidden') &&
              window.ZSMM_UI.state.loaded.has(view) && section.textContent.trim().length > 20 &&
              (view !== 'help' || document.getElementById('product-contract')?.getAttribute('data-product-id') === 'zsmm-windows-studio') });
          }
          return results;
        })()`);
        report.productHelpVerified = verifyProductHelp(report.navigation.find(r => r.view === 'help')?.product);
        report.ok = report.productHelpVerified && report.navigation.every(r => r.ok);
      }
      if (report.ok) {
        report.resultContract = await checkResultContract(window);
        report.resultContractVerified = report.resultContract?.ok === true;
      }
      if (report.ok && report.resultContractVerified && process.env.ZSMM_LIVE_PROBE) {
        report.liveInstrumental = await checkLiveInstrumental(window, process.env.ZSMM_LIVE_PROBE, process.env.GITHUB_SHA);
        report.ok = report.liveInstrumental.ok === true;
      }
      if (report.ok && report.resultContractVerified && process.env.ZSMM_GUI_BEAT_CHECK === '1') {
        report.guiBeat = await checkGuiBeat(window, path.dirname(process.env.ZSMM_WINDOW_CHECK_OUT), app);
        report.guiInputs = await checkGuiInputs(window);
        report.ok = report.guiBeat.ok === true && report.guiInputs.ok === true;
      }
      finish({ ...report, ok: report.ok && report.resultContractVerified && report.creationVisible && errors.length === 0 });
    } catch (error) { finish({ ok: false, error: String(error) }); }
  });
}
module.exports = { checkWindow };
