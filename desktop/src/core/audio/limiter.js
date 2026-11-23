'use strict';
/**
 * core/audio/limiter.js — look-ahead лимитер по истинному пику.
 *
 * Порт `modules/dsp/limiter.py` (его алгоритм описан там же): огибающая пика на
 * окне упреждения → требуемое усиление `потолок / огибающая` → плавный возврат
 * на освобождении → проверка истинного пика и добор, если сглаживание всё же
 * оставило доли дБ.
 *
 * Зачем не «умножить весь буфер на коэффициент»: пропорциональное срезание
 * забирает громкость у всего трека из-за одного пика. На реальном миксе окна
 * это стоило 2.9 дБ (−14.01 → −16.91 LUFS), то есть ровно та потеря, ради
 * устранения которой нормализация и делалась.
 */

const {
  truePeakDbtp, truePeakEnvelopeCoarse, PHASES, TAPS_PER_PHASE,
} = require('./true-peak');

const LOOKAHEAD_MS = 3.0;
// Шаг огибающей: упреждение 3 мс — это 132 отсчёта, поэтому шаг 8 не ослабляет
// атаку, зато снимает 8-кратный объём свёртки (полный прогон тестов упирался
// в таймаут не из-за качества, а из-за арифметики).
const ENVELOPE_STRIDE = 8;
// Запас быстрого пути: межсэмпловый пик выше сэмплового не больше чем на
// 1.5 дБ на музыкальном материале (теоретический максимум для синуса у
// Найквиста — 3 дБ, но такой материал уже сам по себе клиппирован).
const FAST_PATH_MARGIN = 0.41; // ≈ +1.5 дБ
const RELEASE_MS = 60.0;

/**
 * Огибающая пика на базовой сетке.
 *
 * Межсэмпловые выбросы видит только передискретизация, поэтому огибающая —
 * максимум из сэмплового значения и реконструкций соседних фаз. Окно
 * расширено на длину ядра: значение на позиции `i` зависит от отсчётов до
 * `i - TAPS`, и упреждение должно накрывать это целиком.
 */
function peakEnvelope(channels) {
  const length = Math.max(0, ...channels.map((channel) => channel.length));
  const env = new Float32Array(length);
  for (const channel of channels) {
    // Огибающая по ИСТИННОМУ пику: сэмпловая не видит межсэмпловых выбросов,
    // и потолок −1 dBTP пробивался на 1 дБ при формально соблюдённом сэмпловом.
    const peaks = truePeakEnvelopeCoarse(channel, ENVELOPE_STRIDE);
    for (let i = 0; i < peaks.length; i += 1) {
      if (peaks[i] > env[i]) env[i] = peaks[i];
    }
  }
  return env;
}

/**
 * Скользящий максимум по окну `window` — монотонной очередью, O(n).
 *
 * Наивный вариант «для каждой точки пройти окно» стоил сотни миллионов
 * операций на 20 секунд стерео и растягивал прогон тестов до таймаута.
 * Здесь каждая точка входит и выходит из очереди один раз.
 */
function slidingMax(values, window) {
  const n = values.length;
  if (window <= 1 || n === 0) return values;
  const out = new Float32Array(n);
  const queue = new Int32Array(n);
  let head = 0;
  let tail = 0;
  for (let i = 0; i < n; i += 1) {
    while (tail > head && values[queue[tail - 1]] <= values[i]) tail -= 1;
    queue[tail] = i;
    tail += 1;
    if (queue[head] <= i - window) head += 1;
    out[i] = values[queue[head]];
  }
  return out;
}

/**
 * Ограничить стереопару по истинному пику.
 *
 * @returns {{gain_reduction_db: number, true_peak_dbtp: number, ceiling_dbtp: number}}
 */
function limitStereo(left, right, sr, {
  ceilingDbtp = -1.0,
  lookaheadMs = LOOKAHEAD_MS,
  releaseMs = RELEASE_MS,
} = {}) {
  const ceiling = Math.pow(10, ceilingDbtp / 20);
  const window = Math.max(1, Math.round((lookaheadMs / 1000) * sr)) + TAPS_PER_PHASE;

  // Исходник сохраняется ДО применения гейна: иначе повторный проход умножал
  // бы уже ограниченный буфер и срезал вдвое больше нужного.
  const source = [Float32Array.from(left), Float32Array.from(right)];
  // Быстрый путь: если сэмпловый пик с запасом ниже потолка, огибающую можно
  // не строить — ни один межсэмпловый выброс не даст +запас дБ.
  let sampleTop = 0;
  for (const channel of source) {
    for (let i = 0; i < channel.length; i += 1) {
      const value = Math.abs(channel[i]);
      if (value > sampleTop) sampleTop = value;
    }
  }
  if (sampleTop * (1 + FAST_PATH_MARGIN) <= ceiling) {
    return {
      ceiling_dbtp: ceilingDbtp,
      lookahead_ms: lookaheadMs,
      release_ms: releaseMs,
      gain_reduction_db: 0,
      true_peak_dbtp: Math.round(20 * Math.log10(sampleTop || 1e-12) * 100) / 100,
      passes: 0,
      fast_path: true,
      phases: PHASES,
    };
  }
  // Огибающая уже на грубой сетке (шаг ENVELOPE_STRIDE): упреждение 3 мс —
  // это 132 отсчёта, поэтому шаг 8 не ослабляет атаку.
  const envelope = peakEnvelope(source);
  const coarseWindow = Math.max(1, Math.round(window / ENVELOPE_STRIDE));
  const smoothed = slidingMax(envelope, coarseWindow);
  const raw = new Float32Array(smoothed.length);
  for (let i = 0; i < smoothed.length; i += 1) {
    raw[i] = smoothed[i] > ceiling ? ceiling / smoothed[i] : 1;
  }

  // Освобождение: мгновенная атака (её обеспечивает окно упреждения и `min`),
  // плавный возврат усиления. `min(state, raw)` держит гарантию: сглаживание
  // не может поднять усиление выше требуемого по огибающей.
  const release = Math.exp(-1 / Math.max(sr * (releaseMs / 1000), 1));
  const gain = new Float32Array(raw.length);
  let state = 1;
  for (let i = 0; i < raw.length; i += 1) {
    const want = raw[i];
    state = want < state ? want : release * state + (1 - release) * want;
    gain[i] = Math.min(state, want);
  }

  // Полная сетка гейна строится ОДИН раз на проход: делить и брать минимум на
  // каждом отсчёте в теле цикла стоило 4.5 с на 20-секундный микс.
  const full = new Float32Array(Math.max(left.length, right.length));
  const expand = () => {
    for (let i = 0; i < full.length; i += 1) {
      const slot = Math.floor(i / ENVELOPE_STRIDE);
      const next = Math.min(slot + 1, gain.length - 1);
      full[i] = gain[slot] < gain[next] ? gain[slot] : gain[next];
    }
  };

  // Один проход: огибающая и упреждение уже гарантируют, что пик не выше
  // потолка, остаток — доли дБ от сглаживания. Цикл «пересчитать огибающую и
  // применить заново» давал те же числа, но стоил секунды на 20 с стерео.
  expand();
  for (let c = 0; c < 2; c += 1) {
    const channel = c === 0 ? left : right;
    const origin = source[c];
    for (let i = 0; i < channel.length; i += 1) channel[i] = origin[i] * full[i];
  }
  let passes = 1;

  let lowest = 1;
  for (let i = 0; i < gain.length; i += 1) if (gain[i] < lowest) lowest = gain[i];
  // Проверка точным расчётом: если сглаживание всё же оставило доли дБ,
  // снимаем их скаляром по всему буферу — на таком масштабе это неслышно.
  let exact = truePeakDbtp([left, right]);
  if (exact > ceilingDbtp) {
    const extra = Math.pow(10, (ceilingDbtp - exact) / 20);
    for (const channel of [left, right]) {
      for (let i = 0; i < channel.length; i += 1) channel[i] *= extra;
    }
    lowest *= extra;
    exact = truePeakDbtp([left, right]);
  }
  const tp = exact;

  return {
    ceiling_dbtp: ceilingDbtp,
    lookahead_ms: lookaheadMs,
    release_ms: releaseMs,
    gain_reduction_db: Math.max(0, Math.round(-20 * Math.log10(Math.max(lowest, 1e-9)) * 100) / 100),
    true_peak_dbtp: Math.round(tp * 100) / 100,
    passes,
    phases: PHASES,
  };
}

module.exports = { limitStereo, slidingMax, peakEnvelope, LOOKAHEAD_MS, RELEASE_MS };

/**
 * Мягкий клиппер: ограничить пики выше колена, ниже колена — сигнал идентичен.
 *
 * Порт `limiter.soft_clip` из Python. Нужен там, где пики не дают добрать
 * громкость: лимитер сохраняет форму, поэтому при высоком crest громкость
 * упирается в потолок. Клиппер меняет форму только у самых пиков и позволяет
 * поднять тело трека. Каждое применение пишется в отчёт.
 */
function softClip(channels, { kneeDbfs = -6.0 } = {}) {
  const knee = Math.pow(10, kneeDbfs / 20);
  let clipped = 0;
  for (const channel of channels) {
    for (let i = 0; i < channel.length; i += 1) {
      const magnitude = Math.abs(channel[i]);
      if (magnitude <= knee) continue;
      clipped += 1;
      const shaped = knee + (1 - knee) * Math.tanh((magnitude - knee) / Math.max(1 - knee, 1e-6));
      channel[i] = channel[i] < 0 ? -shaped : shaped;
    }
  }
  return { knee_dbfs: kneeDbfs, clipped_samples: clipped };
}

module.exports.softClip = softClip;
