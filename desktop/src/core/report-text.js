'use strict';
/* В браузере все `<script>` делят одну глобальную область: второй
   верхнеуровневый `const` с тем же именем роняет файл целиком. Поэтому
   функции живут внутри IIFE, а наружу отдаётся одно имя (`ZSMM_REPORT_TEXT`). */
(function () {
/**
 * core/report-text.js — текстовые строки отчёта о бите.
 *
 * Чистые функции от объекта отчёта: их можно проверить без DOM, и раздел
 * «Бит» перестал расти выше бюджета в 400 строк. Отчёт — то место, где
 * приложение говорит человеку, что получилось, поэтому строки живут отдельно
 * от разметки.
 */

/**
 * Текстовые строки отчёта — чистые функции, вынесены из `sections/beat.js`.
 *
 * Раздел окна и так упирался в бюджет 400 строк; главное — это и есть место,
 * где отчёт говорит человеку, что получилось: «прозвучало сэмплов», «баланс
 * полос». Чистые функции от объекта отчёта проверяются без DOM.
 */
/** Как описан вокал: источник, уровень, сколько секунд попало в микс. */
function describeVocal(vocal) {
  if (!vocal) return 'не подключён';
  const source = vocal.label || vocal.engine || 'источник не назван';
  const gain = typeof vocal.gain === 'number' ? `, уровень ${vocal.gain}` : '';
  const mixed = typeof vocal.mixed_seconds === 'number' ? `, в миксе ${vocal.mixed_seconds} с` : '';
  return `${source}${gain}${mixed}`;
}

function describeSamples(samples) {
  if (!samples) return 'не считалось';
  const parts = Object.entries(samples.by_instrument || {})
    .map(([name, count]) => `${name} ${count}`).join(', ');
  return `${samples.total} (${parts || 'синтез'})`;
}

function describeSpectrum(spectrum, mixBalance) {
  if (!spectrum || spectrum.ok !== true) {
    return `не измерен: ${(spectrum && spectrum.reason) || 'нет данных'}`;
  }
  const bands = `низ ${spectrum.bands.low}, середина ${spectrum.bands.mid}, `
    + `верх ${spectrum.bands.high} — ${spectrum.reason}`;
  const passes = mixBalance && mixBalance.passes;
  return passes ? `${bands} (правка баланса: ${passes} проход(а))` : bands;
}

// Экспорт для Node (тесты) и для браузера — два способа живут рядом, потому
// что файл грузится и как `<script>`, и как CommonJS.
if (typeof window !== 'undefined') {
  window.ZSMM_REPORT_TEXT = { describeVocal, describeSamples, describeSpectrum };
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { describeVocal, describeSamples, describeSpectrum };
}
})();
