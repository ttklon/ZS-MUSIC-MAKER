'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const { FakeDocument } = require('./fake-dom');
const ZSMM_AGENT_REPORT = require('../src/core/agent-report');
const ZSMM_TASK_EVENTS = require('../src/core/task-events');
const source = fs.readFileSync(path.join(__dirname, '../src/sections/agent.js'), 'utf8');

function fixture(bridge) {
  const document = new FakeDocument();
  const root = document.createElement('div'); root.id = 'agent-body'; document.append(root);
  const $ = id => document.getElementById(id);
  const el = (tag, cls, text) => {
    const node = document.createElement(tag); node.className = cls || ''; node.textContent = text || ''; return node;
  };
  const window = { zsmm: bridge, ZSMM_AGENT_REPORT, ZSMM_TASK_EVENTS, ZSMM_SECTIONS: {}, ZSMM_UI: { $, el, switchView() {}, showError() {} } };
  vm.runInNewContext(source, { window });
  return { $, root, load: () => window.ZSMM_UI.loadAgent() };
}
const flush = () => new Promise(resolve => setImmediate(resolve));

test('restored preferences reach the editable fields but never restore media', async () => {
  const f = fixture({ loadSettings: async () => ({ ok: true, data: { agentMood: 'ночь', agentArtist: 'Артист' } }) });
  await f.load();
  assert.equal(f.$('agent-mood').value, 'ночь');
  assert.equal(f.$('agent-artist').value, 'Артист');
  assert.equal(f.$('agent-refs').value, '');
  assert.equal(f.$('agent-voice').value, '');
});

test('save is explicit, clear persists empty preferences without erasing current form', async () => {
  const patches = [];
  const f = fixture({ saveSettings: async patch => { patches.push(patch); return { ok: true, data: patch }; } });
  await f.load();
  f.$('agent-mood').value = 'светлый припев'; f.$('agent-artist').value = 'Артист';
  f.$('agent-voice').value = 'private.wav';
  assert.equal(patches.length, 0);
  f.$('agent-remember').dispatch('click'); await flush();
  assert.equal(JSON.stringify(patches[0]), JSON.stringify({ agentMood: 'светлый припев', agentArtist: 'Артист' }));
  f.$('agent-forget').dispatch('click'); await flush();
  assert.equal(patches[1].agentMood, '');
  assert.equal(f.$('agent-mood').value, 'светлый припев');
});

test('late settings response does not overwrite newly entered preference', async () => {
  let resolve;
  const f = fixture({ loadSettings: () => new Promise(r => { resolve = r; }) });
  const loading = f.load();
  f.$('agent-mood').value = 'мой новый выбор';
  resolve({ ok: true, data: { agentMood: 'старый выбор', agentArtist: '' } });
  await loading;
  assert.equal(f.$('agent-mood').value, 'мой новый выбор');
});

test('failed persistence reports an error instead of saved status', async () => {
  const f = fixture({ saveSettings: async () => ({ ok: false, error: 'disk full' }) });
  await f.load();
  f.$('agent-remember').dispatch('click'); await flush();
  assert.match(f.root.textContent, /Не сохранено: disk full/);
});

test('agent UI parses typed preflight completion with the strict task-event parser', async () => {
  const listeners = {};
  const bridge = {
    agentHit: async () => ({ ok: true, data: { command: ['bundled-python', 'main.py'] } }),
    onTaskEvent: callback => { listeners.event = callback; return () => { listeners.event = null; }; },
    onTaskDone: callback => { listeners.done = callback; return () => { listeners.done = null; }; },
  };
  const f = fixture(bridge);
  await f.load();
  f.$('agent-go').dispatch('click');
  await flush();
  listeners.done({ taskId: 'installed-preflight-test', ok: false, report: {
    verdict: 'FAILED', master_path: null,
    result: { status: 'failed', succeeded: false },
    blocked: [{ stage: 'hardware_preflight', reason: 'ram_available_gib is below the safety floor' }],
    hardware_preflight: { status: 'blocked', decision: 'refuse', can_attempt: false,
      selected_backend: 'procedural_dsp', reasons: ['ram_available_gib is below the safety floor'],
      inference_verified: false, product_profile_accepted: false },
  } });

  assert.match(f.$('agent-status').textContent, /Аппаратный preflight: blocked/);
  assert.match(f.$('agent-status').textContent, /backend procedural_dsp/);
  assert.match(f.$('agent-status').textContent, /hardware_preflight: ram_available_gib/);
  assert.match(f.$('agent-status').textContent, /Inference не подтверждён; профиль продукта не принят/);
  assert.doesNotMatch(f.$('agent-status').textContent, /Готовый трек:|Результат принят/);
});
