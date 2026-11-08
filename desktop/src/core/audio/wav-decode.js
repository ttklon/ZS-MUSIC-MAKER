'use strict';
/**
 * core/audio/wav-decode.js — чтение WAV без зависимостей.
 *
 * Окно берёт one-shot'ы из `data/samples/` прямо с диска, поэтому нужен
 * декодер. Он поддерживает ровно то, что лежит в банке и что пишет сам
 * проект: RIFF/WAVE, PCM 8/16/24/32 и IEEE float 32/64. Всё остальное —
 * понятная ошибка с названием формата, а не тишина: молча подменять сэмпл
 * синтезом (так когда-то делал Python до правки) значит врать в отчёте.
 */

const FORMAT_PCM = 1;
const FORMAT_FLOAT = 3;
const FORMAT_EXTENSIBLE = 0xfffe;

/** Разобрать заголовок, не трогая сэмплы. */
function parseWavHeader(buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 12) {
    throw new Error('WAV: файл короче заголовка');
  }
  if (buffer.toString('ascii', 0, 4) !== 'RIFF' || buffer.toString('ascii', 8, 12) !== 'WAVE') {
    throw new Error('WAV: это не RIFF/WAVE');
  }
  let offset = 12;
  let fmt = null;
  let dataOffset = -1;
  let dataSize = 0;
  while (offset + 8 <= buffer.length) {
    const id = buffer.toString('ascii', offset, offset + 4);
    const size = buffer.readUInt32LE(offset + 4);
    const body = offset + 8;
    if (id === 'fmt ') {
      if (size < 16) throw new Error('WAV: блок fmt короче 16 байт');
      let format = buffer.readUInt16LE(body);
      const channels = buffer.readUInt16LE(body + 2);
      const sampleRate = buffer.readUInt32LE(body + 4);
      const bits = buffer.readUInt16LE(body + 14);
      if (format === FORMAT_EXTENSIBLE) {
        // WAVE_FORMAT_EXTENSIBLE: настоящий формат лежит в первых двух байтах GUID.
        if (size < 40) throw new Error('WAV: extensible-заголовок короче 40 байт');
        format = buffer.readUInt16LE(body + 24);
      }
      fmt = { format, channels, sampleRate, bits };
    } else if (id === 'data') {
      dataOffset = body;
      dataSize = Math.min(size, buffer.length - body);
    }
    // Чанки выравниваются по чётной границе.
    offset = body + size + (size % 2);
    if (id === 'data') break;
  }
  if (!fmt) throw new Error('WAV: нет блока fmt ');
  if (dataOffset < 0) throw new Error('WAV: нет блока data');
  if (![FORMAT_PCM, FORMAT_FLOAT].includes(fmt.format)) {
    throw new Error(`WAV: формат ${fmt.format} не поддерживается (нужен PCM или float)`);
  }
  if (!fmt.channels) throw new Error('WAV: ноль каналов');
  return { ...fmt, dataOffset, dataSize };
}

function readSample(buffer, offset, header) {
  if (header.format === FORMAT_FLOAT) {
    return header.bits === 64 ? buffer.readDoubleLE(offset) : buffer.readFloatLE(offset);
  }
  if (header.bits === 8) return (buffer.readUInt8(offset) - 128) / 128;
  if (header.bits === 16) return buffer.readInt16LE(offset) / 32768;
  if (header.bits === 24) return buffer.readIntLE(offset, 3) / 8388608;
  if (header.bits === 32) return buffer.readInt32LE(offset) / 2147483648;
  throw new Error(`WAV: ${header.bits} бит на сэмпл не поддерживается`);
}

/**
 * Прочитать WAV в моно float32.
 *
 * @param {Buffer} buffer
 * @param {{sampleRate?: number}} [options] — целевая частота (ресемплинг линейный)
 * @returns {{audio: Float32Array, sampleRate: number, channels: number, bits: number, durationSec: number}}
 */
function decodeWav(buffer, { sampleRate = 44100 } = {}) {
  const header = parseWavHeader(buffer);
  const bytes = header.bits / 8;
  const frames = Math.floor(header.dataSize / (bytes * header.channels));
  const channels = new Float32Array(frames);
  for (let frame = 0; frame < frames; frame += 1) {
    let sum = 0;
    for (let channel = 0; channel < header.channels; channel += 1) {
      const index = header.dataOffset + (frame * header.channels + channel) * bytes;
      if (index + bytes > buffer.length) break;
      sum += readSample(buffer, index, header);
    }
    channels[frame] = sum / header.channels;
  }

  let audio = channels;
  if (header.sampleRate !== sampleRate && frames > 1) {
    // Линейная передискретизация: сэмпл нужен для ритма, а не мастеринга.
    const target = Math.max(1, Math.round((frames * sampleRate) / header.sampleRate));
    audio = new Float32Array(target);
    for (let i = 0; i < target; i += 1) {
      const position = (i * (frames - 1)) / Math.max(1, target - 1);
      const low = Math.floor(position);
      const high = Math.min(frames - 1, low + 1);
      audio[i] = channels[low] + (channels[high] - channels[low]) * (position - low);
    }
  }

  return {
    audio,
    sampleRate,
    sourceSampleRate: header.sampleRate,
    channels: header.channels,
    bits: header.bits,
    durationSec: audio.length / sampleRate,
  };
}

/** Прочитать файл с диска через переданное файловое API. */
function readWavFile(fileSystem, filePath, options) {
  const read = fileSystem.readFileBinary || fileSystem.readFileBuffer;
  if (typeof read !== 'function') throw new Error('нет файлового API для чтения WAV');
  const buffer = read(filePath);
  return decodeWav(buffer, options);
}

module.exports = { decodeWav, parseWavHeader, readWavFile, FORMAT_PCM, FORMAT_FLOAT };
