'use strict';
/**
 * Что окно запоминает между запусками.
 *
 * Дефект: после рендера с вокалом окно звало `rememberBeatOptions(options)`,
 * а в `options.vocal` лежали сами звуковые данные — `pcmBase64` записанного
 * дубля и/или `wavBase64` выбранного файла. Оба поля уходили в
 * `saveSettings`, то есть в `settings.json` каталога пользователя:
 * 30 секунд записи — это 6,7 МБ base64, минута — 13,5 МБ. Файл настроек
 * раздувался до десятков мегабайт, читался и перезаписывался целиком на
 * каждый чих (смена раздела, движение окна) и в конце концов не записывался
 * вовсе — вместе с жанром, темпом и местом окна.
 *
 * Проверяется поведение, а не реализация: после рендера с дублем в
 * `saveSettings` не должно быть ни одного поля с аудиоданными, а параметры
 * бита (жанр, темп, зерно, длительность) должны сохраниться.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { bootWindow } = require('./fake-dom');

const SRC = path.resolve(__dirname, '..', 'src');
const HTML = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const tick = (ms = 80) => new Promise((resolve) => { setTimeout(resolve, ms); });

const FAKE_AUDIO_CONTEXT = `
  class FakeNode { connect() { return this; } disconnect() {} }
  class FakeAudioContext extends FakeNode {
    constructor() { super(); this.sampleRate = 44100; this.destination = new FakeNode(); }
    createMediaStreamSource() { return new FakeNode(); }
    createScriptProcessor() {
      const node = new FakeNode();
      const block = new Float32Array(4410);
      for (let i = 0; i < block.length; i += 1) {
        block[i] = 0.4 * Math.sin((2 * Math.PI * 220 * i) / 44100);
      }
      let timer = null;
      node.connect = () => {
        timer = setInterval(() => {
          if (typeof node.onaudioprocess === 'function') {
            node.onaudioprocess({ inputBuffer: { getChannelData: () => block } });
          }
        }, 10);
        return node;
      };
      // Как настоящий узел: release() в recorder.js зовёт disconnect, и
      // «устройство» должно замолчать. Без этого прогон висит на живом таймере.
      node.disconnect = () => { clearInterval(timer); };
      return node;
    }
    close() { return Promise.resolve(); }
  }
`;

/** Мост: запоминаем всё, что окно пытается сохранить в настройки. */
function bridge({ saved, ...overrides }) {
  return {
    loadSettings: async () => ({ ok: true, data: {} }),
    saveSettings: async (patch) => {
      saved.push(patch);
      return { ok: true, data: patch };
    },
    beatBank: async () => ({ ok: true, data: { status: 'REAL_PASS', total_samples: 1, instruments_with_samples: ['kick'] } }),
    renderBeat: async (options) => ({
      ok: true,
      data: {
        // Отчёт минимальный: проверяется не он, а то, что уходит в настройки.
        report: {
          sections: [{ name: 'intro', bars: 4, start_sec: 0, energy: 0.5, layers: ['kick'] }],
          genre: options.genre,
          bpm: options.bpm,
          key: 'A minor',
          duration_sec: options.durationSec,
          channels: 2,
          bits: 16,
          seed: options.seed,
          drum_engine: { status: 'REAL_PASS', reason: 'банк', sample_bank: null },
          dramaturgy: { hook_within_15s: true },
          humanity: { peak: 0.9 },
          measured_humanity: null,
          repetition: null,
          vocal: { label: 'запись с микрофона', gain: 0.5, mixed_seconds: 2 },
          total_bars: 4,
          bytes: 1024,
        },
        wavBase64: 'UklGRg==',
        vocalWavBase64: 'UklGRnZvY2Fs',
        vocalName: 'vocal-record_2s',
      },
    }),
    onBeatProgress: () => () => {},
    cancelBeat: async () => ({ ok: true, data: { cancelled: false } }),
    vocalInput: async () => ({ ok: true, data: { recording: true } }),
    saveRecording: async () => ({ ok: true, data: { path: '/tmp/x.wav' } }),
    // Переопределения идут последними: тест может подменить загрузку
    // настроек, но забыть про сохранение не должен.
    ...overrides,
  };
}

async function bootBeat(overrides = {}) {
  const saved = [];
  const { document, window } = bootWindow({ srcDir: SRC, html: HTML, bridge: bridge({ saved, ...overrides }) });
  Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    writable: true,
    value: { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) } },
  });
  window.AudioContext = new Function(`${FAKE_AUDIO_CONTEXT}; return FakeAudioContext;`)();
  await window.ZSMM_UI.switchView('beat');
  await tick(120);
  return { document, window, saved };
}

async function press(document, id) {
  const node = document.getElementById(id);
  assert.ok(node, `в разметке нет #${id}`);
  for (const listener of node.listeners.get('click') || []) await listener({ target: node });
}

/**
 * Что считается звуковыми данными.
 *
 * Режим вокала, текст и уровень сохранять можно и нужно — это настройки.
 * Нельзя сохранять сами сэмплы: они приходят полями `*Base64` или строкой в
 * сотни килобайт. Ловим и то, и другое, на двух уровнях вложенности: звук
 * лежит в `vocal.pcmBase64`.
 */
const AUDIO_KEY_RE = /base64|^pcm$|^wav$|^bytes$/i;
function audioKeys(object, prefix = '') {
  const found = [];
  for (const [key, value] of Object.entries(object || {})) {
    const name = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') {
      if (AUDIO_KEY_RE.test(key) || value.length > 512) {
        found.push(`${name} (${value.length} символов)`);
      }
    } else if (value && typeof value === 'object' && prefix === '') {
      found.push(...audioKeys(value, name));
    }
  }
  return found;
}

test('после рендера с записью в настройки не попадают звуковые данные', async () => {
  const { document, saved } = await bootBeat();

  // Записываем дубль с «микрофона» и собираем трек: именно этот путь раньше
  // отправлял pcmBase64 в settings.json.
  const mode = document.getElementById('vocal-mode');
  mode.value = 'record';
  for (const listener of mode.listeners.get('change') || []) listener({ target: mode });
  await tick();
  await press(document, 'vocal-record');
  await tick(250);
  await press(document, 'vocal-stop');
  await tick(150);

  document.getElementById('beat-genre').value = 'phonk';
  document.getElementById('beat-bpm').value = '120';
  document.getElementById('beat-seed').value = '5';
  document.getElementById('beat-duration').value = '4';
  await press(document, 'beat-render');
  // Настройки пишутся с задержкой на «складку» — ждём её.
  await tick(700);

  assert.ok(saved.length > 0, 'после рендера окно должно сохранить параметры');

  for (const patch of saved) {
    const bad = audioKeys(patch);
    assert.deepEqual(bad, [], `в settings.json уходят звуковые данные: ${bad.join(', ')}`);
  }

  // А сами параметры бита сохраниться обязаны: иначе правка «вырезать всё»
  // пройдёт тест, но сломает память окна.
  const last = saved[saved.length - 1];
  assert.equal(last.genre, 'phonk');
  assert.equal(last.bpm, 120);
  assert.equal(last.seed, 5);
  assert.equal(last.durationSec, 4);
});

test('режим вокала запоминается, а его данные — нет', async () => {
  const { document, saved } = await bootBeat();
  const mode = document.getElementById('vocal-mode');
  mode.value = 'record';
  for (const listener of mode.listeners.get('change') || []) listener({ target: mode });
  await tick();
  await press(document, 'vocal-record');
  await tick(200);
  await press(document, 'vocal-stop');
  await tick(120);

  // `vocal-save` недоступен без рендера — но настройки пишутся при рендере,
  // поэтому проверяем именно то, что окно кладёт в патч.
  await press(document, 'beat-render');
  await tick(700);

  const withVocalMode = saved.filter((patch) => Object.prototype.hasOwnProperty.call(patch, 'vocalMode'));
  assert.ok(withVocalMode.length > 0, 'режим вокала должен запоминаться');
  for (const patch of withVocalMode) {
    assert.equal(patch.vocalMode, 'record');
    assert.deepEqual(audioKeys(patch), [], 'режим без данных: сохраняется только название режима');
  }
});

test('выбранный WAV-файл не пересылается в настройки целиком', async () => {
  // Файл с диска приходит в окно как base64 — он тоже не должен оседать в
  // settings.json. Путь при этом не запоминается намеренно (файл мог исчезнуть),
  // но и содержимое файла хранить нечего.
  const { document, window, saved } = await bootBeat();
  window.zsmm.pickVocalFile = async () => ({ ok: true, data: { path: '/tmp/вокал.wav' } });
  await press(document, 'vocal-pick');
  await tick(120);

  document.getElementById('vocal-mode').value = 'file';
  for (const listener of document.getElementById('vocal-mode').listeners.get('change') || []) listener({});
  await tick(80);
  await press(document, 'beat-render');
  await tick(700);

  for (const patch of saved) {
    assert.deepEqual(audioKeys(patch), [], 'содержимое файла не должно попадать в настройки');
  }
});

test('режим записи возвращается как «без вокала», а не как готовый дубль', async () => {
  // Дуге между запусками нет: сэмплы в настройки не сохраняются. Если бы окно
  // показало «запись с микрофона» с прошлого запуска, человек нажал бы
  // «Собрать» и получил отказ «сначала запишите дубль» — или, хуже, трек без
  // голоса там, где он ожидал голос.
  const { document } = await bootBeat({
    loadSettings: async () => ({ ok: true, data: { vocalMode: 'record', genre: 'drill', bpm: 90 } }),
  });
  await tick(150);

  assert.equal(document.getElementById('vocal-mode').value, 'none', 'режим записи не восстанавливается');
  // Жанр — свободное текстовое поле (`#beat-genre` — это input, а не список),
  // поэтому сохранённое значение обязано вернуться в него как есть.
  assert.equal(document.getElementById('beat-genre').value, 'drill', 'а жанр восстанавливается');
  assert.equal(document.getElementById('beat-bpm').value, '90');
});


test('настоящий settings.json остаётся маленьким после рендера с записью', async () => {
  // Сквозная проверка без браузера: окно пишет в НАСТОЯЩЕЕ хранилище
  // (`electron/settings.js`), а не в заглушку. Раньше после рендера с дублем
  // сюда уходило `vocal.pcmBase64` — сотни килобайт на каждые несколько секунд
  // записи, и файл настроек переставал быть файлом настроек.
  const os = require('node:os');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-payload-'));
  const { createSettingsStore } = require('../electron/settings');
  const store = createSettingsStore({ dir });

  const saved = [];
  const { document, window } = bootWindow({
    srcDir: SRC,
    html: HTML,
    bridge: bridge({
      saved,
      loadSettings: async () => store.load(),
      saveSettings: async (patch) => {
        saved.push(patch);
        return { ok: store.save(patch).error === null, data: patch };
      },
    }),
  });
  Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    writable: true,
    value: { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) } },
  });
  window.AudioContext = new Function(`${FAKE_AUDIO_CONTEXT}; return FakeAudioContext;`)();
  await window.ZSMM_UI.switchView('beat');
  await tick(120);

  const mode = document.getElementById('vocal-mode');
  mode.value = 'record';
  for (const listener of mode.listeners.get('change') || []) listener({ target: mode });
  await tick();
  await press(document, 'vocal-record');
  await tick(300);
  await press(document, 'vocal-stop');
  await tick(150);
  await press(document, 'beat-render');
  await tick(800);

  const file = path.join(dir, 'settings.json');
  const size = fs.statSync(file).size;
  const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));

  assert.ok(size < 4096, `settings.json вырос до ${size} байт`);
  assert.equal(parsed.vocalMode, 'record', 'режим вокала запоминается');
  assert.equal(parsed.vocal, undefined, 'звука в файле нет');
  // Параметры бита на месте: правка не должна была выбросить всё вместе с звуком.
  assert.equal(typeof parsed.bpm, 'number');
  assert.equal(typeof parsed.durationSec, 'number');
});

test('режим «файл с диска» не запоминается: путь мог исчезнуть', async () => {
  const { document, window, saved } = await bootBeat();
  // Подменяем выбор файла и режим — как будто человек выбрал WAV.
  window.zsmm.pickVocalFile = async () => ({ ok: true, data: { path: '/tmp/вокал.wav' } });
  await press(document, 'vocal-pick');
  await tick(100);
  await press(document, 'beat-render');
  await tick(700);

  const last = saved[saved.length - 1];
  assert.equal(last.vocalMode, 'none', 'file не сохраняется: файла может не быть');
});
