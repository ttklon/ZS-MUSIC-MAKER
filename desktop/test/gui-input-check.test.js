'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { verifyInputChecks, guiInputScenario } = require('../electron/gui-input-check');
function fixture() {
  return { progress_events: 0, checks: [['beat-bpm', '0'], ['beat-bpm', '221'], ['beat-bpm', 'not-a-number'],
    ['beat-duration', '1'], ['beat-duration', '601'], ['beat-duration', 'not-a-number']]
    .map(([field, value]) => ({ field, value, ok: true, error_visible: true,
      error: field === 'beat-bpm' ? 'BPM должен быть числом от 40 до 220' : 'длительность должна быть от 2 до 600 секунд' })) };
}
test('requires every invalid-input case and visible meaningful error', () => {
  assert.equal(verifyInputChecks(fixture()).ok, true);
  for (const mutate of [r => { r.progress_events = 1; }, r => { r.checks.pop(); },
    r => { r.checks[0].ok = false; }, r => { r.checks[0].error_visible = false; },
    r => { r.checks[0].error = ''; }, r => { r.checks[0].value = '140'; }]) {
    const row = fixture(); mutate(row); assert.throws(() => verifyInputChecks(row));
  }
});
test('scenario uses DOM click and preserves audio/report/blob references', () => {
  const source = guiInputScenario.toString();
  assert.match(source, /get\('beat-render'\)\.click\(\)/);
  assert.match(source, /state.beat === original.audio/);
  assert.match(source, /state.beatReport === original.report/);
  assert.doesNotMatch(source, /zsmm\.renderBeat\s*=/);
});
