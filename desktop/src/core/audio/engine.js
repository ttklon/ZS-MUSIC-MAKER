'use strict';
/**
 * core/audio/engine.js — сборка трека из секций.
 *
 * Порт `modules/beat/arrangement.py` + `track_assembly.py` + `constructor.py`.
 * Здесь только сборка: голоса живут в `voices.js`, план секций — в
 * `arrangement.js`, запись — в `wav.js`.
 *
 * Что сознательно отличается от Python-версии и почему:
 *
 *  * нет сэмплового банка — окно не читает `data/samples/`, поэтому движок
 *    честно помечен FALLBACK (в Python это происходит при пустом банке);
 *  * нет `short-time` FFT-метрик (`repetition_report`), они остаются в
 *    Python: для окна это отчёт, а не звук;
 *  * «человечность» (`microtime.py`) портирована частично: дрейф темпа есть,
 *    шум комнаты тоже, но без scipy-фильтров поверх шума — наклон делается
 *    простым однополюсным ФНЧ.
 */

const { Rng } = require('./rng');
const { filter, zeros, mixInto, peak } = require('./dsp');
const patterns = require('./patterns');
const variation = require('./variation');
const humanize = require('./humanize');
const arrangement = require('./arrangement');
const { VoiceEngine, hookMotif, motifLead, isMajor } = require('./voices');
const { encodeWav } = require('./wav');

const SAMPLE_RATE = 44100;

/**
 * Собрать один такт секции: барабаны, бас, гармония, мелодия, FX.
 *
 * @returns {{left: Float32Array, right: Float32Array}}
 */
function buildBar(engine, bar, section, plan, barSamples) {
  const left = zeros(barSamples);
  const right = zeros(barSamples);
  const stepSamples = Math.floor(barSamples / 16);
  const layers = plan ? plan.layers : ['drums', 'bass', 'pad', 'keys', 'melody', 'fx'];
  const variant = variation.barVariant(engine.rng, bar, section);

  engine.sectionEnergy = plan ? plan.energy : 0.6;

  const addMono = (audio, offset, pan, gain = 1.0) => {
    // Постоянная мощность: панорама не «съедает» громкость в центре.
    const angle = ((pan + 1.0) * Math.PI) / 4.0;
    mixInto(left, audio, offset, Math.cos(angle) * gain);
    mixInto(right, audio, offset, Math.sin(angle) * gain);
  };

  if (layers.includes('bass') && !['intro_pad', 'breakdown_silent', 'outro_fade'].includes(section)) {
    addMono(engine.generateBassLine(bar, barSamples), 0, 0.0);
  }

  if (layers.includes('drums') && !['intro_pad', 'breakdown_silent'].includes(section)) {
    for (let step = 0; step < 16; step += 1) {
      const stepStart = step * stepSamples;

      const kick = engine.generateKick(step, bar);
      addMono(kick, Math.max(0, stepStart + Math.trunc(engine.hitOffsetSec('kick', step, bar) * engine.sr)), 0.0);

      const snare = engine.generateSnare(step, bar);
      addMono(
        snare,
        Math.max(0, stepStart + Math.trunc(engine.hitOffsetSec('snare', step, bar) * engine.sr)),
        engine.rng.uniform(-0.05, 0.05),
      );

      // Хэты панорамируем (шире для стерео-поля). Пропуск шага — это и есть
      // вариация рисунка, а не ошибка сетки.
      if (variant.skipHatSteps.includes(step)) continue;
      const hat = engine.generateHihat(step, bar);
      addMono(
        hat,
        Math.max(0, stepStart + Math.trunc(engine.hitOffsetSec('hat', step, bar) * engine.sr)),
        step % 2 === 0 ? 0.45 : -0.45,
      );
    }

    // Сбивка в конце фразы: 32-е на малом, тише и с нарастанием.
    const fillSteps = humanize.ghostRollSteps(humanize.isFillBar(bar));
    if (fillSteps.length && ['verse', 'pre_chorus', 'hook', 'chorus'].includes(section)) {
      fillSteps.forEach((rollStep, index) => {
        const roll = engine.generateSnare(14, bar, 14);
        const crescendo = 0.35 + 0.2 * index;
        for (let i = 0; i < roll.length; i += 1) roll[i] *= crescendo;
        addMono(roll, rollStep * stepSamples, engine.rng.uniform(-0.08, 0.08));
      });
    }
  }

  // Гармония: пэд + аккордовые стабы (основа «трека», не только ритм)
  if (section !== 'breakdown_silent' && (layers.includes('pad') || layers.includes('keys'))) {
    addMono(engine.generateHarmony(bar, section, barSamples), 0, 0.0);
  }

  if (layers.includes('melody')) {
    addMono(engine.generateMelody(bar, section, barSamples), 0, engine.rng.uniform(-0.6, 0.6));
  }

  if (layers.includes('fx')) {
    addMono(engine.generateFx(bar, section, barSamples), 0, engine.rng.uniform(-0.85, 0.85));
  }

  // Саб-слой только в дропе: измеренный контраст низа ≥6 дБ.
  if (plan && plan.energy >= 0.85 && layers.includes('bass')) {
    const sub = engine.generateSub(bar, barSamples);
    for (let i = 0; i < sub.length; i += 1) sub[i] *= 0.45;
    addMono(sub, 0, 0.0);
  }

  // Ghost-ноты и добавочные хэты из вариации такта.
  for (const ghostStep of variant.ghostSnareSteps) {
    const ghost = engine.generateSnare(ghostStep, bar, ghostStep);
    for (let i = 0; i < ghost.length; i += 1) ghost[i] *= 0.22;
    addMono(ghost, Math.max(0, ghostStep * stepSamples), engine.rng.uniform(-0.12, 0.12));
  }
  for (const extraStep of variant.extraHatSteps) {
    const extra = engine.generateHihat(extraStep, bar, 0.45);
    addMono(extra, Math.max(0, extraStep * stepSamples), extraStep % 2 ? 0.25 : -0.25);
  }

  // Дыхание уровня такта (±0.3 дБ) — часть вариации.
  if (variant.barGainDb) {
    const gain = Math.pow(10, variant.barGainDb / 20);
    for (let i = 0; i < barSamples; i += 1) {
      left[i] *= gain;
      right[i] *= gain;
    }
  }

  return { left, right };
}

/** Спектральный трим низа: ВЧ-часть сохраняется, низ масштабируется. */
function applyLowTrim(left, right, bassGain, sr) {
  if (bassGain === 1.0) return;
  for (const channel of [left, right]) {
    const low = filter('lowpass', channel, 120.0, sr, 3);
    for (let i = 0; i < channel.length; i += 1) {
      channel[i] = channel[i] - low[i] + low[i] * bassGain;
    }
  }
}

/** Мягкое ограничение только того, что выше −3 dBFS. */
function limitBar(left, right) {
  const top = Math.max(peak(left), peak(right));
  if (top <= 0.99) return;
  // Колено −3 dBFS: ниже него сигнал не меняется вообще.
  const knee = Math.pow(10, -3 / 20);
  const ceiling = 0.99;
  for (const channel of [left, right]) {
    for (let i = 0; i < channel.length; i += 1) {
      const value = channel[i];
      const magnitude = Math.abs(value);
      if (magnitude <= knee) continue;
      const limited = knee + (ceiling - knee) * Math.tanh((magnitude - knee) / (ceiling - knee));
      channel[i] = value < 0 ? -limited : limited;
    }
  }
}

const SECTION_GAIN_DB = {
  intro: -8.0,
  intro_pad: -10.0,
  verse: -4.0,
  pre_chorus: -2.0,
  hook: 0.0,
  chorus: 0.0,
  breakdown: -8.0,
  breakdown_silent: -60.0,
  outro: -8.0,
  outro_fade: -10.0,
};

/** Собрать секцию из нескольких тактов (стерео). */
function buildSection(engine, section, nBars, plan) {
  const barSec = (60.0 / engine.bpm) * 4;
  const barSamples = Math.trunc(engine.sr * barSec);
  const left = zeros(barSamples * nBars);
  const right = zeros(barSamples * nBars);

  for (let bar = 0; bar < nBars; bar += 1) {
    const { left: barLeft, right: barRight } = buildBar(engine, bar, section, plan, barSamples);

    // Микро-мутации: во второй половине секции добавляем офф-бит хэты.
    if (bar >= Math.floor(nBars / 2) && (section === 'verse' || section === 'hook')) {
      const stepSamples = Math.floor(barSamples / 16);
      for (const offStep of [7, 15]) {
        const extra = engine.generateHihat(offStep, bar, 0.3 * engine.aggression);
        mixInto(barLeft, extra, offStep * stepSamples, Math.cos(Math.PI / 4) * 0.5);
        mixInto(barRight, extra, offStep * stepSamples, Math.sin(Math.PI / 4) * 0.5);
      }
    }

    if (plan) applyLowTrim(barLeft, barRight, plan.bassGain, engine.sr);
    limitBar(barLeft, barRight);

    left.set(barLeft, bar * barSamples);
    right.set(barRight, bar * barSamples);
  }

  const gainDb = SECTION_GAIN_DB[section] === undefined ? -2.0 : SECTION_GAIN_DB[section];
  const gain = Math.pow(10, gainDb / 20);
  for (let i = 0; i < left.length; i += 1) {
    left[i] *= gain;
    right[i] *= gain;
  }
  return { left, right };
}

/** Таблица секций: имя, такты, старт, громкость. */
function sectionTable(plans, barSec) {
  const info = [];
  let cursor = 0;
  for (const plan of plans) {
    info.push({
      name: plan.name,
      arrangement_name: plan.sourceName || plan.name,
      bars: plan.bars,
      start_sec: Math.round(cursor * 100) / 100,
      duration_sec: Math.round(plan.bars * barSec * 100) / 100,
      energy: plan.energy,
      gain_db: plan.gainDb,
      bass_gain: plan.bassGain,
      layers: plan.layers.slice(),
    });
    cursor += plan.bars * barSec;
  }
  return info;
}

/** 300 мс глубокий провал перед первым хуком: иначе «дроп» не читается. */
function applyDrop(left, right, sectionInfo, sr) {
  const first = sectionInfo.find((info) => info.name === 'hook' || info.name === 'chorus');
  if (!first) return;
  const index = Math.trunc(first.start_sec * sr);
  const fade = Math.trunc(0.3 * sr);
  if (index - fade <= 0) return;
  // Степень 4, а не линейный спад: нужен реальный провал тишины (~120 мс).
  for (let i = 0; i < fade; i += 1) {
    const gain = Math.pow(1.0 - i / fade, 4);
    left[index - fade + i] *= gain;
    right[index - fade + i] *= gain;
  }
}

/** Повторяющийся лид-мотив в интро и припевах (hook_repeatability). */
function applyHookMotif(left, right, sectionInfo, sr, bpm, key) {
  const motif = hookMotif(key);
  const barSec = (60.0 / bpm) * 4;
  const noteSamples = Math.trunc((barSec / 4.0) * sr);
  const forHook = ['hook', 'chorus'];
  const forMotif = ['hook', 'chorus', 'intro'];
  let index = 0;
  for (const info of sectionInfo) {
    if (!forMotif.includes(info.name)) continue;
    const start = Math.trunc(info.start_sec * sr);
    const length = Math.trunc(info.duration_sec * sr);
    let position = start;
    let note = index;
    while (position + noteSamples < start + length && position + noteSamples < left.length) {
      const lead = motifLead(sr, motif[note % 4], noteSamples / sr);
      const pan = note % 2 === 0 ? 0.15 : -0.15;
      const gain = forHook.includes(info.name) ? 0.12 : 0.085;
      const angle = ((pan + 1.0) * Math.PI) / 4.0;
      mixInto(left, lead, position, Math.cos(angle) * gain);
      mixInto(right, lead, position, Math.sin(angle) * gain);
      position += noteSamples;
      note += 1;
    }
    index = note;
  }
}

/** Обрезка/дополнение до запрошенной длительности и нормировка по пику. */
function fitLength(left, right, targetSamples) {
  const fit = (channel) => {
    if (channel.length === targetSamples) return channel;
    const out = zeros(targetSamples);
    out.set(channel.subarray(0, Math.min(channel.length, targetSamples)));
    return out;
  };
  const fittedLeft = fit(left);
  const fittedRight = fit(right);
  const top = Math.max(peak(fittedLeft), peak(fittedRight)) + 1e-9;
  if (top > 0) {
    for (let i = 0; i < targetSamples; i += 1) {
      fittedLeft[i] = (fittedLeft[i] / top) * 0.9;
      fittedRight[i] = (fittedRight[i] / top) * 0.9;
    }
  }
  return { left: fittedLeft, right: fittedRight };
}

/** Финальная mid/side-ширина с сохранением моносовместимости. */
function finalizeStereo(left, right, sr) {
  const n = left.length;
  const mid = new Float32Array(n);
  const side = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    mid[i] = (left[i] + right[i]) * 0.5;
    side[i] = (left[i] - right[i]) * 0.5;
  }
  const highMid = filter('highpass', mid, 800.0, sr, 4);
  // Разность исходного и задержанного ВЧ-сигнала декоррелирована с центром.
  const delay = Math.max(1, Math.trunc(sr * 0.015));
  const widthSeed = new Float32Array(n);
  for (let i = 0; i < n; i += 1) widthSeed[i] = i >= delay ? highMid[i] - highMid[i - delay] : highMid[i];

  const rmsOf = (channel) => {
    let sum = 0;
    for (let i = 0; i < channel.length; i += 1) sum += channel[i] * channel[i];
    return Math.sqrt(sum / Math.max(1, channel.length));
  };
  const seedRms = rmsOf(widthSeed) + 1e-12;
  const midRms = rmsOf(mid) + 1e-12;
  const sideRms = rmsOf(side) + 1e-12;
  // S/M≈0.30 даёт межканальную корреляцию около 0.83–0.95: заметная ширина
  // без инверсии фазы.
  const targetSideRms = Math.max(sideRms, midRms * 0.3);
  const outLeft = new Float32Array(n);
  const outRight = new Float32Array(n);
  if (seedRms > 1e-8 && midRms > 1e-8) {
    const k = targetSideRms / seedRms;
    let candidateRms = 0;
    for (let i = 0; i < n; i += 1) {
      const value = side[i] + widthSeed[i] * k;
      candidateRms += value * value;
    }
    candidateRms = Math.sqrt(candidateRms / Math.max(1, n)) + 1e-12;
    const norm = targetSideRms / candidateRms;
    for (let i = 0; i < n; i += 1) {
      const value = (side[i] + widthSeed[i] * k) * norm;
      outLeft[i] = mid[i] + value;
      outRight[i] = mid[i] - value;
    }
  } else {
    outLeft.set(mid);
    outRight.set(mid);
  }
  const top = Math.max(peak(outLeft), peak(outRight)) + 1e-9;
  if (top > 0.98) {
    const gain = 0.95 / top;
    for (let i = 0; i < n; i += 1) {
      outLeft[i] *= gain;
      outRight[i] *= gain;
    }
  }
  return { left: outLeft, right: outRight };
}

/** Плавный дрейф темпа ±amountPct процентов (линейная интерполяция). */
function tempoDrift(left, right, sr, amountPct = 0.2, periodSec = 45.0) {
  const n = left.length;
  if (!n || amountPct <= 0) return { left, right, report: { drift_pct: 0.0, peak_deviation_ms: 0.0 } };
  const rate = new Float64Array(n);
  const positions = new Float64Array(n);
  let sum = 0;
  for (let i = 0; i < n; i += 1) {
    rate[i] = 1.0 + (amountPct / 100.0) * Math.sin((2.0 * Math.PI * (i / sr)) / Math.max(periodSec, 1e-6));
    sum += rate[i];
    positions[i] = sum;
  }
  const scale = (n - 1) / positions[n - 1];
  let deviation = 0;
  for (let i = 0; i < n; i += 1) {
    positions[i] *= scale;
    deviation = Math.max(deviation, Math.abs(positions[i] - i));
  }
  const warp = (channel) => {
    const out = new Float32Array(n);
    let cursor = 0;
    for (let i = 0; i < n; i += 1) {
      while (cursor < positions[i] && cursor < n - 1) cursor += 1;
      const hi = cursor;
      const lo = Math.max(0, hi - 1);
      const span = positions[i] - lo;
      out[i] = channel[lo] + (channel[hi] - channel[lo]) * Math.min(1, Math.max(0, span));
    }
    return out;
  };
  return {
    left: warp(left),
    right: warp(right),
    report: {
      drift_pct: amountPct,
      period_sec: periodSec,
      peak_deviation_ms: Math.round((deviation / sr) * 1000 * 100) / 100,
    },
  };
}

/** Шумовой пол комнаты: −62 dBFS по умолчанию, спад ниже 40 Гц и выше 4 кГц. */
function addRoomNoise(left, right, sr, levelDbfs = -62.0, seed = 20260101) {
  const rng = new Rng(seed);
  const n = left.length;
  if (!n) return { left, right, report: { noise_dbfs: -120.0 } };
  const lowpass = (channel) => {
    // Однополюсный ФНЧ: scipy-баттерворта тут нет, но наклон нужен.
    const alpha = Math.min(0.9, (2 * Math.PI * 4000.0) / sr);
    const out = new Float32Array(n);
    let state = 0;
    for (let i = 0; i < n; i += 1) {
      state += alpha * (channel[i] - state);
      out[i] = state;
    }
    return out;
  };
  const highAlpha = Math.min(0.9, (2 * Math.PI * 40.0) / sr);
  const highpassNoise = (channel) => {
    const out = new Float32Array(n);
    let state = 0;
    for (let i = 0; i < n; i += 1) {
      state += highAlpha * (channel[i] - state);
      out[i] = channel[i] - state;
    }
    return out;
  };
  const leftNoise = highpassNoise(lowpass(rng.noise(n)));
  const rightNoise = highpassNoise(lowpass(rng.noise(n)));
  let sum = 0;
  for (let i = 0; i < n; i += 1) sum += (leftNoise[i] * leftNoise[i] + rightNoise[i] * rightNoise[i]) / 2;
  const rmsNow = Math.sqrt(sum / n) + 1e-12;
  const target = Math.pow(10, levelDbfs / 20);
  const gain = target / rmsNow;
  for (let i = 0; i < n; i += 1) {
    left[i] += leftNoise[i] * gain;
    right[i] += rightNoise[i] * gain;
  }
  return {
    left,
    right,
    report: {
      noise_dbfs: Math.round(levelDbfs * 10) / 10,
      noise_rms_dbfs: Math.round(20 * Math.log10(Math.max(rmsNow * gain, 1e-12)) * 100) / 100,
    },
  };
}

/** «Человеческие шероховатости»: дрейф темпа ±0.2 % и шум комнаты. */
function applyHumanity(left, right, sr, seed) {
  const drifted = tempoDrift(left, right, sr);
  const noisy = addRoomNoise(drifted.left, drifted.right, sr, -62.0, seed === null || seed === undefined ? 0 : seed);
  const top = Math.max(peak(noisy.left), peak(noisy.right)) + 1e-9;
  if (top > 0.98) {
    const gain = 0.95 / top;
    for (let i = 0; i < noisy.left.length; i += 1) {
      noisy.left[i] *= gain;
      noisy.right[i] *= gain;
    }
  }
  return {
    left: noisy.left,
    right: noisy.right,
    report: {
      tempo_drift: drifted.report,
      room_noise: noisy.report,
      peak: Math.round(peak(noisy.left) * 10000) / 10000,
    },
  };
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
} = {}) {
  if (!(bpm > 0)) throw new Error('bpm должен быть положительным');
  if (!(durationSec > 0)) throw new Error('durationSec должен быть положительным');

  const sr = SAMPLE_RATE;
  const rng = new Rng(seed === null || seed === undefined ? 0 : seed);
  const drive = new Rng(seed === null || seed === undefined ? 0 : seed);

  const slotPatterns = genre === 'legacy' ? patterns.LEGACY_PATTERN : patterns.slotPresetForGenre(genre);
  const velocityMap = genre === 'legacy'
    ? { kick: new Array(16).fill(1), snare: new Array(16).fill(1), hat: new Array(16).fill(1), bass: new Array(16).fill(1), melody: new Array(16).fill(1) }
    : patterns.velocityMapForGenre(genre);

  const engine = new VoiceEngine({ bpm, key, genre, rng: drive, slotPatterns, velocityMap });
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

  const barSec = (60.0 / bpm) * 4;
  const pieces = plans.map((plan) => buildSection(engine, plan.name, plan.bars, plan));
  const totalSamples = pieces.reduce((sum, piece) => sum + piece.left.length, 0);
  let left = zeros(totalSamples);
  let right = zeros(totalSamples);
  let cursor = 0;
  for (const piece of pieces) {
    left.set(piece.left, cursor);
    right.set(piece.right, cursor);
    cursor += piece.left.length;
  }

  const sectionInfo = sectionTable(plans, barSec);
  applyDrop(left, right, sectionInfo, sr);
  applyHookMotif(left, right, sectionInfo, sr, bpm, key);

  const target = Math.trunc(durationSec * sr);
  const fitted = fitLength(left, right, target);
  left = fitted.left;
  right = fitted.right;

  const stereo = finalizeStereo(left, right, sr);
  const humanity = applyHumanity(stereo.left, stereo.right, sr, seed);

  const wav = encodeWav([humanity.left, humanity.right], sr, { float32 });
  const dramaturgy = arrangement.structureReport(plans, bpm);

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
      drum_engine: { ...require('./instruments').CAPABILITIES },
      sections: sectionInfo,
      total_bars: plans.reduce((sum, plan) => sum + plan.bars, 0),
      dramaturgy,
      humanity: humanity.report,
      bytes: wav.length,
      slot_plan: Object.fromEntries(
        Object.entries(slotPatterns).map(([slot, row]) => [slot, row.concat(row, row, row)]),
      ),
      motif_is_major: isMajor(key),
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
  renderBeat,
};
