'use strict';
/**
 * test/recorder.test.js — запись дубля с микрофона без микрофона.
 *
 * Захват проверяется на двойниках `navigator.mediaDevices` и `AudioContext`:
 * в CI ни устройства, ни разрешения нет. Важно не «звук похож на голос»
 * (это дело `takes.js`), а честность: источник называет себя записью только
 * тогда, когда данные пришли со входа, а отказ доступа даёт причину, а не
 * тихую подмену синтезом.
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const recorder = require('../src/sections/recorder');
const {
  startRecording, DEFAULT_SECONDS, MAX_SECONDS,
} = recorder;
const wav = require('../src/core/audio/wav');
const wavDecoder = require('../src/core/audio/wav-decode');
const { recordingToWav } = require('../electron/beat-service');

/** Двойник `navigator.mediaDevices`. */
function fakeDevices({ fail = null, tracks = 1 } = {}) {
  const list = Array.from({ length: tracks }, () => ({
    stopped: false,
    stop() { this.stopped = true; },
  }));
  return {
    list,
    asked: null,
    async getUserMedia(constraints) {
      this.asked = constraints;
      if (fail) {
        const error = new Error('нет доступа');
        error.name = fail;
        throw error;
      }
      return { getTracks: () => list };
    },
  };
}

/** Двойник `AudioContext` с управляемым процессором. */
function fakeAudio({ sampleRate = 48000 } = {}) {
  const processor = {
    onaudioprocess: null,
    connected: false,
    connect() { this.connected = true; },
    disconnect() { this.connected = false; },
  };
  let context = null;
  class Ctx {
    constructor() {
      this.sampleRate = sampleRate;
      this.closed = false;
      context = this;
    }

    createMediaStreamSource() {
      return { connect() {}, disconnect() {} };
    }

    createScriptProcessor() {
      return processor;
    }

    get destination() {
      return {};
    }

    close() { this.closed = true; }
  }
  return { Ctx, processor, get context() { return context; } };
}

/** Скормить «микрофону» куски сигнала. */
function feed(processor, chunks) {
  for (const chunk of chunks) {
    processor.onaudioprocess({ inputBuffer: { getChannelData: () => chunk } });
  }
}

test('запись отдаёт буфер и закрывает микрофон', async () => {
  const devices = fakeDevices();
  const audio = fakeAudio();
  const rec = await startRecording({ mediaDevices: devices, AudioContext: audio.Ctx, seconds: 5 });

  feed(audio.processor, [new Float32Array(128).fill(0.5), new Float32Array(128).fill(-0.5)]);
  const take = await rec.stop();

  assert.equal(take.source, 'record');
  assert.equal(take.simulated, false);
  assert.equal(take.label, 'запись с микрофона');
  assert.equal(take.signal.length, 256);
  assert.equal(take.sampleRate, 48000);
  // Микрофон не должен оставаться включённым после «Стоп».
  assert.equal(devices.list[0].stopped, true);
  assert.equal(audio.context.closed, true);
  assert.equal(audio.processor.connected, false);
  // Просим моно и без «улучшателей»: они съедают тихие концы фраз.
  assert.equal(devices.asked.audio.channelCount, 1);
  assert.equal(devices.asked.audio.echoCancellation, false);
});

test('доступ запрещён — причина названа, подмены нет', async () => {
  const devices = fakeDevices({ fail: 'NotAllowedError' });
  await assert.rejects(
    () => startRecording({ mediaDevices: devices, AudioContext: fakeAudio().Ctx }),
    /доступ к микрофону запрещён/,
  );

  const missing = fakeDevices({ fail: 'NotFoundError' });
  await assert.rejects(
    () => startRecording({ mediaDevices: missing, AudioContext: fakeAudio().Ctx }),
    /микрофон не найден/,
  );

  // Окно без доступа к устройствам записи тоже говорит причину.
  await assert.rejects(
    () => startRecording({ mediaDevices: null, AudioContext: fakeAudio().Ctx }),
    /нет доступа к устройствам/,
  );
});

test('отмена записи не отдаёт звук', async () => {
  const devices = fakeDevices();
  const audio = fakeAudio();
  const rec = await startRecording({ mediaDevices: devices, AudioContext: audio.Ctx });
  feed(audio.processor, [new Float32Array(64).fill(0.3)]);

  rec.cancel();
  assert.equal(await rec.stop(), null, 'после отмены дубля нет');
  assert.equal(devices.list[0].stopped, true);
});

test('длительность записи ограничена', async () => {
  const devices = fakeDevices();
  const rec = await startRecording({
    mediaDevices: devices, AudioContext: fakeAudio().Ctx, seconds: 999,
  });
  assert.equal(rec.seconds, MAX_SECONDS);
  rec.cancel();

  const byDefault = await startRecording({ mediaDevices: fakeDevices(), AudioContext: fakeAudio().Ctx });
  assert.equal(byDefault.seconds, DEFAULT_SECONDS);
  byDefault.cancel();
});

test('запись превращается в WAV, который читается обратно', async () => {
  const devices = fakeDevices();
  const audio = fakeAudio({ sampleRate: 44100 });
  const rec = await startRecording({ mediaDevices: devices, AudioContext: audio.Ctx });
  // Полусекунды синуса достаточно, чтобы проверить формат.
  const chunk = new Float32Array(22050);
  for (let i = 0; i < chunk.length; i += 1) chunk[i] = 0.3 * Math.sin((2 * Math.PI * 220 * i) / 44100);
  feed(audio.processor, [chunk]);

  const take = await rec.stop();
  // Как в окне: страница отдаёт PCM, WAV собирает главный процесс.
  const payload = recorder.toPayload(take);
  assert.equal(typeof payload.pcmBase64, 'string');
  assert.equal(payload.frames, take.signal.length);

  const converted = recordingToWav(payload);
  assert.equal(converted.ok, true, converted.error);
  assert.equal(converted.data.buffer.toString('ascii', 0, 4), 'RIFF');

  const decoded = wavDecoder.decodeWav(converted.data.buffer);
  assert.equal(decoded.sampleRate, 44100);
  assert.equal(decoded.channels, 1);
  assert.ok(decoded.audio.length >= 22000, `сэмплов: ${decoded.audio.length}`);

  // Тишина — это не дубль: скорее всего микрофон не дал звука.
  const silent = new Float32Array(4096);
  const silentPayload = recorder.toPayload({ signal: silent, sampleRate: 44100, durationSec: 0.09 });
  assert.match(recordingToWav(silentPayload).error, /тишина/);
  // Пустые данные и мусорная частота тоже отвергаются с причиной.
  assert.match(recordingToWav({ pcmBase64: '' }).error, /пуста/);
  assert.match(recordingToWav({ ...payload, sampleRate: 10 }).error, /частота/);
  // WAV от этого кодировщика не пустой и читается обратно (сверка с движком).
  assert.ok(wav.encodeWav([silent], 44100).length > 44);
});
