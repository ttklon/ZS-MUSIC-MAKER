'use strict';
/**
 * core/audio/wav.js — запись WAV без зависимостей.
 *
 * Замена `soundfile.write(..., subtype="PCM_16")`, которым пользуется
 * Python-движок: тот же формат (RIFF, PCM 16 бит, interleaved), только
 * заголовок собирается здесь. Float-32 тоже поддерживается — им удобно
 * проверять движок в тестах, не теряя точность на 16 битах.
 */

const FORMAT_PCM = 1;
const FORMAT_FLOAT = 3;

/**
 * Собрать WAV-буфер.
 *
 * @param {Float32Array[]} channels — каналы одинаковой длины
 * @param {number} sampleRate
 * @param {{float32?: boolean}} [options]
 * @returns {Buffer}
 */
function encodeWav(channels, sampleRate, { float32 = false } = {}) {
  if (!Array.isArray(channels) || channels.length === 0) {
    throw new Error('encodeWav: нужен хотя бы один канал');
  }
  const frames = channels[0].length;
  for (const channel of channels) {
    if (channel.length !== frames) throw new Error('encodeWav: каналы разной длины');
  }
  const channelCount = channels.length;
  const bitsPerSample = float32 ? 32 : 16;
  const bytesPerSample = bitsPerSample / 8;
  const blockAlign = channelCount * bytesPerSample;
  const dataSize = frames * blockAlign;
  const headerSize = 44;
  const buffer = Buffer.alloc(headerSize + dataSize);

  buffer.write('RIFF', 0, 'ascii');
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write('WAVE', 8, 'ascii');
  buffer.write('fmt ', 12, 'ascii');
  buffer.writeUInt32LE(16, 16); // размер fmt-блока
  buffer.writeUInt16LE(float32 ? FORMAT_FLOAT : FORMAT_PCM, 20);
  buffer.writeUInt16LE(channelCount, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * blockAlign, 28);
  buffer.writeUInt16LE(blockAlign, 32);
  buffer.writeUInt16LE(bitsPerSample, 34);
  buffer.write('data', 36, 'ascii');
  buffer.writeUInt32LE(dataSize, 40);

  let offset = headerSize;
  for (let frame = 0; frame < frames; frame += 1) {
    for (let channel = 0; channel < channelCount; channel += 1) {
      const value = channels[channel][frame];
      if (float32) {
        buffer.writeFloatLE(value, offset);
      } else {
        // 16 бит: клиппинг, а не «заворот» на переполнении.
        const clamped = Math.max(-1, Math.min(1, value));
        buffer.writeInt16LE(Math.round(clamped * 32767), offset);
      }
      offset += bytesPerSample;
    }
  }
  return buffer;
}

/** Размер готового файла в байтах (для отчёта без записи на диск). */
function wavSize(frames, channelCount, { float32 = false } = {}) {
  return 44 + frames * channelCount * (float32 ? 4 : 2);
}

module.exports = { encodeWav, wavSize, FORMAT_PCM, FORMAT_FLOAT };
