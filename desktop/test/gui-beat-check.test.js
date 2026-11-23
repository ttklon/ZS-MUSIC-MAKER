'use strict';
// Small validator fixtures, NOT a DOM/IPC generation run. Windows CI does that.
const test = require('node:test');
const assert = require('node:assert/strict');
const { encodeWav } = require('../src/core/audio/wav');
const { verifyGuiBeat, guiBeatScenario } = require('../electron/gui-beat-check');

function fixture() {
  const samples = new Float32Array(20 * 44100).fill(0.1);
  return { wavBase64: encodeWav([samples, samples], 44100).toString('base64'),
    report: { renderer: 'worker', duration_sec: 20, vocal: null, genre: 'phonk', seed: 7, bpm: 140,
      sections: [{ name: 'fixture' }] },
    cancellation: { clicked: true, progress_count: 1, status: 'Рендер отменён', previous_audio_preserved: true },
    controls: { status: 'Готово', save_enabled: true, open_enabled: true, cancel_disabled: true,
      audio_visible: true, audio_blob: true } };
}

test('GUI validator hashes full WAV and requires real worker metadata', () => {
  const result = verifyGuiBeat(fixture());
  assert.equal(result.audio.seconds, 20);
  assert.equal(result.audio.bytes, 3528044);
  assert.match(result.audio.sha256, /^[a-f0-9]{64}$/);
  for (const mutate of [r => { r.report.renderer = 'main'; }, r => { r.report.vocal = {}; },
    r => { r.cancellation.clicked = false; }, r => { r.cancellation.previous_audio_preserved = false; },
    r => { r.controls.save_enabled = false; }, r => { r.wavBase64 = ''; }]) {
    const row = fixture(); mutate(row); assert.throws(() => verifyGuiBeat(row));
  }
});

test('scenario clicks production controls and never replaces IPC/render functions', () => {
  const source = guiBeatScenario.toString();
  assert.match(source, /get\('beat-render'\)\.click\(\)/);
  assert.match(source, /get\('beat-cancel'\)\.click\(\)/);
  assert.doesNotMatch(source, /zsmm\.renderBeat\s*=/);
  assert.doesNotMatch(source, /renderInWorker\(/);
});
