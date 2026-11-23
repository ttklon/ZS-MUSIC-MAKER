'use strict';
/**
 * core/audio/true-peak.js — истинный пик (dBTP) через 4× передискретизацию.
 *
 * Зачем отдельный модуль: сэмпловый пик врёт на межсэмпловых выбросах. Окно
 * держало «пик −0.26 dBFS» и этим успокаивало, а Python-пайплайн мастерит по
 * истинному пику с потолком −1 dBTP (`modules/mastering/targets.py`). Два
 * разных потолка в одном продукте — это два разных мастера.
 *
 * Реализация — полифазный FIR (окно Кайзера над sinc с полосой 1/4) — тот же
 * приём, что `scipy.signal.resample_poly` в Python, поэтому числа сходятся,
 * а не «примерно похожи».
 */

const PHASES = 4; // коэффициент передискретизации
// Параметры повторяют `scipy.signal.resample_poly`, которым меряет Python:
// `firwin(2·10·up + 1, 1/up, window=('kaiser', 5.0))` — 40 отсчётов на фазу.
// Другие окна и длины дают другой ответ на межсэмпловых пиках: первая версия
// с 16 отсчётами и β=8 занижала пик на 0.29 дБ относительно scipy.
const TAPS_PER_PHASE = 40;
const KAISER_BETA = 5.0;
// Шаг сетки для фазового пика: проверено на реальном миксе, шаги 1/2/4/8 дают
// одно и то же значение (1.115 dBTP), а работы в 4 раза меньше. Фаза
// передискретизации меняется медленно по сравнению с отсчётами.
const PEAK_STRIDE = 4;
const CUTOFF = 1 / PHASES; // доля от Найквиста на новой частоте

/** Модифицированная функция Бесселя первого рода нулевого порядка. */
function besselI0(x) {
  let sum = 1;
  let term = 1;
  const half = x / 2;
  for (let k = 1; k < 40; k += 1) {
    term *= (half / k) * (half / k);
    sum += term;
    if (term < 1e-14 * sum) break;
  }
  return sum;
}

/**
 * Полифазные коэффициенты.
 *
 * Вывод: при нулевой вставке отсчётов и свёртке с h фильтром-полуполосой
 * отсчёт `i` с дробным сдвигом `p/PHASES` равен `Σ x[i−k]·h[p + k·PHASES]`.
 * Каждая фаза нормируется отдельно — иначе постоянная составляющая «плывёт»
 * по фазе и пик оказывается завышенным.
 */
function phaseTaps() {
  // Симметричное ядро: 2·half+1 отсчётов, как у firwin.
  const half = TAPS_PER_PHASE;
  const total = 2 * half + 1;
  const h = new Float64Array(total);
  for (let n = 0; n < total; n += 1) {
    const t = n - half; // целые смещения в единицах новой частоты
    // sinc с обрезом на CUTOFF: h[t] = CUTOFF·sinc(CUTOFF·t)
    const arg = CUTOFF * t;
    const sinc = Math.abs(arg) < 1e-12 ? 1 : Math.sin(Math.PI * arg) / (Math.PI * arg);
    const r = t / half;
    const window = besselI0(KAISER_BETA * Math.sqrt(Math.max(0, 1 - r * r))) / besselI0(KAISER_BETA);
    h[n] = CUTOFF * sinc * window;
  }

  const out = [];
  for (let p = 0; p < PHASES; p += 1) {
    // Фаза p берёт отводы через PHASES начиная со смещения (PHASES-1-p),
    // чтобы отсчёты ложились по возрастанию времени назад от текущего.
    const taps = new Float64Array(TAPS_PER_PHASE);
    let sum = 0;
    for (let k = 0; k < TAPS_PER_PHASE; k += 1) {
      const index = (PHASES - 1 - p) + k * PHASES;
      taps[k] = index < total ? h[index] : 0;
      sum += taps[k];
    }
    // Постоянная составляющая на каждой фазе — ровно единица.
    for (let k = 0; k < TAPS_PER_PHASE; k += 1) taps[k] /= sum || 1;
    out.push(taps);
  }
  return out;
}

const PHASE_TAPS = phaseTaps();

/**
 * Пик одного канала: максимум по исходным отсчётам и по всем фазам.
 *
 * Фазы считаются только на грубой сетке (шаг `PEAK_STRIDE`): межсэмпловый
 * пик — это огибающая с периодом в единицы отсчётов, и точное значение на
 * каждом отсчёте не нужно, чтобы ответить «сколько dBTP». Наивный расчёт по
 * всем отсчётам и фазам занимал 3/4 времени нормализации и валил прогон
 * тестов в таймаут.
 */
function peakOfChannel(signal, stride = PEAK_STRIDE) {
  let best = 0;
  for (let i = 0; i < signal.length; i += 1) {
    const value = Math.abs(signal[i]);
    if (value > best) best = value;
  }
  const step = Math.max(1, Math.trunc(stride));
  for (let p = 0; p < PHASES; p += 1) {
    const taps = PHASE_TAPS[p];
    for (let i = TAPS_PER_PHASE; i < signal.length; i += step) {
      let acc = 0;
      for (let k = 0; k < TAPS_PER_PHASE; k += 1) acc += signal[i - k] * taps[k];
      const value = Math.abs(acc);
      if (value > best) best = value;
    }
  }
  return best;
}

/**
 * По-отсчётная огибающая истинного пика: `out[i]` — максимум из отсчёта и его
 * реконструкций между отсчётами (все фазы). Именно её должен видеть лимитер:
 * огибающая по сэмпловому пику не накрывает межсэмпловые выбросы, и потолок
 * пробивается на десятые доли дБ.
 *
 * `stride > 1` считает огибающую через `stride` отсчётов: для лимитера с
 * упреждением 3 мс (132 отсчёта) шаг 8 даёт ту же атаку, но в 8 раз меньше
 * работы. Значения между узлами заполняются максимумом, потому что гейн
 * должен быть безопасным, а не «плавным любой ценой».
 */
function truePeakEnvelope(signal, stride = 1) {
  const out = new Float32Array(signal.length);
  const step = Math.max(1, Math.trunc(stride));
  for (let i = 0; i < signal.length; i += 1) out[i] = Math.abs(signal[i]);
  const coarse = new Float32Array(Math.ceil(signal.length / step));
  for (let i = 0; i < signal.length; i += step) coarse[Math.floor(i / step)] = out[i];
  for (let p = 0; p < PHASES; p += 1) {
    const taps = PHASE_TAPS[p];
    for (let i = TAPS_PER_PHASE; i < signal.length; i += step) {
      let acc = 0;
      for (let k = 0; k < TAPS_PER_PHASE; k += 1) acc += signal[i - k] * taps[k];
      const value = Math.abs(acc);
      const slot = Math.floor(i / step);
      if (value > coarse[slot]) coarse[slot] = value;
    }
  }
  if (step === 1) {
    for (let i = 0; i < signal.length; i += 1) out[i] = coarse[i];
    return out;
  }
  // Заполнение между узлами — максимум из соседних узлов: огибающая не может
  // оказаться ниже реального пика ни в одной точке.
  for (let i = 0; i < signal.length; i += 1) {
    const slot = Math.floor(i / step);
    let best = coarse[slot];
    if (slot > 0 && coarse[slot - 1] > best) best = coarse[slot - 1];
    if (slot + 1 < coarse.length && coarse[slot + 1] > best) best = coarse[slot + 1];
    out[i] = best;
  }
  return out;
}

/** Истинный пик по всем каналам, в дБTP (от полной шкалы). */
function truePeakDbtp(channels) {
  let best = 0;
  for (const channel of channels || []) {
    if (!channel || !channel.length) continue;
    const value = peakOfChannel(channel);
    if (value > best) best = value;
  }
  return best > 0 ? 20 * Math.log10(best) : -Infinity;
}

/**
 * Огибающая истинного пика на грубой сетке (шаг `stride`).
 *
 * Лимитеру не нужна огибающая на каждом отсчёте: при упреждении 3 мс шаг 8
 * даёт ту же атаку. Считается только сэмпловый максимум слота плюс все фазы
 * передискретизации — этого достаточно, чтобы гейн был безопасным.
 */
function truePeakEnvelopeCoarse(signal, stride = 8) {
  const step = Math.max(1, Math.trunc(stride));
  const out = new Float32Array(Math.ceil(signal.length / step));
  for (let i = 0; i < signal.length; i += step) {
    const slot = Math.floor(i / step);
    let best = 0;
    const stop = Math.min(i + step, signal.length);
    for (let j = i; j < stop; j += 1) {
      const value = Math.abs(signal[j]);
      if (value > best) best = value;
    }
    out[slot] = best;
  }
  for (let p = 0; p < PHASES; p += 1) {
    const taps = PHASE_TAPS[p];
    for (let i = TAPS_PER_PHASE; i < signal.length; i += step) {
      let acc = 0;
      for (let k = 0; k < TAPS_PER_PHASE; k += 1) acc += signal[i - k] * taps[k];
      const value = Math.abs(acc);
      const slot = Math.floor(i / step);
      if (value > out[slot]) out[slot] = value;
    }
  }
  return out;
}

module.exports = {
  truePeakDbtp, truePeakEnvelope, truePeakEnvelopeCoarse, peakOfChannel,
  PHASES, TAPS_PER_PHASE,
};
