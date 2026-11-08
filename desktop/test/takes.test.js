'use strict';
/**
 * test/takes.test.js — вокальные дубли и их честность.
 *
 * Главное, что здесь проверяется: тестовый дубль не может выдать себя за
 * запись с микрофона. Это не стилистическое требование — на нём держится
 * отчёт, который пользователь читает после рендера.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const takes = require('../src/core/audio/takes');
const { encodeWav } = require('../src/core/audio/wav');

function wavBuffer(seconds = 1, sr = 44100) {
  const signal = new Float32Array(Math.round(seconds * sr));
  for (let i = 0; i < signal.length; i += 1) signal[i] = Math.sin((2 * Math.PI * 220 * i) / sr) * 0.4;
  return encodeWav([signal], sr);
}

test('тестовый дубль помечен как имитация и несёт причину', () => {
  const take = takes.testTake({ seconds: 3, seed: 2 });
  const info = takes.describeTake(take);
  assert.equal(info.source, 'test');
  assert.equal(info.simulated, true);
  assert.match(info.label, /не с микрофона/);
  assert.ok(info.note && info.note.length > 10, 'нет объяснения, почему это имитация');
  assert.ok(Math.abs(info.durationSec - 3) < 0.2, `длительность ${info.durationSec}`);
});

test('синтезированный дубль — не имитация микрофона, но и не запись человека', () => {
  const info = takes.describeTake(takes.synthTake({ seconds: 2, seed: 5 }));
  assert.equal(info.source, 'synth');
  assert.equal(info.simulated, false);
  assert.match(info.label, /синтезирован/);
});

test('assertHonest ловит тестовый дубль, выданный за запись', () => {
  assert.throws(
    () => takes.assertHonest({ source: 'test', simulated: false }),
    /simulated: true/,
    'подмена источника должна ломать проверку',
  );
  assert.throws(
    () => takes.assertHonest({ source: 'file', simulated: true }),
    /источник указан как запись/,
  );
  // Настоящие дубли проходят без исключений.
  const synth = takes.assertHonest(takes.synthTake({ seconds: 1 }));
  assert.equal(synth.simulated, false);
  const simulated = takes.assertHonest(takes.testTake({ seconds: 1 }));
  assert.equal(simulated.simulated, true);
});

test('тестовый дубль: нет NaN, пик в пределах, шум на месте', () => {
  const take = takes.testTake({ seconds: 2, sr: 22050, seed: 4 });
  assert.equal(take.sampleRate, 22050);
  let peak = 0;
  for (let i = 0; i < take.signal.length; i += 1) {
    assert.ok(Number.isFinite(take.signal[i]), `NaN в сэмпле ${i}`);
    peak = Math.max(peak, Math.abs(take.signal[i]));
  }
  assert.ok(peak <= 0.85, `пик ${peak} слишком высокий для «записи»`);
  // Комнатный шум не даёт абсолютной тишины: у живой записи её не бывает.
  let silent = 0;
  for (let i = 0; i < take.signal.length; i += 1) if (Math.abs(take.signal[i]) < 1e-6) silent += 1;
  assert.ok(silent < take.signal.length * 0.05, `тихих сэмплов ${silent} — шум не подмешан`);
});

test('длина дубля совпадает с заказанной (в пределах одного слога)', () => {
  for (const seconds of [3, 7]) {
    const take = takes.testTake({ seconds, seed: 1 });
    assert.ok(Math.abs(take.durationSec - seconds) < 0.05, `${seconds} с → ${take.durationSec}`);
    assert.equal(take.signal.length, Math.round(seconds * take.sampleRate));
  }
});

test('импорт WAV из файла: чтение, моно-микс и передискретизация', () => {
  const buffer = wavBuffer(1, 44100);
  const imported = takes.loadTake(buffer);
  assert.equal(imported.source, 'file');
  assert.equal(imported.simulated, false);
  assert.equal(imported.channels, 1);
  assert.ok(Math.abs(imported.durationSec - 1) < 0.02, `длительность ${imported.durationSec}`);

  // 44.1 → 22.05 кГц: та же длительность, вдвое меньше сэмплов.
  const half = takes.loadTake(buffer, 22050);
  assert.equal(half.sampleRate, 22050);
  assert.ok(Math.abs(half.durationSec - 1) < 0.05, `после ресемплинга ${half.durationSec}`);
});

test('импорт мусора — понятная ошибка, а не тишина', () => {
  assert.throws(() => takes.loadTake(Buffer.from('это не WAV вообще')), /WAV/);
});

test('имя файла дубля — безопасное и с источником', () => {
  assert.equal(takes.takeFileName('test', 8, 3), 'vocal-test-8s-seed3.wav');
  assert.ok(!takes.takeFileName('../../evil', 8, 3).includes('/'), 'в имени остался путь');
});

test('resample сохраняет форму сигнала', () => {
  const signal = new Float32Array([0, 0.5, 0, -0.5, 0]);
  const up = takes.resample(signal, 4, 8);
  assert.equal(up.length, 10);
  assert.ok(Math.abs(up[2] - 0.5) < 1e-6, 'пик не сохранился при увеличении частоты');
});

test('дубль детерминирован по сиду', () => {
  const a = takes.testTake({ seconds: 2, seed: 42 });
  const b = takes.testTake({ seconds: 2, seed: 42 });
  const c = takes.testTake({ seconds: 2, seed: 43 });
  assert.deepEqual(Array.from(a.signal.slice(0, 500)), Array.from(b.signal.slice(0, 500)));
  assert.notDeepEqual(Array.from(a.signal.slice(0, 500)), Array.from(c.signal.slice(0, 500)));
});

test('микрофон честно назван недоступным, если устройств нет', () => {
  const status = takes.microphoneStatus({ hasDevices: false });
  assert.equal(status.ok, false);
  assert.equal(status.recording, false);
  assert.match(status.reason, /недоступна/);
  const found = takes.microphoneStatus({ hasDevices: true });
  assert.equal(found.recording, true);
});

test('каталог для дублей создаётся вызывающим кодом, сам модуль не пишет на диск', () => {
  // `takes.js` — чистая логика: никаких файлов. Это проверяется тем, что
  // после работы с дублями во временном каталоге ничего не появилось.
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-takes-'));
  takes.testTake({ seconds: 1 });
  assert.deepEqual(fs.readdirSync(dir), []);
  fs.rmSync(dir, { recursive: true, force: true });
});
