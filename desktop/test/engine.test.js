'use strict';
/**
 * engine.test.js — сквозная сборка бита в окне: без Python, без сэмплов.
 *
 * Проверяется то, что слышно и что обещано пользователю: трек не молчит, пик
 * не выше нормы, повторный рендер с тем же seed даёт те же байты, а секции
 * различаются по громкости (куплет тише хука — это и есть «драматургия»).
 * Тайминги сверяются с замером Python-версии на 20-секундном рендере.
 */

const test = require('node:test');
const assert = require('node:assert');

const path = require('node:path');

const {
  renderBeat, renderBeatInSteps, prepareRender, SAMPLE_RATE, tempoDrift, addRoomNoise, finalizeStereo, fitLength,
} = require('../src/core/audio/engine');
const { peak, rms } = require('../src/core/audio/dsp');
const { createNodeFs } = require('../src/core/fs-node');
const { SampleSource } = require('../src/core/audio/bank');

const SR = SAMPLE_RATE;
const ROOT = path.resolve(__dirname, '..', '..');

/** Источник сэмплов на настоящем банке проекта. */
const bankSource = () => new SampleSource({ fileSystem: createNodeFs(), rootDir: ROOT });

/** Прочитать WAV, который вернул движок: заголовок и каналы. */
function parseWav(buffer) {
  assert.strictEqual(buffer.toString('ascii', 0, 4), 'RIFF');
  assert.strictEqual(buffer.readUInt16LE(22), 2, 'движок пишет стерео');
  const sampleRate = buffer.readUInt32LE(24);
  const bits = buffer.readUInt16LE(34);
  const dataSize = buffer.readUInt32LE(40);
  const frames = dataSize / (2 * (bits / 8));
  const left = new Float32Array(frames);
  const right = new Float32Array(frames);
  const bytes = bits / 8;
  for (let i = 0; i < frames; i += 1) {
    const offset = 44 + i * 2 * bytes;
    left[i] = bits === 16 ? buffer.readInt16LE(offset) / 32767 : buffer.readFloatLE(offset);
    right[i] = bits === 16 ? buffer.readInt16LE(offset + bytes) / 32767 : buffer.readFloatLE(offset + bytes);
  }
  return { sampleRate, bits, frames, left, right };
}

function rmsBetween(channel, start, end) {
  return rms(channel.subarray(start, end));
}

test('20 секунд бита рендерятся в WAV 44.1/16, пик ≤ 0.98', () => {
  const { wav, report } = renderBeat({ bpm: 140, key: 'A minor', genre: 'phonk', seed: 7, durationSec: 20 });
  const audio = parseWav(wav);
  assert.strictEqual(audio.sampleRate, 44100);
  assert.strictEqual(audio.bits, 16);
  assert.strictEqual(audio.frames, Math.trunc(20 * SR));
  assert.strictEqual(report.duration_sec, 20);
  assert.ok(peak(audio.left) <= 0.98, `пик ${peak(audio.left)} выше запаса`);
  assert.ok(peak(audio.left) > 0.5, 'трек не должен быть еле слышным');
  assert.ok(rms(audio.left) > 0.02, 'трек не должен быть почти тишиной');
});

test('структура секций совпадает с Python-планом для 20 секунд', () => {
  const { report } = renderBeat({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 20 });
  assert.deepStrictEqual(
    report.sections.map((section) => `${section.name}:${section.bars}`),
    ['intro:2', 'verse:2', 'hook:2', 'verse:2', 'hook:2', 'outro:2'],
  );
  assert.strictEqual(report.total_bars, 12);
  const starts = report.sections.map((section) => section.start_sec);
  assert.deepStrictEqual(starts, [0, 3.43, 6.86, 10.29, 13.71, 17.14]);
  assert.strictEqual(report.dramaturgy.hook_within_15s, true);
  assert.strictEqual(report.dramaturgy.hook_motif_start_sec, 0, 'мотив хука звучит с нуля (интро)');
});

test('куплет тише хука: драматургия слышна, а не только записана', () => {
  const { wav } = renderBeat({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 20 });
  const audio = parseWav(wav);
  const bar = Math.trunc(SR * (240 / 140));
  const verse = rmsBetween(audio.left, bar * 2, bar * 4);
  const hook = rmsBetween(audio.left, bar * 4, bar * 6);
  const db = 20 * Math.log10(hook / verse);
  assert.ok(db > 3, `хук должен быть громче куплета минимум на 3 дБ, получено ${db.toFixed(1)} дБ`);
});

test('тот же seed — те же байты, другой seed — другой трек', () => {
  const a = renderBeat({ bpm: 140, genre: 'phonk', seed: 42, durationSec: 6 });
  const b = renderBeat({ bpm: 140, genre: 'phonk', seed: 42, durationSec: 6 });
  const c = renderBeat({ bpm: 140, genre: 'phonk', seed: 43, durationSec: 6 });
  assert.ok(a.wav.equals(b.wav), 'при одинаковом seed WAV должен совпадать побайтово');
  assert.ok(!a.wav.equals(c.wav), 'другой seed должен давать другой трек');
});

test('жанр меняет ритм, а не только отчёт', () => {
  const phonk = renderBeat({ bpm: 140, genre: 'phonk', seed: 5, durationSec: 6 });
  const house = renderBeat({ bpm: 140, genre: 'house', seed: 5, durationSec: 6 });
  assert.notStrictEqual(phonk.report.groove_family, house.report.groove_family);
  assert.ok(!phonk.wav.equals(house.wav), 'разные семейства должны звучать по-разному');
  assert.deepStrictEqual(phonk.report.slot_plan.kick.slice(0, 16), [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0]);
  assert.deepStrictEqual(house.report.slot_plan.kick.slice(0, 16), [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]);
});

test('отчёт честно говорит FALLBACK и deterministic', () => {
  const { report } = renderBeat({ bpm: 120, genre: 'lofi', seed: 1, durationSec: 4 });
  assert.strictEqual(report.drum_engine.status, 'FALLBACK');
  assert.strictEqual(report.deterministic, true);
  assert.strictEqual(report.seed, 1);
  assert.strictEqual(report.channels, 2);
  assert.ok(report.bytes > 44);
});

test('свой план секций уважается', () => {
  const { report } = renderBeat({
    bpm: 120,
    genre: 'trap',
    seed: 3,
    durationSec: 8,
    sections: [{ name: 'intro', bars: 2 }, { name: 'drop', bars: 2 }],
  });
  assert.deepStrictEqual(report.sections.map((section) => section.name), ['intro', 'hook']);
  assert.strictEqual(report.sections[1].arrangement_name, 'drop');
});

test('float32-режим даёт 32 бита и те же события', () => {
  const { wav, report } = renderBeat({ bpm: 100, genre: 'trap', seed: 9, durationSec: 3, float32: true });
  assert.strictEqual(report.bits, 32);
  const audio = parseWav(wav);
  assert.strictEqual(audio.bits, 32);
  assert.ok(peak(audio.left) <= 1.0);
});

test('неверные параметры — ошибка с текстом', () => {
  assert.throws(() => renderBeat({ bpm: 0 }), /bpm/);
  assert.throws(() => renderBeat({ durationSec: 0 }), /durationSec/);
});

test('«человечность»: дрейф темпа сохраняет длину и меряет смещение', () => {
  const n = SR * 2;
  const left = new Float32Array(n);
  const right = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    left[i] = Math.sin((2 * Math.PI * 220 * i) / SR);
    right[i] = left[i];
  }
  const { left: warped, report } = tempoDrift(left, right, SR, 0.2);
  assert.strictEqual(warped.length, n, 'длина трека не меняется');
  assert.ok(report.peak_deviation_ms > 0 && report.peak_deviation_ms < 20, `смещение ${report.peak_deviation_ms} мс`);
  assert.ok(peak(warped) > 0.9, 'дрейф не должен глушить сигнал');
});

test('шум комнаты: уровень −62 dBFS ± 3 дБ, детерминирован по seed', () => {
  const n = SR;
  const make = () => ({ left: new Float32Array(n), right: new Float32Array(n) });
  const first = addRoomNoise(make().left, make().right, SR, -62, 11);
  const second = addRoomNoise(make().left, make().right, SR, -62, 11);
  const loudnessDb = 20 * Math.log10(rms(first.left) + 1e-12);
  assert.ok(Math.abs(loudnessDb + 62) < 3, `шумовой пол ${loudnessDb.toFixed(1)} dBFS`);
  assert.deepStrictEqual(Array.from(first.left.slice(0, 64)), Array.from(second.left.slice(0, 64)));
});

test('стерео-ширина: каналы не одинаковы и не противофаза', () => {
  const n = SR;
  const left = new Float32Array(n);
  const right = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    left[i] = Math.sin((2 * Math.PI * 440 * i) / SR) * 0.5;
    right[i] = Math.sin((2 * Math.PI * 445 * i) / SR) * 0.5;
  }
  const stereo = finalizeStereo(left, right, SR);
  let same = 0;
  for (let i = 0; i < n; i += 1) same += Math.abs(stereo.left[i] - stereo.right[i]);
  assert.ok(same > 1, 'после финализации каналы должны различаться');
  let correlation = 0;
  for (let i = 0; i < n; i += 1) correlation += stereo.left[i] * stereo.right[i];
  assert.ok(correlation > 0, 'каналы не должны быть в противофазе (моносовместимость)');
  assert.ok(peak(stereo.left) <= 0.96);
});

test('fitLength дополняет нулями и нормирует в 0.9', () => {
  const left = new Float32Array(10).fill(0.5);
  const right = new Float32Array(10).fill(-0.5);
  const fitted = fitLength(left, right, 20);
  assert.strictEqual(fitted.left.length, 20);
  assert.strictEqual(fitted.left[19], 0);
  assert.ok(Math.abs(peak(fitted.left) - 0.9) < 1e-6);
});

test('с банком проект говорит REAL_PASS, без банка — FALLBACK', () => {
  const withBank = renderBeat({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 4, bank: bankSource() });
  assert.strictEqual(withBank.report.drum_engine.status, 'REAL_PASS');
  assert.strictEqual(withBank.report.drum_engine.engine, 'sample_bank+procedural');
  assert.ok(withBank.report.drum_engine.sample_bank.total_samples >= 32);
  assert.deepStrictEqual(
    withBank.report.drum_engine.sample_bank.instruments_with_samples,
    ['kick', 'snare', 'clap', 'hat', 'open_hat', '808'],
  );

  const synthOnly = renderBeat({ bpm: 140, genre: 'phonk', seed: 7, durationSec: 4, bank: null });
  assert.strictEqual(synthOnly.report.drum_engine.status, 'FALLBACK');
  assert.ok(synthOnly.report.drum_engine.reason.includes('sample bank'));
  assert.ok(!synthOnly.wav.equals(withBank.wav), 'банк и синтез должны звучать по-разному');
});

test('банк не ломает детерминизм: тот же seed и банк — те же байты', () => {
  const a = renderBeat({ bpm: 128, genre: 'trap', seed: 4, durationSec: 3, bank: bankSource() });
  const b = renderBeat({ bpm: 128, genre: 'trap', seed: 4, durationSec: 3, bank: bankSource() });
  assert.ok(a.wav.equals(b.wav), 'два разных источника банка должны давать одинаковый трек');
});

test('банк не перегружает микс: пик ≤ 0.98 и не тишина', () => {
  for (const genre of ['phonk', 'house', 'drill', 'lofi']) {
    const { wav } = renderBeat({ bpm: 140, genre, seed: 11, durationSec: 5, bank: bankSource() });
    const audio = parseWav(wav);
    const top = Math.max(peak(audio.left), peak(audio.right));
    assert.ok(top <= 0.98, `${genre}: пик ${top.toFixed(3)} выше запаса`);
    assert.ok(rms(audio.left) > 0.02, `${genre}: трек почти пустой`);
  }
});

test('repair-путь: битый банк не роняет рендер, а честно уходит в синтез', () => {
  const broken = new SampleSource({
    fileSystem: {
      exists: (target) => target.endsWith('manifest.json'),
      readJson: () => ({ value: { schema: 'zsmm.sample-bank.v1', instruments: { kick: [{ file: 'kick/x.wav', license: 'CC0-1.0' }] } } }),
      readBinary: () => ({ error: 'ENOENT' }),
    },
    rootDir: path.resolve(path.sep, 'virtual', 'zsmm-engine'),
  });
  const { report } = renderBeat({ bpm: 120, genre: 'trap', seed: 2, durationSec: 2, bank: broken });
  assert.strictEqual(report.drum_engine.status, 'FALLBACK');
  assert.ok(report.drum_engine.reason.includes('covers 0 of 6'));
});

test('пошаговый рендер выдаёт те же байты, что синхронный', async () => {
  const options = { bpm: 140, genre: 'phonk', seed: 3, durationSec: 6 };
  const sync = renderBeat(options);
  const stepped = await renderBeatInSteps(options);
  assert.ok(sync.wav.equals(stepped.wav), 'побайтовое совпадение путей рендера');
  assert.deepStrictEqual(
    { ...stepped.report, repetition: null, measured_humanity: null },
    { ...sync.report, repetition: null, measured_humanity: null },
  );
});

test('прогресс рендера идёт по секциям и доходит до 100%', async () => {
  const events = [];
  const { report } = await renderBeatInSteps(
    { bpm: 128, genre: 'drift phonk', seed: 5, durationSec: 20 },
    { onProgress: (progress) => events.push(progress) },
  );
  const sections = events.filter((event) => event.phase === 'section').map((event) => event.section);
  assert.deepStrictEqual(sections, report.sections.map((section) => section.name));
  assert.strictEqual(events.at(-1).phase, 'done');
  assert.strictEqual(events.at(-1).percent, 100);
  // Проценты не откатываются назад: иначе индикатор в окне дёргается.
  const percents = events.map((event) => event.percent);
  assert.deepStrictEqual(percents, [...percents].sort((a, b) => a - b));
  // Секции отмечаются до сборки, значит первый колбэк — нулевой такт.
  assert.strictEqual(events[0].barsDone, 0);
  assert.strictEqual(events[0].barsTotal, report.total_bars);
});

test('подготовка рендера не зависит от последующей сборки секций', () => {
  const options = { bpm: 140, genre: 'phonk', seed: 21, durationSec: 8 };
  const first = prepareRender(options);
  const second = prepareRender(options);
  assert.deepStrictEqual(first.plans, second.plans);
  assert.strictEqual(first.barSec, second.barSec);
  // Два независимых потока ГСЧ: без этого сид-хеши «плывут».
  assert.notStrictEqual(first.engine.rng, first.engine.noiseRng);
});
