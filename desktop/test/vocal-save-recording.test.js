'use strict';
/**
 * Запись с микрофона: дубль можно сохранить, даже если трек ещё не собран.
 *
 * Дефект, который ловит этот файл: окно держало запись только в памяти и
 * отдавало её наружу единственным путём — `vocal-save`, а эта кнопка
 * включалась лишь после `renderBeat`. Человек записывал дубль, но сохранить
 * его отдельным WAV не мог: канал `zsmm:vocal-save-recording` и
 * `vocalService.saveRecording` в главном процессе были готовы и покрыты
 * тестами модуля, а из окна не вызывались. Запись исчезала при закрытии
 * приложения, хотя она уже состоялась.
 *
 * Проверяется весь путь, как у человека: микрофон (двойник устройства, тот же
 * код записи) → «Остановить запись» → «Сохранить запись как WAV» → главный
 * процесс получает непустой PCM. Рендер бита при этом не нужен.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { bootWindow } = require('./fake-dom');
const { recordingToWav } = require('../electron/vocal-service');

const SRC = path.resolve(__dirname, '..', 'src');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tick = (ms = 80) => new Promise((resolve) => { setTimeout(resolve, ms); });

// «Настоящий» микрофон: Web Audio отдаёт Float32-сэмплы во Float32Array.
// Кодовый блок собирает из них base64 — так же, как это делает браузер.
const FAKE_AUDIO_CONTEXT = `
  class FakeParam { constructor() { this.value = 0; } }
  class FakeNode {
    connect() { return this; }
    disconnect() {}
  }
  class FakeAudioContext extends FakeNode {
    constructor() {
      super();
      this.sampleRate = 44100;
      this.destination = new FakeNode();
      FakeAudioContext.instances.push(this);
    }
    createMediaStreamSource() { return new FakeNode(); }
    createScriptProcessor() {
      const node = new FakeNode();
      const block = new Float32Array(4410);
      for (let i = 0; i < block.length; i += 1) {
        block[i] = 0.4 * Math.sin((2 * Math.PI * 220 * i) / 44100);
      }
      let timer = null;
      node.connect = () => {
        // Устройство отдаёт по 100 мс звука, пока запись не остановят.
        timer = setInterval(() => {
          if (typeof node.onaudioprocess === 'function') {
            node.onaudioprocess({ inputBuffer: { getChannelData: () => block } });
          }
        }, 10);
        node._timer = timer;
        return node;
      };
      node.disconnect = () => { clearInterval(timer); };
      return node;
    }
    close() { return Promise.resolve(); }
  }
  FakeAudioContext.instances = [];
`;

/** Мост: ответы на всё, что окно спрашивает при открытии «Бита». */
function bridge(overrides = {}) {
  const calls = { saveRecording: [], renderBeat: 0 };
  const api = {
    calls,
    loadSettings: async () => ({ ok: true, data: {} }),
    saveSettings: async () => ({ ok: true, data: {} }),
    beatBank: async () => ({ ok: true, data: { status: 'REAL_PASS', total_samples: 1, instruments_with_samples: ['kick'] } }),
    renderBeat: async () => { calls.renderBeat += 1; throw new Error('рендер в этом тесте не нужен'); },
    onBeatProgress: () => () => {},
    cancelBeat: async () => ({ ok: true, data: { cancelled: false } }),
    vocalInput: async () => ({ ok: true, data: { recording: true } }),
    saveRecording: async (payload) => {
      calls.saveRecording.push(payload);
      const converted = recordingToWav(payload);
      if (!converted.ok) return converted;
      return { ok: true, data: { path: '/tmp/дубль.wav', bytes: converted.data.buffer.length, seconds: converted.data.seconds, recorded: true } };
    },
    ...overrides,
  };
  return api;
}

/** Открыть «Бит», подсунуть окну двойник звукового контекста и микрофон. */
async function bootBeat(overrides) {
  const built = bridge(overrides);
  const { document, window } = bootWindow({ srcDir: SRC, html: HTML, bridge: built });
  // В браузере `navigator` и `AudioContext` — свойства окна. В Node у
  // глобального `navigator` нет `mediaDevices`, поэтому микрофон подставляем
  // глобально, а класс звукового контекста — свойством окна.
  // В Node `navigator` объявлен только на чтение, поэтому свойство ставим
  // через `defineProperty` — иначе тест падает на стенде, а не проверяет окно.
  const hadNavigator = Object.prototype.hasOwnProperty.call(globalThis, 'navigator');
  const previousNavigator = globalThis.navigator;
  Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    writable: true,
    value: { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) } },
  });
  // Класс создаётся в контексте страницы: тесту не нужен доступ к её scope.
  window.AudioContext = new Function(`${FAKE_AUDIO_CONTEXT}; return FakeAudioContext;`)();
  built.restore = () => {
    if (hadNavigator) {
      Object.defineProperty(globalThis, 'navigator', { configurable: true, writable: true, value: previousNavigator });
    } else {
      delete globalThis.navigator;
    }
  };
  await window.ZSMM_UI.switchView('beat');
  await tick(120);
  return { document, window, bridge: built };
}

/** Нажать по id так, как это сделал бы человек: через навешенный обработчик. */
async function press(document, id) {
  const node = document.getElementById(id);
  assert.ok(node, `в разметке нет #${id}`);
  const listeners = node.listeners.get('click') || [];
  assert.ok(listeners.length > 0, `на #${id} нет обработчика — кнопка мертва`);
  for (const listener of listeners) await listener({ target: node });
}

async function chooseRecordMode(document) {
  const mode = document.getElementById('vocal-mode');
  mode.value = 'record';
  for (const listener of mode.listeners.get('change') || []) listener({ target: mode });
  await tick();
}

test('запись с микрофона сохраняется отдельным WAV до сборки трека', async () => {
  const { document, bridge: built } = await bootBeat();
  await chooseRecordMode(document);

  const saveButton = document.getElementById('vocal-save-recording');
  assert.equal(saveButton.disabled, true, 'до записи сохранять нечего — кнопка заблокирована');

  await press(document, 'vocal-record');
  await tick(200);
  await press(document, 'vocal-stop');
  await tick(120);

  assert.equal(built.calls.renderBeat, 0, 'сохранение не должно требовать рендера');
  assert.equal(saveButton.disabled, false, 'после записи кнопка сохранения доступна');
  assert.match(document.getElementById('vocal-record-status').textContent, /записано/i);

  await press(document, 'vocal-save-recording');
  await tick(120);

  assert.equal(built.calls.saveRecording.length, 1, 'главный процесс получил ровно одно сохранение');
  const payload = built.calls.saveRecording[0];
  assert.equal(payload.sampleRate, 44100);
  assert.ok(payload.pcmBase64.length > 64, 'PCM непустой — сохраняется именно запись');
  assert.ok(payload.seconds > 0, 'длительность записи известна');
  assert.match(
    document.getElementById('vocal-record-status').textContent,
    /сохранена/i,
    'окно говорит, куда легла запись',
  );
});

test('скачивание в браузере не выдаётся за отмену', async () => {
  // Предпросмотр отдаёт файл без пути: `{path: null, downloaded: true}`.
  // Раньше окно печатало «сохранение записи отменено» при только что
  // скачанном WAV — это видел живой Chromium, а не тесты.
  const { document } = await bootBeat({
    saveRecording: async () => ({ ok: true, data: { path: null, downloaded: true } }),
  });
  await chooseRecordMode(document);
  await press(document, 'vocal-record');
  await tick(150);
  await press(document, 'vocal-stop');
  await tick(100);
  await press(document, 'vocal-save-recording');
  await tick(100);

  const text = document.getElementById('vocal-record-status').textContent;
  assert.match(text, /скачан/i);
  assert.doesNotMatch(text, /отменено/i, 'скачанный файл — не отмена');
});

test('отмена диалога сохранения записи не считается ошибкой', async () => {
  const { document } = await bootBeat({
    saveRecording: async () => ({ ok: true, data: { path: null, cancelled: true } }),
  });
  await chooseRecordMode(document);
  await press(document, 'vocal-record');
  await tick(150);
  await press(document, 'vocal-stop');
  await tick(100);
  await press(document, 'vocal-save-recording');
  await tick(100);

  assert.match(document.getElementById('vocal-record-status').textContent, /отменено/i);
  // Отмена — не ошибка: сообщение об ошибке остаётся пустым (в двойнике DOM
  // классы разметки не разбираются, поэтому проверяется текст, а не плашка;
  // видимость плашки проверяет E2E в настоящем Chromium).
  // Важно, что в плашке нет «Запись не сохранена»: постороннее сообщение
  // (например, про отсутствующий раздел) к отмене отношения не имеет.
  assert.doesNotMatch(document.getElementById('error-text').textContent, /Запись не сохранена/);
});

test('без записи кнопка не отправляет пустой буфер в главный процесс', async () => {
  const { document, bridge: built } = await bootBeat();
  await chooseRecordMode(document);
  const saveButton = document.getElementById('vocal-save-recording');
  await press(document, 'vocal-save-recording');
  await tick(60);
  assert.equal(built.calls.saveRecording.length, 0, 'пустой PCM не должен уходить в главный процесс');
  assert.equal(saveButton.disabled, true);
});

test('канал сохранения записи действительно есть в мосте и в главном процессе', () => {
  // Связка, из-за которой дефект жил незамеченным: кнопка, канал и обработчик
  // проверились по отдельности. Здесь они названы вместе.
  const preload = fs.readFileSync(path.join(SRC, '..', 'electron', 'preload.js'), 'utf8');
  const service = fs.readFileSync(path.join(SRC, '..', 'electron', 'beat-service.js'), 'utf8');
  assert.match(preload, /saveRecording/, 'preload отдаёт saveRecording окну');
  assert.match(service, /zsmm:vocal-save-recording/, 'главный процесс регистрирует канал');
  const vocal = fs.readFileSync(path.join(SRC, 'sections', 'vocal.js'), 'utf8');
  assert.match(vocal, /zsmm\.saveRecording\(/, 'окно действительно зовёт этот канал');
});
