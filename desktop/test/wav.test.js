'use strict';
/**
 * wav.test.js — WAV-писатель без зависимостей.
 *
 * Заголовок проверяется побайтово: если поле встанет не на своё место, ни один
 * плеер не откроет файл, а глазами это не видно. PCM 16 бит — формат, которым
 * пишет Python-версия (`subtype="PCM_16"`), float32 — для тестов движка.
 */

const test = require('node:test');
const assert = require('node:assert');

const { encodeWav, wavSize } = require('../src/core/audio/wav');

function readHeader(buffer) {
  return {
    riff: buffer.toString('ascii', 0, 4),
    riffSize: buffer.readUInt32LE(4),
    wave: buffer.toString('ascii', 8, 12),
    fmt: buffer.toString('ascii', 12, 16),
    fmtSize: buffer.readUInt32LE(16),
    format: buffer.readUInt16LE(20),
    channels: buffer.readUInt16LE(22),
    sampleRate: buffer.readUInt32LE(24),
    byteRate: buffer.readUInt32LE(28),
    blockAlign: buffer.readUInt16LE(32),
    bits: buffer.readUInt16LE(34),
    data: buffer.toString('ascii', 36, 40),
    dataSize: buffer.readUInt32LE(40),
  };
}

test('заголовок PCM 16 бит: RIFF/WAVE/fmt/data на своих местах', () => {
  const left = Float32Array.from([0.0, 0.5, -0.5, 1.0]);
  const right = Float32Array.from([0.0, -0.5, 0.5, -1.0]);
  const buffer = encodeWav([left, right], 44100);
  const header = readHeader(buffer);

  assert.strictEqual(header.riff, 'RIFF');
  assert.strictEqual(header.wave, 'WAVE');
  assert.strictEqual(header.fmt, 'fmt ');
  assert.strictEqual(header.data, 'data');
  assert.strictEqual(header.fmtSize, 16);
  assert.strictEqual(header.format, 1, 'PCM, а не IEEE float');
  assert.strictEqual(header.channels, 2);
  assert.strictEqual(header.sampleRate, 44100);
  assert.strictEqual(header.bits, 16);
  assert.strictEqual(header.blockAlign, 4);
  assert.strictEqual(header.byteRate, 44100 * 4);
  assert.strictEqual(header.dataSize, 4 * 4);
  assert.strictEqual(header.riffSize, buffer.length - 8);
  assert.strictEqual(buffer.length, wavSize(4, 2));
});

test('сэмплы: клиппинг вместо заворота, interleaved L/R', () => {
  const buffer = encodeWav([Float32Array.from([0.5]), Float32Array.from([-0.5])], 48000);
  assert.strictEqual(buffer.readInt16LE(44), Math.round(0.5 * 32767));
  // −0.5·32767 = −16383.5: Math.round тянет к плюс бесконечности, поэтому −16383.
  assert.strictEqual(buffer.readInt16LE(46), -16383);
  const loud = encodeWav([Float32Array.from([3.0, -3.0])], 48000);
  assert.strictEqual(loud.readInt16LE(44), 32767, 'перегруз должен ограничиваться, а не заворачиваться');
  assert.strictEqual(loud.readInt16LE(46), -32767);
});

test('float32: формат 3, 32 бита, значения без квантования', () => {
  const buffer = encodeWav([Float32Array.from([0.123456])], 44100, { float32: true });
  const header = readHeader(buffer);
  assert.strictEqual(header.format, 3);
  assert.strictEqual(header.bits, 32);
  assert.strictEqual(header.blockAlign, 4);
  assert.ok(Math.abs(buffer.readFloatLE(44) - 0.123456) < 1e-6);
  assert.strictEqual(buffer.length, wavSize(1, 1, { float32: true }));
});

test('ошибки входа объясняются, а не молчат', () => {
  assert.throws(() => encodeWav([], 44100), /хотя бы один канал/);
  assert.throws(
    () => encodeWav([new Float32Array(4), new Float32Array(3)], 44100),
    /каналы разной длины/,
  );
});
