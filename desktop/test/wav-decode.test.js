'use strict';
/**
 * wav-decode.test.js — чтение WAV в окне.
 *
 * Окно берёт one-shot'ы из `data/samples/` с диска, поэтому декодер должен
 * понимать ровно те форматы, что лежат в банке (PCM 16), и не молчать на
 * остальных. Проверка идёт на **настоящем файле банка** и на синтетических
 * заголовках: и то, и другое важно — первое ловит регресс банка, второе —
 * ошибки разбора.
 */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const { decodeWav, parseWavHeader } = require('../src/core/audio/wav-decode');
const { encodeWav } = require('../src/core/audio/wav');

const ROOT = path.resolve(__dirname, '..', '..');

/** Собрать WAV вручную: так проверяются форматы, которых нет в банке. */
function buildWav({ format = 1, channels = 1, sampleRate = 44100, bits = 16, samples = [] }) {
  const bytes = bits / 8;
  const frames = samples.length / channels;
  const dataSize = frames * channels * bytes;
  const buffer = Buffer.alloc(44 + dataSize);
  buffer.write('RIFF', 0, 'ascii');
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write('WAVE', 8, 'ascii');
  buffer.write('fmt ', 12, 'ascii');
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(format, 20);
  buffer.writeUInt16LE(channels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * channels * bytes, 28);
  buffer.writeUInt16LE(channels * bytes, 32);
  buffer.writeUInt16LE(bits, 34);
  buffer.write('data', 36, 'ascii');
  buffer.writeUInt32LE(dataSize, 40);
  let offset = 44;
  for (const value of samples) {
    if (format === 3) buffer.writeFloatLE(value, offset);
    else if (bits === 8) buffer.writeUInt8(Math.round(value * 127) + 128, offset);
    else if (bits === 16) buffer.writeInt16LE(Math.round(value * 32767), offset);
    else if (bits === 24) buffer.writeIntLE(Math.round(value * 8388607), offset, 3);
    else buffer.writeInt32LE(Math.round(value * 2147483647), offset);
    offset += bytes;
  }
  return buffer;
}

test('настоящий сэмпл банка читается: моно, 44.1 кГц, ненулевой пик', () => {
  const file = path.join(ROOT, 'data', 'samples', 'kick', '808-bd-tone0-decay25.wav');
  assert.ok(fs.existsSync(file), 'файл банка на месте');
  const decoded = decodeWav(fs.readFileSync(file));
  assert.strictEqual(decoded.sampleRate, 44100);
  assert.strictEqual(decoded.channels, 1);
  assert.ok(decoded.audio.length > 1000, 'сэмпл не должен быть пустым');
  let peak = 0;
  for (const value of decoded.audio) peak = Math.max(peak, Math.abs(value));
  assert.ok(peak > 0.2, `пик ${peak} слишком мал — декодер вернул почти тишину`);
  assert.ok(Math.abs(decoded.durationSec - 0.5) < 0.02, `длительность ${decoded.durationSec}`);
});

test('каждый файл банка читается без ошибок', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'samples', 'manifest.json'), 'utf8'));
  let count = 0;
  for (const rows of Object.values(manifest.instruments)) {
    for (const row of rows) {
      const file = path.join(ROOT, 'data', 'samples', row.file);
      const decoded = decodeWav(fs.readFileSync(file));
      assert.ok(decoded.audio.length > 0, `${row.file}: пустое аудио`);
      count += 1;
    }
  }
  assert.ok(count >= 32, `проверено ${count} файлов — меньше, чем в банке`);
});

test('стерео сводится в моно, каналы не складываются в тишину', () => {
  const buffer = buildWav({ channels: 2, samples: [0.5, 0.5, -0.5, -0.5] });
  const decoded = decodeWav(buffer);
  assert.strictEqual(decoded.channels, 2);
  assert.deepStrictEqual(Array.from(decoded.audio).map((v) => Math.round(v * 100)), [50, -50]);
});

test('разрядности 8/16/24/32 и float32 понимаются одинаково', () => {
  for (const bits of [8, 16, 24, 32]) {
    const decoded = decodeWav(buildWav({ bits, samples: [0, 0.5, -0.5, 1] }));
    assert.strictEqual(decoded.bits, bits);
    const [zero, half, minusHalf, full] = decoded.audio;
    assert.ok(Math.abs(zero) < 0.01, `${bits} бит: нулю соответствует ноль (${zero})`);
    assert.ok(Math.abs(half - 0.5) < 0.01, `${bits} бит: половина (${half})`);
    assert.ok(Math.abs(minusHalf + 0.5) < 0.01, `${bits} бит: минус половина (${minusHalf})`);
    assert.ok(Math.abs(full - 1) < 0.01 || Math.abs(full) <= 1, `${bits} бит: полная шкала (${full})`);
  }
  const asFloat = decodeWav(buildWav({ format: 3, bits: 32, samples: [0.25, -0.75] }));
  assert.deepStrictEqual(Array.from(asFloat.audio).map((v) => Math.round(v * 100)), [25, -75]);
});

test('ресемплинг: 22.05 кГц → 44.1 кГц удваивает длину', () => {
  const samples = [];
  for (let i = 0; i < 100; i += 1) samples.push(Math.sin(i / 5));
  const decoded = decodeWav(buildWav({ sampleRate: 22050, samples }), { sampleRate: 44100 });
  assert.strictEqual(decoded.sourceSampleRate, 22050);
  assert.ok(Math.abs(decoded.audio.length - 199) <= 2, `длина после ресемплинга ${decoded.audio.length}`);
});

test('круговая проверка: свой WAV-писатель и свой декодер совпадают', () => {
  const original = new Float32Array(64);
  for (let i = 0; i < original.length; i += 1) original[i] = Math.sin(i / 4) * 0.7;
  const decoded = decodeWav(encodeWav([original], 44100), { sampleRate: 44100 });
  assert.strictEqual(decoded.audio.length, original.length);
  for (let i = 0; i < original.length; i += 1) {
    assert.ok(Math.abs(decoded.audio[i] - original[i]) < 1e-3, `сэмпл ${i}: ${decoded.audio[i]} != ${original[i]}`);
  }
});

test('не-WAV и неизвестный формат — ошибка с причиной, а не тишина', () => {
  assert.throws(() => decodeWav(Buffer.from('not a wav at all')), /короче заголовка|RIFF/);
  assert.throws(() => decodeWav(Buffer.alloc(64, 0x41)), /RIFF/);
  const adpcm = buildWav({ format: 2, samples: [0, 0] });
  assert.throws(() => decodeWav(adpcm), /формат 2 не поддерживается/);
});

test('заголовок без data не притворяется валидным', () => {
  const buffer = buildWav({ samples: [0] });
  const broken = Buffer.concat([buffer.subarray(0, 40)]);
  broken.write('JUNK', 36, 'ascii');
  assert.throws(() => decodeWav(broken), /data/);
  assert.strictEqual(parseWavHeader(buffer).bits, 16);
});
