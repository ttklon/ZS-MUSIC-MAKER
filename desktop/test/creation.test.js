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
  let event, done, activeKey;
  const calls = [];
  const bridge = {
    saveSettings: async patch => { calls.push(['settings', patch]); return { ok: true }; },
    startTask: async key => { activeKey = key; calls.push(['task', key]); return { ok: true, data: { taskId: 'fixture' } }; },
    agentHit: async answers => { activeKey = 'agent-hit'; calls.push(['argv', buildCommand('agent-hit', answers)]); calls.push(['create', answers]); return { ok: true, data: { taskId: 'fixture' } }; },
    onTaskEvent: fn => { event = fn; return () => {}; }, onTaskDone: fn => { done = fn; return () => {}; },
    stopTask: async () => ({ ok: true }), agentOpen: async () => ({ ok: true }),
  };
  const window = { ZSMM_CREATION_STATE: require('../src/core/creation-state'), zsmm: bridge, ZSMM_JOURNEY: require('../src/core/journey'), ZSMM_SECTIONS: {}, ZSMM_UI: {
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
  return { root, bridge, calls, click, document, urls, ui: window.ZSMM_UI, load: () => window.ZSMM_UI.loadCreation(), event: e => event({ taskId: 'fixture', ...e }), done: r => done({ taskId: 'fixture', ...(activeKey === 'bootstrap' ? { report: { setup: { schema: 1, ok: true, inference_verified: false } } } : {}), ...r }) };
}

test('one window connects idea, preparation, generation and partial result', async () => {
  const f = fixture(); await f.load();
  f.document.getElementById('creation-mood').value = 'ночной город';
  f.document.getElementById('creation-mood').dispatch('input');
  f.document.getElementById('creation-artist').value = 'Артист';
  f.document.getElementById('creation-artist').dispatch('input');
  f.document.getElementById('creation-refs').value = 'reference.wav';
  f.document.getElementById('creation-refs').dispatch('input');
  f.document.getElementById('creation-voice').value = 'C:\\Users\\Test\\own.wav';
  f.document.getElementById('creation-voice').dispatch('input');
  await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически');
  assert.equal(f.calls.find(c => c[0] === 'task')[1], 'bootstrap');
  assert.equal(f.calls.find(c => c[1]?.networkOnline !== undefined)[1].networkOnline, false);
  f.done({ ok: true });
  await f.click('Создать трек');
  assert.equal(JSON.stringify(f.calls.find(c => c[0] === 'create')[1]), JSON.stringify({
    mood: 'ночной город', artist: 'Артист', refs: 'reference.wav', voice: 'C:\\Users\\Test\\own.wav',
  }));
  assert.deepEqual(f.calls.find(c => c[0] === 'argv')[1], [
    '--agent-hit', '--agent-mood', 'ночной город', '--agent-refs', 'reference.wav',
    '--agent-voice', 'C:\\Users\\Test\\own.wav', '--agent-artist', 'Артист',
  ]);
  f.event({ type: 'protocol', event: { type: 'done', report: { master_path: '/music/draft.wav', verdict: 'PARTIAL', blocked: [{ stage: 'voice', reason: 'нет вокала' }] } } });
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
  f.event({ type: 'protocol', event: { type: 'done', report: { master_path: '/music/master.wav', verdict: 'PARTIAL' } } }); f.done({ ok: true });
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

test('current creation UI exposes hardware preflight reasons and unverified status', async () => {
  const f = fixture(); await f.load();
  await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически'); f.done({ ok: true });
  await f.click('Создать трек');
  const reason = 'ram_available_gib is below the safety floor';
  f.done({ ok: false, report: {
    master_path: null,
    result: { label: 'Аудиочерновик: состав не подтверждён', status: 'failed', reasons: [reason] },
    hardware_preflight: { status: 'blocked', decision: 'refuse', selected_backend: 'not_selected',
      reasons: [reason], inference_verified: false, product_profile_accepted: false },
    blocked: [{ stage: 'hardware_preflight', reason }],
  } });
  assert.match(f.root.textContent, /Аппаратный preflight: blocked · refuse/);
  assert.match(f.root.textContent, /Inference не подтверждён; профиль продукта не принят/);
  assert.match(f.root.textContent, /ram_available_gib is below the safety floor/);
});

test('legacy HIT flag cannot label a draft as a complete result', async () => {
  const f = fixture(); await f.load(); await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически'); f.done({ ok: true });
  await f.click('Создать трек');
  f.event({ type: 'protocol', event: { type: 'done', report: { master_path: '/music/draft.wav', verdict: 'HIT', blocked: [],
    result: { schema: 1, status: 'degraded', succeeded: false, label: 'Речевой черновик', reasons: ['Нет пения'] } } } });
  f.done({ ok: false });
  assert.match(f.root.textContent, /неполный результат/);
  assert.match(f.root.textContent, /Нет пения/);
  assert.match(f.root.textContent, /Речевой черновик/);
});


test('guide explains actual action and incomplete recipe instead of a false workflow promise', async () => {
  const f = fixture(); await f.load();
  assert.match(f.root.textContent, /Сначала — замысел/);
  assert.match(f.root.textContent, /передаются в общий Python-рецепт/);
  assert.match(f.root.textContent, /Открыть настройки/);
  await f.click('Далее — подготовить студию');
  assert.match(f.root.textContent, /Затем — подготовка/);
  assert.match(f.root.textContent, /не доказывает готовность модели/);
  const map = require('../src/core/journey');
  assert.equal(map.length, 4);
  assert.match(map[3].output, /ещё не приняты/);
});

test('ordinary JSON and foreign task completion never overwrite the active creation result', async () => {
  const f = fixture(); await f.load(); await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически'); f.done({ ok: true });
  await f.click('Создать трек');
  f.event({ line: '{"master_path":"fake.wav","verdict":"COMPLETE"}' });
  f.event({ taskId: 'foreign', type: 'protocol', event: { type: 'done', report: { master_path: 'foreign.wav' } } });
  f.done({ taskId: 'foreign', ok: true, report: { master_path: 'foreign.wav' } });
  assert.doesNotMatch(f.root.textContent, /4\. Получен/);
  f.done({ ok: false });
  assert.doesNotMatch(f.root.textContent, /Загрузить для прослушивания здесь/);
});

test('bootstrap exit zero with missing or incomplete report does not unlock generation', async () => {
  const f = fixture(); await f.load(); await f.click('Далее — подготовить студию');
  await f.click('Проверить и подготовить автоматически');
  f.done({ ok: true, report: null });
  assert.match(f.root.textContent, /Состояние: blocked/);
  assert.doesNotMatch(f.root.textContent, /3\. Создадим трек/);
});

function acceptedContentFixture() {
  return { master_path: '/music/singing.wav', blocked: [], result: {
    schema: 1, kind: 'generated_singing', requested_kind: 'generated_singing', status: 'success', succeeded: true,
    label: 'Автоматическое пение', reasons: [], quality_accepted: false,
    artifact: { valid: true, path: '/music/singing.wav', sha256: 'a'.repeat(64) }
  } };
}
test('result boundary accepts only matching requested content and a validated current artifact', () => {
  const { isCompleteResult } = require('../src/core/creation-state');
  assert.equal(isCompleteResult(acceptedContentFixture(), true), true);
  for (const mutate of [r => { r.result.kind = 'speech_draft'; }, r => { r.result.kind = 'instrumental'; },
    r => { r.result.requested_kind = 'instrumental'; }, r => { r.result.artifact.valid = false; },
    r => { r.result.artifact.path = '/old.wav'; }, r => { r.result.artifact.sha256 = ''; },
    r => { r.result.reasons = ['missing singing']; }, r => { r.blocked = {}; },
    r => { r.outcome = { status: 'failed', succeeded: false }; }, r => { r.canceled = true; },
    r => { r.dry_run = true; }, r => { r.only = ['master']; }]) {
    const report = acceptedContentFixture(); mutate(report);
    assert.equal(isCompleteResult(report, true), false);
  }
  assert.equal(isCompleteResult(acceptedContentFixture(), false), false);
});

test('UI does not promote forged success on speech or invalid audio; positive typed singing renders result', async () => {
  for (const mode of ['speech', 'invalid', 'singing']) {
    const f = fixture(); await f.load(); await f.click('Далее — подготовить студию');
    await f.click('Проверить и подготовить автоматически'); f.done({ ok: true });
    await f.click('Создать трек');
    const report = acceptedContentFixture();
    if (mode === 'speech') report.result.kind = 'speech_draft';
    if (mode === 'invalid') report.result.artifact.valid = false;
    f.done({ ok: true, report });
    if (mode === 'singing') assert.match(f.root.textContent, /Результат создан/);
    else { assert.match(f.root.textContent, /неполный результат/); assert.doesNotMatch(f.root.textContent, /Результат создан/); }
  }
});

test('packaged result-boundary script runs typed positive/negative fixtures without a backend', async () => {
  const { checkResultContract } = require('../electron/result-contract-check');
  const run = state => checkResultContract({ webContents: {
    executeJavaScript: source => vm.runInNewContext(source, { window: { ZSMM_CREATION_STATE: state } })
  } });
  const report = await run(require('../src/core/creation-state'));
  assert.equal(report.ok, true);
  assert.equal(report.checks.length, 7);
  assert.equal(report.kind, 'typed-fixtures-not-generation');
  assert.equal((await run({})).ok, false);
});
