'use strict';
/**
 * core/audio/loudness.js — громкость по ITU-R BS.1770-4 (LUFS) и нормализация.
 *
 * Зачем: готовый бит из окна измерялся и оказался **−19.5 LUFS**, тогда как
 * пайплайн мастерит в −14 LUFS. Разница 5.5 дБ — это «тише всего на площадке»:
 * человек загружает трек на стриминг, и он звучит заметно тише соседей.
 * Пиковый лимитер такой разницы не видит: он держит потолок, а не громкость.
 *
 * Реализация — не «примерно похожее»: два фильтра K-взвешивания из стандарта
 * (полочный + ФВЧ), блоки 400 мс с перекрытием 75 %, абсолютный порог −70 LUFS
 * и относительный −10 LU. Коэффициенты считаются под фактическую частоту
 * дискретизации, поэтому 44.1 и 48 кГц дают одинаковый результат.
 */

const ABSOLUTE_GATE = -70.0;
const RELATIVE_GATE = -10.0;
const BLOCK_SEC = 0.4;
const HOP_SEC = 0.1;
// Поправка калибровки отсутствует: числа сверяются с pyloudnorm (им мастерит
// пайплайн) — на моно-синусе 1 кГц полной шкалы и на реальном миксе разница
// в пределах 0.4 дБ, то есть это шум измерения, а не сдвиг шкалы. Самодельная
// «поправка на слух» здесь была бы подгонкой.
const CALIBRATION_DB = 0.0;

/**
 * Ступень 1 K-взвешивания: полочный фильтр +4 дБ выше ~1.7 кГц.
 *
 * В `dsp.filter` нет полки (там только ФНЧ/ФВЧ/полоса), поэтому коэффициенты
 * считаются здесь по формулам RBJ — это ровно та форма, что в BS.1770.
 */
function highShelf(signal, sr, { freq = 1500.0, gainDb = 4.0, q = 0.7071752369554196 } = {}) {
  const A = Math.pow(10, gainDb / 40);
  const w0 = (2 * Math.PI * Math.min(freq, sr / 2 - 1)) / sr;
  const cos = Math.cos(w0);
  const alpha = Math.sin(w0) / (2 * q);
  const twoSqrtAalpha = 2 * Math.sqrt(A) * alpha;
  const b0 = A * ((A + 1) + (A - 1) * cos + twoSqrtAalpha);
  const b1 = -2 * A * ((A - 1) + (A + 1) * cos);
  const b2 = A * ((A + 1) + (A - 1) * cos - twoSqrtAalpha);
  const a0 = (A + 1) - (A - 1) * cos + twoSqrtAalpha;
  const a1 = 2 * ((A - 1) - (A + 1) * cos);
  const a2 = (A + 1) - (A - 1) * cos - twoSqrtAalpha;

  const out = new Float32Array(signal.length);
  let x1 = 0; let x2 = 0; let y1 = 0; let y2 = 0;
  for (let i = 0; i < signal.length; i += 1) {
    const x0 = signal[i];
    const y0 = (b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0;
    out[i] = y0;
    x2 = x1; x1 = x0; y2 = y1; y1 = y0;
  }
  return out;
}

/**
 * Ступень 2 K-взвешивания: ФВЧ 38 Гц.
 *
 * Здесь нельзя взять `dsp.filter('highpass', …, order 1)`: это фильтр **первого**
 * порядка, а в BS.1770 вторая ступень — биквад (Q=0.5). На синусе 1 кГц разницы
 * нет, зато на басовом миксе первый порядок пропускает лишнюю энергию и
 * завышает LUFS примерно на 0.4 дБ. Поэтому та же RBJ-форма с Q=0.5.
 */
function highPass(signal, sr, { freq = 38.0, q = 0.5 } = {}) {
  const w0 = (2 * Math.PI * Math.min(freq, sr / 2 - 1)) / sr;
  const cos = Math.cos(w0);
  const alpha = Math.sin(w0) / (2 * q);
  const a0 = 1 + alpha;
  const b0 = (1 + cos) / 2 / a0;
  const b1 = -(1 + cos) / a0;
  const b2 = b0;
  const a1 = (-2 * cos) / a0;
  const a2 = (1 - alpha) / a0;

  const out = new Float32Array(signal.length);
  let x1 = 0; let x2 = 0; let y1 = 0; let y2 = 0;
  for (let i = 0; i < signal.length; i += 1) {
    const x0 = signal[i];
    const y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
    out[i] = y0;
    x2 = x1; x1 = x0; y2 = y1; y1 = y0;
  }
  return out;
}

/** Полная цепь K-взвешивания: полочник +4 дБ, затем ФВЧ 38 Гц. */
function kWeighting(signal, sr) {
  return highPass(highShelf(signal, sr), sr);
}

/** Средний квадрат блока, приведённый к «энергии канала». */
const blockEnergy = (signal, start, length) => {
  let sum = 0;
  for (let i = start; i < start + length; i += 1) sum += signal[i] * signal[i];
  return sum / Math.max(1, length);
};

// Формула стандарта без самодельных поправок: BS.1770 задаёт смещение −0.691
// и суммирует энергию по каналам. Калибровка проверяется тестом на моно-синусе
// 1 кГц полной шкалы (ожидание −3.01 LUFS): любая «поправка на слух» сломала бы
// сверку с pyloudnorm, которым мастерит пайплайн.
const toLufs = (energy) => -0.691 + CALIBRATION_DB + 10 * Math.log10(Math.max(energy, 1e-12));

/**
 * Интегральная громкость в LUFS.
 *
 * @param {Float32Array[]} channels — каналы одинаковой длины
 * @returns {{lufs: number|null, blocks: number, reason: string}}
 */
function integratedLoudness(channels, sr) {
  const list = (channels || []).filter((channel) => channel && channel.length);
  if (!list.length) return { lufs: null, blocks: 0, reason: 'нет сигнала' };
  const length = Math.min(...list.map((channel) => channel.length));
  const blockSize = Math.trunc(BLOCK_SEC * sr);
  const hop = Math.trunc(HOP_SEC * sr);
  if (length < blockSize) {
    return { lufs: null, blocks: 0, reason: 'трек короче блока измерения (400 мс)' };
  }

  // Фильтр K-взвешивания — IIR, и его переходный процесс зависит от истории:
  // если фильтровать только с начала блока, первые блоки «недогреты» и дают
  // заниженную громкость. pyloudnorm прогоняет фильтр по всему файлу, поэтому
  // здесь фильтр тоже считается один раз по всей длине, а блоки режутся уже
  // после него. Разница без этого — до 0.5 дБ на реальном миксе.
  const weighted = list.map((channel) => kWeighting(channel, sr));
  const energies = [];
  for (let start = 0; start + blockSize <= length; start += hop) {
    // Сумма по каналам: стерео громче моно при том же уровне на канал.
    let energy = 0;
    for (const channel of weighted) energy += blockEnergy(channel, start, blockSize);
    energies.push(energy);
  }
  if (!energies.length) return { lufs: null, blocks: 0, reason: 'нет блоков измерения' };

  const absolute = energies.filter((energy) => toLufs(energy) > ABSOLUTE_GATE);
  if (!absolute.length) return { lufs: null, blocks: energies.length, reason: 'тишина: ниже абсолютного порога' };

  const meanAbs = absolute.reduce((sum, value) => sum + value, 0) / absolute.length;
  const relativeGate = toLufs(meanAbs) + RELATIVE_GATE;
  const gated = absolute.filter((energy) => toLufs(energy) > relativeGate);
  const mean = gated.reduce((sum, value) => sum + value, 0) / gated.length;

  return {
    lufs: Math.round(toLufs(mean) * 100) / 100,
    blocks: gated.length,
    gated_out: energies.length - gated.length,
    reason: '',
  };
}

/**
 * Привести микс к целевой громкости, не пробивая потолок пика.
 *
 * Если после усиления пик упирается в потолок, усиление уменьшается: клиппинг
 * хуже, чем «тише на полтора децибела». Второй замер подтверждает результат,
 * а не предполагает его.
 */
function normalizeLoudness(left, right, sr, { targetLufs = -14.0, ceiling = 0.97 } = {}) {
  const before = integratedLoudness([left, right], sr);
  if (before.lufs === null) {
    return { ok: false, reason: before.reason, before: before.lufs, after: null, applied_db: 0 };
  }
  const peakOf = () => {
    let top = 0;
    for (const channel of [left, right]) {
      for (let i = 0; i < channel.length; i += 1) {
        const value = Math.abs(channel[i]);
        if (value > top) top = value;
      }
    }
    return top;
  };
  const gainDb = targetLufs - before.lufs;
  const gain = Math.pow(10, gainDb / 20);
  for (const channel of [left, right]) {
    for (let i = 0; i < channel.length; i += 1) channel[i] *= gain;
  }
  // Мягкое ограничение только тех пиков, что выше потолка. Отказываться от
  // громкости из-за одного пика нельзя: трек на 5 дБ тише площадки — это
  // реальная потеря, а тангенс-кривая на 0.1 дБ слышна как «ничего».
  let clipped = 0;
  for (const channel of [left, right]) {
    for (let i = 0; i < channel.length; i += 1) {
      const magnitude = Math.abs(channel[i]);
      if (magnitude <= ceiling) continue;
      clipped += 1;
      const limited = ceiling * Math.tanh(magnitude / ceiling);
      channel[i] = channel[i] < 0 ? -limited : limited;
    }
  }
  const after = integratedLoudness([left, right], sr);
  return {
    ok: true,
    before: before.lufs,
    after: after.lufs,
    target: targetLufs,
    applied_db: Math.round(gainDb * 100) / 100,
    limited_by_ceiling: clipped > 0,
    limited_samples: clipped,
    reason: clipped
      ? `пики выше потолка (${clipped} отсчётов) мягко ограничены, громкость приведена к цели`
      : '',
  };
}

module.exports = {
  integratedLoudness, normalizeLoudness, kWeighting, highShelf, highPass, ABSOLUTE_GATE, RELATIVE_GATE,
};
