'use strict';
/** Technical result-envelope fixtures in the actual renderer, NOT model inference. */
async function checkResultContract(window) {
  return window.webContents.executeJavaScript(`(() => {
    const check = window.ZSMM_CREATION_STATE?.isCompleteResult;
    if (typeof check !== 'function') return { ok: false, error: 'Result boundary missing' };
    const make = () => ({ master_path: '/fixture/singing.wav', blocked: [], result: {
      schema: 1, status: 'success', succeeded: true, kind: 'generated_singing',
      requested_kind: 'generated_singing', reasons: [], quality_accepted: false,
      artifact: { valid: true, path: '/fixture/singing.wav', sha256: 'a'.repeat(64) }
    } });
    const checks = [{ name: 'typed-positive-not-inference', ok: check(make(), true) === true }];
    for (const [name, mutate] of [
      ['speech-not-singing', r => { r.result.kind = 'speech_draft'; }],
      ['instrumental-not-singing', r => { r.result.kind = 'instrumental'; }],
      ['invalid-artifact', r => { r.result.artifact.valid = false; }],
      ['canceled-task', r => { r.canceled = true; }],
      ['failed-outcome', r => { r.outcome = { status: 'failed', succeeded: false }; }]
    ]) { const report = make(); mutate(report); checks.push({ name, ok: check(report, true) === false }); }
    checks.push({ name: 'nonzero-exit-not-success', ok: check(make(), false) === false });
    return { ok: checks.every(row => row.ok), kind: 'typed-fixtures-not-generation', checks };
  })()`);
}
module.exports = { checkResultContract };
