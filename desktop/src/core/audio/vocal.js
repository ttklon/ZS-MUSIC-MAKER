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
 * 4. источник — пилообразная волна с дрожанием высоты (вибрато + дрейф),
 *    дальше три резонансных пика (форманты) и огибающая слога;
 * 5. результат — Float32Array в тональности трека, готовый к миксу.
 */

const dsp = require('./dsp');

/**
 * Гласные: форманты в герцах и относительная громкость.
 *
 * Значения — усреднённые певческие форманты (мужской голос, близко к
 * «нейтральному»): F1 отвечает за «открытость», F2 — за ряд (у/и/а), F3 —
 * за индивидуальность тембра.
 */
const VOWELS = {
  a: { f: [800, 1150, 2900], gain: 1.0 },
  o: { f: [500, 900, 2600], gain: 0.95 },
  u: { f: [350, 700, 2500], gain: 0.85 },
  e: { f: [500, 1800, 2700], gain: 0.95 },
  i: { f: [320, 2200, 3000], gain: 0.9 },
  y: { f: [380, 1500, 2600], gain: 0.85 },
  // латиница сводится к тем же артикуляциям
  ɑ: { f: [800, 1150, 2900], gain: 1.0 },
  æ: { f: [700, 1700, 2800], gain: 0.95 },
};

/** Согласные: тип шума и его длина в секундах. */
const CONSONANTS = {
  s: { kind: 'fricative', center: 6500, bw: 3000, dur: 0.09, gain: 0.35 },
  sh: { kind: 'fricative', center: 3200, bw: 1800, dur: 0.1, gain: 0.32 },
  f: { kind: 'fricative', center: 4500, bw: 4000, dur: 0.07, gain: 0.25 },
  h: { kind: 'aspirate', center: 1800, bw: 2500, dur: 0.06, gain: 0.22 },
  t: { kind: 'stop', center: 4000, bw: 2500, dur: 0.03, gain: 0.4 },
  k: { kind: 'stop', center: 2500, bw: 1800, dur: 0.03, gain: 0.4 },
  p: { kind: 'stop', center: 1200, bw: 1200, dur: 0.03, gain: 0.35 },
  b: { kind: 'voiced_stop', center: 900, bw: 900, dur: 0.04, gain: 0.3 },
  d: { kind: 'voiced_stop', center: 2500, bw: 1500, dur: 0.04, gain: 0.3 },
  g: { kind: 'voiced_stop', center: 1800, bw: 1200, dur: 0.04, gain: 0.3 },
  m: { kind: 'nasal', center: 250, bw: 200, dur: 0.06, gain: 0.35 },
  n: { kind: 'nasal', center: 300, bw: 220, dur: 0.06, gain: 0.35 },
  l: { kind: 'liquid', center: 900, bw: 600, dur: 0.05, gain: 0.3 },
  r: { kind: 'liquid', center: 1300, bw: 700, dur: 0.05, gain: 0.32 },
  v: { kind: 'voiced_fricative', center: 2000, bw: 1500, dur: 0.05, gain: 0.22 },
  z: { kind: 'voiced_fricative', center: 5000, bw: 2500, dur: 0.07, gain: 0.25 },
  zh: { kind: 'voiced_fricative', center: 3000, bw: 1500, dur: 0.08, gain: 0.26 },
  ch: { kind: 'fricative', center: 3500, bw: 1500, dur: 0.08, gain: 0.32 },
  ts: { kind: 'fricative', center: 5000, bw: 2000, dur: 0.08, gain: 0.3 },
  kh: { kind: 'fricative', center: 2200, bw: 1200, dur: 0.07, gain: 0.26 },
};

// Русские буквы → гласная или согласный. Й и ь/ъ не несут слога.
const RU_VOWELS = { а: 'a', о: 'o', у: 'u', э: 'e', е: 'e', и: 'i', ы: 'y', ё: 'o', ю: 'u', я: 'a' };
const RU_CONSONANTS = {
  б: 'b', в: 'v', г: 'g', д: 'd', ж: 'zh', з: 'z', й: 'l', к: 'k', л: 'l', м: 'm',
  н: 'n', п: 'p', р: 'r', с: 's', т: 't', ф: 'f', х: 'kh', ц: 'ts', ч: 'ch', ш: 'sh', щ: 'sh',
};

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
 * Реализация — каскад биквадов из `dsp.js` (те же коэффициенты, что сверены
 * с scipy), поэтому вокал звучит «в тон» остальному движку.
 */
function formantFilter(signal, formants, sr) {
  let out = signal;
  for (let i = 0; i < formants.length; i += 1) {
    const center = formants[i];
    // Полоса расширяется с ростом частоты: у верхних формант пик шире.
    const bw = Math.max(60, center * (i === 0 ? 0.16 : 0.22));
    out = dsp.bandpass(out, Math.max(80, center - bw / 2), center + bw / 2, sr, 2);
  }
  return out;
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
  // Пилообразная волна: она даёт все гармоники разом, а форманты вырезают
  // из них нужные. Фаза копится, чтобы вибрато не давало щелчков.
  let phase = 0;
  const drift = random() * 0.6;
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    // Вибрато включается не сразу: у живого голоса оно «дозревает» ~0.15 с.
    const vibDepth = vibrato * Math.min(1, t / 0.15);
    // Дрейф высоты — медленный, на всю ноту, чтобы не было «синтетики».
    const detune = drift + Math.sin(2 * Math.PI * 5.2 * t) * (vibDepth / 1200);
    const f = freq * (2 ** detune);
    phase += (2 * Math.PI * f) / sr;
    // -2 дБ на октаву: у настоящего голоса спектр не плоский.
    source[i] = Math.sin(phase) * 0.6 + Math.sin(2 * phase) * 0.25 + Math.sin(3 * phase) * 0.12;
  }

  const voiced = formantFilter(source, spec.f, sr);
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
