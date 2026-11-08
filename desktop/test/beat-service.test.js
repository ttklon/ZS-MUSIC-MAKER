'use strict';
/**
 * beat-service.test.js — IPC-слой бита без Electron.
 *
 * `ipcMain`, `dialog` и окно подменяются двойниками: проверяется то, что
 * раньше жило внутри `main.js` и не проверялось вовсе — сохранение WAV и
 * отчёта, отказ писать мусор, имя файла по умолчанию.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { registerBeatIpc, saveBeat, saveTextCopy, defaultBeatPath } = require('../electron/beat-service');

const ROOT = path.resolve(__dirname, '..', '..');

/** Минимальный ipcMain: запоминает обработчики по каналам. */
function fakeIpc() {
  const handlers = new Map();
  return {
    handlers,
    handle(channel, handler) {
      handlers.set(channel, handler);
    },
  };
}

/** Диалог, который «выбрал» файл. */
function fakeDialog(filePath) {
  return {
    calls: [],
    async showSaveDialog(_window, options) {
      this.calls.push(options);
      return { canceled: filePath === null, filePath };
    },
  };
}

function tempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-beat-'));
}

/** Настоящий WAV от движка: проверяем сохранение на реальных байтах. */
async function realWav() {
  const { renderBeat } = require('../src/core/audio/engine');
  return renderBeat({ bpm: 120, genre: 'house', seed: 4, durationSec: 2 }).wav;
}

test('конвейер регистрирует все каналы бита', () => {
  const ipc = fakeIpc();

  registerBeatIpc({
    ipcMain: ipc,
    dialog: fakeDialog(null),
    rootDir: ROOT,
    getWindow: () => null,
    musicDir: tempDir,
  });

  assert.deepEqual(
    [...ipc.handlers.keys()].sort(),
    ['zsmm:beat-bank', 'zsmm:beat-cancel', 'zsmm:beat-render', 'zsmm:beat-save', 'zsmm:save-copy'],
  );
});

test('банк отдаёт отчёт, а рендер — WAV', async () => {
  const ipc = fakeIpc();
  registerBeatIpc({ ipcMain: ipc, dialog: fakeDialog(null), rootDir: ROOT, getWindow: () => null, musicDir: tempDir });

  const bank = await ipc.handlers.get('zsmm:beat-bank')();
  assert.equal(bank.ok, true, bank.error);
  assert.equal(bank.data.status, 'REAL_PASS');

  const events = [];
  const reply = await ipc.handlers.get('zsmm:beat-render')(
    { sender: { isDestroyed: () => false, send: (_channel, payload) => events.push(payload) } },
    { bpm: 140, genre: 'phonk', seed: 7, durationSec: 2 },
  );

  assert.equal(reply.ok, true, reply.error);
  assert.ok(reply.data.wavBase64.length > 1000);
  assert.equal(Buffer.from(reply.data.wavBase64, 'base64').toString('ascii', 0, 4), 'RIFF');
  assert.ok(['worker', 'main'].includes(reply.data.report.renderer), 'путь рендера должен быть назван');
  assert.ok(events.some((event) => event.phase === 'done'), 'прогресс уходит окну');
});

test('WAV сохраняется на диск побайтово', async () => {
  const dir = tempDir();
  const target = path.join(dir, 'beat.wav');
  const wav = await realWav();

  const reply = await saveBeat({
    dialog: fakeDialog(target),
    getWindow: () => null,
    musicDir: () => dir,
    wavBase64: wav.toString('base64'),
  });

  assert.equal(reply.ok, true, reply.error);
  assert.equal(reply.data.bytes, wav.length);
  assert.deepEqual(fs.readFileSync(target), wav);
});

test('не-WAV не сохраняется, даже если диалог выбрал путь', async () => {
  const dir = tempDir();
  const reply = await saveBeat({
    dialog: fakeDialog(path.join(dir, 'bad.wav')),
    getWindow: () => null,
    musicDir: () => dir,
    wavBase64: Buffer.from('это точно не RIFF, а обычный текст').toString('base64'),
  });

  assert.equal(reply.ok, false);
  assert.match(reply.error, /не WAV/);
  assert.equal(fs.existsSync(path.join(dir, 'bad.wav')), false, 'файл не должен появиться');
});

test('отмена диалога — это не ошибка приложения', async () => {
  const reply = await saveBeat({
    dialog: fakeDialog(null),
    getWindow: () => null,
    musicDir: tempDir,
    wavBase64: Buffer.alloc(128, 1).toString('base64'),
  });

  assert.equal(reply.ok, false);
  assert.match(reply.error, /отменено/);
});

test('отчёт сохраняется как JSON с тем же содержимым', async () => {
  const dir = tempDir();
  const target = path.join(dir, 'beat.json');
  const report = { genre: 'phonk', bpm: 140, sections: ['intro', 'verse'] };

  const reply = await saveTextCopy({
    dialog: fakeDialog(target),
    getWindow: () => null,
    musicDir: () => dir,
    name: 'beat_phonk_140.json',
    text: JSON.stringify(report, null, 2),
  });

  assert.equal(reply.ok, true, reply.error);
  assert.deepEqual(JSON.parse(fs.readFileSync(target, 'utf8')), report);
});

test('пустой отчёт не пишется', async () => {
  const reply = await saveTextCopy({ dialog: fakeDialog(null), getWindow: () => null, musicDir: tempDir, name: 'x.json', text: '   ' });

  assert.equal(reply.ok, false);
  assert.match(reply.error, /пуст/);
});

test('имя отчёта очищается от путей, каталог — пользовательский', () => {
  const dir = tempDir();
  const dialog = fakeDialog(null);

  return saveTextCopy({
    dialog,
    getWindow: () => null,
    musicDir: () => dir,
    name: '../../windows/system32/beat.json',
    text: '{"ok":true}',
  }).then(() => {
    const { defaultPath } = dialog.calls[0];
    assert.equal(path.dirname(defaultPath), dir, 'писать можно только в каталог пользователя');
    assert.doesNotMatch(path.basename(defaultPath), /[\\/]/);
  });
});

test('путь по умолчанию — «Музыка» пользователя, а не папка проекта', () => {
  const target = defaultBeatPath(() => 'C:\\Users\\user\\Music');

  assert.match(target, /beat_.*\.wav$/);
  assert.ok(target.startsWith('C:\\Users\\user\\Music'), target);
});

test('канал отмены регистрируется и честно говорит, было ли что отменять', async () => {
  const ipc = fakeIpc();
  registerBeatIpc({ ipcMain: ipc, dialog: fakeDialog(null), rootDir: ROOT, getWindow: () => null, musicDir: tempDir });

  assert.ok([...ipc.handlers.keys()].includes('zsmm:beat-cancel'));

  const idle = await ipc.handlers.get('zsmm:beat-cancel')();
  assert.equal(idle.ok, true);
  assert.equal(idle.data.cancelled, false, 'когда рендера нет, отменять нечего');
});

test('отмена во время рендера возвращает отменённый результат, а не бит', async () => {
  const ipc = fakeIpc();
  registerBeatIpc({ ipcMain: ipc, dialog: fakeDialog(null), rootDir: ROOT, getWindow: () => null, musicDir: tempDir });
  const sender = { isDestroyed: () => false, send: () => {} };

  // Длинный бит: рендер идёт секунды, отменяем сразу после старта.
  const rendering = ipc.handlers.get('zsmm:beat-render')(
    { sender },
    { bpm: 128, genre: 'drift phonk', seed: 5, durationSec: 120 },
  );
  const cancelled = await ipc.handlers.get('zsmm:beat-cancel')();
  const result = await rendering;

  assert.equal(cancelled.data.cancelled, true);
  assert.equal(result.ok, false);
  assert.equal(result.cancelled, true);
  assert.match(result.error, /отменён/);

  // После отмены канал снова свободен.
  const again = await ipc.handlers.get('zsmm:beat-cancel')();
  assert.equal(again.data.cancelled, false);
});
