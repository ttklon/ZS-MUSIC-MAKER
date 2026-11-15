'use strict';
/**
 * core/audio/engine-report.js — отчёт об источнике звука (банк или синтез).
 *
 * Вынесено из `engine.js` (лимит 400 строк) и остаётся честным: имя движка
 * `sample_bank+procedural` ставится только когда из банка покрыто ≥ 4
 * барабанных инструмента, иначе FALLBACK с причиной, сколько покрыто.
 * Сколько сэмплов реально прозвучало — отдельный счётчик `samples_used`
 * в отчёте рендера: статус без числа был утверждением без факта.
 */

const drums = require('./instruments');

/**
 * Отчёт об источнике звука — замена `_drum_engine_report()` из Python.
 *
 * Правило то же: если из банка покрыто ≥ 4 барабанных инструмента, статус
 * REAL_PASS и имя движка не врёт (`sample_bank+procedural`); иначе FALLBACK с
 * причиной, сколько инструментов реально покрыто.
 */
function drumEngineReport(bank) {
  const base = { ...drums.CAPABILITIES };
  if (!bank || typeof bank.report !== 'function') {
    base.reason = 'банк сэмплов не подключён к этому рендеру: удары синтезированы';
    return base;
  }
  const report = bank.report();
  const covered = (report.drum_instruments_with_samples || [])
    .filter((name) => ['kick', 'snare', 'clap', 'hat', 'open_hat', '808'].includes(name));
  const out = {
    ...base,
    sample_bank: {
      instruments_with_samples: covered,
      total_samples: report.total_samples || 0,
      loaded_samples: report.loaded_samples || 0,
      velocity_mode: report.velocity_mode,
    },
  };
  if (covered.length >= 4) {
    out.status = 'REAL_PASS';
    out.engine = 'sample_bank+procedural';
    out.reason = 'удары взяты из лицензионного банка сэмплов';
  } else {
    out.reason = `банк покрывает ${covered.length} из 6 барабанных инструментов, остальное синтезировано`;
  }
  if (report.errors && report.errors.length) out.sample_load_errors = report.errors.slice();
  return out;
}


module.exports = { drumEngineReport };
