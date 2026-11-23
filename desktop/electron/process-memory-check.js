'use strict';
/** Electron app metrics: sampled sum of working sets, not unique physical RAM/VRAM. */
function memorySample(metrics) {
  if (!Array.isArray(metrics) || !metrics.length) throw new Error('No Electron process metrics');
  const seen = new Set();
  const processes = metrics.map(row => {
    const kb = row.memory?.workingSetSize;
    if (!Number.isSafeInteger(row.pid) || row.pid <= 0 || seen.has(row.pid) ||
        typeof row.type !== 'string' || !row.type || !Number.isFinite(kb) || kb < 0) {
      throw new Error('Invalid Electron working set metric');
    }
    seen.add(row.pid);
    return { type: row.type, working_set_bytes: kb * 1024 };
  });
  if (!processes.some(row => row.type === 'Browser') || !processes.some(row => row.type === 'Tab')) {
    throw new Error('Electron metrics omit Browser or renderer');
  }
  const total = processes.reduce((sum, row) => sum + row.working_set_bytes, 0);
  if (!Number.isSafeInteger(total) || total <= 0) throw new Error('Invalid Electron total working set');
  return { total_working_set_bytes: total, processes };
}

function startProcessMemory(app, intervalMs = 50) {
  let baseline, peak, samples = 0, error = null, stopped = false;
  const start = performance.now();
  function capture() {
    try {
      const sample = memorySample(app.getAppMetrics());
      samples += 1;
      if (!baseline) baseline = sample;
      if (!peak || sample.total_working_set_bytes > peak.total_working_set_bytes) peak = sample;
    } catch (err) { error = String(err); }
  }
  capture();
  const timer = setInterval(capture, intervalMs);
  return { stop() {
    if (stopped) throw new Error('Memory sampler already stopped');
    stopped = true; clearInterval(timer); capture();
    if (error) throw new Error(error);
    if (samples < 2) throw new Error('Insufficient Electron memory samples');
    return { scope: 'electron_app_metrics_sum_working_sets_including_shared_pages_not_unique_ram_or_vram',
      worker_scope: 'worker_threads share owning process working set; no separate summation',
      interval_ms: intervalMs, samples, elapsed_seconds: (performance.now() - start) / 1000,
      baseline, peak, peak_minus_baseline_bytes: peak.total_working_set_bytes - baseline.total_working_set_bytes };
  } };
}
module.exports = { memorySample, startProcessMemory };
