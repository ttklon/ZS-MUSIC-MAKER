'use strict';
/**
 * core/audio/dsp.js — минимальный DSP-арсенал для генерации бита.
 *
 * Порт того, что реально используется в `modules/beat/drums.py` и
 * `harmony.py`: фильтры Баттерворта (через биквады, как это делает scipy в
 * режиме sos), огибающие, нормализация, сатурация, конволюция и склейка.
 * Всё работает на `Float32Array` — без зависимостей и без нативной сборки.
 *
 * Почему фильтры расписаны так подробно: «похожий» полосовой фильтр слышно.
 * При полосе 900–3600 Гц наивный bandpass с Q=f0/Δf даёт −6 дБ на границах
 * вместо −3 дБ, и clap звучит ярче и «тоньше» эталона. Здесь используется тот
 * же путь, что у scipy: аналоговый прототип → билинейное преобразование →
 * каскад биквадов. Совпадение АЧХ со scipy проверяется в
 * `test/dsp.test.js` по коэффициентам, а не «на слух».
 */

/** Биквад (Direct Form II transposed) — звено фильтра. */
function biquad(signal, coefficients) {
  const { b0, b1, b2, a1, a2 } = coefficients;
  const out = new Float32Array(signal.length);
  let x1 = 0;
  let x2 = 0;
  let y1 = 0;
  let y2 = 0;
  for (let i = 0; i < signal.length; i += 1) {
    const x0 = signal[i];
    const y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
    out[i] = y0;
    x2 = x1;
    x1 = x0;
    y2 = y1;
    y1 = y0;
  }
  return out;
}

// --- комплексная арифметика для дизайна фильтров (только на этапе проектирования)
const cAdd = ([ar, ai], [br, bi]) => [ar + br, ai + bi];
const cSub = ([ar, ai], [br, bi]) => [ar - br, ai - bi];
const cMul = ([ar, ai], [br, bi]) => [ar * br - ai * bi, ar * bi + ai * br];
const cDiv = ([ar, ai], [br, bi]) => {
  const denom = br * br + bi * bi;
  return [(ar * br + ai * bi) / denom, (ai * br - ar * bi) / denom];
};
const cScale = ([ar, ai], k) => [ar * k, ai * k];
const cSqrt = ([re, im]) => {
  const magnitude = Math.hypot(re, im);
  const rootRe = Math.sqrt(Math.max(0, (magnitude + re) / 2));
  const rootIm = Math.sign(im || 1) * Math.sqrt(Math.max(0, (magnitude - re) / 2));
  return [rootRe, rootIm];
};

/** АЧХ каскада биквадов на цифровой частоте omega (рад/сэмпл). */
function cascadeMagnitude(sections, omega) {
  const zr = Math.cos(omega);
  const zi = -Math.sin(omega);
  const z2r = zr * zr - zi * zi;
  const z2i = 2 * zr * zi;
  let magnitude = 1;
  for (const section of sections) {
    const numR = section.b0 + section.b1 * zr + section.b2 * z2r;
    const numI = section.b1 * zi + section.b2 * z2i;
    const denR = 1 + section.a1 * zr + section.a2 * z2r;
    const denI = section.a1 * zi + section.a2 * z2i;
    magnitude *= Math.hypot(numR, numI) / Math.hypot(denR, denI);
  }
  return magnitude;
}

/**
 * Каскад биквадов Баттерворта — замена `scipy.signal.butter(..., output="sos")`.
 *
 * Путь тот же, что у scipy: полюса аналогового прототипа → денормировка
 * (ФНЧ/ФВЧ/полоса) → билинейное преобразование → пары сопряжённых полюсов
 * становятся биквадами. Нормировка — по эталонной точке (DC у ФНЧ, Найквист
 * у ФВЧ, центр полосы у полосового), поэтому −3 дБ на срезе получаются
 * такими же, как в Python-версии.
 */
function butterSos(kind, cutoff, sr, order = 2) {
  if (!['lowpass', 'highpass', 'bandpass'].includes(kind)) {
    throw new Error(`butterSos: неизвестный тип ${kind}`);
  }
  const n = Math.max(1, Math.round(order));
  const prewarp = (freq) => Math.tan((Math.PI * Math.min(sr / 2 - 1e-6, Math.max(1e-3, freq))) / sr);

  // Полюса аналогового прототипа Баттерворта порядка n (левая полуплоскость).
  const prototype = [];
  for (let k = 0; k < n; k += 1) {
    const theta = (Math.PI * (2 * k + n + 1)) / (2 * n);
    prototype.push([Math.cos(theta), Math.sin(theta)]);
  }

  let analog;
  let zeros; // нули цифрового фильтра: [-1,-1] у ФНЧ, [1,1] у ФВЧ, [1,-1] у полосы
  let referenceOmega;
  if (kind === 'bandpass') {
    const low = prewarp(Math.max(20.0, cutoff[0]));
    const high = prewarp(Math.max(cutoff[1], cutoff[0] + 1.0));
    const center = Math.sqrt(low * high);
    const bandwidth = high - low;
    analog = [];
    for (const pole of prototype) {
      const half = cScale(pole, bandwidth / 2);
      const root = cSqrt(cSub(cMul(half, half), [center * center, 0]));
      analog.push(cAdd(half, root), cSub(half, root));
    }
    zeros = [1, -1];
    // Центр полосы в цифровой частоте: 2·atan(√(w1·w2)).
    referenceOmega = 2 * Math.atan(Math.sqrt(low * high));
  } else {
    const w = prewarp(kind === 'lowpass' ? cutoff : Math.min(cutoff, sr / 2 - 100.0));
    analog = prototype.map((pole) => (kind === 'lowpass'
      ? cScale(pole, w)
      : cScale(cDiv([1, 0], pole), w)));
    zeros = kind === 'lowpass' ? [-1, -1] : [1, 1];
    referenceOmega = kind === 'lowpass' ? 0 : Math.PI;
  }

  // Билинейное преобразование s → z: z = (1 + s) / (1 − s).
  const digital = analog.map((pole) => cDiv(cAdd([1, 0], pole), cSub([1, 0], pole)));

  // Пары сопряжённых полюсов → биквады; вещественный полюс → звено 1-го порядка.
  const sections = [];
  const used = new Array(digital.length).fill(false);
  for (let i = 0; i < digital.length; i += 1) {
    if (used[i]) continue;
    const [re, im] = digital[i];
    used[i] = true;
    let a1;
    let a2;
    let realFirstOrder = Math.abs(im) < 1e-12;
    if (!realFirstOrder) {
      const partner = digital.findIndex(
        (candidate, index) => !used[index]
          && Math.abs(candidate[0] - re) < 1e-9
          && Math.abs(candidate[1] + im) < 1e-9,
      );
      if (partner >= 0) used[partner] = true;
      a1 = -2 * re;
      a2 = re * re + im * im;
    } else {
      a1 = -re;
      a2 = 0;
    }
    if (kind === 'bandpass') {
      sections.push({ b0: 1, b1: 0, b2: -1, a1, a2 });
    } else if (realFirstOrder) {
      sections.push(kind === 'lowpass'
        ? { b0: 1, b1: 1, b2: 0, a1, a2 }
        : { b0: 1, b1: -1, b2: 0, a1, a2 });
    } else {
      sections.push(kind === 'lowpass'
        ? { b0: 1, b1: 2, b2: 1, a1, a2 }
        : { b0: 1, b1: -2, b2: 1, a1, a2 });
    }
    realFirstOrder = false;
  }

  // Нормировка одним звеном: эталонная точка даёт 0 дБ, остальные звенья не
  // трогаем — иначе суммарный гейн возводится в степень числа звеньев.
  const gain = cascadeMagnitude(sections, referenceOmega);
  if (gain > 1e-12 && Number.isFinite(gain)) {
    sections[0].b0 /= gain;
    sections[0].b1 /= gain;
    sections[0].b2 /= gain;
  }
  return sections;
}

/** Полосовой/ВЧ/НЧ фильтр: каскад биквадов, как `sosfilt` в scipy. */
function filter(kind, signal, cutoff, sr, order = 2) {
  let out = signal;
  for (const stage of butterSos(kind, cutoff, sr, order)) out = biquad(out, stage);
  return out;
}

const bandpass = (signal, low, high, sr, order = 2) => filter('bandpass', signal, [low, high], sr, order);
const highpass = (signal, cutoff, sr, order = 2) => filter('highpass', signal, cutoff, sr, order);
const lowpass = (signal, cutoff, sr, order = 2) => filter('lowpass', signal, cutoff, sr, order);

/** Пиковая нормализация в target (по умолчанию 1.0). */
function peakNormalize(signal, target = 1.0) {
  let peak = 0;
  for (let i = 0; i < signal.length; i += 1) {
    const value = Math.abs(signal[i]);
    if (value > peak) peak = value;
  }
  if (peak <= 1e-9) return Float32Array.from(signal);
  const gain = target / peak;
  const out = new Float32Array(signal.length);
  for (let i = 0; i < signal.length; i += 1) out[i] = signal[i] * gain;
  return out;
}

/** tanh-сатурация с компенсацией громкости. */
function softClip(signal, drive = 1.6) {
  if (drive <= 0) return Float32Array.from(signal);
  const norm = Math.tanh(drive);
  const out = new Float32Array(signal.length);
  for (let i = 0; i < signal.length; i += 1) out[i] = Math.tanh(signal[i] * drive) / norm;
  return out;
}

/** Огибающая: экспоненциальный спад, ограниченный атакой. */
function env(n, sr, attack, tau) {
  const out = new Float32Array(n);
  const safeTau = Math.max(tau, 1e-4);
  const safeAttack = Math.max(attack, 1e-5);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const rise = Math.min(1, Math.max(0, t / safeAttack));
    out[i] = Math.exp(-t / safeTau) * rise;
  }
  return out;
}

/** Поэлементное умножение. */
function mul(a, b) {
  const n = Math.min(a.length, b.length);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i += 1) out[i] = a[i] * b[i];
  return out;
}

const zeros = (n) => new Float32Array(Math.max(0, n | 0));

/** Добавить `source` в `target` со смещением и усилением (в границах длины). */
function mixInto(target, source, offset, gain = 1.0) {
  const start = Math.max(0, offset | 0);
  const end = Math.min(target.length, start + source.length);
  for (let i = start; i < end; i += 1) target[i] += source[i - start] * gain;
  return target;
}

/** Обрезать/дополнить нулями до ровно n сэмплов. */
function fit(signal, n) {
  if (signal.length === n) return signal;
  const out = new Float32Array(n);
  out.set(signal.subarray(0, Math.min(signal.length, n)));
  return out;
}

/** Свёртка `same` — замена `np.convolve(..., mode="same")`. */
function convolveSame(signal, kernel) {
  const n = signal.length;
  const k = kernel.length;
  if (k === 0) return Float32Array.from(signal);
  const out = new Float32Array(n);
  const left = Math.floor((k - 1) / 2);
  for (let i = 0; i < n; i += 1) {
    let sum = 0;
    for (let j = 0; j < k; j += 1) {
      const index = i - j + left;
      if (index >= 0 && index < n) sum += signal[index] * kernel[j];
    }
    out[i] = sum;
  }
  return out;
}

/** Скользящее среднее (фильтр «яркости» пэда). */
function movingAverage(signal, window) {
  if (window <= 1) return Float32Array.from(signal);
  const kernel = new Float32Array(window).fill(1 / window);
  return convolveSame(signal, kernel);
}

/** RMS сигнала. */
function rms(signal) {
  if (!signal.length) return 0;
  let sum = 0;
  for (let i = 0; i < signal.length; i += 1) sum += signal[i] * signal[i];
  return Math.sqrt(sum / signal.length);
}

/** Пиковое значение. */
function peak(signal) {
  let value = 0;
  for (let i = 0; i < signal.length; i += 1) {
    const abs = Math.abs(signal[i]);
    if (abs > value) value = abs;
  }
  return value;
}

module.exports = {
  biquad,
  butterSos,
  filter,
  bandpass,
  highpass,
  lowpass,
  peakNormalize,
  softClip,
  env,
  mul,
  zeros,
  mixInto,
  fit,
  convolveSame,
  movingAverage,
  rms,
  peak,
};
