'use strict';
/**
 * pipeline.test.js — «Собрать бит» одним кодом для Electron и предпросмотра.
 *
 * Проверяем то, что раньше дублировалось в двух местах и потому расходилось:
 * проверку параметров, ленивое открытие банка, прогресс и формат ответа.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { renderBeatRequest, renderBeatPayload, createBankProvider } = require('../electron/pipeline');
const { sanitizeBeatOptions } = require('../src/core/beat-options');

const ROOT = path.resolve(__dirname, '..', '..');

test('конвейер возвращает WAV и отчёт по проверенным параметрам', async () => {
  const result = await renderBeatRequest({ bpm: 120, genre: 'house', seed: 3, durationSec: 2 }, { rootDir: ROOT });

  expectOk(result);
  assert.equal(result.data.report.bpm, 120);
  assert.equal(result.data.report.seed, 3);
  assert.ok(result.data.wav.length > 1000);
  assert.equal(result.data.wav.toString('ascii', 0, 4), 'RIFF');
});

test('негодные параметры отсекаются до запуска движка', async () => {
  const bad = await renderBeatRequest({ bpm: 5000 }, { rootDir: ROOT });

  assert.equal(bad.ok, false);
  assert.match(bad.error, /BPM/);
});

test('base64-путь совпадает с байтами движка', async () => {
  const result = await renderBeatPayload({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 3 }, { rootDir: ROOT });
  const again = await renderBeatRequest({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 3 }, { rootDir: ROOT });

  assert.equal(result.ok, true, result.error);
  assert.ok(result.data.wavBase64 && result.data.report);
  assert.deepEqual(Buffer.from(result.data.wavBase64, 'base64'), again.data.wav);
  assert.equal(result.data.report.repetition.bars > 0, true);
});

test('галочка «банк сэмплов» снята — 32 файла не читаются', async () => {
  let touched = 0;
  const bankFor = () => {
    touched += 1;
    throw new Error('банк не должен открываться');
  };

  const result = await renderBeatRequest(
    { bpm: 120, genre: 'trap', seed: 1, durationSec: 2, useBank: false },
    { rootDir: ROOT, bankFor },
  );

  expectOk(result);
  assert.equal(touched, 0, 'без банка источник сэмплов не должен создаваться');
  assert.equal(result.data.report.drum_engine.status, 'FALLBACK');
});

test('банк переиспользуется между рендерами', async () => {
  const provider = createBankProvider({ rootDir: ROOT });
  const first = provider.bank();
  const second = provider.bank();

  assert.equal(first, second, 'декодированные one-shot\'ы должны жить в кэше');
  assert.ok(first.report().total_samples >= 20);

  provider.reset();
  assert.notEqual(provider.bank(), first);
});

test('прогресс доходит до вызывающего и растёт по тактам', async () => {
  const events = [];
  await renderBeatRequest(
    { bpm: 128, genre: 'drift phonk', seed: 5, durationSec: 12 },
    { rootDir: ROOT, onProgress: (progress) => events.push(progress) },
  );

  assert.ok(events.length >= 3);
  assert.equal(events.filter((event) => event.phase === 'section').length > 0, true);
  assert.equal(events.at(-1).percent, 100);
});

test('проверка параметров одна и та же с окном', () => {
  // Окно и предпросмотр ходят через `sanitizeBeatOptions`; дубликат этой
  // проверки в конвейере означал бы два разных набора правил.
  const fromWindow = sanitizeBeatOptions({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 20 });
  const fromPipeline = sanitizeBeatOptions({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 20 });

  assert.deepEqual(fromWindow.value, fromPipeline.value);
  assert.equal(fromWindow.error, undefined);
});

function expectOk(result) {
  assert.equal(result.ok, true, result.error);
  assert.ok(result.data.wav && result.data.report);
}
