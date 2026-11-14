const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { documentFromHtml, windowScripts } = require('./fake-dom');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const SRC = path.resolve(__dirname, '..', 'src');
const ROOT = path.resolve(__dirname, '..', '..');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');

/** Мост с настоящими данными и запоминаемыми настройками. */
function bootWindow(stored) {
  const project = createProject(createNodeFs(), ROOT);
  const wrap = (loader) => async () => ({ ok: true, data: loader() });
  const saved = [];
  const bridge = {
    version: wrap(() => project.version()),
    genres: wrap(() => project.genres()),
    modules: wrap(() => project.modules()),
    readiness: wrap(() => project.readiness()),
    dossiers: wrap(() => project.dossiers()),
    system: wrap(() => project.systemInfo()),
    loadSettings: async () => ({ ok: true, data: { ...stored } }),
    saveSettings: async (patch) => { saved.push(patch); return { ok: true, data: {} }; },
    revealRoot: async () => ({ ok: true }),
  };

  const document = documentFromHtml(HTML);
  const window = document.createElement('window');
  window.zsmm = bridge;
  const timers = [];
  global.window = window;
  global.document = document;
  global.setTimeout = (fn, ms) => { timers.push({ fn, ms }); return timers.length; };
  global.clearTimeout = () => {};
  window.setTimeout = global.setTimeout;
  window.clearTimeout = global.clearTimeout;
  for (const script of windowScripts(SRC)) {
    new Function('window', 'document', 'setTimeout', 'clearTimeout', script.source)(
      window, document, global.setTimeout, global.clearTimeout,
    );
  }
  document.dispatch('DOMContentLoaded');
  return { document, window, saved };
}

const flush = () => new Promise((resolve) => setImmediate(resolve));

test('окно открывается на запомненном разделе', async (t) => {
  t.after(() => { delete global.window; delete global.document; });
  const { document } = bootWindow({ view: 'health' });
  await flush();
  await flush();
  assert.equal(document.getElementById('view-health').classList.contains('is-hidden'), false);
  assert.equal(document.getElementById('view-overview').classList.contains('is-hidden'), true);
  const active = [...document.querySelectorAll('.nav-item')].filter((b) => b.classList.contains('is-active'));
  assert.equal(active.length, 1);
  assert.equal(active[0].dataset.view, 'health');
});

test('смена раздела запоминается, а битый раздел — нет', async (t) => {
  t.after(() => { delete global.window; delete global.document; });
  const { document, saved } = bootWindow({ view: 'nope' });
  await flush();
  await flush();
  assert.equal(document.getElementById('view-overview').classList.contains('is-hidden'), false, 'неизвестный раздел → «Обзор»');

  const button = [...document.querySelectorAll('[data-view]')].find((b) => b.dataset.view === 'tracks');
  button.dispatch('click');
  await flush();
  await flush();
  assert.ok(saved.some((patch) => patch.view === 'tracks'), 'раздел записан');
  assert.equal(document.getElementById('view-tracks').classList.contains('is-hidden'), false);
});
