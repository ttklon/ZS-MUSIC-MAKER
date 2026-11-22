'use strict';
/** Windows desktop updates use the released NSIS installer, never a source ZIP.
 * Only assets returned by the official release API may be downloaded/launched.
 * User data stays in userData; the installer replaces application binaries.
 */
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const https = require('node:https');
const crypto = require('node:crypto');
const { pipeline } = require('node:stream/promises');

const GITHUB_LATEST = 'https://api.github.com/repos/ttklon/ZS-MUSIC-MAKER/releases/latest';
const HEADERS = { 'User-Agent': 'ZS-Music-Maker-Updater', Accept: 'application/vnd.github+json' };

function readVersion(root) {
  try {
    const raw = JSON.parse(fs.readFileSync(path.join(root, 'version.json'), 'utf8'));
    return { version: raw.version || 'unknown', raw };
  } catch (e) { return { version: 'unknown', error: e.message }; }
}

function compareVersions(a, b) {
  const parse = v => {
    if (!/^v?\d+\.\d+\.\d+$/.test(String(v))) throw new Error(`Invalid release version: ${v}`);
    return String(v).replace(/^v/, '').split('.').map(Number);
  };
  const pa = parse(a), pb = parse(b);
  for (let i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pa[i] < pb[i] ? -1 : 1;
  return 0;
}

function request(url, redirects = 0) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const hosts = ['api.github.com', 'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'];
    if (u.protocol !== 'https:' || u.username || u.password || !hosts.includes(u.hostname) || redirects > 5) {
      reject(new Error('Unsafe update URL or too many redirects')); return;
    }
    const req = https.get(u, { headers: HEADERS, timeout: 30000 }, res => {
      if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location) {
        res.resume();
        request(new URL(res.headers.location, u).href, redirects + 1).then(resolve, reject);
      } else if (res.statusCode !== 200) {
        res.resume(); reject(new Error(`GitHub HTTP ${res.statusCode}`));
      } else resolve(res);
    });
    req.on('error', reject);
    req.on('timeout', () => req.destroy(new Error('Update request timed out')));
  });
}

async function getRelease() {
  const res = await request(GITHUB_LATEST);
  let text = '';
  for await (const chunk of res) {
    text += chunk;
    if (text.length > 4 * 1024 * 1024) { res.destroy(); throw new Error('Release response too large'); }
  }
  return JSON.parse(text);
}

async function download(url, dest) {
  const res = await request(url);
  await pipeline(res, fs.createWriteStream(dest, { flags: 'wx' }));
}

async function sha256(file) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) hash.update(chunk);
  return 'sha256:' + hash.digest('hex');
}

function selectInstaller(release) {
  const asset = (release.assets || []).find(a => /^ZS-Music-Maker-Setup-\d+\.\d+\.\d+\.exe$/.test(a.name));
  if (!asset) return null;
  const prefix = 'https://github.com/ttklon/ZS-MUSIC-MAKER/releases/download/';
  if (!asset.browser_download_url?.startsWith(prefix) || !/^sha256:[a-f0-9]{64}$/.test(asset.digest || '')) return null;
  return { name: asset.name, url: asset.browser_download_url, size: asset.size, digest: asset.digest };
}

function registerUpdaterIpc({ ipcMain, root, settingsStore, app, shell, confirmInstall,
  platform = process.platform, fetchRelease = getRelease, downloadFile = download }) {
  let offered = null, downloaded = null, busy = false, installing = false;
  function online() {
    let s = {};
    try { s = settingsStore?.load().value || {}; } catch {}
    return s.networkOnline === true || s['network.online'] === true || process.env.ZSMM_ONLINE === '1';
  }
  ipcMain.handle('zsmm:updater-check', async () => {
    const cur = readVersion(root);
    if (busy) return { ok: false, error: 'Обновление уже скачивается' };
    offered = null; downloaded = null;
    if (!online()) return { ok: false, offline: true, current: cur.version, error: 'Включите доступ к сети в настройках приложения для проверки обновлений.' };
    try {
      const release = await fetchRelease();
      if (release.draft || release.prerelease) throw new Error('Release is not stable');
      const latest = String(release.tag_name || '').replace(/^v/, '');
      const updateAvailable = compareVersions(cur.version, latest) < 0;
      const installer = selectInstaller(release);
      if (updateAvailable && platform === 'win32') offered = installer;
      return { ok: true, current: cur.version, latest, updateAvailable,
        installer: offered, changelog: release.body || '', releaseUrl: release.html_url,
        unavailableReason: platform !== 'win32' ? 'Автоустановка доступна только в Windows.' :
          !installer ? 'Установщик с SHA-256 ещё не опубликован. Повторите проверку позже.' : '' };
    } catch (e) { return { ok: false, current: cur.version, error: e.message }; }
  });
  ipcMain.handle('zsmm:updater-download', async (_event, args = {}) => {
    if (busy) return { ok: false, error: 'Обновление уже скачивается' };
    if (!online()) return { ok: false, error: 'Доступ к сети выключен' };
    if (!offered || args.url !== offered.url || args.name !== offered.name) return { ok: false, error: 'Сначала проверьте обновления; файл не принадлежит выбранному релизу' };
    busy = true;
    downloaded = null;
    let dir;
    try {
      dir = await fsp.mkdtemp(path.join(os.tmpdir(), 'zsmm-update-'));
      const dest = path.join(dir, offered.name);
      await downloadFile(offered.url, dest);
      const stat = await fsp.stat(dest);
      if (!Number.isSafeInteger(offered.size) || stat.size !== offered.size || stat.size < 1024) throw new Error('Размер установщика не совпадает с релизом');
      if (await sha256(dest) !== offered.digest) throw new Error('SHA-256 установщика не совпадает с релизом');
      downloaded = { path: dest, digest: offered.digest };
      return { ok: true, path: dest, bytes: stat.size };
    } catch (e) {
      if (dir) await fsp.rm(dir, { recursive: true, force: true }).catch(() => {});
      return { ok: false, error: e.message };
    } finally { busy = false; }
  });
  ipcMain.handle('zsmm:updater-install', async (_event, args = {}) => {
    if (installing) return { ok: false, error: 'Подтверждение установки уже открыто' };
    installing = true;
    try {
      if (!downloaded || args.zipPath !== downloaded.path) throw new Error('Нет проверенного скачанного установщика');
      if (await sha256(downloaded.path) !== downloaded.digest) throw new Error('Установщик изменён после скачивания');
      if (!shell || !app || platform !== 'win32') throw new Error('Установка доступна в Windows-приложении');
      if (typeof confirmInstall !== 'function' || await confirmInstall(downloaded.path) !== true) {
        return { ok: false, canceled: true, error: 'Установка не подтверждена пользователем' };
      }
      // Recheck after the asynchronous consent dialog (the file may have changed).
      if (await sha256(downloaded.path) !== downloaded.digest) throw new Error('Установщик изменён после подтверждения');
      const error = await shell.openPath(downloaded.path);
      if (error) throw new Error(error);
      downloaded = null;
      app.quit();
      return { ok: true, installerLaunched: true };
    } catch (e) { return { ok: false, error: e.message }; }
    finally { installing = false; }
  });
  ipcMain.handle('zsmm:updater-info', async () => ({ ok: true, ...readVersion(root) }));
}

module.exports = { registerUpdaterIpc, readVersion, compareVersions, selectInstaller, sha256 };
