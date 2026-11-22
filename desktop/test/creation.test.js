'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const { FakeDocument } = require('./fake-dom');
const { buildCommand } = require('../electron/tasks');
const source = fs.readFileSync(path.join(__dirname, '../src/sections/creation.js'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
function fixture() {
  const document = new FakeDocument();
  const root = document.createElement('div'); root.id = 'agent-body'; document.append(root);
  for (const id of ['models-body', 'settings-body']) { const node = document.createElement('div'); node.id = id; document.append(node); }
  let event, done;
  const calls = [];
  const bridge = {
    saveSettings: async patch => { calls.push(['settings', patch]); return { ok: true }; },
    startTask: async key => { calls.push(['task', key]); return { ok: true }; },
    agentHit: async answers => { calls.push(['argv', buildCommand('agent-hit', answers)]); calls.push(['create', answers]); return { ok: true }; },
    onTaskEvent: fn => { event = fn; return () => {}; }, onTaskDone: fn => { done = fn; return () => {}; },
    stopTask: async () => ({ ok: true }), agentOpen: async () => ({ ok: true }),
  };
  const window = { zsmm: bridge, ZSMM_SECTIONS: {}, ZSMM_UI: {
    state: { view: 'agent' },
    $: id => document.getElementById(id),
    el: (tag, cls, text) => { const n = document.createElement(tag); n.textContent = text || ''; n.className = cls || ''; return n; },
  } };
  const urls = { created: 0, revoked: 0 };
  vm.runInNewContext(source, { window, atob, Blob, Uint8Array, URL: {
    createObjectURL: () => 'blob:test-' + (++urls.created),
    revokeObjectURL: () => { urls.revoked++; },
  } }); window.ZSMM_SECTIONS.initCreation();
  const click = async text => {
    const b = [...root.walk()].find(n => n.tagName === 'BUTTON' && n.textContent === text);
    assert.ok(b, 'button: ' + text); b.dispatch('click'); await flush();
  };
  return { root, bridge, calls, click, document, urls, ui: window.ZSMM_UI, load: () => window.ZSMM_UI.loadCreation(), event: e => event(e), done: r => done(r) };
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
  assert.deepEqual(f.calls.find(c => c[0] === 'argv')[1], ['--agent-hit', '--agent-mood', 'ночной город']);
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


test('inline player releases its URL when result is left', async () => {
  const f = fixture();
  f.bridge.agentAudio = async () => ({ ok: true, data: { base64: 'UklGRg==' } });
  await f.load(); await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически'); f.done({ ok: true });
  await f.click('Создать трек');
  f.event({ line: JSON.stringify({ master_path: '/music/master.wav', verdict: 'PARTIAL' }) }); f.done({ ok: true });
  await f.click('Загрузить для прослушивания здесь');
  assert.equal(f.urls.created, 1);
  assert.ok([...f.root.walk()].some(n => n.tagName === 'AUDIO' && n.controls));
  await f.click('Изменить пожелания и создать заново');
  assert.equal(f.urls.revoked, 1);
});


test('models screen exposes live log, errors and retry without hidden details', async () => {
  const f = fixture(); await f.load(); f.ui.state.view = 'models';
  f.ui.loadModelsScreen();
  const host = f.document.getElementById('models-body');
  const start = [...host.walk()].find(n => n.textContent === 'Проверить и подготовить автоматически' && n.tagName === 'BUTTON');
  start.dispatch('click'); await flush();
  assert.match(host.textContent, /Подготовка выполняется/);
  f.event({ line: 'Downloading weights: C:\\models\\voice.pt' });
  assert.match(host.textContent, /voice.pt/);
  f.done({ ok: false });
  assert.match(host.textContent, /Операция не завершена/);
  assert.ok([...host.walk()].some(n => n.tagName === 'BUTTON' && n.textContent === 'Проверить и подготовить автоматически' && !n.disabled));
});

test('settings persist network consent and show actual environment paths', async () => {
  const f = fixture();
  f.bridge.loadSettings = async () => ({ ok: true, data: { networkOnline: false } });
  f.bridge.environment = async () => ({ ok: true, data: { pipeline_root: 'C:/Users/Test/workspace' } });
  await f.ui.loadStudioSettings();
  const host = f.document.getElementById('settings-body');
  assert.match(host.textContent, /C:\/Users\/Test\/workspace/);
  const box = [...host.walk()].find(n => n.tagName === 'INPUT');
  box.checked = true; box.dispatch('change'); await flush();
  assert.equal(f.calls.at(-1)[1].networkOnline, true);
  assert.match(host.textContent, /Сохранено/);
  f.bridge.saveSettings = async () => ({ ok: false, error: 'disk full' });
  box.checked = false; box.dispatch('change'); await flush();
  assert.equal(box.checked, true);
  assert.match(host.textContent, /disk full/);
});

test('legacy HIT flag cannot label a draft as a complete result', async () => {
  const f = fixture(); await f.load(); await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически'); f.done({ ok: true });
  await f.click('Создать трек');
  f.event({ line: JSON.stringify({ master_path: '/music/draft.wav', verdict: 'HIT', blocked: [],
    result: { schema: 1, status: 'degraded', succeeded: false, label: 'Речевой черновик', reasons: ['Нет пения'] } }) });
  f.done({ ok: false });
  assert.match(f.root.textContent, /неполный результат/);
  assert.match(f.root.textContent, /Нет пения/);
  assert.match(f.root.textContent, /Речевой черновик/);
});
