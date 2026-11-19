'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { readMasterAudio, MAX_BYTES } = require('../electron/agent-audio');
const { encodeWav } = require('../src/core/audio/wav');
async function fixture(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'zsmm-audio-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  return root;
}
test('reads generated WAV for in-window playback', async t => {
  const root = await fixture(t), file = path.join(root, 'master.wav');
  const wav = encodeWav([new Float32Array(800), new Float32Array(800)], 8000);
  await fs.writeFile(file, Buffer.from(wav));
  const r = await readMasterAudio(file, [root]);
  assert.equal(r.mime, 'audio/wav');
  assert.deepEqual(Buffer.from(r.base64, 'base64'), Buffer.from(wav));
});
test('rejects file outside result roots, relative path and malformed WAV', async t => {
  const root = await fixture(t), other = await fixture(t);
  const file = path.join(other, 'private.wav'); await fs.writeFile(file, Buffer.alloc(100));
  await assert.rejects(readMasterAudio(file, [root]), /вне каталога/);
  await assert.rejects(readMasterAudio('relative.wav', [root]), /абсолютный/);
  await assert.rejects(readMasterAudio(file, [other]), /WAV/);
});
test('rejects oversized audio before transfer', async t => {
  const root = await fixture(t), file = path.join(root, 'large.wav');
  const h = await fs.open(file, 'w'); await h.truncate(MAX_BYTES + 1); await h.close();
  await assert.rejects(readMasterAudio(file, [root]), /64 МБ/);
});
