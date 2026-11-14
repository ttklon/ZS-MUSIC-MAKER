'use strict';
/**
 * core/audio/rng.js — детерминированный генератор случайных чисел.
 *
 * Зачем свой: `Math.random()` не воспроизводим, а «тот же seed → тот же трек»
 * — обещание проекта. Используется mulberry32: 32-битное состояние, одинаковый
 * результат на любой платформе (JavaScript не гарантирует бит-в-бит совпадение
 * с numpy, поэтому совпадение с Python проверяется отдельно — по свойствам, а
 * не по слепому равенству сэмплов).
 */

class Rng {
  constructor(seed = 0) {
    // seed приводим к uint32: отрицательные и дробные значения тоже работают
    this.state = (Number(seed) >>> 0) || 1;
  }

  /** Равномерное число в [0, 1). */
  next() {
    this.state = (this.state + 0x6d2b79f5) >>> 0;
    let t = this.state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /** Равномерное число в [low, high). */
  uniform(low, high) {
    return low + (high - low) * this.next();
  }

  /** Целое в [0, n). */
  int(n) {
    if (n <= 0) return 0;
    return Math.floor(this.next() * n);
  }

  /** Нормальное распределение (Box–Muller), как numpy standard_normal. */
  normal() {
    let u = 0;
    let v = 0;
    while (u === 0) u = this.next();
    while (v === 0) v = this.next();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  /** Массив нормального шума — замена `rng.standard_normal(size)`. */
  noise(size) {
    const out = new Float32Array(Math.max(0, size | 0));
    for (let i = 0; i < out.length; i += 1) out[i] = this.normal();
    return out;
  }
}

module.exports = { Rng };
