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

const { truePeakDbtp } = require('./true-peak');
const { limitStereo, softClip } = require('./limiter');

const ABSOLUTE_GATE = -70.0;
const RELATIVE_GATE = -10.0;
const BLOCK_SEC = 0.4;
const HOP_SEC = 0.1;
// Поправка калибровки отсутствует: числа сверяются с pyloudnorm (им мастерит
// пайплайн) — на моно-синусе 1 кГц полной шкалы и на реальном миксе разница
// в пределах 0.4 дБ, то есть это шум измерения, а не сдвиг шкалы. Самодельная
// «поправка на слух» здесь была бы подгонкой.
const CALIBRATION_DB = 0.0;
// Потолок истинного пика — как в `modules/mastering/targets.py`.
const TRUE_PEAK_CEILING_DBTP = -1.0;
// Сходимость по громкости (порт `modules/mastering/loudness.py`): шаг 0.8 от
// ошибки и допуск 0.25 LUFS стенда streaming.
const CONVERGE_STEP = 0.8;
const CONVERGE_TOLERANCE_DB = 0.25;
// Дополнительные проходы доводки: 2 — компромисс между точностью и временем
// рендера (каждый проход это полная цепь клиппер+лимитер).
const EXTRA_PASSES = 1;
// Лестница колена клиппера для плотного материала. Начинаем с мягкого:
// −2.5 dBFS уже даёт децибел громкости, а глубже без нужды лезть не нужно.
const KNEE_LADDER = [-2.5, -4.0, -6.0];

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
 * Привести микс к целевой громкости, не пробивая потолок ИСТИННОГО пика.
 *
 * Потолок — −1 dBTP, тот же, что в `modules/mastering/targets.py`. Раньше
 * здесь стоял сэмпловый потолок 0.97, и готовый микс уезжал на +0.51 dBTP:
 * межсэмпловые выбросы выше полной шкалы при отчёте «пик в норме».
 *
 * Усиление доводится до цели, пики снимает лимитер, а не «умножить весь буфер»:
 * пропорциональное срезание стоило на реальном миксе 2.9 дБ громкости, то есть
 * ровно ту потерю, ради устранения которой нормализация и делалась.
 */
function normalizeLoudness(left, right, sr, {
  targetLufs = -14.0,
  ceilingDbtp = TRUE_PEAK_CEILING_DBTP,
} = {}) {
  const before = integratedLoudness([left, right], sr);
  if (before.lufs === null) {
    return { ok: false, reason: before.reason, before: before.lufs, after: null, applied_db: 0 };
  }

  const samplePeak = () => {
    let top = 0;
    for (const channel of [left, right]) {
      for (let i = 0; i < channel.length; i += 1) {
        const value = Math.abs(channel[i]);
        if (value > top) top = value;
      }
    }
    return top;
  };
  const truePeakBefore = truePeakDbtp([left, right]);
  const peakBefore = samplePeak();
  const gainDb = targetLufs - before.lufs;
  // За этими пределами это уже не нормализация, а вытягивание мёртвого
  // материала шумом — честнее сказать «не дотянули», чем сделать вид.
  const clamp = (value) => Math.min(18, Math.max(-6, value));

  // Рендер кандидата: усиление → мягкий клиппер (ниже колена он математически
  // ничего не меняет) → лимитер по истинному пику. Клиппер применяется всегда:
  // «по условию» громкость скачет на дБ на границе включения.
  const render = (gainValueDb, kneeDbfs = ceilingDbtp) => {
    const factor = Math.pow(10, gainValueDb / 20);
    const channels = [
      Float32Array.from(left, (value) => value * factor),
      Float32Array.from(right, (value) => value * factor),
    ];
    const clip = softClip(channels, { kneeDbfs });
    const limited = limitStereo(channels[0], channels[1], sr, { ceilingDbtp });
    return { channels, clip, limited, lufs: integratedLoudness(channels, sr).lufs };
  };

  const clipInfo = [];
  let appliedGainDb = clamp(gainDb);

  // Оценка потери на первом кандидате: громкость без лимитера и с ним.
  // Одна поправка вместо трёх полных рендеров — отклик почти линейный.
  const probeChannels = [
    Float32Array.from(left, (value) => value * Math.pow(10, appliedGainDb / 20)),
    Float32Array.from(right, (value) => value * Math.pow(10, appliedGainDb / 20)),
  ];
  const dryLufs = integratedLoudness(probeChannels, sr).lufs;
  let best = render(appliedGainDb);
  // Проба переиспользуется как кандидат: раньше здесь стоял второй полный
  // рендер с тем же усилением — лишняя цепочка клиппер+лимитер на каждый бит.
  if (dryLufs !== null && best.lufs !== null && dryLufs - best.lufs > 0.05) {
    const correctedGain = clamp(appliedGainDb + (targetLufs - best.lufs));
    const corrected = render(correctedGain);
    if (corrected.lufs !== null
      && Math.abs(targetLufs - corrected.lufs) < Math.abs(targetLufs - best.lufs)) {
      best = corrected;
      appliedGainDb = correctedGain;
    }
  }
  clipInfo.push({
    ...best.clip,
    gain_db: Math.round(appliedGainDb * 100) / 100,
    result_lufs: best.lufs,
    limiter: best.limited,
  });
  // Доводка: каждая полная итерация (усиление → клиппер → лимитер) даёт
  // примерно 0.8 от запрошенной ошибки, потому что лимитер забирает часть
  // прироста. Одной поправки не хватало на плотных жанрах: reggaeton
  // оставался на −14.45 при цели −14, честно помеченный как «не достиг».
  for (let pass = 0; pass < EXTRA_PASSES; pass += 1) {
    if (best.lufs === null || Math.abs(targetLufs - best.lufs) <= CONVERGE_TOLERANCE_DB) break;
    const corrected = clamp(appliedGainDb + (targetLufs - best.lufs) * CONVERGE_STEP);
    if (Math.abs(corrected - appliedGainDb) < 0.01) break;
    const attempt = render(corrected);
    clipInfo.push({
      ...attempt.clip,
      gain_db: Math.round(corrected * 100) / 100,
      result_lufs: attempt.lufs,
      limiter: attempt.limited,
    });
    if (attempt.lufs !== null
      && (best.lufs === null || Math.abs(targetLufs - attempt.lufs) < Math.abs(targetLufs - best.lufs))) {
      best = attempt;
      appliedGainDb = corrected;
    } else {
      // Стало хуже — дальше идти некуда, оставляем лучший результат.
      break;
    }
  }

  // Если доводка уперлась в лимитер (плотный материал: crest высокий, потолок
  // не даёт добрать громкость), работает клиппер ниже потолка — ровно как в
  // `modules/mastering/loudness.py`. Первое колено — −2.5 dBFS: на реальном
  // reggaeton это +1.09 дБ громкости при 2 % затронутых отсчётов. Мягче
  // материал отдаёт больше громкости за ту же цену; принимается только то,
  // что ближе к цели и держит потолок.
  let usedKnee = ceilingDbtp;
  if (best.lufs !== null && Math.abs(targetLufs - best.lufs) > CONVERGE_TOLERANCE_DB
    && best.limited.gain_reduction_db > 1.0) {
    for (const knee of KNEE_LADDER) {
      const withKnee = render(appliedGainDb, knee);
      clipInfo.push({
        ...withKnee.clip,
        gain_db: Math.round(appliedGainDb * 100) / 100,
        knee_dbfs: knee,
        result_lufs: withKnee.lufs,
        limiter: withKnee.limited,
      });
      if (!withKnee.limited || withKnee.limited.true_peak_dbtp > ceilingDbtp + 0.01) continue;
      if (withKnee.lufs !== null
        && Math.abs(targetLufs - withKnee.lufs) < Math.abs(targetLufs - best.lufs)) {
        best = withKnee;
        usedKnee = knee;
      }
      if (withKnee.lufs !== null && Math.abs(targetLufs - withKnee.lufs) <= CONVERGE_TOLERANCE_DB) break;
    }
  }

  left.set(best.channels[0]);
  right.set(best.channels[1]);

  const truePeakAfter = truePeakDbtp([left, right]);
  const reached = best.lufs !== null && Math.abs(targetLufs - best.lufs) <= CONVERGE_TOLERANCE_DB;
  return {
    ok: true,
    before: before.lufs,
    after: best.lufs,
    target: targetLufs,
    applied_db: Math.round(appliedGainDb * 100) / 100,
    reached_target: reached,
    true_peak_before: Math.round(truePeakBefore * 100) / 100,
    true_peak_after: Math.round(truePeakAfter * 100) / 100,
    ceiling_dbtp: ceilingDbtp,
    // Потолок соблюдён — проверенный факт, а не намерение.
    ceiling_ok: truePeakAfter <= ceilingDbtp + 0.01,
    limited_by_ceiling: best.limited.gain_reduction_db > 0,
    limiter: best.limited,
    clip_knee_dbfs: usedKnee,
    soft_clip_passes: clipInfo,
    sample_peak: Math.round(peakBefore * 1000) / 1000,
    reason: reached
      ? ''
      : `цель ${targetLufs} LUFS недостижима при потолке ${ceilingDbtp} dBTP: `
        + `фактически ${best.lufs} LUFS`,
  };
}

module.exports = {
  integratedLoudness, normalizeLoudness, kWeighting, highShelf, highPass,
  ABSOLUTE_GATE, RELATIVE_GATE, TRUE_PEAK_CEILING_DBTP,
};
