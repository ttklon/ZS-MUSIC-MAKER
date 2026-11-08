'use strict';
/**
 * core/audio/analysis.js — измерение трека: «формульность» и честный отчёт.
 *
 * Порт `modules/beat/variation.py::repetition_report` + `microtime.humanity_report`.
 * Зачем это в окне: без метрики нельзя сказать «трек не формульный» — можно
 * только надеяться. Отчёт считается по спектральным признакам тактов, поэтому
 * здесь реализовано своё БПФ (в Node нет numpy), а не «примерно похожее».
 *
 * Все числа на выходе — те же поля, что у Python-версии: `bars`,
 * `distinct_types`, `entropy`, `entropy_normalized`, `bar_similarity`,
 * `formulaic`, `min_entropy`.
 */

const BAR_FEATURES = ['rms_db', 'centroid_hz', 'low_high_ratio_db', 'onset_density'];
const MIN_ENTROPY = 0.35;
const MAX_TYPES = 8;

/**
 * Итеративное БПФ с основанием 2 (radix-2, in-place по копии).
 *
 * Возвращает массив комплексных пар [re, im] — только первая половина
 * (спектр вещественного сигнала симметричен).
 */
function fft(signal) {
  const input = signal.length;
  let size = 1;
  while (size < input) size *= 2;
  const re = new Float64Array(size);
  const im = new Float64Array(size);
  re.set(signal.subarray(0, Math.min(input, size)));

  // Бит-реверс перестановка.
  for (let i = 1, j = 0; i < size; i += 1) {
    let bit = size >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      const tmpRe = re[i];
      re[i] = re[j];
      re[j] = tmpRe;
      const tmpIm = im[i];
      im[i] = im[j];
      im[j] = tmpIm;
    }
  }

  for (let length = 2; length <= size; length *= 2) {
    const angle = (-2 * Math.PI) / length;
    const wRe = Math.cos(angle);
    const wIm = Math.sin(angle);
    for (let start = 0; start < size; start += length) {
      let curRe = 1;
      let curIm = 0;
      for (let k = 0; k < length / 2; k += 1) {
        const a = start + k;
        const b = a + length / 2;
        const tRe = re[b] * curRe - im[b] * curIm;
        const tIm = re[b] * curIm + im[b] * curRe;
        re[b] = re[a] - tRe;
        im[b] = im[a] - tIm;
        re[a] += tRe;
        im[a] += tIm;
        const nextRe = curRe * wRe - curIm * wIm;
        curIm = curRe * wIm + curIm * wRe;
        curRe = nextRe;
      }
    }
  }

  const half = Math.floor(size / 2) + 1;
  const out = new Float64Array(half);
  for (let i = 0; i < half; i += 1) out[i] = Math.hypot(re[i], im[i]);
  return { magnitudes: out, size };
}

/** Окно Ханна (в numpy — `np.hanning`). */
function hann(size) {
  const out = new Float64Array(size);
  for (let i = 0; i < size; i += 1) {
    out[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / Math.max(1, size - 1));
  }
  return out;
}

/**
 * Признаки одного такта: уровень, яркость, баланс полос, плотность атак.
 *
 * Ровно те же четыре признака и та же формула, что в Python: RMS в дБ,
 * спектральный центроид (кГц), отношение низ/верх в дБ (граница 150 Гц),
 * число атак на секунду по порогу 3σ от разности огибающей.
 */
function barFeatures(mono, sampleRate) {
  if (mono.length < 16) return [0, 0, 0, 0];
  let sumSquares = 0;
  for (let i = 0; i < mono.length; i += 1) sumSquares += mono[i] * mono[i];
  const rms = Math.sqrt(sumSquares / mono.length) + 1e-12;
  const rmsDb = 20 * Math.log10(Math.max(rms, 1e-9));

  const window = hann(mono.length);
  const windowed = new Float32Array(mono.length);
  for (let i = 0; i < mono.length; i += 1) windowed[i] = mono[i] * window[i];
  const { magnitudes, size } = fft(windowed);

  const binHz = sampleRate / size;
  let total = 0;
  let weighted = 0;
  let low = 0;
  let high = 0;
  for (let bin = 0; bin < magnitudes.length; bin += 1) {
    const value = magnitudes[bin];
    const freq = bin * binHz;
    total += value;
    weighted += value * freq;
    if (freq < 150) low += value;
    else high += value;
  }
  const centroid = total > 1e-12 ? weighted / total : 0;
  const lowHighDb = 20 * Math.log10(Math.max(low, 1e-9) / (high + 1e-12));

  // Атаки: разность огибающей, порог 3σ.
  const flux = new Float64Array(Math.max(0, mono.length - 1));
  let mean = 0;
  for (let i = 1; i < mono.length; i += 1) {
    flux[i - 1] = Math.abs(mono[i]) - Math.abs(mono[i - 1]);
    mean += flux[i - 1];
  }
  if (flux.length) {
    mean /= flux.length;
    let variance = 0;
    for (const value of flux) variance += (value - mean) ** 2;
    const threshold = 3 * Math.sqrt(variance / flux.length);
    let onsets = 0;
    if (threshold > 0) for (const value of flux) if (value > threshold) onsets += 1;
    const seconds = Math.max(mono.length / sampleRate, 1e-6);
    return [rmsDb, centroid / 1000, lowHighDb, onsets / seconds];
  }
  return [rmsDb, centroid / 1000, lowHighDb, 0];
}

/** Матрица признаков по тактам (4/4). */
function barsMatrix(mono, sampleRate, bpm) {
  const barSamples = Math.round(4 * (60 / Math.max(bpm, 1)) * sampleRate);
  if (barSamples <= 0 || mono.length < barSamples) return [];
  const rows = [];
  for (let start = 0; start + barSamples <= mono.length; start += barSamples) {
    rows.push(barFeatures(mono.subarray(start, start + barSamples), sampleRate));
  }
  return rows;
}

/** Кластеризация k-средними с детерминированной инициализацией (как в Python). */
function clusterTypes(rows, maxTypes = MAX_TYPES) {
  const n = rows.length;
  if (!n) return [];
  const k = Math.min(maxTypes, Math.max(1, Math.floor(n / 2)));
  const centers = [];
  for (let index = 0; index < k; index += 1) {
    const position = n === 1 ? 0 : Math.round((index * (n - 1)) / Math.max(1, k - 1));
    centers.push(rows[position].slice());
  }
  let labels = new Array(n).fill(0);
  for (let iteration = 0; iteration < 12; iteration += 1) {
    labels = rows.map((row) => {
      let best = 0;
      let bestDistance = Infinity;
      centers.forEach((center, index) => {
        let distance = 0;
        for (let dim = 0; dim < row.length; dim += 1) distance += (row[dim] - center[dim]) ** 2;
        if (distance < bestDistance) {
          bestDistance = distance;
          best = index;
        }
      });
      return best;
    });
    for (let index = 0; index < k; index += 1) {
      const members = rows.filter((_, row) => labels[row] === index);
      if (!members.length) continue;
      for (let dim = 0; dim < rows[0].length; dim += 1) {
        centers[index][dim] = members.reduce((sum, row) => sum + row[dim], 0) / members.length;
      }
    }
  }
  return labels;
}

/**
 * Отчёт «формульности»: энтропия типов тактов и сходство соседей.
 *
 * `formulaic: true` — рисунок повторяется (энтропия ниже `MIN_ENTROPY`), то
 * есть трек звучит как луп. Это не «оценка вкуса», а измерение.
 */
function repetitionReport(mono, sampleRate, bpm, { maxTypes = MAX_TYPES } = {}) {
  const rows = barsMatrix(mono, sampleRate, bpm);
  if (rows.length < 4) {
    return {
      bars: rows.length,
      distinct_types: 0,
      entropy: 0.0,
      entropy_normalized: 0.0,
      bar_similarity: 1.0,
      formulaic: true,
      reason: 'too few bars to measure',
    };
  }

  const dims = rows[0].length;
  const means = new Array(dims).fill(0);
  for (const row of rows) for (let dim = 0; dim < dims; dim += 1) means[dim] += row[dim] / rows.length;
  const scales = new Array(dims).fill(0);
  for (const row of rows) {
    for (let dim = 0; dim < dims; dim += 1) scales[dim] += ((row[dim] - means[dim]) ** 2) / rows.length;
  }
  const scale = scales.map((value) => {
    const dev = Math.sqrt(value);
    return dev < 1e-9 ? 1.0 : dev;
  });
  const normalized = rows.map((row) => row.map((value, dim) => (value - means[dim]) / scale[dim]));
  const labels = clusterTypes(normalized, maxTypes);

  const counts = new Map();
  for (const label of labels) counts.set(label, (counts.get(label) || 0) + 1);
  let entropy = 0;
  for (const count of counts.values()) {
    const probability = count / labels.length;
    entropy -= probability * Math.log2(probability);
  }
  const entropyNormalized = labels.length > 1 ? entropy / Math.log2(labels.length) : 0;

  // Косинусное сходство соседних тактов; полностью одинаковые такты после
  // z-нормировки дают нулевой вектор — для них сходство 1.0 по определению.
  const norms = normalized.map((row) => Math.hypot(...row));
  let similaritySum = 0;
  let pairs = 0;
  for (let index = 0; index + 1 < normalized.length; index += 1) {
    const a = normalized[index];
    const b = normalized[index + 1];
    let value;
    if (norms[index] < 1e-9 && norms[index + 1] < 1e-9) value = 1.0;
    else if (norms[index] < 1e-9 || norms[index + 1] < 1e-9) value = 0.0;
    else {
      let dot = 0;
      for (let dim = 0; dim < a.length; dim += 1) dot += a[dim] * b[dim];
      value = dot / (norms[index] * norms[index + 1]);
    }
    similaritySum += value;
    pairs += 1;
  }

  return {
    bars: rows.length,
    distinct_types: counts.size,
    entropy: Math.round(entropy * 1000) / 1000,
    entropy_normalized: Math.round(entropyNormalized * 1000) / 1000,
    bar_similarity: Math.round((pairs ? similaritySum / pairs : 0) * 1000) / 1000,
    formulaic: entropyNormalized < MIN_ENTROPY,
    min_entropy: MIN_ENTROPY,
  };
}

/**
 * Измерение «человечности» готового трека: шумовой пол и вариативность уровня.
 *
 * Порт `microtime.humanity_report`: 5-й процентиль уровня кадров по 50 мс и
 * стандартное отклонение уровней.
 */
function humanityReport(mono, sampleRate) {
  const frame = Math.max(1, Math.trunc(0.05 * sampleRate));
  const frames = Math.floor(mono.length / frame);
  if (frames < 4) return { noise_floor_dbfs: -120.0, level_variation_db: 0.0 };
  const levels = [];
  for (let index = 0; index < frames; index += 1) {
    let sum = 0;
    for (let i = index * frame; i < (index + 1) * frame; i += 1) sum += mono[i] * mono[i];
    levels.push(20 * Math.log10(Math.max(Math.sqrt(sum / frame), 1e-9)));
  }
  levels.sort((a, b) => a - b);
  const percentile = levels[Math.min(levels.length - 1, Math.floor(levels.length * 0.05))];
  const mean = levels.reduce((sum, value) => sum + value, 0) / levels.length;
  const variance = levels.reduce((sum, value) => sum + (value - mean) ** 2, 0) / levels.length;
  return {
    noise_floor_dbfs: Math.round(percentile * 100) / 100,
    level_variation_db: Math.round(Math.sqrt(variance) * 100) / 100,
  };
}

module.exports = {
  BAR_FEATURES,
  MIN_ENTROPY,
  MAX_TYPES,
  fft,
  hann,
  barFeatures,
  barsMatrix,
  clusterTypes,
  repetitionReport,
  humanityReport,
};
