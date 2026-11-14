'use strict';
/**
 * core/audio/arrangement.js — драматургия трека и сетка секций.
 *
 * Порт `modules/beat/dramaturgy.py`. Трек отличается от «лупа на три минуты»
 * тем, что у него есть кривая: вход, нарастание, дроп, спад, выход. Здесь —
 * план секций (`planSections`), энергия и трим низа по секциям, потолок
 * плотности слоёв и отчёт структуры.
 *
 * Функции чистые: одинаковый вход — одинаковая структура.
 */

// Энергия секции по умолчанию (0…1). Дроп — 1.0, куплет — около 0.6.
const SECTION_ENERGY = {
  intro: 0.42,
  intro_pad: 0.32,
  verse: 0.62,
  pre_chorus: 0.78,
  hook: 1.0,
  chorus: 1.0,
  bridge: 0.48,
  breakdown: 0.3,
  breakdown_silent: 0.0,
  outro: 0.4,
  outro_fade: 0.28,
};

// Потолок одновременных слоёв: анти-«каша».
const MAX_LAYERS = {
  intro: 3,
  intro_pad: 2,
  verse: 5,
  pre_chorus: 5,
  hook: 7,
  chorus: 7,
  bridge: 3,
  breakdown: 2,
  breakdown_silent: 0,
  outro: 3,
  outro_fade: 2,
};

const LAYER_ORDER = ['drums', 'bass', 'pad', 'keys', 'melody', 'fx', 'hook_lead'];

// Трим низа по секциям: куплет звучит «суше», дроп — полноценно.
const LOW_TRIM = {
  intro: 0.58,
  intro_pad: 0.48,
  verse: 0.55,
  pre_chorus: 0.8,
  hook: 1.0,
  chorus: 1.0,
  bridge: 0.5,
  breakdown: 0.45,
  breakdown_silent: 0.0,
  outro: 0.6,
  outro_fade: 0.5,
};

// Базовые размеры секций в тактах (4/4).
const BASE_BARS = { intro: 4, verse: 8, pre_chorus: 4, hook: 8, bridge: 4, outro: 4 };

const TARGET_MIN_SEC = 150.0;
const TARGET_MAX_SEC = 210.0;
const HOOK_WITHIN_SEC = 15.0;

const ARRANGEMENT_SECTION_ALIASES = {
  intro: 'intro',
  intro_pad: 'intro_pad',
  verse: 'verse',
  prechorus: 'pre_chorus',
  pre_chorus: 'pre_chorus',
  build: 'pre_chorus',
  chorus: 'chorus',
  hook: 'hook',
  drop: 'hook',
  bridge: 'bridge',
  break: 'breakdown',
  breakdown: 'breakdown',
  outro: 'outro',
  outro_fade: 'outro_fade',
};

/** Каноническое имя секции бита для имени из плана аранжировки. */
function canonicalSectionName(name) {
  const raw = String(name || '').trim().toLowerCase();
  const stripped = raw.replace(/[0-9]+$/, '');
  return ARRANGEMENT_SECTION_ALIASES[stripped] || ARRANGEMENT_SECTION_ALIASES[raw] || 'verse';
}

/** Слои секции с учётом потолка плотности и её энергии. */
function layersForSection(name, energy) {
  let limit = MAX_LAYERS[name] === undefined ? 5 : MAX_LAYERS[name];
  if (energy >= 0.9) limit = Math.max(limit, 6);
  let allowed = LAYER_ORDER.slice(0, limit);
  if (name === 'intro' || name === 'intro_pad') {
    // Правило TikTok: мотив хука звучит с первых тактов.
    allowed = ['drums', 'pad', 'hook_lead'];
  }
  if (name === 'outro' || name === 'outro_fade' || name === 'breakdown') {
    // В аутро и бридже остаётся атмосфера, мотив уходит в тень.
    allowed = ['pad', 'keys', 'drums'];
  }
  if ((name === 'verse' || name === 'pre_chorus') && allowed.includes('hook_lead')) {
    allowed = allowed.filter((layer) => layer !== 'hook_lead');
  }
  return allowed;
}

function makePlan(name, bars, energy, extra = {}) {
  const rounded = Math.round(energy * 1000) / 1000;
  return {
    name,
    bars,
    energy: rounded,
    layers: layersForSection(name, rounded),
    sourceName: extra.sourceName === undefined ? null : extra.sourceName,
    // Гейн секции: 0 дБ на дропе, −12 дБ в полной тишине.
    // `+ 0` нужен, чтобы у полной энергии получился 0, а не −0.
    gainDb: Math.round(-12.0 * (1.0 - rounded) * 100) / 100 + 0,
    // Трим низа: в куплете −3 дБ, в дропе 0 дБ.
    bassGain: Math.round((LOW_TRIM[name] === undefined ? 0.8 : LOW_TRIM[name]) * 1000) / 1000,
  };
}

/** Энергия по именам секций (без побочных эффектов). */
function energyCurve(names) {
  return Array.from(names).map((name) => (SECTION_ENERGY[name] === undefined ? 0.6 : SECTION_ENERGY[name]));
}

/** Построить план бита из секций плана аранжировки. */
function sectionsFromArrangement(sections, bpm) {
  if (!(bpm > 0)) throw new Error('bpm должен быть положительным');
  const plans = [];
  for (const section of sections || []) {
    if (!section || typeof section !== 'object') continue;
    const canonical = canonicalSectionName(section.name || '');
    const bars = Math.max(1, Math.trunc(section.bars || BASE_BARS[canonical] || 4));
    let energy = section.energy;
    if (energy === null || energy === undefined) {
      energy = SECTION_ENERGY[canonical] === undefined ? 0.6 : SECTION_ENERGY[canonical];
    } else {
      energy = Math.max(0.0, Math.min(1.0, Number(energy)));
    }
    plans.push(makePlan(canonical, bars, energy, { sourceName: String(section.name || canonical) }));
  }
  return plans;
}

/**
 * Раскладывает целевую длительность на осмысленные секции.
 *
 * Скелет: intro → (verse → pre_chorus → hook) × n → bridge → hook × m → outro.
 * Если тактов меньше, чем нужно скелету, секции укорачиваются, но не меньше
 * двух тактов; разницу добираем припевами, а не бесконечным лупом.
 */
function planSections({
  bpm,
  durationSec,
  includeIntro = true,
  includeOutro = true,
  includeBridge = true,
  nVerses = 2,
  nChoruses = 2,
} = {}) {
  if (!(bpm > 0)) throw new Error('bpm должен быть положительным');
  const barSec = 240.0 / bpm;
  const targetBars = Math.max(8, Math.round(Math.max(durationSec, 1.0) / barSec));

  const names = [];
  if (includeIntro) names.push('intro');
  for (let i = 0; i < Math.max(1, nVerses); i += 1) names.push('verse', 'pre_chorus', 'hook');
  if (includeBridge) names.push('bridge');
  for (let i = 0; i < Math.max(1, nChoruses) - 1; i += 1) names.push('hook');
  if (includeOutro) names.push('outro');

  const dropOne = () => {
    for (const candidate of ['pre_chorus', 'bridge', 'hook', 'verse']) {
      for (let index = names.length - 1; index >= 0; index -= 1) {
        if (names[index] !== candidate) continue;
        const count = names.filter((name) => name === candidate).length;
        if (count > 1 || candidate === 'pre_chorus' || candidate === 'bridge') {
          names.splice(index, 1);
          return true;
        }
      }
    }
    return false;
  };

  while (names.length > 2 && names.length * 2 > targetBars) {
    if (!dropOne()) break;
  }

  const weights = names.map((name) => (BASE_BARS[name] === undefined ? 4 : BASE_BARS[name]));
  const totalWeight = weights.reduce((sum, value) => sum + value, 0);
  const bars = weights.map((weight) => Math.max(2, Math.round((weight / totalWeight) * targetBars)));

  // Догоняем/срезаем разницу за счёт припевов: это музыкально безопаснее всего.
  const hookIndexes = names.map((name, index) => (name === 'hook' ? index : -1)).filter((i) => i >= 0);
  let diff = targetBars - bars.reduce((sum, value) => sum + value, 0);
  let guard = 0;
  while (diff !== 0 && guard < 512) {
    guard += 1;
    if (diff > 0) {
      const index = hookIndexes.length ? hookIndexes[Math.floor(hookIndexes.length / 2)] : bars.length - 1;
      bars[index] += 1;
      diff -= 1;
    } else {
      const candidates = bars.map((value, index) => (value > 2 ? index : -1)).filter((i) => i >= 0);
      if (!candidates.length) break;
      bars[candidates[candidates.length - 1]] -= 1;
      diff += 1;
    }
  }

  return names.map((name, index) =>
    makePlan(name, bars[index], SECTION_ENERGY[name] === undefined ? 0.6 : SECTION_ENERGY[name]));
}

/** Секунда, на которой начинается первый припев. */
function hookPosition(sections, bpm) {
  const barSec = 240.0 / bpm;
  let cursor = 0.0;
  for (const section of sections) {
    if (section.name === 'hook' || section.name === 'chorus') return Math.round(cursor * 100) / 100;
    cursor += section.bars * barSec;
  }
  return Math.round(cursor * 100) / 100;
}

/** Когда впервые звучит мотив хука (правило «хук в первые 15 секунд»). */
function hookMotifStartSec(sections, bpm) {
  const barSec = 240.0 / bpm;
  let cursor = 0.0;
  for (const section of sections) {
    if (section.layers.includes('hook_lead')) return Math.round(cursor * 100) / 100;
    cursor += section.bars * barSec;
  }
  return hookPosition(sections, bpm);
}

const hookWithinLimit = (sections, bpm) => hookMotifStartSec(sections, bpm) <= HOOK_WITHIN_SEC;

/** Длительность плана в секундах. */
function totalSeconds(sections, bpm) {
  const barSec = 240.0 / bpm;
  const bars = sections.reduce((sum, section) => sum + section.bars, 0);
  return Math.round(bars * barSec * 100) / 100;
}

/** Сводка для логов и отчёта: структура, энергия, дроп-контраст. */
function structureReport(sections, bpm) {
  const hooks = sections.filter((s) => s.name === 'hook' || s.name === 'chorus').map((s) => s.energy);
  const verses = sections.filter((s) => s.name === 'verse').map((s) => s.energy);
  const contrast = hooks.length && verses.length
    ? Math.round((Math.max(...hooks) - Math.min(...verses)) * 1000) / 1000
    : 0.0;
  return {
    total_sec: totalSeconds(sections, bpm),
    sections: sections.map((section) => ({
      name: section.name,
      bars: section.bars,
      energy: section.energy,
      gain_db: section.gainDb,
      bass_gain: section.bassGain,
      layers: section.layers.slice(),
    })),
    hook_start_sec: hookPosition(sections, bpm),
    hook_motif_start_sec: hookMotifStartSec(sections, bpm),
    hook_within_15s: hookWithinLimit(sections, bpm),
    drop_contrast: contrast,
    max_layers: sections.reduce((best, section) => Math.max(best, section.layers.length), 0),
  };
}

module.exports = {
  SECTION_ENERGY,
  MAX_LAYERS,
  LAYER_ORDER,
  LOW_TRIM,
  BASE_BARS,
  TARGET_MIN_SEC,
  TARGET_MAX_SEC,
  HOOK_WITHIN_SEC,
  canonicalSectionName,
  layersForSection,
  energyCurve,
  sectionsFromArrangement,
  planSections,
  hookPosition,
  hookMotifStartSec,
  hookWithinLimit,
  totalSeconds,
  structureReport,
};
