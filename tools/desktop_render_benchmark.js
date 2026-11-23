'use strict';
/** Real production DSP worker, not model inference or an Electron GUI test. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { performance } = require('node:perf_hooks');
const { renderInWorker, createCancelSignal } = require('../desktop/electron/render-host');
const { parseWavHeader } = require('../desktop/src/core/audio/wav-decode');
const ROOT = path.resolve(__dirname, '..');

function inspectAudio(wav, seconds) {
  const h = parseWavHeader(wav);
  if (h.format !== 1 || h.bits !== 16 || h.channels !== 2 || h.sampleRate !== 44100) {
    throw new Error('Expected stereo PCM16 at 44100 Hz');
  }
  const expectedBytes = Math.trunc(seconds * h.sampleRate) * 4;
  if (h.dataSize !== expectedBytes || wav.length !== h.dataOffset + expectedBytes
      || wav.readUInt32LE(4) + 8 !== wav.length
      || wav.readUInt32LE(h.dataOffset - 4) !== expectedBytes) {
    throw new Error('Truncated or wrong duration WAV');
  }
  let peak = 0; let sum = 0;
  for (let i = h.dataOffset; i < wav.length; i += 2) {
    const value = wav.readInt16LE(i) / 32768;
    peak = Math.max(peak, Math.abs(value)); sum += value * value;
  }
  const rms = Math.sqrt(sum / (expectedBytes / 2));
  if (peak < 0.01 || rms < 0.001 || peak > 0.98) throw new Error('Silent or clipped WAV');
  return { seconds, channels: h.channels, sample_rate: h.sampleRate, bits: h.bits, peak, rms,
    bytes: wav.length, sha256: crypto.createHash('sha256').update(wav).digest('hex') };
}

function optionsFor(seconds) {
  if (!Number.isInteger(seconds) || seconds < 2 || seconds > 120) throw new Error('Duration must be integer 2..120');
  return { bpm: 140, genre: 'phonk', key: 'A minor', seed: 7, durationSec: seconds,
    useBank: false, vocal: { mode: 'none' } };
}

async function benchmark(seconds, directory) {
  const options = optionsFor(seconds);
  fs.mkdirSync(directory, { recursive: true });
  const report = { schema: 1, ok: false, kind: 'real_desktop_dsp_instrumental_not_neural', options,
    platform: process.platform, arch: process.arch, node: process.version, source: process.env.GITHUB_SHA || null,
    hardware: { cpu: os.cpus()[0]?.model, logical_cpus: os.cpus().length,
      available_parallelism: os.availableParallelism(), total_ram_bytes: os.totalmem(), free_ram_before_bytes: os.freemem() },
    product_profile_accepted: false, network_verified: false };
  try {
    const signal = createCancelSignal();
    const canceled = await renderInWorker({ options, rootDir: ROOT, signal,
      onProgress: () => signal.abort(), timeoutMs: 120000 });
    if (canceled.cancelled !== true || canceled.ok !== false) throw new Error('Real worker cancellation failed');
    report.cancel_on_progress_verified = true;
    const start = performance.now();
    const result = await renderInWorker({ options, rootDir: ROOT, timeoutMs: 600000 });
    report.wall_seconds = (performance.now() - start) / 1000;
    if (result.ok !== true || result.renderer !== 'worker') throw new Error(result.error || 'No real worker result');
    const wav = Buffer.from(result.data.wavBase64, 'base64');
    report.audio = inspectAudio(wav, seconds);
    report.real_time_factor = report.wall_seconds / seconds;
    report.engine_report = result.data.report;
    fs.writeFileSync(path.join(directory, 'instrumental.wav'), wav);
    report.ok = true;
  } catch (error) { report.error = error.stack; }
  report.process_lifetime_max_rss_bytes = process.resourceUsage().maxRSS * 1024;
  report.memory_scope = 'process lifetime including worker threads, cancellation and validation; not per-render GPU memory';
  fs.writeFileSync(path.join(directory, 'report.json'), JSON.stringify(report, null, 2));
  return report;
}

function summaryFor(report) {
  const { engine_report, ...summary } = report;
  summary.engine = engine_report ? { drum_engine: engine_report.drum_engine,
    samples_used: engine_report.samples_used, vocal: engine_report.vocal,
    duration_sec: engine_report.duration_sec } : null;
  return summary;
}

if (require.main === module) {
  benchmark(Number(process.argv[2] || 20), path.resolve(process.argv[3] || 'output/desktop-render-benchmark'))
    .then(report => {
      console.log('::notice title=Real desktop DSP benchmark::' + JSON.stringify(summaryFor(report)));
      process.exitCode = report.ok ? 0 : 1;
    }).catch(error => { console.error(error); process.exitCode = 1; });
}
module.exports = { inspectAudio, optionsFor, benchmark, summaryFor };
