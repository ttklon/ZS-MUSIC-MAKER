'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { registerUpdaterIpc, compareVersions, selectInstaller } = require('../electron/updater-service');

async function fixture(t, options = {}) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'zsmm-updater-test-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  await fs.writeFile(path.join(root, 'version.json'), JSON.stringify({ version: '42.0.26' }));
  const data = Buffer.alloc(2048, 42);
  const asset = { name: 'ZS-Music-Maker-Setup-42.0.27.exe', size: data.length,
    browser_download_url: 'https://github.com/ttklon/ZS-MUSIC-MAKER/releases/download/v42.0.27/Setup.exe',
    digest: 'sha256:' + crypto.createHash('sha256').update(data).digest('hex') };
  const release = { tag_name: 'v42.0.27', assets: [asset], body: 'fixes' };
  const state = { online: true, fetched: 0, downloaded: 0, opened: [], quit: 0 };
  const handlers = {};
  registerUpdaterIpc({ root, platform: 'win32',
    ipcMain: { handle: (name, fn) => { handlers[name] = fn; } },
    settingsStore: { load: () => ({ value: { networkOnline: state.online } }) },
    app: { quit: () => state.quit++ },
    shell: { openPath: async file => { state.opened.push(file); return options.openError || ''; } },
    fetchRelease: async () => { state.fetched++; return release; },
    downloadFile: async (_url, dest) => { state.downloaded++; await fs.writeFile(dest, options.corrupt ? Buffer.alloc(2048) : data); },
  });
  const call = (name, args) => handlers['zsmm:updater-' + name](null, args);
  return { call, state, release, asset, data };
}

test('version comparison rejects missing/malformed versions', () => {
  assert.equal(compareVersions('42.0.26', 'v42.0.27'), -1);
  assert.equal(compareVersions('42.0.27', '42.0.27'), 0);
  assert.throws(() => compareVersions('unknown', '42.0.27'));
});

test('installer selection never chooses portable or source archives', () => {
  assert.equal(selectInstaller({ assets: [{ name: 'Source.zip' }] }), null);
  assert.equal(selectInstaller({ assets: [{ name: 'ZS-Music-Maker-Setup-1.0.0.exe', browser_download_url: 'https://evil.test/a', digest: 'sha256:' + 'a'.repeat(64) }] }), null);
});

test('check download verify and installer launch without Python', async t => {
  const f = await fixture(t);
  const check = await f.call('check');
  assert.equal(check.updateAvailable, true);
  assert.equal(check.installer.name, f.asset.name);
  const dl = await f.call('download', { url: f.asset.browser_download_url, name: f.asset.name });
  assert.equal(dl.ok, true);
  t.after(() => fs.rm(path.dirname(dl.path), { recursive: true, force: true }));
  assert.equal((await f.call('install', { zipPath: dl.path })).installerLaunched, true);
  assert.deepEqual(f.state.opened, [dl.path]);
  assert.equal(f.state.quit, 1);
});

test('offline check and download never touch the network', async t => {
  const f = await fixture(t);
  f.state.online = false;
  assert.equal((await f.call('check')).offline, true);
  assert.equal((await f.call('download', {})).ok, false);
  assert.equal(f.state.fetched, 0);
  assert.equal(f.state.downloaded, 0);
});

test('arbitrary URL and local executable are rejected', async t => {
  const f = await fixture(t);
  await f.call('check');
  assert.equal((await f.call('download', { url: 'https://evil.test/a', name: '../a.exe' })).ok, false);
  assert.equal((await f.call('install', { zipPath: '/tmp/arbitrary.exe' })).ok, false);
  assert.equal(f.state.downloaded, 0);
  assert.equal(f.state.quit, 0);
});

test('digest mismatch prevents installation', async t => {
  const f = await fixture(t, { corrupt: true });
  await f.call('check');
  const dl = await f.call('download', { url: f.asset.browser_download_url, name: f.asset.name });
  assert.equal(dl.ok, false);
  assert.match(dl.error, /SHA-256/);
  assert.equal(f.state.opened.length, 0);
});

test('tampering after download prevents launch', async t => {
  const f = await fixture(t);
  await f.call('check');
  const dl = await f.call('download', { url: f.asset.browser_download_url, name: f.asset.name });
  t.after(() => fs.rm(path.dirname(dl.path), { recursive: true, force: true }));
  await fs.writeFile(dl.path, 'tampered');
  assert.equal((await f.call('install', { zipPath: dl.path })).ok, false);
  assert.equal(f.state.quit, 0);
});

test('missing installer digest disables installation', async t => {
  const f = await fixture(t);
  delete f.asset.digest;
  const check = await f.call('check');
  assert.equal(check.updateAvailable, true);
  assert.equal(check.installer, null);
  assert.match(check.unavailableReason, /SHA-256/);
});

test('failed new check invalidates an old offer', async t => {
  const f = await fixture(t);
  await f.call('check');
  f.release.tag_name = 'not-a-version';
  assert.equal((await f.call('check')).ok, false);
  assert.equal((await f.call('download', { url: f.asset.browser_download_url, name: f.asset.name })).ok, false);
});

test('installer launch failure leaves app open', async t => {
  const f = await fixture(t, { openError: 'Windows refused launch' });
  await f.call('check');
  const dl = await f.call('download', { url: f.asset.browser_download_url, name: f.asset.name });
  t.after(() => fs.rm(path.dirname(dl.path), { recursive: true, force: true }));
  assert.equal((await f.call('install', { zipPath: dl.path })).ok, false);
  assert.equal(f.state.quit, 0);
});
