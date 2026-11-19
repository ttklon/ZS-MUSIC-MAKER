'use strict';
/** Bounded audio transfer; renderer cannot use this channel to read arbitrary files. */
const fs = require('node:fs/promises');
const path = require('node:path');
const { parseWavHeader } = require('../src/core/audio/wav-decode');
const MAX_BYTES = 64 * 1024 * 1024;

async function readMasterAudio(file, roots) {
  if (typeof file !== 'string' || !path.isAbsolute(file) || path.extname(file).toLowerCase() !== '.wav') {
    throw new Error('Нужен абсолютный путь к WAV результата');
  }
  const real = await fs.realpath(file);
  let allowed = false;
  for (const root of roots) {
    let base;
    try { base = await fs.realpath(root); } catch { continue; }
    const relative = path.relative(base, real);
    if (relative && relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative)) allowed = true;
  }
  if (!allowed) throw new Error('Файл вне каталога результатов приложения');
  const handle = await fs.open(real, 'r');
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size < 44 || stat.size > MAX_BYTES) throw new Error('WAV пуст или превышает лимит 64 МБ');
    const buffer = Buffer.alloc(stat.size);
    let offset = 0;
    while (offset < buffer.length) {
      const { bytesRead } = await handle.read(buffer, offset, buffer.length - offset, offset);
      if (!bytesRead) throw new Error('WAV изменился во время чтения');
      offset += bytesRead;
    }
    const header = parseWavHeader(buffer);
    if (header.channels > 2 || ![8, 16, 24, 32, 64].includes(header.bits) ||
        header.sampleRate < 8000 || header.sampleRate > 192000 || !header.dataSize) throw new Error('Неподдерживаемые параметры WAV');
    return { base64: buffer.toString('base64'), mime: 'audio/wav', bytes: buffer.length };
  } finally { await handle.close(); }
}
module.exports = { readMasterAudio, MAX_BYTES };
