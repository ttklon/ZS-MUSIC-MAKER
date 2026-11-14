'use strict';
/**
 * sections/recorder.js — запись дубля с микрофона в окне.
 *
 * Почему захват живёт в окне, а не в главном процессе: `getUserMedia` есть
 * только у страницы (Chromium внутри Electron), отдельный native-модуль для
 * этого не нужен, и разрешение на микрофон спрашивает сам Windows 11 — то
 * есть человек видит, что происходит.
 *
 * Честность записи:
 *  - это действительно микрофон (`source: 'record'`), а не тестовый дубль;
 *  - если доступа нет, окно говорит причину и не подставляет синтез;
 *  - байты никуда не уходят: только в память окна и (по кнопке) в WAV-файл.
 *
 * Модуль не обращается к DOM сам: `start`/`stop` получают `mediaDevices` и
 * `AudioContext` аргументами, поэтому его проверяет обычный `node --test`.
 */

/** Сколько секунд пишем по умолчанию и максимум (совпадает с beat-options). */
const DEFAULT_SECONDS = 20;
const MAX_SECONDS = 60;

/**
 * Откуда берётся звук.
 *
 * Обычный путь — `getUserMedia` (настоящий микрофон). Второй транспорт —
 * проверочный: тот же самый код записи получает сэмплы из функции, а не из
 * устройства. Это нужно, чтобы сквозной путь «захват → PCM → WAV → микс»
 * прогонялся без железа, но при этом ничего не выдавалось за микрофон:
 * телефонная метка `source: 'simulated-device'` едет в отчёт.
 */

/** Симулированный вход: сигнал считается функцией, а не приходит с устройства. */
const SIMULATED_SOURCE = 'simulated-device';

/**
 * Симулированное устройство записи.
 *
 * Отдаёт ровно то, что вернул бы микрофон: поток с одной дорожкой и
 * `getUserMedia`. Звук — `fill(chunkIndex)` в диапазоне −1…1.
 *
 * @param {{fill: Function, sampleRate?: number}} params
 * @returns {{mediaDevices: object, AudioContext: Function, stopDevice: Function}}
 */
function simulatedDevice({ fill, sampleRate = 48000 } = {}) {
  if (typeof fill !== 'function') throw new Error('симулированному входу нужна функция сигнала');
  const tracks = [];
  let processor = null;
  let closed = false;
  let chunk = 0;

  class SimulatedContext {
    constructor() {
      this.sampleRate = sampleRate;
    }

    createMediaStreamSource() {
      return { connect() {}, disconnect() {} };
    }

    createScriptProcessor() {
      const self = this;
      processor = {
        onaudioprocess: null,
        connect() {},
        disconnect() {},
      };
      // «Устройство» само отдаёт блоки: 10 мс звука за шаг.
      const step = Math.max(1, Math.round(sampleRate / 100));
      this._timer = setInterval(() => {
        if (closed || !processor || typeof processor.onaudioprocess !== 'function') return;
        const block = new Float32Array(step);
        for (let i = 0; i < step; i += 1) {
          const value = Number(fill(chunk * step + i));
          block[i] = Number.isFinite(value) ? Math.max(-1, Math.min(1, value)) : 0;
        }
        chunk += 1;
        processor.onaudioprocess({ inputBuffer: { getChannelData: () => block } });
      }, 10);
      void self;
      return processor;
    }

    get destination() {
      return {};
    }

    close() {
      closed = true;
      clearInterval(this._timer);
    }
  }

  return {
    mediaDevices: {
      async getUserMedia() {
        const track = {
          stopped: false,
          stop() { this.stopped = true; },
        };
        tracks.push(track);
        return { getTracks: () => tracks };
      },
    },
    AudioContext: SimulatedContext,
    stopDevice() {
      closed = true;
      clearInterval(processor && processor._timer);
    },
    get tracks() {
      return tracks;
    },
  };
}

/**
 * Начать запись.
 *
 * @param {object} params
 * @param {object} params.mediaDevices  `navigator.mediaDevices` (или двойник)
 * @param {Function} params.AudioContext конструктор (или двойник)
 * @param {number} [params.seconds]     сколько писать, 1…60
 * @param {number} [params.sampleRate]  частота для WAV
 * @param {Function} [params.onTick]    обратный отсчёт: (осталось секунд)
 * @param {{fill: Function}} [params.simulated] симулированный вход вместо устройства
 * @returns {Promise<{stop: Function, cancel: Function, seconds: number}>}
 */
async function startRecording({
  mediaDevices,
  AudioContext,
  seconds = DEFAULT_SECONDS,
  sampleRate = 44100,
  onTick = () => {},
  simulated = null,
} = {}) {
  // Симулированный вход подменяет только транспорт: всё остальное — тот же
  // код, что и с микрофоном.
  if (simulated) {
    const device = simulatedDevice(simulated);
    const started = await startRecording({
      mediaDevices: device.mediaDevices, AudioContext: device.AudioContext, seconds, sampleRate, onTick,
    });
    const originalStop = started.stop;
    return {
      ...started,
      stop: async () => {
        const take = await originalStop();
        device.stopDevice();
        return take
          ? { ...take, source: SIMULATED_SOURCE, simulated: true, label: 'симулированный вход (проверка)' }
          : take;
      },
      cancel: () => {
        device.stopDevice();
        started.cancel();
      },
    };
  }
  if (!mediaDevices || typeof mediaDevices.getUserMedia !== 'function') {
    throw new Error('окно не умеет обращаться к микрофону: нет доступа к устройствам');
  }
  const limit = Math.min(MAX_SECONDS, Math.max(1, Math.round(Number(seconds) || DEFAULT_SECONDS)));

  // Просим моно и без обработки, которая «улучшает» голос: эхо-подавление
  // съедает тихие концы фраз, а нам нужен честный вход.
  let stream;
  try {
    stream = await mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false },
    });
  } catch (err) {
    const name = (err && (err.name || err.code)) || '';
    const reason = name === 'NotAllowedError' || name === 'PermissionDeniedError'
      ? 'доступ к микрофону запрещён: разрешите его в параметрах Windows 11 или используйте WAV-файл'
      : name === 'NotFoundError' || name === 'DevicesNotFoundError'
        ? 'микрофон не найден: подключите его или используйте WAV-файл'
        : `микрофон недоступен: ${(err && err.message) || name || 'неизвестная причина'}`;
    throw new Error(reason);
  }

  const context = new AudioContext();
  const source = context.createMediaStreamSource(stream);
  // ScriptProcessor устарел, но работает и в Electron, и в двойниках тестов;
  // заменять его на AudioWorklet — отдельная задача, а не повод не писать.
  const processor = context.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  let frames = 0;
  let finished = false;
  let resolveDone;
  const done = new Promise((resolve) => { resolveDone = resolve; });

  const inputRate = context.sampleRate || sampleRate;
  processor.onaudioprocess = (event) => {
    if (finished) return;
    const channel = event.inputBuffer.getChannelData(0);
    // Копия обязательна: буфер переиспользуется движком.
    const copy = new Float32Array(channel.length);
    copy.set(channel);
    chunks.push(copy);
    frames += copy.length;
  };
  source.connect(processor);
  processor.connect(context.destination);

  const tickEvery = 250;
  const started = Date.now();
  const timer = setInterval(() => {
    const left = Math.max(0, limit - Math.round((Date.now() - started) / 1000));
    onTick(left);
    if (left === 0) stop().catch(() => {});
  }, tickEvery);

  /** Собрать записанное в один буфер и закрыть устройства. */
  function release() {
    clearInterval(timer);
    finished = true;
    try {
      processor.disconnect();
      source.disconnect();
    } catch {
      /* уже отключено — это не ошибка */
    }
    try {
      stream.getTracks().forEach((track) => track.stop());
    } catch {
      /* дорожки могли закрыться сами */
    }
    try {
      if (typeof context.close === 'function') context.close();
    } catch {
      /* контекст мог закрыться сам */
    }
  }

  /** Остановить запись и отдать буфер. */
  async function stop() {
    if (finished) return done;
    release();
    const signal = new Float32Array(frames);
    let offset = 0;
    for (const chunk of chunks) {
      signal.set(chunk, offset);
      offset += chunk.length;
    }
    const result = {
      signal,
      sampleRate: inputRate,
      durationSec: frames / inputRate,
      source: 'record',
      simulated: false,
      label: 'запись с микрофона',
      note: null,
    };
    resolveDone(result);
    return result;
  }

  /** Отменить запись, ничего не отдавая: WAV не появится. */
  function cancel() {
    if (finished) return;
    release();
    resolveDone(null);
  }

  return { stop, cancel, seconds: limit };
}

/**
 * Отдать запись главному процессу.
 *
 * Страница живёт в контексте изоляции: `require` и `Buffer` ей недоступны,
 * поэтому WAV кодирует главный процесс (он это уже умеет для бита). Сюда
 * едет PCM: Float32 → base64. Так окно не изобретает свой формат файла.
 *
 * @param {{signal: Float32Array, sampleRate: number, durationSec: number}} take
 * @returns {{pcmBase64: string, sampleRate: number, seconds: number, frames: number}}
 */
function toPayload(take) {
  if (!take || !take.signal || !take.signal.length) {
    throw new Error('в записи нет звука: проверьте микрофон и попробуйте снова');
  }
  const bytes = new Uint8Array(take.signal.buffer, take.signal.byteOffset, take.signal.byteLength);
  let binary = '';
  // Кусок по 0x8000: `String.fromCharCode(...)` на мегабайтах падает.
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  }
  return {
    pcmBase64: btoa(binary),
    sampleRate: take.sampleRate,
    seconds: take.durationSec,
    frames: take.signal.length,
  };
}

// `sections/vocal.js` — обычный скрипт без `require`, поэтому API отдаётся
// через общий объект; для `node --test` остаётся module.exports.
const API = {
  DEFAULT_SECONDS,
  MAX_SECONDS,
  start: startRecording,
  startRecording,
  toPayload,
};
if (typeof window !== 'undefined') window.ZSMM_RECORDER = API;

// В окне `module` нет вовсе: страница собрана как обычные скрипты.
if (typeof module !== 'undefined' && module.exports) module.exports = API;
