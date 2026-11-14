'use strict';
/**
 * test/vocal-mix.test.js — вокал внутри микса и параметры вокала в запросе.
 *
 * Проверяется то, что видит пользователь: с включённым вокалом трек
 * звучит иначе, отчёт называет источник, а неверные параметры (режим, путь,
 * уровень) отсекаются до рендера, а не после.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { renderBeat, renderBeatInSteps, mixVocal } = require('../src/core/audio/engine');
const takes = require('../src/core/audio/takes');
const { sanitizeBeatOptions, sanitizeVocalOptions } = require('../src/core/beat-options');
const { renderBeatRequest, buildVocal } = require('../electron/pipeline');

const BASE = { genre: 'drift_phonk', bpm: 120, seed: 5, durationSec: 4 };

test('без вокала отчёт говорит «не подключён»', () => {
  const { report } = renderBeat(BASE);
  assert.equal(report.vocal, null);
});

test('с вокалом отчёт называет источник, уровень и длительность в миксе', () => {
  const take = takes.synthTake({ seconds: 4, seed: 5, text: 'мой город спит' });
  const { report } = renderBeat({ ...BASE, vocalTake: take, vocalGain: 0.6 });
  assert.ok(report.vocal, 'вокал не попал в отчёт');
  assert.equal(report.vocal.source, 'synth');
  assert.equal(report.vocal.simulated, false);
  assert.equal(report.vocal.gain, 0.6);
  assert.ok(report.vocal.mixed_seconds > 0);
});

test('тестовый дубль в миксе остаётся помеченным как имитация', () => {
  const { report } = renderBeat({ ...BASE, vocalTake: takes.testTake({ seconds: 4, seed: 5 }) });
  assert.equal(report.vocal.source, 'test');
  assert.equal(report.vocal.simulated, true);
  assert.match(report.vocal.label, /не с микрофона/);
});

test('вокал реально слышен: микс отличается от сухого', () => {
  const dry = renderBeat(BASE);
  const wet = renderBeat({ ...BASE, vocalTake: takes.synthTake({ seconds: 4, seed: 5 }), vocalGain: 0.8 });
  assert.notEqual(dry.wav.length, 0);
  assert.equal(dry.wav.length, wet.wav.length, 'вокал не должен менять длину файла');
  assert.notEqual(Buffer.compare(dry.wav, wet.wav), 0, 'вокал не повлиял на микс');
});

test('уровень 0 выключает вокал, не ломая рендер', () => {
  const dry = renderBeat(BASE);
  const silent = renderBeat({ ...BASE, vocalTake: takes.synthTake({ seconds: 4, seed: 5 }), vocalGain: 0 });
  const decoded = silent.report.vocal;
  assert.equal(decoded.gain, 0);
  // Разница только в шумовом поле вокала на нулевом уровне: файл цел.
  assert.equal(dry.wav.length, silent.wav.length);
});

test('mixVocal возвращает null на пустом дубле и не падает на коротком', () => {
  const left = new Float32Array(1000);
  const right = new Float32Array(1000);
  assert.equal(mixVocal({ left, right, take: null, gain: 0.5, sr: 1000, target: 1000 }), null);
  const short = mixVocal({
    left, right, take: { signal: new Float32Array(10), sampleRate: 1000 }, gain: 0.5, sr: 1000, target: 1000,
  });
  assert.equal(short.starts_outside, false);
  for (let i = 0; i < left.length; i += 1) assert.ok(Number.isFinite(left[i]));
});

test('вокал длиннее трека обрезается и об этом сказано в отчёте', () => {
  const long = takes.synthTake({ seconds: 30, seed: 1 });
  const { report } = renderBeat({ ...BASE, vocalTake: long });
  assert.equal(report.vocal.starts_outside, true);
  assert.ok(report.vocal.mixed_seconds <= BASE.durationSec + 0.01);
});

test('вокал через renderBeatInSteps попадает в отчёт', async () => {
  const { report } = await renderBeatInSteps(
    { ...BASE, vocalTake: takes.testTake({ seconds: 4 }), vocalGain: 0.5 },
    { yieldToEventLoop: false },
  );
  assert.equal(report.vocal.source, 'test');
});

test('режимы вокала проверяются до рендера', () => {
  assert.ok(sanitizeVocalOptions({ mode: 'nope' }).error);
  assert.ok(sanitizeVocalOptions({ mode: 'file' }).error, 'без пути режим «файл» недопустим');
  assert.ok(sanitizeVocalOptions({ mode: 'file', file: '../secret.wav' }).error);
  assert.ok(sanitizeVocalOptions({ mode: 'file', file: 'C:/a/b.mp3' }).error);

  const none = sanitizeVocalOptions({ mode: 'none' }).value;
  assert.equal(none.gain, 0);
  const testMode = sanitizeVocalOptions({ mode: 'test' }).value;
  assert.equal(testMode.mode, 'test');
  assert.ok(testMode.text.length > 0, 'текст по умолчанию должен быть непустым');
  const loud = sanitizeVocalOptions({ mode: 'synth', gain: 5 }).value;
  assert.equal(loud.gain, 1, 'уровень должен зажиматься, а не пропускаться');
  const quiet = sanitizeVocalOptions({ mode: 'synth', gain: -2 }).value;
  assert.equal(quiet.gain, 0);
  const longText = sanitizeVocalOptions({ mode: 'synth', text: 'а'.repeat(5000) }).value;
  assert.ok(longText.text.length <= 600, 'текст не ограничен по длине');
});

test('вокал едет внутри параметров бита и проверяется вместе с ними', () => {
  const ok = sanitizeBeatOptions({ bpm: 128, durationSec: 10, vocal: { mode: 'test' } });
  assert.equal(ok.error, undefined);
  assert.equal(ok.value.vocal.value.mode, 'test');

  const bad = sanitizeBeatOptions({ bpm: 128, vocal: { mode: 'nope' } });
  assert.match(bad.error, /режим вокала/);

  const absent = sanitizeBeatOptions({ bpm: 128 });
  assert.equal(absent.value.vocal.value.mode, 'none');
});

test('buildVocal собирает дубль по проверенным параметрам', () => {
  const sanitized = sanitizeBeatOptions({ bpm: 120, durationSec: 5, seed: 3, key: 'D minor', vocal: { mode: 'test' } }).value;
  const built = buildVocal(sanitized, {});
  assert.ok(built.take, built.error);
  assert.equal(built.take.source, 'test');
  assert.equal(built.gain, 0.5);
  assert.ok(Math.abs(built.take.durationSec - 5) < 0.2);
});

test('buildVocal читает файл через переданное файловое API', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-vocal-'));
  const file = path.join(dir, 'take.wav');
  fs.writeFileSync(file, require('../src/core/audio/wav').encodeWav([new Float32Array(4410)], 44100));
  const vfs = {
    exists: (target) => fs.existsSync(target),
    readBinary: (target) => ({ value: fs.readFileSync(target) }),
  };
  const built = buildVocal({ durationSec: 5, vocal: { value: { mode: 'file', file, gain: 0.4 } } }, { vocalFileSystem: vfs });
  assert.ok(built.take, built.error);
  assert.equal(built.take.source, 'file');
  assert.equal(built.gain, 0.4);

  const missing = buildVocal(
    { durationSec: 5, vocal: { value: { mode: 'file', file: path.join(dir, 'нет.wav'), gain: 0.4 } } },
    { vocalFileSystem: vfs },
  );
  assert.match(missing.error, /не найден/);
  fs.rmSync(dir, { recursive: true, force: true });
});

test('renderBeatRequest: три режима и честные отказы', async () => {
  const context = { rootDir: path.resolve(__dirname, '..', '..'), yieldToEventLoop: false };
  const dry = await renderBeatRequest({ ...BASE, durationSec: 3 }, context);
  assert.equal(dry.ok, true, dry.error);
  assert.equal(dry.data.report.vocal, null);

  const testMode = await renderBeatRequest({ ...BASE, durationSec: 3, vocal: { mode: 'test' } }, context);
  assert.equal(testMode.ok, true, testMode.error);
  assert.equal(testMode.data.report.vocal.source, 'test');
  assert.equal(testMode.data.report.vocal.simulated, true);

  const synthMode = await renderBeatRequest({ ...BASE, durationSec: 3, vocal: { mode: 'synth', gain: 0.3 } }, context);
  assert.equal(synthMode.ok, true, synthMode.error);
  assert.equal(synthMode.data.report.vocal.gain, 0.3);

  const badMode = await renderBeatRequest({ ...BASE, vocal: { mode: 'чужой' } }, context);
  assert.equal(badMode.ok, false);
  assert.equal(badMode.fatal, true);

  const badFile = await renderBeatRequest({ ...BASE, vocal: { mode: 'file', file: 'C:/nope/x.wav' } }, context);
  assert.equal(badFile.ok, false);
  assert.match(badFile.error, /не найден/);
});
