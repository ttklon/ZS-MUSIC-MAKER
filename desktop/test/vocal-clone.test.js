'use strict';
/**
 * test/vocal-clone.test.js — кнопка «Клонировать мой голос (RVC)».
 *
 * Раньше запись жила только в памяти окна: человек записывал голос, нажимал
 * «Сохранить», и обучение всё равно отвечало «в vault нет записей». Здесь
 * проверяется весь путь кнопки: запись → сохранение в файл → индексация в
 * голосовом хранилище → запуск задачи обучения. Если шаг падает, причина
 * должна быть видна, а не проглочена.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { documentFromHtml } = require('./fake-dom');

const SRC = path.resolve(__dirname, '..', 'src');

/** Поддельный захват: отдаёт дубль без микрофона и без Web Audio. */
function fakeRecorder() {
  const calls = [];
  return {
    calls,
    async start(options) {
      calls.push(['start', options && options.seconds]);
      return {
        async stop() {
          return { durationSec: 12.5, channels: 1 };
        },
      };
    },
    toPayload: () => ({ pcmBase64: 'UklGRgAAAABXQVZF', sampleRate: 48000, seconds: 12.5 }),
  };
}

/** Загрузить только раздел «Вокал» с поддельным мостом `window.zsmm`. */
function bootVocal(bridge, recorder = fakeRecorder()) {
  const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
  const document = documentFromHtml(html);
  const window = document.createElement('window');
  window.zsmm = bridge;
  window.ZSMM_RECORDER = recorder;
  const ui = {
    $: (id) => document.getElementById(id),
    showError: (message) => { window.lastError = message; },
    setStatus: (message) => { window.lastStatus = message; },
    state: {},
  };
  window.ZSMM_UI = ui;
  window.ZSMM_SECTIONS = {};
  // Раздел — IIFE с `const W = window.ZSMM_UI`: подставляем свой объект.
  const source = fs.readFileSync(path.join(SRC, 'sections', 'vocal.js'), 'utf8');
  const parse = new Function('window', 'document', 'navigator', source);
  parse(window, document, { mediaDevices: {} });
  window.ZSMM_SECTIONS.initVocal();
  window.ZSMM_UI.wireVocal();
  return { document, window, recorder, ui };
}

const flush = () => new Promise((resolve) => setImmediate(resolve));

/** Записать дубль через настоящие кнопки раздела. */
async function recordTake(env) {
  const { document } = env;
  // `bootVocal` уже вызвал `wireVocal`: повторная подписка дала бы по два
  // обработчика на кнопку и удвоила бы действия — так и ловится двойная
  // регистрация в реальном окне.
  document.getElementById('vocal-mode').value = 'record';
  document.getElementById('vocal-record').disabled = false;
  document.getElementById('vocal-record').dispatch('click');
  await flush();
  document.getElementById('vocal-stop').disabled = false;
  document.getElementById('vocal-stop').dispatch('click');
  await flush();
}

test('без записи кнопка клонирования выключена и ничего не запускает', () => {
  const calls = [];
  const { document } = bootVocal({
    startTask: (...args) => { calls.push(args); return { ok: true }; },
  });

  const button = document.getElementById('vocal-clone');

  assert.ok(button, 'кнопки клонирования нет в разметке');
  assert.equal(button.disabled, true);
  assert.equal(calls.length, 0);
});

test('после записи кнопка доступна, а весь путь идёт по порядку', async () => {
  const calls = { saved: [], indexed: [], tasks: [] };
  const env = bootVocal({
    saveRecording: async (payload) => {
      calls.saved.push(payload);
      return { ok: true, data: { path: '/tmp/vocal-record_13s.wav' } };
    },
    indexRecording: async (filePath) => {
      calls.indexed.push(filePath);
      return { ok: true, data: { ok: true } };
    },
    startTask: async (key, options) => {
      calls.tasks.push([key, options]);
      return { ok: true, data: { pid: 7, command: ['main.py', '--rvc-train'] } };
    },
  });

  await recordTake(env);
  const clone = env.document.getElementById('vocal-clone');
  assert.equal(clone.disabled, false, 'после записи клонирование должно быть доступно');

  clone.dispatch('click');
  await flush();
  await flush();

  // Сначала файл, потом хранилище, потом обучение: другой порядок оставлял бы
  // обучение без записей.
  // Раздел сохраняет запись сам (её сохраняет и «Сохранить запись как WAV»):
  // здесь важно, что клонирование не сохраняет повторно уже сохранённый файл.
  assert.ok(calls.saved.length >= 1, 'запись не сохранена в файл');
  assert.equal(calls.saved.length, 1, 'уже сохранённый файл не сохраняется второй раз');
  assert.deepEqual(calls.indexed, ['/tmp/vocal-record_13s.wav']);
  assert.deepEqual(calls.tasks, [['rvc-train', { voice: 'my_voice', rvcVoice: 'my_voice' }]]);
  assert.equal(env.window.lastError, undefined);
});

test('отказ хранилища останавливает обучение и говорит причину', async () => {
  const calls = [];
  const env = bootVocal({
    saveRecording: async () => ({ ok: true, data: { path: '/tmp/take.wav' } }),
    indexRecording: async () => ({ ok: false, error: 'vault недоступен' }),
    startTask: async (key) => { calls.push(key); return { ok: true }; },
  });

  await recordTake(env);
  env.document.getElementById('vocal-clone').dispatch('click');
  await flush();
  await flush();

  assert.equal(calls.length, 0, 'обучение не должно стартовать без записи в хранилище');
  assert.match(env.window.lastError || '', /vault недоступен/);
});

test('индексация без Python не превращается в успех', async () => {
  const vocalService = require('../electron/vocal-service');

  const reply = await vocalService.indexRecording({
    spawn: () => { throw new Error('не должен вызываться'); },
    python: null,
    root: '/repo',
    filePath: '/tmp/take.wav',
  });

  assert.equal(reply.ok, false);
  assert.match(reply.error, /Python/);
});
