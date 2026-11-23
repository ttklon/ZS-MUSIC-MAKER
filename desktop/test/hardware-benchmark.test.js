'use strict';
// Validation fixtures, not hardware certification. Integration uses the real worker.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { inspectAudio, optionsFor, benchmark, summaryFor } = require('../../tools/desktop_render_benchmark');
const { encodeWav } = require('../src/core/audio/wav');

test('benchmark rejects invalid durations and silent/truncated audio', () => {
  for (const value of [NaN, Infinity, -1, 0, 1, 121, 2.5, '20']) {
    assert.throws(() => optionsFor(value));
  }
  const signal = new Float32Array(88200).fill(0.2);
  const wav = encodeWav([signal, signal], 44100);
  assert.equal(inspectAudio(wav, 2).seconds, 2);
  assert.throws(() => inspectAudio(wav.subarray(0, wav.length - 10), 2));
  assert.throws(() => inspectAudio(wav, 3));
  const corrupt = Buffer.from(wav);
  corrupt.writeUInt32LE(1, 4);
  assert.throws(() => inspectAudio(corrupt, 2));
  signal.fill(0);
  assert.throws(() => inspectAudio(encodeWav([signal, signal], 44100), 2));
});

test('real worker cancellation then instrumental render produces verified WAV', async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-hardware-'));
  try {
    const report = await benchmark(2, directory);
    assert.equal(report.ok, true, report.error);
    assert.equal(report.cancel_on_progress_verified, true);
    assert.equal(report.product_profile_accepted, false);
    assert.ok(report.wall_seconds > 0);
    assert.ok(report.process_lifetime_max_rss_bytes > 0);
    assert.equal(report.audio.sha256.length, 64);
    const summary = summaryFor(report);
    assert.equal(summary.audio.sha256, report.audio.sha256);
    assert.ok(JSON.stringify(summary).length < 3800, 'GitHub annotation must not truncate JSON');
    assert.equal(summary.engine.vocal, null);
    assert.equal(report.audio.bytes, fs.statSync(path.join(directory, 'instrumental.wav')).size);
  } finally { fs.rmSync(directory, { recursive: true, force: true }); }
});
