'use strict';
/**
 * core/audio/balance.js — спектральный баланс микса: измерение и коррекция.
 *
 * Вынесено из `master.js`: там файл упирался в лимит 400 строк, а сама задача
 * самостоятельная — «низ не должен съедать середину». Обещание без измерения
 * ничего не стоит, поэтому сначала `analysis.spectrumReport`, потом мягкая
 * коррекция и повторное измерение. Если после двух проходов низ всё ещё
 * доминирует, отчёт говорит это честно (`still_low_heavy`).
 */

const { filter } = require('./dsp');
const analysis = require('./analysis');

/**
 * Баланс микса: измерение → коррекция → повторное измерение.
 *
 * Измерение готовых треков показало 67–73 % энергии в полосе 60–250 Гц:
 * кик и 808 маскировали середину, и трек звучал «бочкой». Обещание «низ не
 * съедает середину» без измерения было ничем не подкреплено.
 *
 * Коррекция мягкая и детерминированная: срез низа ниже 120 Гц и подъём
 * полосы 250–4000 Гц. Обе операции — фильтры, а не «магия»: их слышно как
 * более читаемую мелодию и хэты, а не как эквалайзер «на глаз». Если после
 * двух проходов низ всё ещё доминирует, отчёт честно говорит об этом
 * (`still_low_heavy`), а не делает вид, что всё хорошо.
 */
function balanceMix(left, right, sr, { maxPasses = 2 } = {}) {
  const monoOf = () => {
    const mono = new Float32Array(left.length);
    for (let i = 0; i < left.length; i += 1) mono[i] = (left[i] + right[i]) * 0.5;
    return mono;
  };
  const before = analysis.spectrumReport(monoOf(), sr);
  let after = before;
  let passes = 0;
  if (!before.ok || !before.low_heavy) {
    return { before, after, passes, correction: null };
  }
  for (let pass = 0; pass < maxPasses && after.low_heavy; pass += 1) {
    for (const channel of [left, right]) {
      const low = filter('lowpass', channel, 120.0, sr, 3);
      const presence = filter('bandpass', channel, [250.0, 4000.0], sr, 2);
      for (let i = 0; i < channel.length; i += 1) {
        channel[i] = channel[i] - low[i] * 0.28 + presence[i] * 0.55;
      }
    }
    passes += 1;
    after = analysis.spectrumReport(monoOf(), sr);
  }
  return {
    before,
    after,
    passes,
    correction: { low_trim: 0.28, presence_boost: 0.55 },
    still_low_heavy: Boolean(after.low_heavy),
  };
}


module.exports = { balanceMix };
