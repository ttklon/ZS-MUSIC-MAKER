'use strict';
/**
 * core/audio/voices.js — голоса бита: ударные, бас, суб, мелодия, FX, пэд.
 *
 * Порт `modules/beat/voices.py` + `harmony.py::HarmonyMixin`. Каждый голос
 * берёт случайность из RNG конструктора, а не из глобального состояния,
 * поэтому seed → идентичный трек.
 *
 * Сэмпловый банк здесь не используется: в окне нет ни `data/samples/`, ни
 * декодера WAV-ов с диска. Движок честно помечает себя FALLBACK (как и
 * Python-версия без банка) и синтезирует one-shot'ы.
 */

const drums = require('./instruments');
const humanize = require('./humanize');
const harmony = require('./harmony');
const { zeros, mixInto, movingAverage, peak } = require('./dsp');

const ROOT_FREQS = {
  C: 261.63,
  'C#': 277.18,
  D: 293.66,
  'D#': 311.13,
  E: 329.63,
  F: 349.23,
  'F#': 369.99,
  G: 392.0,
  'G#': 415.3,
  A: 440.0,
  'A#': 466.16,
  B: 493.88,
};

const KICK_VARIANTS = 3;
const SNARE_VARIANTS = 3;
const HAT_VARIANTS = 4;

/** Частоты нот по именам — для баса и мотива. */
function rootFreq(key) {
  const text = String(key || 'A minor');
  const root = text.includes(' ') ? text.split(' ')[0] : 'A';
  return ROOT_FREQS[root] === undefined ? 440.0 : ROOT_FREQS[root];
}

function isMajor(key) {
  const text = String(key || 'A minor');
  if (!text.includes(' ')) return false;
  return text.split(' ').pop().toLowerCase().startsWith('maj');
}

/**
 * Конструктор голосов: держит слоты, velocity-карту, RNG и сетку.
 *
 * Это не класс ради класса — Python-версия делает то же через миксины;
 * состояние нужно, чтобы паттерн, акценты и «человечность» видели одни и те
 * же данные такта.
 */
class VoiceEngine {
  constructor({ bpm, key, genre, rng, slotPatterns, velocityMap, groove = {} }) {
    this.bpm = bpm;
    this.key = key;
    this.genre = genre;
    this.rng = rng;
    this.slotPatterns = slotPatterns;
    this.velocityMap = velocityMap;
    this.groove = groove || {};
    this.sr = 44100;
    this.sectionEnergy = 0.6;
    this.previousChord = null;
    this.progression = null;
  }

  get stepMs() {
    return 60000.0 / this.bpm / 4.0;
  }

  /** Смещение удара: кач референса (если есть) + человеческий джиттер. */
  hitOffsetSec(part, step, bar) {
    const feel = humanize.timingOffsetMs(
      this.rng,
      part,
      step,
      bar,
      this.groove.swing || 0.0,
      this.stepMs,
    );
    const reference = this.groove.timing_offsets_ms;
    if (Array.isArray(reference) && reference.length === 16) {
      const jitter = this.rng.uniform(-1.5, 1.5);
      const offsetMs = Math.min(20.0, Math.max(-20.0, reference[step % 16] + jitter));
      return offsetMs / 1000.0;
    }
    // Ограничение ±9 мс: дальше это уже не грув, а рассинхрон.
    return Math.min(9.0, Math.max(-9.0, feel)) / 1000.0;
  }

  /** Громкость удара: акценты семейства × человеческий джиттер. */
  velocity(part, step, bar, ghost = false) {
    let gain = humanize.velocityGain(this.rng, part, step, bar, ghost);
    const accents = (this.velocityMap || {})[part];
    if (Array.isArray(accents) && accents.length === 16) gain *= accents[step % 16];
    return gain;
  }

  /** Кик: сэмпл банка → пользовательские сэмплы → синтез (здесь — синтез). */
  generateKick(step, bar) {
    let pattern = this.slotPatterns.kick;
    // Сбивка в конце 4-тактовой фразы: три удара вместо ровной доли.
    if (bar % 4 === 3 && step >= 12) pattern = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1];
    if (pattern[step % pattern.length] === 0) return zeros(1);

    const velocity = this.velocity('kick', step, bar);
    const variant = humanize.variantIndex(this.rng, KICK_VARIANTS);
    let kick = drums.synthKick(this.sr, this.rng, {
      tune: 1.0 + (variant - 1) * 0.035,
      decay: 0.23 + 0.03 * variant,
    });

    if (this.sectionEnergy >= 0.85) {
      const tail = drums.synth808(this.sr, 41.0, kick.length / this.sr, { glide: 0.02, drive: 1.2 });
      // Не перенормируем: иначе атака кика «проседает». Пик держит финальная
      // нормализация трека, а не отдельный удар.
      for (let i = 0; i < kick.length; i += 1) kick[i] += (tail[i] || 0) * 0.6;
    }
    const gain = velocity * drums.INSTRUMENT_GAIN.kick;
    for (let i = 0; i < kick.length; i += 1) kick[i] *= gain;
    return kick;
  }

  /** Снейр/клэп: синтез корпуса и шума или ghost-нота. */
  generateSnare(step, bar, forceStep = null) {
    const position = forceStep === null ? step % 16 : forceStep % 16;
    const isGhost = forceStep === null && humanize.ghostNote(this.rng, 'snare', position);
    if (this.slotPatterns.snare[position] === 0 && !isGhost) return zeros(1);

    // Чередуем снейр и клэп на 2 и 4 доле нечётного такта.
    const wantsClap = position === 4 || position === 12 ? bar % 2 === 1 : false;
    const velocity = this.velocity('snare', step, bar, isGhost);
    const variant = humanize.variantIndex(this.rng, SNARE_VARIANTS);
    let hit = drums.synthSnare(this.sr, this.rng, {
      tune: 1.0 + (variant - 1) * 0.03,
      decay: 0.155 + 0.012 * variant,
      bright: 1.0 + 0.08 * variant,
    });
    if (wantsClap) {
      const clap = drums.synthClap(this.sr, this.rng);
      for (let i = 0; i < hit.length; i += 1) hit[i] = hit[i] * 0.75 + (clap[i] || 0) * 0.55;
    }
    const gain = velocity * drums.INSTRUMENT_GAIN.snare;
    for (let i = 0; i < hit.length; i += 1) hit[i] *= gain;
    return hit;
  }

  /** Хэт: закрытый/открытый, round-robin тембров, свинг по нечётным. */
  generateHihat(step, bar, amount = 1.0) {
    const density = this.groove.hihat_density === undefined ? 0.5 : this.groove.hihat_density;
    const swing = this.groove.swing || 0.0;

    let play;
    if (this.genre === 'legacy') {
      play = this.rng.next() < density;
    } else {
      play = Boolean(this.slotPatterns.hat[step % 16]);
      if (!play) play = this.rng.next() < density * 0.12;
    }
    if (step % 2 === 1 && this.rng.next() < swing * 0.5) play = true;

    if (!play) return zeros(1);

    const velocity = this.velocity('hat', step, bar);
    // Открытый хэт — на последней шестнадцатой такта, как в живом груве.
    const openHat = step % 16 === 15 && bar % 2 === 1;
    const variant = humanize.variantIndex(this.rng, HAT_VARIANTS);
    const hat = drums.synthHat(this.sr, this.rng, {
      openHat,
      tune: 1.0 + (variant - 1) * 0.045,
      metallic: 0.66 + 0.06 * variant,
    });
    const gain = velocity * drums.INSTRUMENT_GAIN.hat * amount;
    for (let i = 0; i < hat.length; i += 1) hat[i] *= gain;
    return hat;
  }

  /** Нота баса по ступеням лада, на октаву ниже тоники. */
  bassNoteFreq(index) {
    const major = [0, 2, 4, 7];
    const minor = [0, -2, -5, -7];
    const steps = isMajor(this.key) ? major : minor;
    const semitones = steps[index % steps.length];
    return (rootFreq(this.key) / 2.0) * Math.pow(2, semitones / 12);
  }

  /** Базовая линия на такт: 808 с humanize-смещениями. */
  generateBassLine(bar, barSamples) {
    const pattern = this.slotPatterns.bass;
    const bass = zeros(barSamples);
    const stepLen = Math.floor(barSamples / 16);
    let noteIndex = 0;
    for (let i = 0; i < pattern.length; i += 1) {
      if (!pattern[i]) continue;
      const offset = Math.trunc(this.hitOffsetSec('bass', i, bar) * this.sr);
      const start = Math.max(0, Math.min(barSamples - 1, i * stepLen + offset));
      const end = Math.min(start + stepLen * 2, barSamples);
      if (end <= start) continue;
      const note = drums.synth808(this.sr, this.bassNoteFreq(noteIndex), (end - start) / this.sr, {
        glide: 0.028,
        drive: 1.7 + 0.2 * (bar % 2),
      });
      const gain = drums.INSTRUMENT_GAIN.bass808 * this.velocity('bass', i, bar);
      mixInto(bass, note, start, gain);
      noteIndex += 1;
    }
    return bass;
  }

  /** Сабы на октаву ниже баса: то, что отличает дроп от куплета (≥6 дБ низа). */
  generateSub(bar, barSamples) {
    const pattern = this.slotPatterns.bass;
    const out = zeros(barSamples);
    const stepLen = Math.floor(barSamples / 16);
    let noteIndex = 0;
    for (let i = 0; i < pattern.length; i += 1) {
      if (!pattern[i]) continue;
      const start = i * stepLen;
      const end = Math.min(start + stepLen * 2, barSamples);
      if (end <= start) continue;
      // Октава ниже басовой ноты: 40–60 Гц — тело дропа.
      const freq = Math.max(28.0, this.bassNoteFreq(noteIndex) / 2.0);
      const note = drums.synth808(this.sr, freq, (end - start) / this.sr, { glide: 0.032, drive: 1.4 });
      mixInto(out, note, start, 0.55);
      noteIndex += 1;
    }
    return out;
  }

  /** Мелодический слой: без сэмплов банка его строит мотив хука. */
  generateMelody(bar, section, barSamples) {
    return zeros(barSamples);
  }

  /** FX: импакт на первом такте хука, стоп-тайм в конце фразы. */
  generateFx(bar, section, barSamples) {
    if ((section === 'hook' || section === 'chorus') && bar === 0) {
      const impact = drums.synthSubImpact(this.sr, this.rng);
      const out = zeros(barSamples);
      const length = Math.min(impact.length, barSamples);
      for (let i = 0; i < length; i += 1) out[i] = impact[i] * drums.INSTRUMENT_GAIN.impact;
      return out;
    }
    if (section === 'hook' && bar % 4 === 3) {
      const stopSamples = Math.floor(barSamples / 16) * 2;
      const out = zeros(barSamples);
      for (let i = barSamples - stopSamples; i < barSamples; i += 1) out[i] = 0.001;
      return out;
    }
    return zeros(barSamples);
  }

  progressionDegrees() {
    if (!this.progression) {
      this.progression = harmony.progressionFor(this.genre, this.rng.int(1e9));
    }
    return this.progression;
  }

  /** Аккорд на такт: ступень прогрессии, септаккорд каждый четвёртый такт. */
  chordForBar(bar) {
    const progression = this.progressionDegrees();
    const degree = progression[bar % progression.length];
    const root = rootFreq(this.key) / 2.0;
    return harmony.chordFreqs(root, degree, !isMajor(this.key), bar % 4 === 3);
  }

  /** Пэд + аккордовые стабы для такта (моно, длина такта). */
  generateHarmony(bar, section, barSamples) {
    if (section === 'breakdown_silent') return zeros(barSamples);

    const barSec = barSamples / this.sr;
    const chord = harmony.voiceLead(this.chordForBar(bar), this.previousChord);
    this.previousChord = chord;

    const soft = ['intro', 'outro', 'breakdown', 'intro_pad', 'outro_fade'].includes(section);
    const loud = ['hook', 'chorus'].includes(section);
    const padGain = soft ? 0.36 : loud ? 0.34 : 0.28;
    const keysGain = soft ? 0.0 : loud ? 0.2 : 0.12;

    const out = zeros(barSamples);
    const pad = harmony.synthPad(this.sr, chord, barSec, {
      attack: loud ? 0.05 : 0.16,
      brightness: loud ? 0.7 : 0.5,
    });
    for (let i = 0; i < Math.min(pad.length, barSamples); i += 1) out[i] += pad[i] * padGain;

    if (keysGain > 0) {
      // Стабы на офф-битах: «2» и «4» с человеческим опозданием.
      for (const step of [6, 14]) {
        let start = Math.trunc(step * (barSamples / 16) + this.hitOffsetSec('melody', step, bar) * this.sr);
        start = Math.max(0, Math.min(barSamples - 1, start));
        const stab = harmony.synthKeys(this.sr, chord, Math.min(0.45, barSec / 2));
        mixInto(out, stab, start, keysGain * this.velocity('melody', step, bar));
      }
    }
    return out;
  }
}

/** Мотив хука: повторяющийся лид, по которому трек узнаётся. */
function hookMotif(key) {
  const root = rootFreq(key);
  if (isMajor(key)) return [root, (root * 9) / 8, (root * 5) / 4, (root * 4) / 3];
  return [root, root * Math.pow(2, -2 / 12), root * Math.pow(2, -5 / 12), root * Math.pow(2, -7 / 12)];
}

/** Сглаживающий «воздух» для мотива: тот же фильтр, что у пэда. */
function motifLead(sr, freq, duration) {
  const n = Math.max(16, Math.trunc(sr * duration));
  const out = new Float32Array(n);
  for (let i = 0; i < n; i += 1) {
    const t = i / sr;
    const env = Math.exp(-t * 4.0) * (1.0 - Math.exp(-t * 60.0));
    out[i] = (
      0.6 * Math.sin(2 * Math.PI * freq * t)
      + 0.25 * Math.sin(2 * Math.PI * freq * 2 * t)
      + 0.1 * Math.sin(2 * Math.PI * freq * 3 * t)
    ) * env;
  }
  return movingAverage(out, 3);
}

module.exports = {
  ROOT_FREQS,
  KICK_VARIANTS,
  SNARE_VARIANTS,
  HAT_VARIANTS,
  rootFreq,
  isMajor,
  hookMotif,
  motifLead,
  VoiceEngine,
  peak,
};
