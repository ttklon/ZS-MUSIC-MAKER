'use strict';
/**
 * core/audio/vocal-mix.js — как вокальный дубль попадает в микс.
 *
 * Отдельный файл по двум причинам: это единственное место, где микс знает про
 * вокал (источник, уровень, обрезка), и `engine.js` упирался в лимит 400 строк.
 *
 * Правило честности: функция возвращает не «ок», а описание дубля из
 * `takes.describeTake`, включая `simulated`. Тестовый дубль, попавший в трек,
 * остаётся помеченным как имитация и в отчёте.
 */

const takes = require('./takes');

/**
 * Подмешать вокальный дубль в стерео-микс.
 *
 * Дубль приводится к частоте движка, получает собственный уровень и лёгкое
 * расширение стерео (задержка 9 мс справа): голос в центре микса звучит
 * «наклеенно», а копия с задержкой — как живая запись.
 *
 * @param {object} params
 * @param {Float32Array} params.left
 * @param {Float32Array} params.right
 * @param {object|null} params.take   результат takes.testTake/synthTake/loadTake
 * @param {number} params.gain        0…1
 * @param {number} params.sr
 * @param {number} params.target      длина микса в сэмплах
 * @returns {object|null} описание для отчёта либо null, если вокала нет
 */
function mixVocal({ left, right, take, gain, sr, target }) {
  if (!take || !take.signal || !take.signal.length) return null;
  const source = take.sampleRate && take.sampleRate !== sr
    ? takes.resample(take.signal, take.sampleRate, sr)
    : take.signal;
  const level = Math.max(0, Math.min(1, Number(gain) || 0));
  const delay = Math.round(0.009 * sr);
  const n = Math.min(target, source.length);
  for (let i = 0; i < n; i += 1) {
    const dry = source[i] * level;
    left[i] += dry * 0.92;
    // Правая сторона с задержкой — эффект «двойного дубля» без реверба.
    right[i] += i >= delay ? source[i - delay] * level : dry;
  }
  const info = takes.describeTake(take);
  return {
    ...info,
    gain: Math.round(level * 100) / 100,
    mixed_seconds: Math.round((n / sr) * 100) / 100,
    starts_outside: source.length > target,
  };
}

module.exports = { mixVocal };
