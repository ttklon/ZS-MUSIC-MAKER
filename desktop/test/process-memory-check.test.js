'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { memorySample, startProcessMemory } = require('../electron/process-memory-check');
const rows = () => [{ pid: 1, type: 'Browser', memory: { workingSetSize: 100 } },
  { pid: 2, type: 'Tab', memory: { workingSetSize: 200 } },
  { pid: 3, type: 'GPU', memory: { workingSetSize: 50 } }];

test('sums current simultaneous working sets in KiB, not lifetime process peaks', () => {
  const value = memorySample(rows());
  assert.equal(value.total_working_set_bytes, 350 * 1024);
  assert.equal(value.processes.length, 3);
  assert.equal(JSON.stringify(value).includes('pid'), false);
  for (const data of [[], rows().slice(0, 1), [...rows(), rows()[0]],
    [{ pid: 1, type: 'Browser', memory: { workingSetSize: NaN } }]]) {
    assert.throws(() => memorySample(data));
  }
});

test('captures baseline and peak and clears sampler after success', async () => {
  let calls = 0;
  const sampler = startProcessMemory({ getAppMetrics() {
    const data = rows(); data[0].memory.workingSetSize += calls++ === 1 ? 100 : 0; return data;
  } }, 5);
  await new Promise(resolve => setTimeout(resolve, 25));
  const result = sampler.stop();
  assert.ok(result.samples >= 3);
  assert.equal(result.baseline.total_working_set_bytes, 350 * 1024);
  assert.equal(result.peak.total_working_set_bytes, 450 * 1024);
  assert.equal(result.peak_minus_baseline_bytes, 100 * 1024);
  assert.match(result.scope, /not_unique_ram_or_vram/);
  assert.throws(() => sampler.stop());
});

test('unavailable process metrics fail closed instead of claiming zero memory', () => {
  const sampler = startProcessMemory({ getAppMetrics() { throw new Error('unavailable'); } });
  assert.throws(() => sampler.stop(), /unavailable/);
});
