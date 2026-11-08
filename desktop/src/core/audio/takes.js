'use strict';
/**
 * core/audio/takes.js — вокальные дубли: что делать, когда микрофона нет.
 *
 * Задача: окно должно уметь работать с вокальной дорожкой и без записи с
 * микрофона. Поэтому здесь три честно названных источника:
 *
 *  - `file`    — пользователь приносит WAV (своя запись с телефона, диктофона,
 *                любой DAW). Это настоящая запись, просто сделанная не здесь;
 *  - `synth`   — вокальная линия, синтезированная движком `vocal.js`;
 *  - `test`    — «тестовый дубль»: он **не** выдаёт себя за микрофон.
 *                В отчёте у него `source: 'test'` и `simulated: true`, а в
 *                интерфейсе — подпись «тестовый, не с микрофона».
 *
 * Зачем третий режим вообще: без него нельзя ни проверить вокальную цепочку
 * (чистка, эффекты, микс), ни прогнать её в CI, где микрофона физически нет.
 * Подмена настоящей записи тестовой — это ложь в отчёте, и она запрещена:
 * `describeTake` всегда возвращает `simulated` и `label`, а `assertHonest`
 * падает, если тестовый дубль выдан за запись.
 */

const vocal = require('./vocal');
const wavDecoder = require('./wav-decode');
const dsp = require('./dsp');

/** Что это за дубль. */
const SOURCES = {
  FILE: 'file',
  SYNTH: 'synth',
  TEST: 'test',
};

const LABELS = {
  file: 'запись из файла',
  synth: 'синтезированный вокал',
  test: 'тестовый дубль (не с микрофона)',
};

/** Микрофон в этом окружении недоступен — так и говорим. */
function microphoneStatus({ platform = process.platform, hasDevices = false } = {}) {
  if (hasDevices) {
    return { ok: true, recording: true, reason: null, label: 'микрофон найден' };
  }
  return {
    ok: false,
    recording: false,
    reason: 'входных аудиоустройств не найдено: запись с микрофона недоступна, '
      + 'используйте файл или тестовый дубль',
    label: 'микрофон недоступен',
    platform,
  };
}

/**
 * Разобрать WAV пользователя в моно Float32.
 *
 * @param {Buffer} buffer
 * @param {number} [targetRate] частота, к которой привести (по умолчанию как есть)
 * @returns {{signal: Float32Array, sampleRate: number, durationSec: number, channels: number}}
 */
function loadTake(buffer, targetRate = null) {
  // `decodeWav` отдаёт уже моно-микс (`audio`) и число каналов отдельно.
  const decoded = wavDecoder.decodeWav(buffer);
  const rate = decoded.sampleRate;
  const signal = targetRate && targetRate !== rate ? resample(decoded.audio, rate, targetRate) : decoded.audio;
  return {
    signal,
    sampleRate: targetRate || rate,
    durationSec: signal.length / (targetRate || rate),
    channels: decoded.channels,
    source: SOURCES.FILE,
    simulated: false,
    label: LABELS.file,
    note: null,
  };
}

/** Линейная передискретизация: для вокала в миксе этого достаточно. */
function resample(signal, from, to) {
  if (from === to) return signal;
  const ratio = to / from;
  const length = Math.max(1, Math.round(signal.length * ratio));
  const out = new Float32Array(length);
  for (let i = 0; i < length; i += 1) {
    const position = i / ratio;
    const left = Math.floor(position);
    const right = Math.min(signal.length - 1, left + 1);
    const frac = position - left;
    out[i] = signal[left] * (1 - frac) + signal[right] * frac;
  }
  return out;
}

/**
 * Тестовый дубль: правдоподобная «запись с микрофона», сделанная из синтеза.
 *
 * Что делает её похожей на запись: комнатный шум, неровный уровень,
 * лёгкий сдвиг высоты и дыхание перед фразой. Что она не делает: не
 * притворяется настоящей — `simulated: true` едет дальше в отчёт.
 *
 * @param {object} params
 * @param {string} [params.text]      что «поётся»
 * @param {number} [params.seconds]   длительность
 * @param {number} [params.seed]
 * @param {number} [params.sr]
 * @param {number[]} [params.midiNotes]
 * @returns {object}
 */
function testTake({ text = 'тестовый дубль вокала для проверки цепочки', seconds = 8, seed = 7, sr = 44100, midiNotes = [57, 59, 60, 62] } = {}) {
  const random = vocal.rng(seed);
  const sung = vocal.singLine({ text, midiNotes, sr, seed, style: 'sung' });
  const wanted = Math.max(sr, Math.round(seconds * sr));

  // Один и тот же текст повторяется, пока не наберётся нужная длина:
  // так дубль не обрывается на середине фразы.
  const out = new Float32Array(wanted);
  let offset = 0;
  let pass = 0;
  while (offset < wanted) {
    const line = pass === 0 ? sung.signal : vocal.singLine({
      text, midiNotes: midiNotes.map((n) => (pass % 2 ? n + 2 : n)), sr, seed: seed + pass,
    }).signal;
    const copy = Math.min(line.length, wanted - offset);
    out.set(line.subarray(0, copy), offset);
    offset += copy;
    // Пауза на дыхание между фразами.
    offset += Math.round(0.18 * sr);
    pass += 1;
  }

  // Комнатный шум: −54 dBFS, как у тихой комнаты с обычным микрофоном.
  const noiseLevel = 10 ** (-54 / 20);
  for (let i = 0; i < out.length; i += 1) out[i] = out[i] * 0.85 + random() * noiseLevel;

  // Неровный уровень по фразам: живая запись никогда не ровная.
  const phrase = Math.round(1.6 * sr);
  for (let start = 0; start < out.length; start += phrase) {
    const gain = 0.85 + random() * 0.15;
    const end = Math.min(out.length, start + phrase);
    for (let i = start; i < end; i += 1) out[i] *= gain;
  }

  // Микрофон режет низ: 70 Гц снизу — слышимая, но не портящая голос правка.
  const filtered = dsp.highpass(out, 70, sr, 2);
  return {
    signal: dsp.peakNormalize(filtered, 0.8),
    sampleRate: sr,
    durationSec: wanted / sr,
    source: SOURCES.TEST,
    simulated: true,
    label: LABELS.test,
    note: 'сгенерирован движком: микрофон в этом окружении недоступен',
  };
}

/**
 * Синтезированный вокальный дубль заданной длины.
 *
 * @param {object} params
 * @returns {object}
 */
function synthTake({ text = 'я читаю твой трек', seconds = 8, seed = 7, sr = 44100, midiNotes = [57, 60, 62, 64], style = 'sung' } = {}) {
  const random = vocal.rng(seed);
  const wanted = Math.max(sr, Math.round(seconds * sr));
  const out = new Float32Array(wanted);
  let offset = 0;
  let pass = 0;
  while (offset < wanted) {
    const line = vocal.singLine({
      text, midiNotes: midiNotes.map((n) => n + (pass % 3)), sr, seed: seed + pass, style,
    }).signal;
    const copy = Math.min(line.length, wanted - offset);
    out.set(line.subarray(0, copy), offset);
    offset += copy + Math.round(0.12 * sr);
    pass += 1;
  }
  // Тот же шумовой пол, что у тестового дубля: иначе синтез звучит «в вакууме».
  const noiseLevel = 10 ** (-60 / 20);
  for (let i = 0; i < out.length; i += 1) out[i] += random() * noiseLevel;
  return {
    signal: dsp.peakNormalize(out, 0.85),
    sampleRate: sr,
    durationSec: wanted / sr,
    source: SOURCES.SYNTH,
    simulated: false,
    label: LABELS.synth,
    note: 'голос синтезирован формантным движком, не записан',
  };
}

/**
 * Описание дубля для отчёта и интерфейса.
 *
 * @param {object} take результат `loadTake`/`testTake`/`synthTake`
 * @returns {{source: string, simulated: boolean, label: string, durationSec: number,
 *            sampleRate: number, note: string|null}}
 */
function describeTake(take = {}) {
  const source = take.source || SOURCES.FILE;
  const simulated = source === SOURCES.TEST || take.simulated === true;
  return {
    source,
    simulated,
    label: take.label || LABELS[source] || source,
    durationSec: Number(take.durationSec || 0),
    sampleRate: Number(take.sampleRate || 0),
    note: take.note || null,
  };
}

/**
 * Проверка честности: тестовый дубль не должен называться записью.
 *
 * @param {object} take
 * @returns {object} то же описание
 * @throws {Error} если тестовый дубль подан как запись с микрофона
 */
function assertHonest(take) {
  const declared = take && take.simulated === true;
  const source = take && take.source;
  if (declared && source !== SOURCES.TEST) {
    throw new Error('дубль помечен как тестовый, но источник указан как запись');
  }
  if (source === SOURCES.TEST && !declared) {
    throw new Error('тестовый дубль обязан нести simulated: true');
  }
  // `describeTake` всегда выставляет `simulated` по источнику, поэтому
  // проверять его результат бессмысленно: смотреть надо исходные поля.
  return describeTake(take);
}

/** Имя файла дубля: без путей и без чужих символов. */
function takeFileName(source = SOURCES.TEST, seconds = 8, seed = 7) {
  const kind = Object.values(SOURCES).includes(source) ? source : 'take';
  const base = ['vocal', kind, `${Math.max(1, Math.round(seconds))}s`, `seed${Math.max(0, Math.round(seed))}`];
  return `${base.join('-').replace(/[^\w.-]+/g, '_')}.wav`;
}

module.exports = {
  SOURCES,
  LABELS,
  microphoneStatus,
  loadTake,
  testTake,
  synthTake,
  describeTake,
  assertHonest,
  takeFileName,
  resample,
};
