'use strict';
/**
 * core/audio/report.js — отчёт о собранном бите.
 *
 * Вынесено из `engine.js`: файл упирался в лимит 400 строк, а отчёт — это
 * отдельная обязанность. Здесь же важно, чтобы ни одно число не было
 * «обещанием»: `drum_engine` говорит, чем сыгран трек, `samples_used` —
 * сколько сэмплов реально прозвучало, `spectrum` — измеренный баланс полос,
 * `mix_balance` — правился ли он и сколько раз.
 */

const { drumEngineReport } = require('./engine-report');
const { isMajor } = require('./voices');

/** Полный отчёт о рендере: те же поля, что у Python-конструктора. */
function buildReport({
  sr, float32, humanity, bpm, key, genre, seed, bank, engine, sectionInfo,
  plans, dramaturgy, balance, measured, repetition, wav, isMajorKey,
  slotPatterns, vocalInfo, loudness = null,
}) {
  return {
    ok: true,
    sample_rate: sr,
    channels: 2,
    bits: float32 ? 32 : 16,
    duration_sec: Math.round((humanity.left.length / sr) * 100) / 100,
    bpm,
    key,
    genre,
    seed: seed === null || seed === undefined ? null : seed,
    deterministic: seed !== null && seed !== undefined,
    groove_family: require('./patterns').familyForGenre(genre),
    drum_engine: drumEngineReport(bank),
    // `drum_engine` говорит, что банк покрывает инструменты; `samples_used`
    // — сколько сэмплов реально прозвучало. Без второго числа первый статус
    // был утверждением без факта.
    samples_used: engine && engine.samplesReport ? engine.samplesReport() : null,
    sections: sectionInfo,
    total_bars: plans.reduce((sum, plan) => sum + plan.bars, 0),
    dramaturgy,
    humanity: humanity.report,
    measured_humanity: measured,
    // Баланс полос — измерение, а не обещание: он попадает в отчёт и в окно.
    spectrum: balance.after,
    // Громкость по BS.1770: целевая, фактическая и сколько дБ добавлено.
    loudness: loudness || null,
    mix_balance: {
      bands_before: balance.before.bands,
      passes: balance.passes,
      correction: balance.correction,
      still_low_heavy: Boolean(balance.still_low_heavy),
    },
    repetition,
    bytes: wav.length,
    slot_plan: Object.fromEntries(
      Object.entries(slotPatterns).map(([slot, row]) => [slot, row.concat(row, row, row)]),
    ),
    motif_is_major: isMajorKey === undefined ? isMajor(key) : isMajorKey,
    vocal: vocalInfo,
  };
}

module.exports = { buildReport };
