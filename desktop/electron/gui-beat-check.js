'use strict';
/** Real DOM click -> preload IPC -> production worker. No model/voice certification. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { parseWavHeader } = require('../src/core/audio/wav-decode');

async function guiBeatScenario() {
  const waitFor = async (predicate, ms, label) => {
    const end = Date.now() + ms;
    while (!predicate()) {
      if (Date.now() > end) throw new Error(`GUI beat timeout: ${label}`);
      await new Promise(resolve => setTimeout(resolve, 50));
    }
  };
  const get = id => {
    const element = document.getElementById(id);
    if (!element) throw new Error(`Missing GUI control ${id}`);
    return element;
  };
  document.querySelector('[data-view="beat"]').click();
  await waitFor(() => window.ZSMM_UI.state.loaded.has('beat'), 15000, 'load section');
  for (const [id, value] of Object.entries({ 'beat-genre': 'phonk', 'beat-bpm': '140',
    'beat-seed': '7', 'beat-duration': '120', 'vocal-mode': 'none' })) {
    get(id).value = value; get(id).dispatchEvent(new Event('change', { bubbles: true }));
  }
  get('beat-use-bank').checked = false;
  const before = window.ZSMM_UI.state.beat;
  let progressCount = 0, cancelClicked = false;
  const unsubscribe = window.zsmm.onBeatProgress(() => {
    progressCount += 1;
    if (!cancelClicked && !get('beat-cancel').disabled) {
      cancelClicked = true; get('beat-cancel').click();
    }
  });
  try {
    get('beat-render').click();
    if (!get('beat-render').disabled) throw new Error('GUI did not start cancellation render');
    await waitFor(() => !get('beat-render').disabled, 30000, 'cancel real render');
  } finally { unsubscribe(); }
  const cancellation = { clicked: cancelClicked, progress_count: progressCount,
    status: get('beat-status').textContent, previous_audio_preserved: window.ZSMM_UI.state.beat === before };
  if (!cancelClicked || !cancellation.previous_audio_preserved || !cancellation.status.includes('отменён')) {
    throw new Error('GUI cancellation did not complete correctly');
  }
  get('beat-duration').value = '20';
  const start = performance.now();
  get('beat-render').click();
  if (!get('beat-render').disabled) throw new Error('GUI did not start positive render');
  await waitFor(() => !get('beat-render').disabled, 90000, 'render retry');
  const state = window.ZSMM_UI.state;
  return { wavBase64: state.beat, report: state.beatReport, cancellation,
    render_wall_seconds: (performance.now() - start) / 1000,
    controls: { status: get('beat-status').textContent, save_enabled: !get('beat-save').disabled,
      open_enabled: !get('beat-open').disabled, cancel_disabled: get('beat-cancel').disabled,
      audio_visible: !get('beat-audio').classList.contains('is-hidden'),
      audio_blob: get('beat-audio').src.startsWith('blob:') } };
}

function verifyGuiBeat(result) {
  const report = result?.report, c = result?.controls, canceled = result?.cancellation;
  if (report?.renderer !== 'worker' || report.duration_sec !== 20 || report.vocal !== null ||
      report.genre !== 'phonk' || report.seed !== 7 || report.bpm !== 140 ||
      !Array.isArray(report.sections) || !report.sections.length) throw new Error('Unexpected GUI worker result');
  if (!c?.save_enabled || !c.open_enabled || !c.cancel_disabled || !c.audio_visible || !c.audio_blob ||
      !c.status.includes('Готово') || !canceled?.clicked || canceled.progress_count < 1 ||
      canceled.previous_audio_preserved !== true || !canceled.status.includes('отменён')) {
    throw new Error('GUI result controls/cancellation failed');
  }
  if (typeof result.wavBase64 !== 'string' || result.wavBase64.length > 8 * 1024 * 1024) throw new Error('Invalid GUI audio size');
  const wav = Buffer.from(result.wavBase64, 'base64'), h = parseWavHeader(wav);
  if (h.format !== 1 || h.bits !== 16 || h.channels !== 2 || h.sampleRate !== 44100 ||
      h.dataSize !== 20 * 44100 * 4 || wav.length !== h.dataOffset + h.dataSize ||
      wav.readUInt32LE(4) + 8 !== wav.length) throw new Error('Wrong GUI WAV format or duration');
  let peak = 0, sum = 0;
  for (let i = h.dataOffset; i < wav.length; i += 2) {
    const sample = wav.readInt16LE(i) / 32768;
    peak = Math.max(peak, Math.abs(sample)); sum += sample * sample;
  }
  const rms = Math.sqrt(sum / (h.dataSize / 2));
  if (peak < 0.01 || peak > 0.98 || rms < 0.001) throw new Error('Silent or clipped GUI WAV');
  return { wav, audio: { seconds: 20, channels: 2, sample_rate: 44100, bits: 16, peak, rms,
    bytes: wav.length, sha256: crypto.createHash('sha256').update(wav).digest('hex') } };
}

async function checkGuiBeat(window, outputDirectory) {
  const start = Date.now();
  const result = await window.webContents.executeJavaScript(`(${guiBeatScenario.toString()})()`);
  const { wav, audio } = verifyGuiBeat(result);
  fs.writeFileSync(path.join(outputDirectory, 'gui-click-instrumental.wav'), wav, { flag: 'wx' });
  return { ok: true, kind: 'real_packaged_dom_ipc_worker_instrumental_not_singing',
    source: process.env.GITHUB_SHA || null, audio, cancellation: result.cancellation,
    controls: result.controls, renderer: result.report.renderer,
    render_wall_seconds: result.render_wall_seconds, gui_end_to_end_seconds: (Date.now() - start) / 1000,
    quality_accepted: false, product_profile_accepted: false };
}

module.exports = { guiBeatScenario, verifyGuiBeat, checkGuiBeat };
