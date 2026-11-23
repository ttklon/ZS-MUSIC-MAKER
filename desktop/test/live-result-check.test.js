'use strict';
// Fixtures test boundary logic only; real packaged render evidence comes from Windows CI.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const { encodeWav } = require('../src/core/audio/wav');
const { isCompleteResult } = require('../src/core/creation-state');
const { readInstrumentalProbe, checkLiveInstrumental } = require('../electron/live-result-check');

function fixture(directory) {
  const audio = path.join(directory, 'fixture.wav');
  const wav = encodeWav([new Float32Array(1600).fill(0.1), new Float32Array(1600).fill(0.1)], 8000);
  fs.writeFileSync(audio, wav);
  const sha256 = crypto.createHash('sha256').update(wav).digest('hex');
  const result = { schema: 1, status: 'success', succeeded: true, reasons: [], kind: 'instrumental',
    requested_kind: 'instrumental', quality_accepted: false,
    artifact: { path: audio, valid: true, bytes: wav.length, sha256 } };
  const probe = { source: 'a'.repeat(40), ok: true, typed_result: result,
    adapter_outcome: { status: 'success', succeeded: true }, pipeline: { master_path: audio,
      outcome: { status: 'success', succeeded: true }, render_evidence: { kind: 'instrumental', master_sha256: sha256 } } };
  const filename = path.join(directory, 'probe.json');
  fs.writeFileSync(filename, JSON.stringify(probe));
  return { audio, filename, probe, source: probe.source };
}

test('actual bytes are rehashed before passing the envelope to renderer', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-live-'));
  try {
    const { audio, filename, source } = fixture(dir);
    const window = { webContents: { executeJavaScript: async script => vm.runInNewContext(script,
      { window: { ZSMM_CREATION_STATE: { isCompleteResult } } }) } };
    const result = await checkLiveInstrumental(window, filename, source);
    assert.equal(result.ok, true);
    assert.equal(result.checks.length, 6);
    assert.equal(result.quality_accepted, false);
    assert.throws(() => readInstrumentalProbe(filename, 'b'.repeat(40)), /source/);
    const bytes = fs.readFileSync(audio); bytes[bytes.length - 1] ^= 1; fs.writeFileSync(audio, bytes);
    assert.throws(() => readInstrumentalProbe(filename, source), /changed/);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('unbound, failed or mislabelled producer cannot feed the packaged check', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-live-'));
  try {
    const { filename, probe, source } = fixture(dir);
    for (const mutate of [r => { r.ok = false; }, r => { r.typed_result.kind = 'generated_singing'; },
      r => { r.pipeline.render_evidence.master_sha256 = 'b'.repeat(64); },
      r => { r.typed_result.artifact.bytes += 1; }]) {
      const row = JSON.parse(JSON.stringify(probe)); mutate(row); fs.writeFileSync(filename, JSON.stringify(row));
      assert.throws(() => readInstrumentalProbe(filename, source));
    }
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});
