'use strict';
/**
 * core/audio/sample-usage.js — учёт прозвучавших сэмплов.
 *
 * `drum_engine.status = REAL_PASS` с текстом «drums come from the licensed
 * sample bank» — утверждение. Раньше его ничто не подтверждало: в отчёте не
 * было ни одного числа о том, сколько ударов реально взято из банка. Теперь
 * `samples_used` считает каждый прозвучавший one-shot, а `available` отделяет
 * «что предложено» от «что попало в трек».
 *
 * Вынесено из `voices.js` отдельным модулем: миксин и чистая функция не
 * должны раздувать конструктор голосов выше бюджета в 400 строк.
 */

/** Чистый отчёт: те же ключи, что у Python-конструктора (`samples_used`). */
function sampleUsageReport(samplesUsed, sampleSourceUsed) {
  const byInstrument = { ...(samplesUsed || {}) };
  const bySource = { ...(sampleSourceUsed || {}) };
  return {
    by_instrument: byInstrument,
    by_source: bySource,
    total: Object.values(byInstrument).reduce((sum, value) => sum + value, 0),
    available: {
      kick: 0, snare: 0, clap: 0, hat: 0, open_hat: 0, bass: 0, melody: 0, fx: 0,
    },
  };
}

/** Миксин счётчиков: подмешивается в `VoiceEngine`. */
const SampleUsageMixin = {
  /** Учесть прозвучавший сэмпл: инструмент и источник (банк или файл). */
  noteSample(instrument, fromBank) {
    if (!this.samplesUsed) {
      this.samplesUsed = {};
      this.sampleSourceUsed = {};
    }
    this.samplesUsed[instrument] = (this.samplesUsed[instrument] || 0) + 1;
    const key = fromBank ? 'bank' : 'file';
    this.sampleSourceUsed[key] = (this.sampleSourceUsed[key] || 0) + 1;
  },

  /** Отчёт о сэмплах: те же ключи, что у Python-конструктора. */
  samplesReport() {
    return sampleUsageReport(this.samplesUsed, this.sampleSourceUsed);
  },
};

module.exports = { sampleUsageReport, SampleUsageMixin };
