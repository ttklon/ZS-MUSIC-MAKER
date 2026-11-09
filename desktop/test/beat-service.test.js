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

const {
  registerBeatIpc, saveBeat, saveTextCopy, defaultBeatPath, describeInput,
} = require('../electron/beat-service');

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
    [
      'zsmm:beat-bank', 'zsmm:beat-cancel', 'zsmm:beat-open-external', 'zsmm:beat-render',
      'zsmm:beat-save', 'zsmm:save-copy',
      // Вокал: выбор WAV, статус входа, запись с микрофона и выгрузка дубля.
      'zsmm:vocal-export', 'zsmm:vocal-input', 'zsmm:vocal-pick',
      'zsmm:vocal-save-recording',
    ].sort(),
  );
});

test('состояние входа записи: захват делает окно, подмены нет', async () => {
  const ipc = fakeIpc();
  registerBeatIpc({ ipcMain: ipc, dialog: fakeDialog(null), rootDir: ROOT, getWindow: () => null, musicDir: tempDir });
  const reply = await ipc.handlers.get('zsmm:vocal-input')();
  assert.equal(reply.ok, true);
  // Главный процесс не может проверить микрофон — и не утверждает ни «есть»,
  // ни «нет»: `available: null` значит «пробовать можно, отказ покажет окно».
  assert.equal(reply.data.available, null);
  assert.equal(reply.data.recording, true);
  assert.match(reply.data.reason, /микрофон/i);
  assert.match(reply.data.reason, /никуда не|не отправляется/i);
  assert.equal(reply.data.simulatedAvailable, true, 'тестовый дубль остаётся доступен');
  assert.equal(reply.data.maxSeconds, 60);

  // Отказ доступа из окна — единственный источник «микрофона нет».
  assert.equal(describeInput({ available: false }).recording, false);
  assert.match(describeInput({ available: false }).reason, /не получило доступ/);
});

test('запись с микрофона сохраняется только как настоящий WAV', async () => {
  const ipc = fakeIpc();
  const dialog = fakeDialog(null);
  registerBeatIpc({ ipcMain: ipc, dialog, rootDir: ROOT, getWindow: () => null, musicDir: tempDir });

  // Тишина — не дубль: скорее всего микрофон не дал звука.
  const silent = Buffer.alloc(4 * 4410).toString('base64');
  const empty = await ipc.handlers.get('zsmm:vocal-save-recording')({}, { pcmBase64: silent, sampleRate: 44100 });
  assert.equal(empty.ok, false);
  assert.match(empty.error, /тишина/);

  // Мусор и неверная частота отвергаются до диалога: имя файла — не доказательство.
  const junk = await ipc.handlers.get('zsmm:vocal-save-recording')({}, { pcmBase64: 'AAAA', sampleRate: 44100 });
  assert.equal(junk.ok, false);
  assert.match(junk.error, /повреждены|пуста/);

  // Настоящая запись: полусекунда синуса, сохраняется через диалог.
  const frames = 22050;
  const raw = Buffer.alloc(frames * 4);
  for (let i = 0; i < frames; i += 1) raw.writeFloatLE(0.4 * Math.sin((2 * Math.PI * 220 * i) / 44100), i * 4);
  const path = require('node:path').join(tempDir(), 'record-saved.wav');
  dialog.showSaveDialog = async () => ({ canceled: false, filePath: path });
  const saved = await ipc.handlers.get('zsmm:vocal-save-recording')(
    {}, { pcmBase64: raw.toString('base64'), sampleRate: 44100, seconds: 0.5 },
  );
  assert.equal(saved.ok, true, saved.error);
  assert.equal(saved.data.recorded, true);
  const written = fs.readFileSync(path);
  assert.equal(written.toString('ascii', 0, 4), 'RIFF');
  assert.ok(written.length > 44, 'в WAV есть данные');
  fs.rmSync(path, { force: true });
});

test('выбор вокального WAV: отмена и выбранный путь', async () => {
  const ipc = fakeIpc();
  const dialog = fakeDialog(null);
  registerBeatIpc({ ipcMain: ipc, dialog, rootDir: ROOT, getWindow: () => null, musicDir: tempDir });

  dialog.showOpenDialog = async () => ({ canceled: true, filePaths: [] });
  const cancelled = await ipc.handlers.get('zsmm:vocal-pick')();
  assert.equal(cancelled.ok, true);
  assert.equal(cancelled.data.path, null);

  dialog.showOpenDialog = async () => ({ canceled: false, filePaths: ['C:/music/take.wav'] });
  const picked = await ipc.handlers.get('zsmm:vocal-pick')();
  assert.equal(picked.data.path, 'C:/music/take.wav');
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


test('готовый WAV открывается в системном плеере, мусор — нет', async () => {
  const ipc = fakeIpc();
  const opened = [];
  registerBeatIpc({
    ipcMain: ipc,
    dialog: fakeDialog(null),
    rootDir: ROOT,
    getWindow: () => null,
    musicDir: tempDir,
    openPath: async (file) => {
      opened.push(file);
      return null;
    },
    tempDir: tempDir(),
  });

  const wav = await realWav();
  const reply = await ipc.handlers.get('zsmm:beat-open-external')({}, wav.toString('base64'));
  assert.equal(reply.ok, true, reply.error);
  assert.equal(opened.length, 1, 'плеер не получил файл');
  assert.ok(opened[0].endsWith('.wav'));
  assert.ok(fs.existsSync(opened[0]), 'временный файл не создан');
  assert.ok(fs.statSync(opened[0]).size > 1000);
  fs.rmSync(opened[0], { force: true });

  // Не-WAV и пустая строка отвергаются: открывать «что-то» в плеере нельзя.
  // Достаточно длинный, но не RIFF: проверка «это не WAV» срабатывает после
  // проверки длины, поэтому мусор должен быть длиннее 64 символов.
  const junk = await ipc.handlers.get('zsmm:beat-open-external')(
    {}, Buffer.from('это точно не wav, а просто текст длиной больше шестидесяти четырёх символов').toString('base64'),
  );
  assert.equal(junk.ok, false);
  assert.match(junk.error, /не WAV/);
  const empty = await ipc.handlers.get('zsmm:beat-open-external')({}, '');
  assert.equal(empty.ok, false);

  // Ошибка плеера возвращается текстом, а не тишиной.
  const failing = fakeIpc();
  registerBeatIpc({
    ipcMain: failing,
    dialog: fakeDialog(null),
    rootDir: ROOT,
    getWindow: () => null,
    musicDir: tempDir,
    openPath: async () => 'нет приложения для .wav',
    tempDir: tempDir(),
  });
  const failed = await failing.handlers.get('zsmm:beat-open-external')({}, wav.toString('base64'));
  assert.equal(failed.ok, false);
  assert.match(failed.error, /плеер не открылся/);
});

test('вокальный дубль сохраняется отдельным WAV', async () => {
  const dir = tempDir();
  const ipc = fakeIpc();
  const dialog = fakeDialog(path.join(dir, 'vocal-test.wav'));
  registerBeatIpc({ ipcMain: ipc, dialog, rootDir: ROOT, getWindow: () => null, musicDir: () => dir });

  const takes = require('../src/core/audio/takes');
  const { encodeWav } = require('../src/core/audio/wav');
  const take = takes.testTake({ seconds: 1, seed: 2 });
  const payload = { wavBase64: encodeWav([take.signal], 44100).toString('base64'), name: 'vocal-test-1s-seed2' };

  const saved = await ipc.handlers.get('zsmm:vocal-export')({}, payload);
  assert.equal(saved.ok, true, saved.error);
  assert.ok(fs.existsSync(saved.data.path), 'дубль не записан');
  const bytes = fs.readFileSync(saved.data.path);
  assert.equal(bytes.subarray(0, 4).toString('ascii'), 'RIFF');

  // Пустая нагрузка и отмена диалога — не ошибка приложения, но и не файл.
  const empty = await ipc.handlers.get('zsmm:vocal-export')({}, {});
  assert.equal(empty.ok, false);
  const cancelling = fakeIpc();
  registerBeatIpc({ ipcMain: cancelling, dialog: fakeDialog(null), rootDir: ROOT, getWindow: () => null, musicDir: () => dir });
  const cancelled = await cancelling.handlers.get('zsmm:vocal-export')({}, payload);
  assert.equal(cancelled.ok, true);
  assert.equal(cancelled.data.path, null);
});

test('рендер с вокалом отдаёт окну WAV дубля, без вокала — нет', async () => {
  const ipc = fakeIpc();
  registerBeatIpc({ ipcMain: ipc, dialog: fakeDialog(null), rootDir: ROOT, getWindow: () => null, musicDir: tempDir });
  const sender = { isDestroyed: () => false, send: () => {} };

  const withVocal = await ipc.handlers.get('zsmm:beat-render')(
    { sender },
    { bpm: 120, genre: 'phonk', seed: 3, durationSec: 2, vocal: { mode: 'test' } },
  );
  assert.equal(withVocal.ok, true, withVocal.error);
  assert.ok(withVocal.data.vocalWavBase64, 'дубль не приложен');
  const bytes = Buffer.from(withVocal.data.vocalWavBase64, 'base64');
  assert.equal(bytes.subarray(0, 4).toString('ascii'), 'RIFF');
  assert.match(withVocal.data.vocalName, /^vocal-test-/);
  assert.equal(withVocal.data.report.vocal.source, 'test');

  const dry = await ipc.handlers.get('zsmm:beat-render')(
    { sender },
    { bpm: 120, genre: 'phonk', seed: 3, durationSec: 2 },
  );
  assert.equal(dry.ok, true, dry.error);
  assert.equal(dry.data.vocalWavBase64, null);
  assert.equal(dry.data.vocalName, null);
});
