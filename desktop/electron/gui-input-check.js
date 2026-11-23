'use strict';
/** Production DOM validation after a real render; no replacement of IPC or controls. */
async function guiInputScenario() {
  const get = id => document.getElementById(id);
  const state = window.ZSMM_UI.state;
  if (!state.beat || !state.beatReport) throw new Error('Input check requires completed real render');
  const original = { audio: state.beat, report: state.beatReport, url: state.beatUrl,
    status: get('beat-status').textContent };
  const cases = [['beat-bpm', '0'], ['beat-bpm', '221'], ['beat-bpm', 'not-a-number'],
    ['beat-duration', '1'], ['beat-duration', '601'], ['beat-duration', 'not-a-number']];
  let progress = 0;
  const unsubscribe = window.zsmm.onBeatProgress(() => { progress += 1; });
  const checks = [];
  try {
    for (const [id, value] of cases) {
      const input = get(id), saved = input.value, before = progress;
      input.value = value;
      try {
        get('beat-render').click();
        const immediatelyIdle = !get('beat-render').disabled && get('beat-cancel').disabled;
        await new Promise(resolve => setTimeout(resolve, 250));
        const error = get('error-text').textContent;
        const errorVisible = !get('error-banner').classList.contains('is-hidden');
        checks.push({ field: id, value, error_visible: errorVisible, error, ok: errorVisible &&
          error.includes(id === 'beat-bpm' ? 'BPM' : 'длительность') && immediatelyIdle && !get('beat-render').disabled &&
          get('beat-cancel').disabled && progress === before && state.beat === original.audio &&
          state.beatReport === original.report && state.beatUrl === original.url &&
          get('beat-status').textContent === original.status && !get('beat-save').disabled &&
          !get('beat-open').disabled && get('beat-audio').src === original.url });
      } finally { input.value = saved; }
    }
  } finally { unsubscribe(); }
  return { checks, progress_events: progress };
}

function verifyInputChecks(result) {
  const expected = [['beat-bpm', '0'], ['beat-bpm', '221'], ['beat-bpm', 'not-a-number'],
    ['beat-duration', '1'], ['beat-duration', '601'], ['beat-duration', 'not-a-number']];
  if (result?.progress_events !== 0 || !Array.isArray(result.checks) || result.checks.length !== expected.length ||
      !expected.every(([field, value], i) => result.checks[i]?.field === field &&
        result.checks[i].value === value && result.checks[i].ok === true &&
        result.checks[i].error_visible === true && typeof result.checks[i].error === 'string' &&
        result.checks[i].error.includes(field === 'beat-bpm' ? 'BPM' : 'длительность'))) {
    throw new Error('GUI invalid input did not preserve completed result');
  }
  return { ok: true, kind: 'real_dom_invalid_input_preserves_completed_audio',
    observation_ms_per_case: 250, ...result };
}

async function checkGuiInputs(window) {
  return verifyInputChecks(await window.webContents.executeJavaScript(`(${guiInputScenario.toString()})()`));
}
module.exports = { guiInputScenario, verifyInputChecks, checkGuiInputs };
