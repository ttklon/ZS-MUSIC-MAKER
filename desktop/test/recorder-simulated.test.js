'use strict';
/**
 * test/recorder-simulated.test.js — «живая» запись без микрофона.
 *
 * Здесь проверяется не двойник `AudioContext` (это делает `recorder.test.js`),
 * а весь путь целиком: симулированное устройство → настоящий код записи
 * (`ZSMM_RECORDER.start/stop/toPayload`) → WAV главного процесса → обратное
 * чтение. Звук известен заранее, поэтому результат можно измерить: длительность,
 * частоту, пик и корреляцию с исходным сигналом.
 *
 * Честность: симулированный вход обязан называться собой (`source: 'simDevice'`,
 * `simulated: true`) и не может выдаваться за запись с микрофона.
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const recorder = require('../src/sections/recorder');
const takes = require('../src/core/audio/takes');
const wavDecoder = require('../src/core/audio/wav-decode');
const { recordingToWav } = require('../electron/beat-service');

/** Тестовый синус: тот же сигнал, что «поёт» устройство. */
function sine({ hz = 200, amplitude = 0.5, sampleRate = 48000 } = {}) {
  return (i) => amplitude * Math.sin((2 * Math.PI * hz * i) / sampleRate);
}

/** Пик сигнала. */
function peak(signal) {
  let max = 0;
  for (const value of signal) max = Math.max(max, Math.abs(value));
  return max;
}

/**
 * Частота по переходам через ноль — для чистого синуса этого достаточно,
 * и это независимая проверка от кода синтеза.
 */
function zeroCrossingHz(signal, sampleRate) {
  let crossings = 0;
  for (let i = 1; i < signal.length; i += 1) {
    if ((signal[i - 1] < 0 && signal[i] >= 0) || (signal[i - 1] >= 0 && signal[i] < 0)) crossings += 1;
  }
  return (crossings / 2) / (signal.length / sampleRate);
}

/** Нормированная корреляция: 1 — сигналы совпадают по форме. */
function correlation(a, b) {
  const length = Math.min(a.length, b.length);
  let ab = 0;
  let aa = 0;
  let bb = 0;
  for (let i = 0; i < length; i += 1) {
    ab += a[i] * b[i];
    aa += a[i] * a[i];
    bb += b[i] * b[i];
  }
  if (aa === 0 || bb === 0) return 0;
  return ab / Math.sqrt(aa * bb);
}

test('симулированный вход проходит весь путь записи и измеряется', async () => {
  const sampleRate = 48000;
  const source = sine({ hz: 200, amplitude: 0.5, sampleRate });
  const rec = await recorder.start({
    simulated: { fill: source, sampleRate },
    seconds: 3,
    onTick: () => {},
  });

  assert.equal(rec.seconds, 3);
  // Даём «устройству» отдать звук: оно тикает каждые 10 мс. Останавливаем
  // вручную раньше лимита — как человек нажимает «Стоп».
  await new Promise((resolve) => { setTimeout(resolve, 1200); });
  const take = await rec.stop();

  assert.equal(take.source, 'simulated-device');
  assert.equal(take.simulated, true);
  assert.equal(take.label, 'симулированный вход (проверка)');
  assert.equal(take.sampleRate, sampleRate);

  // Длительность: около секунды, не «пусто» и не 20 секунд по умолчанию.
  assert.ok(take.durationSec > 0.5 && take.durationSec < 2, `длительность ${take.durationSec}`);

  // Пик совпадает с тем, что подавали (±0.01 — допуск на округление).
  assert.ok(Math.abs(peak(take.signal) - 0.5) < 0.01, `пик ${peak(take.signal)}`);

  // Частота — по переходам через ноль, независимо от устройства.
  const hz = zeroCrossingHz(take.signal, sampleRate);
  assert.ok(Math.abs(hz - 200) < 5, `частота ${hz}`);

  // Форма сигнала не искажена захватом: корреляция с исходным синусом высокая.
  const reference = new Float32Array(take.signal.length);
  for (let i = 0; i < reference.length; i += 1) reference[i] = source(i);
  const r = correlation(take.signal, reference);
  assert.ok(r > 0.99, `корреляция ${r}`);
});

test('симулированная запись превращается в WAV и читается обратно', async () => {
  const sampleRate = 44100;
  const source = sine({ hz: 220, amplitude: 0.4, sampleRate });
  const rec = await recorder.start({ simulated: { fill: source, sampleRate }, seconds: 1 });
  await new Promise((resolve) => { setTimeout(resolve, 600); });
  const take = await rec.stop();

  const payload = recorder.toPayload(take);
  assert.equal(payload.sampleRate, 44100);
  assert.equal(payload.frames, take.signal.length);

  const converted = recordingToWav(payload);
  assert.equal(converted.ok, true, converted.error);
  const decoded = wavDecoder.decodeWav(converted.data.buffer);
  assert.equal(decoded.sampleRate, 44100);
  assert.equal(decoded.channels, 1);
  assert.ok(Math.abs(decoded.audio.length - take.signal.length) <= 1, 'длина не изменилась');

  // WAV не «испортил» сигнал: частота и пик те же.
  assert.ok(Math.abs(zeroCrossingHz(decoded.audio, 44100) - 220) < 6);
  assert.ok(Math.abs(peak(decoded.audio) - 0.4) < 0.02, `пик ${peak(decoded.audio)}`);
});

test('симулированный вход не выдаёт себя за микрофон', () => {
  const signal = new Float32Array(4410).fill(0.1);

  const simulated = takes.recordedTake({ signal, sampleRate: 44100, simulated: true });
  assert.equal(simulated.source, takes.SOURCES.SIMULATED);
  assert.equal(simulated.simulated, true);
  assert.match(simulated.label, /не микрофон|проверка/);
  const described = takes.assertHonest(simulated);
  assert.equal(described.simulated, true);

  // Настоящая запись с микрофона остаётся записью.
  const real = takes.recordedTake({ signal, sampleRate: 44100 });
  assert.equal(real.source, takes.SOURCES.RECORD);
  assert.equal(real.simulated, false);
  assert.equal(real.label, 'запись с микрофона');
  assert.equal(takes.describeTake(real).simulated, false);

  // А подменить одно другим нельзя.
  assert.throws(
    () => takes.assertHonest({ source: takes.SOURCES.RECORD, simulated: true }),
    /нельзя называть записью с микрофона/,
  );
  assert.throws(
    () => takes.assertHonest({ source: takes.SOURCES.SIMULATED, simulated: false }),
    /обязан нести simulated/,
  );
});

test('симулированное устройство: тишина, клиппинг и отмена', async () => {
  // Тишина — это не дубль: главный процесс обязан отказать с причиной.
  const quiet = await recorder.start({ simulated: { fill: () => 0 }, seconds: 1 });
  await new Promise((resolve) => { setTimeout(resolve, 300); });
  const silentTake = await quiet.stop();
  assert.equal(peak(silentTake.signal), 0);
  assert.match(recordingToWav(recorder.toPayload(silentTake)).error, /тишина/);

  // Устройство может отдать больше единицы — захват обязан срезать по ±1.
  const hot = await recorder.start({ simulated: { fill: () => 5 }, seconds: 1 });
  await new Promise((resolve) => { setTimeout(resolve, 300); });
  const hotTake = await hot.stop();
  assert.equal(peak(hotTake.signal), 1, 'значения за пределами ±1 срезаны');

  // Отмена: звука нет, WAV не появляется.
  const cancelled = await recorder.start({ simulated: { fill: () => 0.2 }, seconds: 1 });
  await new Promise((resolve) => { setTimeout(resolve, 120); });
  cancelled.cancel();
  assert.equal(await cancelled.stop(), null);
});

test('симулированный вход без функции сигнала отвергается', async () => {
  await assert.rejects(
    () => recorder.start({ simulated: {}, seconds: 1 }),
    /нужна функция сигнала/,
  );
});
