'use strict';
/**
 * vocal-service.js — вокальный вход: что известно о микрофоне и как запись
 * превращается в WAV.
 *
 * Вынесено из `beat-service.js`: каналы бита — это IPC и диалоги, а здесь
 * проверка записи. Захват делает окно (Web Audio, `getUserMedia`), поэтому
 * главный процесс не может сказать «микрофон есть» или «микрофона нет» —
 * он проверяет то, что окно принесло, и собирает файл тем же кодировщиком,
 * что пишет бит.
 */

const path = require('node:path');
const fsp = require('node:fs/promises');

const { VOCAL_RECORD_MAX_SEC } = require('../src/core/beat-options');
const { encodeWav } = require('../src/core/audio/wav');

/**
 * Что приложение знает о входе записи.
 *
 * Захват делает окно (Web Audio, `getUserMedia`), а не главный процесс:
 * отдельный native-модуль для этого не нужен, и разрешение спрашивает сам
 * Windows 11. Главный процесс не может проверить наличие микрофона — поэтому
 * он и не утверждает ни «есть», ни «нет»: `recording` значит «попробовать
 * можно, отказ покажет окно».
 *
 * @param {{available?: boolean|null}} [probe] результат проверки из окна, если он есть
 */
function describeInput(probe = {}) {
  const available = probe && typeof probe.available === 'boolean' ? probe.available : null;
  return {
    recording: available !== false,
    available,
    label: available === false
      ? 'микрофон недоступен для окна'
      : 'запись с микрофона: захват делает окно',
    reason: available === false
      ? 'окно не получило доступ к микрофону; доступны WAV-файл и тестовый дубль'
      : 'микрофон используется только по нажатию «Записать дубль»; звук никуда не '
        + 'отправляется и остаётся в памяти приложения',
    simulatedAvailable: true,
    maxSeconds: require('../src/core/beat-options').VOCAL_RECORD_MAX_SEC,
  };
}

/**
 * Собрать WAV из PCM, записанного окном.
 *
 * Страница живёт в контексте изоляции: `Buffer` и файлового API у неё нет,
 * поэтому WAV собирает главный процесс — тем же кодировщиком, что пишет бит.
 * `pcmBase64` — Float32-сэмплы моно, little-endian (как их отдал Web Audio).
 *
 * @param {{pcmBase64?: string, sampleRate?: number, seconds?: number}} payload
 * @returns {{ok: boolean, data?: {buffer: Buffer, seconds: number, sampleRate: number}, error?: string}}
 */
function recordingToWav(payload = {}) {
  const { pcmBase64, sampleRate, seconds } = payload || {};
  if (typeof pcmBase64 !== 'string' || pcmBase64.length < 32) {
    return { ok: false, error: 'запись пуста: окно не передало аудио' };
  }
  const { VOCAL_RECORD_MAX_SEC } = require('../src/core/beat-options');
  const rate = Number(sampleRate);
  if (!Number.isFinite(rate) || rate < 8000 || rate > 192000) {
    return { ok: false, error: 'частота записи вне диапазона 8000…192000 Гц' };
  }
  const raw = Buffer.from(pcmBase64, 'base64');
  if (raw.length < 4 || raw.length % 4 !== 0) {
    return { ok: false, error: 'данные записи повреждены: ожидались Float32-сэмплы' };
  }
  const frames = raw.length / 4;
  const durationSec = frames / rate;
  if (durationSec > VOCAL_RECORD_MAX_SEC + 1) {
    return { ok: false, error: `запись длиннее ${VOCAL_RECORD_MAX_SEC} с — сохраните короче` };
  }
  if (seconds !== undefined && seconds !== null && Math.abs(Number(seconds) - durationSec) > 2) {
    return { ok: false, error: 'длительность записи не совпадает с данными' };
  }
  const signal = new Float32Array(frames);
  for (let i = 0; i < frames; i += 1) signal[i] = raw.readFloatLE(i * 4);
  // Полная тишина — это не дубль: скорее всего микрофон не дал звука.
  let peak = 0;
  for (let i = 0; i < frames; i += 1) peak = Math.max(peak, Math.abs(signal[i]));
  if (peak < 1e-4) {
    return { ok: false, error: 'в записи тишина: проверьте микрофон и уровень входа' };
  }
  const { encodeWav } = require('../src/core/audio/wav');
  return {
    ok: true,
    data: { buffer: encodeWav([signal], rate), seconds: durationSec, sampleRate: rate },
  };
}

/**
 * Сохранить запись с микрофона в файл.
 *
 * «Записью» называется только то, что действительно пришло со входа: данные
 * проверяются (WAV с заголовком RIFF и правдоподобный размер), а не берутся
 * на слово из имени файла.
 *
 * @param {object} params
 * @param {object} params.dialog
 * @param {Function} params.getWindow
 * @param {Function|string} params.musicDir
 * @param {{pcmBase64?: string, sampleRate?: number, seconds?: number, name?: string}} params.payload
 */
async function saveRecording({ dialog, getWindow, musicDir, payload = {} }) {
  const converted = recordingToWav(payload);
  if (!converted.ok) return { ok: false, error: converted.error };
  const { buffer, seconds } = converted.data;
  const base = String((payload && payload.name) || 'vocal-record').replace(/[^\w.-]+/g, '_').slice(0, 80) || 'vocal-record';
  const suggestion = path.join(typeof musicDir === 'function' ? musicDir() : musicDir, `${base}.wav`);
  const { canceled, filePath } = await dialog.showSaveDialog(getWindow() || undefined, {
    title: 'Сохранить запись с микрофона',
    defaultPath: suggestion,
    filters: [{ name: 'WAV', extensions: ['wav'] }],
  });
  if (canceled || !filePath) return { ok: true, data: { path: null, cancelled: true } };
  try {
    await fsp.mkdir(path.dirname(filePath), { recursive: true });
    await fsp.writeFile(filePath, buffer);
    return { ok: true, data: { path: filePath, bytes: buffer.length, seconds, recorded: true } };
  } catch (err) {
    return { ok: false, error: `файл не записан: ${err.message}` };
  }
}

/** Сохранить WAV через диалог. base64 проверяется до записи. */

module.exports = {
  describeInput,
  recordingToWav,
  saveRecording,
};
