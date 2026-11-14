'use strict';
/**
 * core/audio/engine.js — сборка трека: план, рендер, отчёт.
 *
 * Порт `modules/beat/arrangement.py` + `track_assembly.py` + `constructor.py`.
 * Здесь точка входа рендера и отчёт; подробности разложены по файлам:
 *
 *  * `bar.js`    — один такт и одна секция (что играет);
 *  * `master.js` — уровни, дроп, ширина, дрейф, шум, лимитер (как звучит);
 *  * `voices.js` — голоса и мотив хука; `arrangement.js` — план секций;
 *  * `wav.js`    — запись, `analysis.js` — замеры «формульности».
 *
 * Что сознательно отличается от Python-версии и почему:
 *
 *  * сэмпловый банк читается через `audio/bank.js`, поэтому статус движка
 *    REAL_PASS при покрытии ≥ 4 барабанных инструментов и FALLBACK иначе;
 *  * метрики «формульности» и «человечности» считаются здесь же
 *    (`analysis.js`), но не влияют на звук — только на отчёт;
 *  * «человечность» (`microtime.py`): дрейф темпа и шум комнаты есть, но
 *    наклон шума делается простым однополюсным ФНЧ вместо scipy-баттерворта;
 *  * рендер можно вести секциями (`renderBeatInSteps`): между секциями
 *    управление возвращается в цикл событий, поэтому окно не замирает и
 *    может показывать прогресс;
 *  * вокал миксуется до мастеринга (`mixVocal`) и называет свой источник в
 *    отчёте — тестовый дубль не выдаёт себя за запись с микрофона.
 */

const { Rng } = require('./rng');
const { zeros, peak } = require('./dsp');
const patterns = require('./patterns');
const arrangement = require('./arrangement');
const { VoiceEngine, isMajor } = require('./voices');
const drums = require('./instruments');
const bar = require('./bar');
const { mixVocal } = require('./vocal-mix');
const master = require('./master');
const takes = require('./takes');
const { encodeWav } = require('./wav');
const analysis = require('./analysis');

const SAMPLE_RATE = 44100;

// Сборка и мастеринг живут в отдельных модулях, но экспортируются отсюда:
// для вызывающего кода движок остаётся одним объектом.
const {
  buildBar,
  buildSection,
  SECTION_GAIN_DB,
  sectionTable,
  applyDrop,
  applyHookMotif,
  fitLength,
  finalizeStereo,
  tempoDrift,
  addRoomNoise,
  applyHumanity,
  limitBar,
  applyLowTrim,
} = master;

/**
 * Подготовить план и движок: общая часть синхронного и пошагового рендера.
 *
 * Дублировать её нельзя: любые расхождения в seed или velocity-карте сделают
 * «тот же seed» ложью между двумя путями рендера.
 */
function prepareRender({
  bpm = 140,
  key = 'A minor',
  genre = 'phonk',
  seed = 7,
  durationSec = 20,
  nVerses = 2,
  nChoruses = 2,
  aggression = 0.7,
  includeIntro = true,
  includeOutro = true,
  sections = null,
  bank = null,
  // Вокал: null — без голоса (как раньше), иначе готовый дубль из takes.js.
  vocalTake = null,
  vocalGain = 0.5,
} = {}) {
  if (!(bpm > 0)) throw new Error('bpm должен быть положительным');
  if (!(durationSec > 0)) throw new Error('durationSec должен быть положительным');

  const baseSeed = seed === null || seed === undefined ? 0 : seed;
  // Два независимых потока, как `_py_rng` и `_np_rng` в Python: человечность
  // и вариативность не должны зависеть от того, сколько сэмплов выбрал банк.
  const rng = new Rng(baseSeed);
  const drive = new Rng(baseSeed);
  const noise = new Rng((baseSeed ^ 0x9e3779b9) >>> 0);

  const slotPatterns = genre === 'legacy' ? patterns.LEGACY_PATTERN : patterns.slotPresetForGenre(genre);
  const velocityMap = genre === 'legacy'
    ? {
      kick: new Array(16).fill(1), snare: new Array(16).fill(1), hat: new Array(16).fill(1),
      bass: new Array(16).fill(1), melody: new Array(16).fill(1),
    }
    : patterns.velocityMapForGenre(genre);

  const engine = new VoiceEngine({
    bpm, key, genre, rng: drive, noiseRng: noise, slotPatterns, velocityMap, bank,
  });
  engine.aggression = aggression;

  const plans = sections && sections.length
    ? arrangement.sectionsFromArrangement(sections, bpm)
    : arrangement.planSections({
      bpm,
      durationSec,
      includeIntro,
      includeOutro,
      nVerses,
      nChoruses,
    });

  return {
    engine,
    plans,
    slotPatterns,
    bpm,
    key,
    genre,
    seed,
    durationSec,
    bank,
    barSec: (60.0 / bpm) * 4,
    vocalTake,
    vocalGain,
  };
}

/**
 * Завершить сборку: склеить секции, применить пост-обработку и записать WAV.
 *
 * @returns {{wav: Buffer, report: object}}
 */
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
    base.reason = 'sample bank is not connected to this render; synthesised one-shots are used';
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
    out.reason = 'drums come from the licensed sample bank';
  } else {
    out.reason = `sample bank covers ${covered.length} of 6 drum instruments; the rest is synthesised`;
  }
  if (report.errors && report.errors.length) out.sample_load_errors = report.errors.slice();
  return out;
}

/**
 * Полная сборка трека — замена `BeatConstructor.build_track`.
 *
 * @returns {{wav: Buffer, report: object}}
 */
function renderBeat({
  bpm = 140,
  key = 'A minor',
  genre = 'phonk',
  seed = 7,
  durationSec = 20,
  nVerses = 2,
  nChoruses = 2,
  aggression = 0.7,
  includeIntro = true,
  includeOutro = true,
  sections = null,
  float32 = false,
  // Источник сэмплов (`audio/bank.js::SampleSource`). Без него трек целиком
  // синтезируется, и отчёт честно говорит FALLBACK.
  bank = null,
  // Вокал: готовый дубль (файл, синтез или тестовый) и его уровень.
  vocalTake = null,
  vocalGain = 0.5,
} = {}) {
  const prepared = prepareRender({
    bpm, key, genre, seed, durationSec, nVerses, nChoruses, aggression,
    includeIntro, includeOutro, sections, bank, vocalTake, vocalGain,
  });
  const pieces = prepared.plans.map(
    (plan) => buildSection(prepared.engine, plan.name, plan.bars, plan),
  );
  const totalSamples = pieces.reduce((sum, piece) => sum + piece.left.length, 0);
  const left = zeros(totalSamples);
  const right = zeros(totalSamples);
  let cursor = 0;
  for (const piece of pieces) {
    left.set(piece.left, cursor);
    right.set(piece.right, cursor);
    cursor += piece.left.length;
  }
  return finishRender({ ...prepared, left, right, float32 });
}

/**
 * Рендер секциями: между секциями управление возвращается в цикл событий.
 *
 * Зачем: 3 минуты бита — это десятки секунд синхронной работы, и всё это
 * время окно не отвечает. Здесь работа режется по секциям, а прогресс
 * приходит колбэком `onProgress({index, total, section, barsDone, barsTotal})`.
 * Итоговый WAV побайтово совпадает с `renderBeat` — это проверяется тестом.
 */
async function renderBeatInSteps(
  options = {},
  { onProgress = null, yieldToEventLoop = true, isCancelled = null } = {},
) {
  const prepared = prepareRender(options);
  const { plans, barSec } = prepared;
  const barsTotal = plans.reduce((sum, plan) => sum + plan.bars, 0);
  const pieces = [];
  let barsDone = 0;

  for (const [index, plan] of plans.entries()) {
    // Отмена проверяется между секциями: бросать посреди такта незачем —
    // результат всё равно не попадёт в WAV, а секция считается быстро.
    if (typeof isCancelled === 'function' && isCancelled()) {
      const cancelled = new Error('рендер отменён');
      cancelled.name = 'RenderCancelled';
      throw cancelled;
    }
    if (typeof onProgress === 'function') {
      onProgress({
        phase: 'section',
        index,
        total: plans.length,
        section: plan.name,
        barsDone,
        barsTotal,
        percent: Math.round((barsDone / Math.max(1, barsTotal)) * 80),
      });
    }
    pieces.push(buildSection(prepared.engine, plan.name, plan.bars, plan));
    barsDone += plan.bars;
    if (typeof isCancelled === 'function' && isCancelled()) {
      const cancelled = new Error('рендер отменён');
      cancelled.name = 'RenderCancelled';
      throw cancelled;
    }
    if (yieldToEventLoop) await new Promise((resolve) => setImmediate(resolve));
  }

  if (typeof onProgress === 'function') {
    onProgress({
      phase: 'master',
      index: plans.length,
      total: plans.length,
      section: 'master',
      barsDone: barsTotal,
      barsTotal,
      percent: 90,
    });
  }
  if (yieldToEventLoop) await new Promise((resolve) => setImmediate(resolve));

  const totalSamples = pieces.reduce((sum, piece) => sum + piece.left.length, 0);
  const left = zeros(totalSamples);
  const right = zeros(totalSamples);
  let cursor = 0;
  for (const piece of pieces) {
    left.set(piece.left, cursor);
    right.set(piece.right, cursor);
    cursor += piece.left.length;
  }

  const result = finishRender({ ...prepared, left, right, float32: options.float32 === true });
  if (typeof onProgress === 'function') {
    onProgress({
      phase: 'done',
      index: plans.length,
      total: plans.length,
      section: 'done',
      barsDone: barsTotal,
      barsTotal,
      percent: 100,
      sectionSeconds: Math.round(barSec * 100) / 100,
    });
  }
  return result;
}

/**
 * Пост-обработка и запись: общая часть обоих путей рендера.
 *
 * @returns {{wav: Buffer, report: object}}
 */
function finishRender({
  plans, bpm, key, genre, seed, durationSec, bank, left, right, float32 = false,
  vocalTake = null, vocalGain = 0.5,
}) {
  const sr = SAMPLE_RATE;
  const barSec = (60.0 / bpm) * 4;
  const sectionInfo = sectionTable(plans, barSec);
  applyDrop(left, right, sectionInfo, sr);
  applyHookMotif(left, right, sectionInfo, sr, bpm, key);

  const target = Math.trunc(durationSec * sr);
  // Вокал миксуется до мастеринга: он часть трека, а не украшение поверх
  // готового микса. Источник называется в отчёте — тестовый дубль никогда
  // не выдаёт себя за запись с микрофона.
  const vocalInfo = mixVocal({ left, right, take: vocalTake, gain: vocalGain, sr, target });
  const fitted = fitLength(left, right, target);
  const stereo = finalizeStereo(fitted.left, fitted.right, sr);
  const humanity = applyHumanity(stereo.left, stereo.right, sr, seed);

  const wav = encodeWav([humanity.left, humanity.right], sr, { float32 });
  const dramaturgy = arrangement.structureReport(plans, bpm);

  // Отчёт «формульности» и «человечности» — по готовому миксу, как в Python.
  const mono = new Float32Array(humanity.left.length);
  for (let i = 0; i < mono.length; i += 1) mono[i] = (humanity.left[i] + humanity.right[i]) * 0.5;
  const repetition = analysis.repetitionReport(mono, sr, bpm);
  const measured = analysis.humanityReport(mono, sr);

  const slotPatterns = genre === 'legacy'
    ? patterns.LEGACY_PATTERN
    : patterns.slotPresetForGenre(genre);

  return {
    wav,
    report: {
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
      groove_family: patterns.familyForGenre(genre),
      drum_engine: drumEngineReport(bank),
      sections: sectionInfo,
      total_bars: plans.reduce((sum, plan) => sum + plan.bars, 0),
      dramaturgy,
      humanity: humanity.report,
      measured_humanity: measured,
      repetition,
      bytes: wav.length,
      slot_plan: Object.fromEntries(
        Object.entries(slotPatterns).map(([slot, row]) => [slot, row.concat(row, row, row)]),
      ),
      motif_is_major: isMajor(key),
      vocal: vocalInfo,
    },
  };
}

module.exports = {
  SAMPLE_RATE,
  SECTION_GAIN_DB,
  buildBar,
  buildSection,
  sectionTable,
  applyDrop,
  applyHookMotif,
  fitLength,
  finalizeStereo,
  tempoDrift,
  addRoomNoise,
  applyHumanity,
  limitBar,
  applyLowTrim,
  drumEngineReport,
  prepareRender,
  finishRender,
  renderBeat,
  renderBeatInSteps,
  mixVocal,
};
