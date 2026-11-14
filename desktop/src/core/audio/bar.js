'use strict';
/**
 * core/audio/bar.js — один такт: барабаны, бас, гармония, мелодия, FX.
 *
 * Отделено от `engine.js` ради читаемости: сборка такта — самая подробная
 * часть движка (16 шагов, слои, velocity), и вместе с мастерингом файл
 * упирался в лимит 400 строк.
 */

const { zeros, mixInto } = require('./dsp');
const variation = require('./variation');
const humanize = require('./humanize');

/**
 * Собрать один такт секции: барабаны, бас, гармония, мелодия, FX.
 *
 * @returns {{left: Float32Array, right: Float32Array}}
 */
function buildBar(engine, bar, section, plan, barSamples) {
  const left = zeros(barSamples);
  const right = zeros(barSamples);
  const stepSamples = Math.floor(barSamples / 16);
  const layers = plan ? plan.layers : ['drums', 'bass', 'pad', 'keys', 'melody', 'fx'];
  const variant = variation.barVariant(engine.rng, bar, section);

  engine.sectionEnergy = plan ? plan.energy : 0.6;

  const addMono = (audio, offset, pan, gain = 1.0) => {
    // Постоянная мощность: панорама не «съедает» громкость в центре.
    const angle = ((pan + 1.0) * Math.PI) / 4.0;
    mixInto(left, audio, offset, Math.cos(angle) * gain);
    mixInto(right, audio, offset, Math.sin(angle) * gain);
  };

  if (layers.includes('bass') && !['intro_pad', 'breakdown_silent', 'outro_fade'].includes(section)) {
    addMono(engine.generateBassLine(bar, barSamples), 0, 0.0);
  }

  if (layers.includes('drums') && !['intro_pad', 'breakdown_silent'].includes(section)) {
    for (let step = 0; step < 16; step += 1) {
      const stepStart = step * stepSamples;

      const kick = engine.generateKick(step, bar);
      addMono(kick, Math.max(0, stepStart + Math.trunc(engine.hitOffsetSec('kick', step, bar) * engine.sr)), 0.0);

      const snare = engine.generateSnare(step, bar);
      addMono(
        snare,
        Math.max(0, stepStart + Math.trunc(engine.hitOffsetSec('snare', step, bar) * engine.sr)),
        engine.rng.uniform(-0.05, 0.05),
      );

      // Хэты панорамируем (шире для стерео-поля). Пропуск шага — это и есть
      // вариация рисунка, а не ошибка сетки.
      if (variant.skipHatSteps.includes(step)) continue;
      const hat = engine.generateHihat(step, bar);
      addMono(
        hat,
        Math.max(0, stepStart + Math.trunc(engine.hitOffsetSec('hat', step, bar) * engine.sr)),
        step % 2 === 0 ? 0.45 : -0.45,
      );
    }

    // Сбивка в конце фразы: 32-е на малом, тише и с нарастанием.
    const fillSteps = humanize.ghostRollSteps(humanize.isFillBar(bar));
    if (fillSteps.length && ['verse', 'pre_chorus', 'hook', 'chorus'].includes(section)) {
      fillSteps.forEach((rollStep, index) => {
        const roll = engine.generateSnare(14, bar, 14);
        const crescendo = 0.35 + 0.2 * index;
        for (let i = 0; i < roll.length; i += 1) roll[i] *= crescendo;
        addMono(roll, rollStep * stepSamples, engine.rng.uniform(-0.08, 0.08));
      });
    }
  }

  // Гармония: пэд + аккордовые стабы (основа «трека», не только ритм)
  if (section !== 'breakdown_silent' && (layers.includes('pad') || layers.includes('keys'))) {
    addMono(engine.generateHarmony(bar, section, barSamples), 0, 0.0);
  }

  if (layers.includes('melody')) {
    addMono(engine.generateMelody(bar, section, barSamples), 0, engine.rng.uniform(-0.6, 0.6));
  }

  if (layers.includes('fx')) {
    addMono(engine.generateFx(bar, section, barSamples), 0, engine.rng.uniform(-0.85, 0.85));
  }

  // Саб-слой только в дропе: измеренный контраст низа ≥6 дБ.
  if (plan && plan.energy >= 0.85 && layers.includes('bass')) {
    const sub = engine.generateSub(bar, barSamples);
    for (let i = 0; i < sub.length; i += 1) sub[i] *= 0.45;
    addMono(sub, 0, 0.0);
  }

  // Ghost-ноты и добавочные хэты из вариации такта.
  for (const ghostStep of variant.ghostSnareSteps) {
    const ghost = engine.generateSnare(ghostStep, bar, ghostStep);
    for (let i = 0; i < ghost.length; i += 1) ghost[i] *= 0.22;
    addMono(ghost, Math.max(0, ghostStep * stepSamples), engine.rng.uniform(-0.12, 0.12));
  }
  for (const extraStep of variant.extraHatSteps) {
    const extra = engine.generateHihat(extraStep, bar, 0.45);
    addMono(extra, Math.max(0, extraStep * stepSamples), extraStep % 2 ? 0.25 : -0.25);
  }

  // Дыхание уровня такта (±0.3 дБ) — часть вариации.
  if (variant.barGainDb) {
    const gain = Math.pow(10, variant.barGainDb / 20);
    for (let i = 0; i < barSamples; i += 1) {
      left[i] *= gain;
      right[i] *= gain;
    }
  }

  return { left, right };
}

module.exports = { buildBar };
