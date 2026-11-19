'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const { FakeDocument } = require('./fake-dom');
const source = fs.readFileSync(path.join(__dirname, '../src/sections/creation.js'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
function fixture() {
  const document = new FakeDocument();
  const root = document.createElement('div'); root.id = 'agent-body'; document.append(root);
  let event, done;
  const calls = [];
  const bridge = {
    saveSettings: async patch => { calls.push(['settings', patch]); return { ok: true }; },
    startTask: async key => { calls.push(['task', key]); return { ok: true }; },
    agentHit: async answers => { calls.push(['create', answers]); return { ok: true }; },
    onTaskEvent: fn => { event = fn; return () => {}; }, onTaskDone: fn => { done = fn; return () => {}; },
    stopTask: async () => ({ ok: true }), agentOpen: async () => ({ ok: true }),
  };
  const window = { zsmm: bridge, ZSMM_SECTIONS: {}, ZSMM_UI: {
    $: id => document.getElementById(id),
    el: (tag, cls, text) => { const n = document.createElement(tag); n.textContent = text || ''; n.className = cls || ''; return n; },
  } };
  vm.runInNewContext(source, { window }); window.ZSMM_SECTIONS.initCreation();
  const click = async text => {
    const b = [...root.walk()].find(n => n.tagName === 'BUTTON' && n.textContent === text);
    assert.ok(b, 'button: ' + text); b.dispatch('click'); await flush();
  };
  return { root, bridge, calls, click, document, load: () => window.ZSMM_UI.loadCreation(), event: e => event(e), done: r => done(r) };
}

test('one window connects idea, preparation, generation and partial result', async () => {
  const f = fixture(); await f.load();
  f.document.getElementById('creation-mood').value = 'ночной город';
  f.document.getElementById('creation-mood').dispatch('input');
  await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически');
  assert.equal(f.calls.find(c => c[0] === 'task')[1], 'bootstrap');
  assert.equal(f.calls.find(c => c[1]?.networkOnline !== undefined)[1].networkOnline, false);
  f.done({ ok: true });
  await f.click('Создать трек');
  assert.equal(f.calls.find(c => c[0] === 'create')[1].mood, 'ночной город');
  f.event({ line: JSON.stringify({ master_path: '/music/draft.wav', verdict: 'PARTIAL', blocked: [{ stage: 'voice', reason: 'нет вокала' }] }) });
  f.done({ ok: true });
  assert.match(f.root.textContent, /неполный результат/);
  assert.match(f.root.textContent, /нет вокала/);
  await f.load();
  assert.match(f.root.textContent, /draft.wav/, 'refresh preserves the session');
});

test('failed preparation stays on preparation with retry and visible cause', async () => {
  const f = fixture(); await f.load(); await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически');
  f.event({ line: 'BLOCKED torch: network disabled' }); f.done({ ok: false });
  assert.match(f.root.textContent, /network disabled/);
  assert.doesNotMatch(f.root.textContent, /3\. Создадим трек/);
  await f.click('Проверить и подготовить автоматически');
  assert.equal(f.calls.filter(c => c[0] === 'task').length, 2);
});

test('launch error is visible without changing to success', async () => {
  const f = fixture(); f.bridge.startTask = async () => ({ ok: false, error: 'Python missing' });
  await f.load(); await f.click('Далее — подготовить студию'); await f.click('Проверить и подготовить автоматически');
  assert.match(f.root.textContent, /Python missing/);
});
