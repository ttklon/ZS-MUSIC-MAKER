'use strict';
/**
 * core/audio/vocal.js — вокальная линия без внешних моделей.
 *
 * Зачем это здесь: у проекта нет ни RVC-модели, ни записанного вокала, а
 * «трек без голоса» — это не хит, а минус. Здесь голос синтезируется так же,
 * как остальные инструменты: формантный синтез (источник-фильтр) на
 * JavaScript, без сети, без Python и без весов на гигабайты.
 *
 * Что это даёт честно: разборчивую мелодию с слогами текста, вибрато,
 * бreath-шумом и согласными. Чего это не даёт: живого тембра и дикции
 * настоящего певца — поющая модель (RVC/DiffSinger) остаётся отдельной
 * задачей, и в «Справке» это названо.
 *
 * Как устроено:
 * 1. текст → слоги (грубая, но устойчивая разбивка для русского и латиницы);
 * 2. слог → гласная + согласные; гласная — набор формант (F1…F3), согласная —
 *    шумовая или взрывная вставка;
 * 3. мелодия — ступени лада, привязанные к аккордам секции;
 * 4. источник — пилообразная волна (десятки гармоник со спадом 1/k) с
 *    дрожанием высоты (вибрато ±22 цента, дрейф ±18 центов);
 * 5. форманты — три полосы, снятые **с источника параллельно** и сложенные
 *    с весами 0 / −3 / −9 дБ и с компенсацией спада источника (+3 дБ на
 *    октаву к верхним формантам). Каскад здесь не работает: первая полоса
 *    вырезает вторую и третью, и от голоса остаётся один основной тон;
 * 6. результат — Float32Array в тональности трека, готовый к миксу.
 *
 * Измерения этого синтеза (нота, форманты, гармоники, огибающая) — в
 * `test/vocal-measure.test.js`, а не «на слух».
 */

const dsp = require('./dsp');
const { VOWELS, CONSONANTS, RU_VOWELS, RU_CONSONANTS } = require('./formants');

/**
 * Разбить текст на слоги.
 *
 * Правило простое и предсказуемое: слог = согласные + гласная. Такой разбор
 * ошибается реже, чем «правильный» перенос (в русском он неоднозначен), и
 * для пения этого достаточно: важно, чтобы слог получил одну ноту.
 *
 * @param {string} text
 * @returns {Array<{vowel: string, onset: string[], coda: string[]}>}
 */
function splitSyllables(text) {
  const clean = String(text || '')
    .toLowerCase()
    .replace(/[^a-zа-яё\s'-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  const syllables = [];
  for (const word of clean.split(' ')) {
    if (!word) continue;
    let onset = [];
    // Буквы текущего слога: из них собирается `text`, чтобы окно могло
    // показать «я-чи-та-ю», а не только фонемы.
    let letters = [];
    const chars = [...word];
    for (let i = 0; i < chars.length; i += 1) {
      const ch = chars[i];
      const vowel = RU_VOWELS[ch] || (/[aeiouy]/.test(ch) ? ch : null);
      if (vowel) {
        syllables.push({ vowel, onset, coda: [], text: letters.join('') + ch });
        letters = [];
        onset = [];
        continue;
      }
      const mapped = RU_CONSONANTS[ch] || (/[bcdfghjklmnpqrstvwxz]/.test(ch) ? ch : null);
      if (!mapped) continue;
      letters.push(ch);
      if (!syllables.length) {
        onset.push(mapped);
        continue;
      }
      const last = syllables[syllables.length - 1];
      // Согласный после гласной — в кодe, но не больше одного: иначе «стр»
      // съедает всю длительность слога.
      if (last.coda.length === 0 && onset.length === 0) last.coda.push(mapped);
      else onset.push(mapped);
    }
    // Хвост слова принадлежит последнему слогу: «трек» → тре + к.
    if (onset.length && syllables.length) {
      const last = syllables[syllables.length - 1];
      last.coda.push(...onset.slice(0, 2));
      last.text += letters.join('');
    }
  }
  return syllables;
}

/** Детерминированный ГСЧ: тот же seed — тот же вокал. */
function rng(seed) {
  let state = (Number(seed) || 1) >>> 0;
  return () => {
    state = (state + 0x9e3779b9) >>> 0;
    let t = state;
    t ^= t << 13;
    t ^= t >>> 17;
    t ^= t << 5;
    return ((t >>> 0) / 4294967296) * 2 - 1;
  };
}

/**
 * Формантный фильтр: три резонансных пика поверх источника.
 *
 * Полосы считаются **от источника и складываются параллельно**. Каскад здесь
 * был бы ошибкой: первый bandpass режет всё ниже F1, второй (F2) получает уже
 * обрезанный сигнал и вырезает F1 из него, третий — F1 и F2. В сумме от голоса
 * оставался один основной тон (проверено измерением: −40…−60 дБ на F2/F3),
 * то есть гласных не было вовсе. Параллельные полосы такого не делают: каждая
 * видит полный источник, веса задают формантную огибающую.
 *
 * Веса: F1 — 0 дБ, F2 — −3 дБ, F3 — −9 дБ. Это не «на глаз»: спектр гласного
 * в среднем падает на 6…12 дБ между F1 и F3, и такие веса дают именно это.
 *
 * @param {Float32Array} signal источник
 * @param {number[]} formants   F1, F2, F3 в Гц
 * @param {number} sr
 * @returns {Float32Array}
 */
function formantFilter(signal, formants, sr, f0 = 0) {
  const out = new Float32Array(signal.length);
  // Ширина полос: F1 около 110 Гц, F2 около 150 Гц, F3 около 200 Гц — как у
  // низкого мужского голоса. Но она не может быть уже шага гармоник: при
  // ноте 260 Гц гармоники стоят через 260 Гц, и в полосу ±75 Гц не попадает
  // ни одна — голос превращался в две-три синусоиды. Поэтому полоса
  // расширяется до ~шага гармоник: в неё гарантированно попадает гармоника,
  // и гласная слышна на любой ноте.
  const natural = [110, 150, 200];
  const levels = [0, -3, -9];
  for (let i = 0; i < formants.length && i < natural.length; i += 1) {
    const center = formants[i];
    let width = natural[i];
    // Гармоники стоят через f0, и при высокой ноте полоса может пройти между
    // ними, не поймав ни одной. Тогда расширяем её до ближайшей гармоники —
    // ровно настолько, насколько нужно, а не «до шага гармоник»: широкая
    // полоса съедает разницу между «у» и «и».
    if (f0 > 0) {
      const nearest = Math.max(f0, Math.round(center / f0) * f0);
      width = Math.max(width, Math.abs(center - nearest) * 2 + natural[i]);
    }
    const low = Math.max(80, center - width / 2);
    const high = center + width / 2;
    if (high >= sr / 2 - 100) continue;
    const band = dsp.bandpass(signal, low, high, sr, 2);
    // Компенсация спада источника (+3 дБ на октаву к верхним формантам).
    // Источник падает как 1/k (−6 дБ на октаву), поэтому F2 и F3 даже при
    // нулевых весах оказываются на −15…−30 дБ, и голос звучит как синус с
    // шумом. Половина компенсации возвращает формантам вес, но не выравнивает
    // их в линейку — разница между «у» и «и» остаётся слышимой.
    const tilt = Math.sqrt(center / Math.max(80, formants[0]));
    const gain = 10 ** (levels[i] / 20) * tilt;
    for (let k = 0; k < out.length; k += 1) out[k] += band[k] * gain;
  }
  const peak = dsp.peak(out);
  return peak > 1e-9 ? dsp.peakNormalize(out, 1) : out;
}

/** Короткий шумовой всплеск для согласной. */
function consonantNoise(spec, sr, random) {
  const n = Math.max(1, Math.round(spec.dur * sr));
  const noise = new Float32Array(n);
  for (let i = 0; i < n; i += 1) noise[i] = random();
  const shaped = dsp.bandpass(noise, Math.max(80, spec.center - spec.bw / 2), spec.center + spec.bw / 2, sr, 2);
  const envelope = dsp.env(n, sr, spec.kind === 'stop' ? 0.002 : 0.012, spec.dur / 2.2);
  const out = dsp.mul(shaped, envelope);
  return dsp.peakNormalize(out, spec.gain);
}

/**
 * Один слог: источник → форманты → огибающая.
 *
 * @param {object} params
 * @param {string} params.vowel      ключ из VOWELS
 * @param {number} params.freq       частота ноты, Гц
 * @param {number} params.duration   длительность, с
 * @param {number} params.sr
 * @param {Function} params.random
 * @param {number} [params.vibrato]  глубина вибрато в центах
 */
function singSyllable({ vowel, freq, duration, sr, random, vibrato = 22, style = 'sung' }) {
  const spec = VOWELS[vowel] || VOWELS.a;
  const n = Math.max(8, Math.round(duration * sr));
  const source = new Float32Array(n);
  // Источник — пила: у голоса в спектре десятки гармоник, и формантам есть что
  // вырезать. Три синуса (как было раньше) давали ровно три гармоники, поэтому
  // F2 и F3 попадали между ними и гласная не формировалась.
  // Гармоник берём до 6 кГц: выше вокал в миксе всё равно не читается, а
  // считать их дешевле. Фаза копится, чтобы вибрато не давало щелчков.
  const maxHarmonic = Math.max(1, Math.floor(Math.min(sr / 2 - 500, 6000) / Math.max(50, freq)));
  let phase = 0;
  // Дрейф высоты — в **центах**, и он маленький: ±18 центов (±0.18 полутона).
  // Раньше это число подставлялось прямо в показатель `2 ** detune`, то есть
  // давало до +0.6 октавы (+7.8 полутона) — синтез просто не попадал в ноту
  // строки. Для «живости» достаточно центов.
  const driftCents = (random() * 2 - 1) * 18;
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    // Вибрато включается не сразу: у живого голоса оно «дозревает» ~0.15 с.
    const vibDepth = vibrato * Math.min(1, t / 0.15);
    // Дрейф высоты — медленный, на всю ноту, чтобы не было «синтетики».
    const detune = (driftCents + Math.sin(2 * Math.PI * 5.2 * t) * vibDepth) / 1200;
    const f = freq * (2 ** detune);
    phase += (2 * Math.PI * f) / sr;
    // Спад 1/k (−6 дБ на октаву) — так устроен и настоящий голос.
    // sin(kφ) считается рекуррентно (s_k = 2cosφ·s_{k−1} − s_{k−2}), а не
    // отдельным `Math.sin` на гармонику: их до сотни на сэмпл, и на строке
    // это разница в разы по времени рендера.
    const cos = Math.cos(phase);
    let prev = 0;
    let cur = Math.sin(phase);
    let value = cur;
    for (let k = 2; k <= maxHarmonic; k += 1) {
      const next = 2 * cos * cur - prev;
      prev = cur;
      cur = next;
      value += cur / k;
    }
    source[i] = value * 0.55;
  }

  const voiced = formantFilter(source, spec.f, sr, freq);
  // Слоговой шейп: атака 25 мс, спад к концу слога — иначе слоги слипаются.
  const attack = style === 'rap' ? 0.008 : 0.025;
  const release = style === 'rap' ? 0.05 : 0.09;
  const shaped = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const rise = Math.min(1, t / Math.max(attack, 1e-4));
    const fall = Math.min(1, Math.max(0, (duration - t) / Math.max(release, 1e-4)));
    // Лёгкая «дрожь» громкости: ровный уровень звучит как орган, не как голос.
    const tremolo = 1 + Math.sin(2 * Math.PI * 4.7 * t) * 0.04;
    shaped[i] = voiced[i] * rise * fall * tremolo * spec.gain;
  }
  return shaped;
}

/**
 * Спеть строку на заданной мелодии.
 *
 * @param {object} params
 * @param {string} params.text            текст (слоги берутся из него)
 * @param {number[]} params.midiNotes     ноты по слогам (если короче — повтор)
 * @param {number} params.sr
 * @param {number} params.seed
 * @param {number} [params.style]         'sung' | 'rap'
 * @param {number} [params.phrasePause]   пауза между словами, с
 * @returns {{signal: Float32Array, syllables: number, notes: number[]}}
 */
function singLine({ text, midiNotes, sr = 44100, seed = 1, style = 'sung', phrasePause = 0.03 }) {
  const syllables = splitSyllables(text);
  if (!syllables.length) return { signal: new Float32Array(0), syllables: [], notes: [] };
  const random = rng(seed);
  const notes = Array.isArray(midiNotes) && midiNotes.length ? midiNotes : [57];
  // Быстрый речитатив короче: в рэпе слог не тянется.
  const baseDur = style === 'rap' ? 0.19 : 0.32;
  const chunks = [];
  const usedNotes = [];
  let total = 0;

  for (let i = 0; i < syllables.length; i += 1) {
    const syllable = syllables[i];
    const midi = notes[i % notes.length];
    usedNotes.push(midi);
    const freq = 440 * (2 ** ((midi - 69) / 12));
    // Ритмическая неровность: 4 % по длительности, иначе строка механическая.
    const jitter = 1 + random() * 0.04;
    const dur = baseDur * jitter;

    // Согласные перед гласной звучат короче самой гласной.
    for (const consonant of syllable.onset.slice(0, 2)) {
      const spec = CONSONANTS[consonant];
      if (!spec) continue;
      const noise = consonantNoise(spec, sr, random);
      chunks.push(noise);
      total += noise.length;
    }
    const voiced = singSyllable({ vowel: syllable.vowel, freq, duration: dur, sr, random, style });
    chunks.push(voiced);
    total += voiced.length;
    const pause = Math.round((phrasePause * random() + 0.01) * sr);
    if (pause > 0) {
      chunks.push(new Float32Array(pause));
      total += pause;
    }
  }

  const out = new Float32Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.length;
  }
  // `syllables` — сами слоги, а не их число: окну нужно показать, что и как
  // поётся, а длину вызывающий код возьмёт как `syllables.length`.
  return { signal: dsp.peakNormalize(out, 0.9), syllables, notes: usedNotes };
}

/**
 * Мелодия для вокала из тональности трека.
 *
 * Берём ступени лада выше середины: вокал не должен конкурировать с басом.
 * `seed` сдвигает рисунок, чтобы строки не были одинаковыми, но оставались
 * в тональности.
 *
 * @param {object} params
 * @param {string} params.key      «A minor»
 * @param {number} params.count    сколько нот нужно
 * @param {number} [params.seed]
 * @returns {number[]} MIDI-ноты
 */
function melodyFor({ key = 'A minor', count = 8, seed = 1 } = {}) {
  const MINOR = [0, 2, 3, 5, 7, 8, 10];
  const MAJOR = [0, 2, 4, 5, 7, 9, 11];
  const ROOTS = {
    C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6,
    Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11,
  };
  // Диапазон разборчивости формантного синтеза: ниже 55 Гц «бубнит», выше
  // 74 Гц (D5) голос начинает свистеть на согласных.
  const LOWEST = 55;
  const HIGHEST = 74;

  const name = String(key || 'A minor').trim();
  const rootName = name.split(/\s+/)[0] || 'A';
  const root = ROOTS[rootName] !== undefined ? ROOTS[rootName] : 9;
  const isMajor = /major/i.test(name) && !/minor/i.test(name);
  const scale = isMajor ? MAJOR : MINOR;

  // Пул допустимых нот: весь лад в диапазоне, по возрастанию. Мелодия ходит
  // по индексам пула, поэтому фальшивых нот не бывает по построению.
  const pool = [];
  for (let midi = LOWEST; midi <= HIGHEST; midi += 1) {
    const pitch = midi % 12;
    const degree = ((pitch - root) % 12 + 12) % 12;
    if (scale.includes(degree)) pool.push(midi);
  }
  if (!pool.length) return new Array(Math.max(1, count)).fill(LOWEST);

  const random = rng(seed);
  let index = Math.min(pool.length - 1, Math.floor(pool.length / 2));
  const notes = [];
  for (let i = 0; i < Math.max(1, count); i += 1) {
    notes.push(pool[index]);
    // Шаг по ступеням: унисон, соседняя ступень или скачок через одну.
    const step = [-1, 0, 0, 1, 1, 2][Math.floor(Math.abs(random()) * 6) % 6];
    index += step;
    // Отражение от границ диапазона: мелодия разворачивается, а не прыгает
    // на октаву вверх, где голос звучит неестественно.
    if (index >= pool.length) index = pool.length - 2;
    if (index < 0) index = 1;
  }
  return notes;
}

module.exports = {
  VOWELS, CONSONANTS, splitSyllables, singSyllable, singLine, formantFilter, rng, melodyFor,
};
