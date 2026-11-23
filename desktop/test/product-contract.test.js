'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const c = require('../src/core/product-contract');
const { checkMetadata, summary } = require('../scripts/product-spec');
const ROOT = path.resolve(__dirname, '../..');

test('product contract matches delivered name, version and per-user x64 NSIS', () => {
  const metadata = checkMetadata(c);
  assert.equal(metadata.version, JSON.parse(fs.readFileSync(path.join(ROOT, 'version.json'))).version);
  assert.equal(c.entry, 'Electron → Создание трека');
  assert.equal(c.scenarios.length, 4);
  assert.ok(c.scenarios.every(s => s.required && s.accepted === false && s.blocker));
});

test('browser and Node receive identical product contract without network or IPC', () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'desktop/src/core/product-contract.js'), 'utf8'), { window });
  assert.deepEqual(JSON.parse(JSON.stringify(window.ZSMM_PRODUCT)), c);
  assert.match(summary(c), /Речь Silero\/XTTS ≠ пение/);
});

test('metadata mismatch refuses acceptance and leaves previous files unchanged', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zs-contract-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, 'desktop'));
  const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'desktop/package.json')));
  fs.writeFileSync(path.join(root, 'version.json'), JSON.stringify({ version: '0.0.0' }));
  fs.writeFileSync(path.join(root, 'desktop/package.json'), JSON.stringify(pkg));
  assert.throws(() => checkMetadata(c, root), /version mismatch/);
  assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'version.json'))).version, '0.0.0');
  fs.writeFileSync(path.join(root, 'version.json'), JSON.stringify({ version: pkg.version }));
  pkg.build.nsis.artifactName = 'Other.exe';
  fs.writeFileSync(path.join(root, 'desktop/package.json'), JSON.stringify(pkg));
  assert.throws(() => checkMetadata(c, root), /Installer name mismatch/);
});

test('generated documentation is current; archived claims are not active help', () => {
  require('node:child_process').execFileSync(process.execPath, ['desktop/scripts/product-spec.js', '--check'], { cwd: ROOT });
  const help = fs.readFileSync(path.join(ROOT, 'desktop/src/sections/help.js'), 'utf8');
  assert.ok(!help.includes('Сеть не используется вовсе'));
  assert.ok(!help.includes('не main.py, app/ и modules/'));
  assert.match(help, /Спецификация недоступна/);
});

test('missing or unsupported browser contract shows a recoverable error, never success claims', async () => {
  const { FakeDocument } = require('./fake-dom');
  for (const product of [undefined, { schema: 99, scenarios: [] }]) {
    const doc = new FakeDocument();
    const host = doc.createElement('div'); host.id = 'help-body'; doc.append(host);
    const window = { zsmm: {}, ZSMM_PRODUCT: product, ZSMM_SECTIONS: {}, ZSMM_UI: {
      $: id => doc.getElementById(id), showError: () => {},
      el: (tag, cls, text) => { const n = doc.createElement(tag); n.className = cls || ''; n.textContent = text || ''; return n; }
    } };
    vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'desktop/src/sections/help.js'), 'utf8'), { window, setTimeout: () => 0 });
    window.ZSMM_SECTIONS.initHelp();
    await window.ZSMM_UI.loadHelp();
    assert.match(host.textContent, /Спецификация недоступна/);
    assert.doesNotMatch(host.textContent, /Что действительно работает/);
  }
});

test('schema rejects empty, duplicated, incomplete or unsupported product scenarios', () => {
  const clone = () => JSON.parse(JSON.stringify(c));
  for (const mutate of [x => { x.scenarios = []; }, x => { x.scenarios[1] = x.scenarios[0]; },
    x => { x.scenarios[0].accepted = 'false'; }, x => { x.scenarios[0].blocker = ''; },
    x => { x.scenarios[0].accepted = true; }, x => { x.notEquivalent = []; },
    x => { x.name = ''; }, x => { x.versionSource = '../version.json'; }]) {
    const bad = clone(); mutate(bad);
    assert.equal(c.validate(bad), false);
    assert.throws(() => checkMetadata(bad), /Invalid product contract/);
  }
  assert.equal(c.validate(c), true);
});

test('valid help really renders all scenario names, boundaries and reasons; malformed schema recovers', async () => {
  const { FakeDocument } = require('./fake-dom');
  for (const bad of [false, true]) {
    const doc = new FakeDocument();
    const host = doc.createElement('div'); host.id = 'help-body'; doc.append(host);
    const window = { zsmm: {}, ZSMM_SECTIONS: {}, ZSMM_UI: {
      $: id => doc.getElementById(id), showError: () => {},
      el: (tag, cls, text) => { const n = doc.createElement(tag); n.className = cls || ''; n.textContent = text || ''; return n; }
    } };
    vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'desktop/src/core/product-contract.js'), 'utf8'), { window });
    if (bad) window.ZSMM_PRODUCT = { ...window.ZSMM_PRODUCT, scenarios: [] };
    vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'desktop/src/sections/help.js'), 'utf8'), { window, setTimeout: () => 0 });
    window.ZSMM_SECTIONS.initHelp(); await window.ZSMM_UI.loadHelp();
    if (bad) assert.match(host.textContent, /Спецификация недоступна/);
    else for (const s of c.scenarios) for (const text of [s.name, s.result, s.blocker]) assert.ok(host.textContent.includes(text));
  }
});

test('packaged probe rejects correct product ID with missing or stale visible contract text', () => {
  const { verifyProductHelp } = require('../electron/product-help-check');
  const snapshot = { contract: JSON.parse(JSON.stringify(c)),
    intro: ['name', 'platform', 'entry', 'state', 'delivery', 'network', 'hardware', 'rights'].map(k => c[k]).join('\n'),
    scenarios: c.scenarios.map(s => `${s.name} Не принят: ${s.result} ${s.blocker}`).join('\n') };
  assert.equal(verifyProductHelp(snapshot), true);
  assert.equal(verifyProductHelp({ ...snapshot, intro: c.id }), false);
  assert.equal(verifyProductHelp({ ...snapshot, scenarios: '' }), false);
  assert.equal(verifyProductHelp({ ...snapshot, contract: { id: c.id } }), false);
});
