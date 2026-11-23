'use strict';
/** Actual CPU artifact -> packaged renderer boundary, not singing/quality certification. */
const fs = require('node:fs');
const crypto = require('node:crypto');
const { parseWavHeader } = require('../src/core/audio/wav-decode');

function readInstrumentalProbe(filename, expectedSource) {
  if (fs.statSync(filename).size > 4 * 1024 * 1024) throw new Error('Probe report too large');
  const probe = JSON.parse(fs.readFileSync(filename, 'utf8'));
  if (!/^[a-f0-9]{40}$/.test(expectedSource || '') || probe.source !== expectedSource) {
    throw new Error('Probe source does not match packaged checkout');
  }
  const result = probe.typed_result, pipeline = probe.pipeline;
  if (probe.ok !== true || pipeline?.outcome?.succeeded !== true || probe.adapter_outcome?.succeeded !== true ||
      result?.status !== 'success' || result.kind !== 'instrumental' || result.requested_kind !== 'instrumental' ||
      result.quality_accepted !== false || result.artifact?.valid !== true) throw new Error('Not a verified instrumental probe');
  const artifact = result.artifact, evidence = pipeline.render_evidence;
  if (!artifact.path || artifact.path !== pipeline.master_path || evidence?.kind !== 'instrumental' ||
      evidence.master_sha256 !== artifact.sha256) throw new Error('Unbound master provenance');
  const stat = fs.lstatSync(artifact.path);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 128 * 1024 * 1024 || stat.size !== artifact.bytes) {
    throw new Error('Invalid master file or changed size');
  }
  const wav = fs.readFileSync(artifact.path);
  const hash = crypto.createHash('sha256').update(wav).digest('hex');
  if (hash !== artifact.sha256) throw new Error('Master changed since Python validation');
  const header = parseWavHeader(wav);
  if (header.channels !== 2 || header.sampleRate < 8000 || header.dataSize <= 0) throw new Error('Invalid stereo WAV');
  return { envelope: { ...pipeline, outcome: probe.adapter_outcome, result },
    artifact: { sha256: hash, bytes: stat.size, channels: header.channels, sample_rate: header.sampleRate },
    source: probe.source };
}

async function checkLiveInstrumental(window, filename, expectedSource) {
  const verified = readInstrumentalProbe(filename, expectedSource);
  const checks = await window.webContents.executeJavaScript(`(() => {
    const report = ${JSON.stringify(verified.envelope)};
    const check = window.ZSMM_CREATION_STATE?.isCompleteResult;
    if (typeof check !== 'function') return [{ name: 'boundary-present', ok: false }];
    const clone = () => JSON.parse(JSON.stringify(report));
    const checks = [
      { name: 'real-instrumental-request', ok: check(report, true, 'instrumental') === true },
      { name: 'real-instrumental-not-singing', ok: check(report, true, 'generated_singing') === false },
      { name: 'failed-task-not-success', ok: check(report, false, 'instrumental') === false }
    ];
    for (const [name, mutate] of [
      ['failed-outcome-not-success', r => { r.outcome = { status: 'failed', succeeded: false }; }],
      ['canceled-task-not-success', r => { r.canceled = true; }],
      ['invalid-artifact-not-success', r => { r.result.artifact.valid = false; }]
    ]) { const row = clone(); mutate(row); checks.push({ name, ok: check(row, true, 'instrumental') === false }); }
    return checks;
  })()`);
  return { ok: Array.isArray(checks) && checks.length === 6 && checks.every(row => row.ok === true),
    kind: 'real_cpu_instrumental_renderer_boundary_not_gui_generation',
    source: verified.source, artifact: verified.artifact, quality_accepted: false, checks };
}

module.exports = { readInstrumentalProbe, checkLiveInstrumental };
