'use strict';
/**
 * test/vocal.test.js — движок вокала: слоги, мелодия, длительность, честность.
 *
 * Проверяются свойства, которые видит пользователь: строка поётся столько,
 * сколько надо, сигнал не врёт (нет NaN, пик ≤ 1), один сид даёт один
 * результат, мелодия остаётся в тональности и в разборчивом диапазоне.
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const vocal = require('../src/core/audio/vocal');

const TEXT = 'я читаю твой трек наизусть';

test('слоги делятся по гласным, согласные остаются при слоге', () => {
  const syllables = vocal.splitSyllables(TEXT);
  assert.ok(syllables.length >= 7, `слогов ${syllables.length}, ожидалось не меньше 7`);
  for (const syllable of syllables) {
    assert.equal(typeof syllable.text, 'string');
    assert.ok(syllable.text.length > 0, 'пустой слог');
    assert.ok(/[аеёиоуыэюяaeiouy]/i.test(syllable.text), `в слоге «${syllable.text}» нет гласной`);
  }
});

test('латиница делится так же, как кириллица', () => {
  const syllables = vocal.splitSyllables('i read your track by heart');
  assert.ok(syllables.length >= 6, `слогов ${syllables.length}`);
});

test('singLine возвращает сигнал нужной длины и без NaN', () => {
  const sr = 44100;
  const { signal, syllables, notes } = vocal.singLine({ text: TEXT, sr, seed: 3 });
  assert.ok(signal.length > sr * 0.5, 'строка короче половины секунды');
  assert.equal(notes.length, syllables.length);
  for (let i = 0; i < signal.length; i += 1) {
    assert.ok(Number.isFinite(signal[i]), `NaN в сэмпле ${i}`);
  }
  let peak = 0;
  for (let i = 0; i < signal.length; i += 1) peak = Math.max(peak, Math.abs(signal[i]));
  assert.ok(peak > 0.1, `слишком тихо: пик ${peak}`);
  assert.ok(peak <= 1.0001, `пик ${peak} выше единицы`);
});

test('стиль rap звучит короче той же строки в стиле sung', () => {
  const sr = 22050;
  const sung = vocal.singLine({ text: TEXT, sr, seed: 5, style: 'sung' });
  const rap = vocal.singLine({ text: TEXT, sr, seed: 5, style: 'rap' });
  assert.ok(rap.signal.length < sung.signal.length, 'rap должен быть плотнее по времени');
});

test('один сид — один и тот же результат, разные сиды различаются', () => {
  const a = vocal.singLine({ text: TEXT, sr: 22050, seed: 11 });
  const b = vocal.singLine({ text: TEXT, sr: 22050, seed: 11 });
  const c = vocal.singLine({ text: TEXT, sr: 22050, seed: 12 });
  assert.equal(a.signal.length, b.signal.length);
  let diff = 0;
  for (let i = 0; i < a.signal.length; i += 1) diff += Math.abs(a.signal[i] - b.signal[i]);
  assert.ok(diff < 1e-6, 'один сид дал разные сигналы');
  let other = 0;
  for (let i = 0; i < Math.min(a.signal.length, c.signal.length); i += 1) {
    other += Math.abs(a.signal[i] - c.signal[i]);
  }
  assert.ok(other > 1e-3, 'разные сиды дали одинаковый сигнал');
});

test('мелодия держится в разборчивом диапазоне и в тональности', () => {
  const MAJOR = [0, 2, 4, 5, 7, 9, 11];
  const MINOR = [0, 2, 3, 5, 7, 8, 10];
  for (const key of ['A minor', 'C major', 'F# minor', 'D minor']) {
    const notes = vocal.melodyFor({ key, count: 12, seed: 4 });
    assert.equal(notes.length, 12);
    for (const note of notes) {
      assert.ok(note >= 55 && note <= 74, `${key}: нота ${note} вне диапазона 55…74`);
      const pitch = ((note % 12) + 12) % 12;
      const root = { A: 9, C: 0, 'F#': 6, D: 2 }[key.split(' ')[0]];
      const scale = /major/i.test(key) ? MAJOR : MINOR;
      const degree = ((pitch - root) % 12 + 12) % 12;
      assert.ok(scale.includes(degree), `${key}: нота ${note} не из лада (ступень ${degree})`);
    }
  }
});

test('мелодия не прыгает случайно: шаги остаются небольшими', () => {
  const notes = vocal.melodyFor({ key: 'A minor', count: 24, seed: 9 });
  for (let i = 1; i < notes.length; i += 1) {
    const step = Math.abs(notes[i] - notes[i - 1]);
    assert.ok(step <= 4, `прыжок ${step} полутонов между ${notes[i - 1]} и ${notes[i]}`);
  }
});

test('пустой текст не ломает синтез, а честно возвращает пустоту', () => {
  // Пустая строка — это не ошибка и не «тишина вместо голоса»: сигнала нет,
  // и вызывающий код сам решает, откуда взять текст.
  const empty = vocal.singLine({ text: '', sr: 16000, seed: 1 });
  assert.equal(empty.signal.length, 0);
  assert.deepEqual(empty.syllables, []);
  assert.deepEqual(empty.notes, []);

  // Текст из одних согласных тоже даёт пустоту, а не мусор.
  const consonants = vocal.singLine({ text: 'бррр', sr: 16000, seed: 1 });
  assert.equal(consonants.signal.length, 0);
});
