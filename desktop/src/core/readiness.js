'use strict';
/**
 * core/readiness.js — тот же честный расчёт готовности, что и в
 * `tools/readiness/scoring.py`, но на JS и по файлам проекта.
 *
 * Зачем дублировать формулу: окно не запускает Python. Риск расхождения
 * снимается тестом `test/readiness.test.js`, который сравнивает результат с
 * выводом `python -m tools.readiness --json` — то есть с эталоном. Если формулы
 * разойдутся, тест падает, а не «окно тихо показывает другое число».
 *
 * Потолки (caps) — это не баг, а честная граница: без реальной записи с
 * микрофона и без тяжёлых движков готовность не может быть выше.
 */

// Веса и статусы — копия `tools/readiness/paths.py`. Расхождение ловится
// тестом: он сверяет результат с выводом Python на тех же данных.
const WEIGHTS = {
  architecture: 10,
  core_modules: 25,
  audio_pipeline: 25,
  voice_recording: 20,
  release: 10,
  testing: 10,
};

const STATUS_WEIGHT = {
  REAL_PASS: 1.0,
  PARTIAL: 0.5,
  // Код есть, но из точек входа недостижим: в готовность продукта не входит,
  // однако и «отсутствующим» не считается.
  DEPRECATED: 0.25,
  FALLBACK_ONLY: 0.25,
  MOCK: 0.0,
  FAILED: 0.0,
  MISSING: 0.0,
  NOT_TESTED: 0.0,
  BLOCKED: 0.0,
};

function blockPercent(statuses) {
  const values = Object.values(statuses || {});
  if (!values.length) return 0;
  let score = 0;
  for (const status of values) score += STATUS_WEIGHT[status] !== undefined ? STATUS_WEIGHT[status] : 0;
  return Math.round((100 * score) / values.length * 100) / 100;
}

/**
 * @param {object} input
 * @param {object} input.probes   { architecture: {key: status}, ... } — ровно как raw_probes в Python
 * @param {object} input.inventory { REAL_PASS, REAL_FAIL, PLANNED, DEPRECATED, tracked_modules }
 */
function computeReadiness({ probes = {}, inventory = null } = {}) {
  const blocks = {};
  for (const name of Object.keys(WEIGHTS)) blocks[name] = blockPercent(probes[name] || {});

  const inv = inventory || { tracked_modules: 0, REAL_PASS: 0, REAL_FAIL: 0 };
  const total = Math.max(1, inv.tracked_modules || 0);
  const liveShare = ((inv.REAL_PASS || 0) + (inv.REAL_FAIL || 0)) / total;
  if (blocks.core_modules !== undefined) {
    blocks.core_modules = Math.round(blocks.core_modules * liveShare * 100) / 100;
  }

  let totalScore = 0;
  for (const [key, weight] of Object.entries(WEIGHTS)) {
    totalScore += ((blocks[key] || 0) * weight) / 100;
  }

  const caps = [];
  const audio = probes.audio_pipeline || {};
  const voice = probes.voice_recording || {};
  const architecture = probes.architecture || {};
  if (voice.mic_recording !== 'REAL_PASS') {
    caps.push([80, 'no real microphone recording available']);
  }
  const heavy = ['musicgen_runtime', 'demucs_runtime'].filter((key) => audio[key] === 'BLOCKED');
  if (heavy.length) caps.push([65, `heavy engines unavailable: ['${heavy.join("', '")}']`]);
  if (architecture.updater_module !== 'REAL_PASS') caps.push([85, 'no updater module']);

  const capMin = caps.length ? Math.min(...caps.map(([value]) => value)) : 100;
  const percent = Math.floor(Math.min(totalScore, capMin));

  return {
    percent,
    blockScores: blocks,
    capsTriggered: caps,
    moduleReachabilityShare: Math.round(liveShare * 10000) / 10000,
    rawTotal: Math.round(totalScore * 100) / 100,
  };
}

module.exports = { computeReadiness, blockPercent, WEIGHTS, STATUS_WEIGHT };
