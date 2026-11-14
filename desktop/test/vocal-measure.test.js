'use strict';
/**
 * test/vocal-measure.test.js — объективные измерения синтеза вокала.
 *
 * `vocal.test.js` проверяет контракт (длина, отсутствие NaN, сид, тональность).
 * Здесь проверяется звук: попадает ли синтез в заданную ноту, различаются ли
 * гласные по формантам, не «режутся» ли форманты фильтром, нет ли клиппинга и
 * сплошного гула вместо слогов.
 *
 * Поводом стали три настоящих дефекта, найденные этими измерениями:
 *  1. форманты шли каскадом — F1 вырезал F2 и F3, на выходе оставался один
 *     основной тон (энергия выше 1 кГц была ровно 0 %);
 *  2. «дрейф высоты» подставлялся в `2 ** detune` без перевода в октавы —
 *     нота уезжала до +7.8 полутона;
 *  3. источником были три синуса, а полосы формант уже шага гармоник — на
 *     ноте 260…330 Гц в полосу не попадала ни одна гармоника.
 * Эти проверки — защита от возврата всех трёх.
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const vocal = require('../src/core/audio/vocal');
const dsp = require('../src/core/audio/dsp');
const analysis = require('../src/core/audio/analysis');

const SR = 44100;

/** MIDI → Гц. */
const hzOf = (midi) => 440 * (2 ** ((midi - 69) / 12));

/** Частота по автокорреляции: пик нормированной корреляции на лаге. */
function pitchOf(signal, from, size = 8192) {
  const minLag = Math.floor(SR / 900);
  const maxLag = Math.ceil(SR / 70);
  let best = -1;
  let bestLag = 0;
  for (let lag = minLag; lag <= maxLag; lag += 1) {
    let cross = 0;
    let left = 0;
    let right = 0;
    for (let i = 0; i < size; i += 1) {
      const a = signal[from + i] || 0;
      const b = signal[from + i + lag] || 0;
      cross += a * b;
      left += a * a;
      right += b * b;
    }
    const r = cross / Math.sqrt((left || 1e-12) * (right || 1e-12));
    if (r > best) {
      best = r;
      bestLag = lag;
    }
  }
  return { hz: SR / bestLag, confidence: best };
}

/** Доли энергии по полосам, в процентах от 250…4200 Гц. */
function bandShares(signal, from, bands = [[250, 700], [700, 1200], [1200, 2400], [2400, 4200]]) {
  const size = 8192;
  const frame = new Float32Array(size);
  for (let i = 0; i < size; i += 1) {
    const window = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (size - 1));
    frame[i] = (signal[from + i] || 0) * window;
  }
  const { magnitudes } = analysis.fft(frame);
  const binHz = SR / size;
  const sums = bands.map(() => 0);
  let total = 0;
  for (let bin = 1; bin < magnitudes.length; bin += 1) {
    const hz = bin * binHz;
    if (hz < 250 || hz > 4200) continue;
    const power = magnitudes[bin] ** 2;
    total += power;
    for (let i = 0; i < bands.length; i += 1) {
      if (hz >= bands[i][0] && hz < bands[i][1]) sums[i] += power;
    }
  }
  return sums.map((sum) => (total ? (sum / total) * 100 : 0));
}

/** Амплитуды первых `count` гармоник ноты в дБ. */
function harmonicLevels(signal, from, f0, count = 30) {
  const size = 8192;
  const frame = new Float32Array(size);
  for (let i = 0; i < size; i += 1) {
    const window = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (size - 1));
    frame[i] = (signal[from + i] || 0) * window;
  }
  const { magnitudes } = analysis.fft(frame);
  const levels = [];
  for (let k = 1; k <= count; k += 1) {
    const bin = Math.round((k * f0 * size) / SR);
    let best = 0;
    for (let d = -2; d <= 2; d += 1) best = Math.max(best, magnitudes[bin + d] || 0);
    levels.push(20 * Math.log10(Math.max(best, 1e-9)));
  }
  return levels;
}

/** Сколько гармоник ноты выше −20 дБ от самой сильной. */
function harmonicCount(signal, from, f0, count = 30) {
  const levels = harmonicLevels(signal, from, f0, count);
  const loudest = Math.max(...levels);
  return levels.filter((db) => db > loudest - 20).length;
}

/** Пилообразный источник той же формы, что в движке (для передаточной функции). */
function sawSource(f0, seconds = 0.6) {
  const n = Math.round(seconds * SR);
  const out = new Float32Array(n);
  const maxHarmonic = Math.max(1, Math.floor(Math.min(SR / 2 - 500, 6000) / f0));
  for (let i = 0; i < n; i += 1) {
    let value = 0;
    for (let k = 1; k <= maxHarmonic; k += 1) value += Math.sin((2 * Math.PI * k * f0 * i) / SR) / k;
    out[i] = value * 0.55;
  }
  return out;
}

/**
 * Пики передаточной функции форманного фильтра, в Гц и дБ.
 *
 * Считаем не «горб спектра голоса» (на него влияет и источник), а отношение
 * «после фильтра / до фильтра» по гармоникам источника — то есть ровно ту
 * огибающую, которую задают форманты.
 */
function transferPeaks(signal, reference, f0, { from = 4000, count = 40 } = {}) {
  const post = harmonicLevels(signal, from, f0, count);
  const before = harmonicLevels(reference, from, f0, count);
  const transfer = post.map((db, index) => db - before[index]);
  // Сглаживание по трём гармоникам: соседние гармоники внутри одной форманты
  // образуют один горб, без сглаживания «пиком» считается шум.
  const smooth = transfer.map((db, index) => (
    transfer[Math.max(0, index - 1)] + db + transfer[Math.min(transfer.length - 1, index + 1)]
  ) / 3);
  const peaks = [];
  for (let index = 1; index < smooth.length - 1; index += 1) {
    if (smooth[index] > smooth[index - 1] && smooth[index] >= smooth[index + 1]) {
      const hz = (index + 1) * f0;
      if (hz >= 150 && hz <= 4200) peaks.push({ hz, db: smooth[index] });
    }
  }
  return peaks.sort((a, b) => b.db - a.db);
}

/** Ближайший к цели пик. */
const nearestPeak = (peaks, target) => peaks
  .map((peak) => ({ ...peak, distance: Math.abs(peak.hz - target) }))
  .sort((a, b) => a.distance - b.distance)[0];

test('синтез попадает в ноту строки', () => {
  for (const midi of [45, 57, 60, 64, 69]) {
    const want = hzOf(midi);
    const syllable = vocal.singSyllable({
      vowel: 'a', freq: want, duration: 0.5, sr: SR, random: vocal.rng(3),
    });
    const measured = pitchOf(syllable, 4000);
    const cents = 1200 * Math.log2(measured.hz / want);
    assert.ok(measured.confidence > 0.85, `midi ${midi}: тон не читается (${measured.confidence})`);
    // ±60 центов — половина полутона: «живое» вибрато и дрейф допустимы,
    // попадание в чужую ноту — нет.
    assert.ok(
      Math.abs(cents) <= 60,
      `midi ${midi}: ${want.toFixed(1)} Гц → ${measured.hz.toFixed(1)} Гц (${cents.toFixed(0)} центов)`,
    );
  }
});

test('гласные различаются формантами, а не только громкостью', () => {
  const shares = {};
  for (const vowel of ['a', 'o', 'u', 'e', 'i']) {
    const syllable = vocal.singSyllable({
      vowel, freq: hzOf(57), duration: 0.6, sr: SR, random: vocal.rng(3),
    });
    shares[vowel] = bandShares(syllable, SR * 0.2);
  }
  // Полосы: 250…700 / 700…1200 / 1200…2400 / 2400…4200 Гц.
  // «а» — открытая: главная форманта в полосе 700…1200 Гц.
  assert.ok(shares.a[1] > 35, `«а»: полоса 700…1200 всего ${shares.a[1].toFixed(0)}%`);
  // «у» и «о» — низкие: почти вся энергия ниже 700 Гц.
  assert.ok(shares.u[0] > 80, `«у»: полоса 250…700 всего ${shares.u[0].toFixed(0)}%`);
  assert.ok(shares.o[0] > 80, `«о»: полоса 250…700 всего ${shares.o[0].toFixed(0)}%`);
  // Пары должны отличаться, иначе это одна и та же гласная с разной громкостью.
  // Измерено: у «а» в полосе 700…1200 Гц 49 %, у «у» — 10 %, у «и» — 1 %.
  assert.ok(shares.a[1] > shares.u[1] + 30, `«а» и «у» не различаются (${shares.a[1].toFixed(0)} / ${shares.u[1].toFixed(0)})`);
  assert.ok(shares.a[1] > shares.i[1] + 30, `«а» и «и» не различаются (${shares.a[1].toFixed(0)} / ${shares.i[1].toFixed(0)})`);
  // «е» ниже по F1 (500 Гц), чем «а» (800 Гц): энергии в самой низкой полосе больше.
  assert.ok(shares.e[0] > shares.a[0] + 30, `«е» и «а» не различаются по F1 (${shares.e[0].toFixed(0)} / ${shares.a[0].toFixed(0)})`);
});

test('Форманты не режутся каскадом: верх спектра есть', () => {
  // Регрессия первого дефекта: каскад полосовых фильтров оставлял один
  // основной тон, и энергия выше 1 кГц была ровно 0 % на всех гласных.
  // Измерено при ноте 220 Гц: «а» 12.7 %, «е» 12.8 %, «и» 18.2 %, «у» 5.4 %,
  // «о» 2.1 %. Каскадный дефект давал ровно 0 % на всех гласных.
  const a = bandShares(vocal.singSyllable({
    vowel: 'a', freq: hzOf(57), duration: 0.6, sr: SR, random: vocal.rng(3),
  }), SR * 0.2);
  assert.ok(a[2] + a[3] > 5, `«а»: выше 1.2 кГц ${(a[2] + a[3]).toFixed(1)}% — форманты снова каскадом?`);

  // «и» и «е» выше по формантам, чем «у» — это уже не шум.
  const i = bandShares(vocal.singSyllable({
    vowel: 'i', freq: hzOf(57), duration: 0.6, sr: SR, random: vocal.rng(3),
  }), SR * 0.2);
  const u = bandShares(vocal.singSyllable({
    vowel: 'u', freq: hzOf(57), duration: 0.6, sr: SR, random: vocal.rng(3),
  }), SR * 0.2);
  assert.ok(i[2] + i[3] > u[2] + u[3], '«и» не выше «у» по высоким формантам');
});

test('форманты ложатся на свои частоты (передаточная функция фильтра)', () => {
  // Тот же дефект, но измеренный точнее: на низкой ноте (110 Гц) гармоники
  // стоят часто, и по ним видно, куда именно попал фильтр.
  const f0 = 110;
  const source = sawSource(f0);
  for (const vowel of ['a', 'o', 'u', 'e', 'i']) {
    const target = vocal.VOWELS[vowel].f;
    const filtered = vocal.formantFilter(source, target, SR, f0);
    const peaks = transferPeaks(filtered, source, f0);
    assert.ok(peaks.length >= 2, `«${vowel}»: пиков в огибающей ${peaks.length}`);

    const f1 = nearestPeak(peaks, target[0]);
    const f2 = nearestPeak(peaks, target[1]);
    assert.ok(Math.abs(f1.hz - target[0]) <= f0 * 1.5, `«${vowel}»: F1 ${target[0]} Гц, ближайший пик ${f1.hz} Гц`);
    assert.ok(Math.abs(f2.hz - target[1]) <= f0 * 1.5, `«${vowel}»: F2 ${target[1]} Гц, ближайший пик ${f2.hz} Гц`);
    // И оба пика должны быть усилением, а не провалом.
    assert.ok(f1.db > 0 && f2.db > -8, `«${vowel}»: F1 ${f1.db.toFixed(0)} дБ, F2 ${f2.db.toFixed(0)} дБ`);
  }
});

test('проверка ловит каскад: старый способ её проваливает', () => {
  // Проверка самой проверки: каскад обязан проваливать предыдущий тест,
  // иначе он ничего не охраняет.
  const f0 = 110;
  const source = sawSource(f0);
  let cascaded = source;
  for (let i = 0; i < 3; i += 1) {
    const center = vocal.VOWELS.a.f[i];
    const bw = Math.max(60, center * (i === 0 ? 0.16 : 0.22));
    cascaded = dsp.bandpass(cascaded, Math.max(80, center - bw / 2), center + bw / 2, SR, 2);
  }
  const f3 = nearestPeak(transferPeaks(cascaded, source, f0), 2900);
  assert.ok(
    !f3 || f3.db < -12,
    `каскад дал F3 ${f3 ? `${f3.db.toFixed(0)} дБ` : 'без пика'} — измерение перестало ловить дефект`,
  );
});

test('высокая нота не оставляет голос без формант', () => {
  // Полосы формант расширяются, если в них не попадает ни одна гармоника:
  // иначе на ноте 260…330 Гц гласная исчезала.
  // Измерено при компенсации спада источника: «и» при нотах 261…392 Гц даёт
  // 8.5…15.8 % энергии выше 1.2 кГц (до правки было 1 %).
  for (const midi of [60, 64, 69]) {
    const closed = vocal.singSyllable({
      vowel: 'i', freq: hzOf(midi), duration: 0.6, sr: SR, random: vocal.rng(3),
    });
    const bands = bandShares(closed, SR * 0.2);
    assert.ok(bands[2] + bands[3] > 3, `midi ${midi}: «и» выше 1.2 кГц ${(bands[2] + bands[3]).toFixed(1)}%`);
  }
  // Гармоник должно быть больше одной, иначе это синус. Проверяем на «а»:
  // у закрытой «и» первая форманта (320 Гц) на высокой ноте сама попадает
  // на основной тон, и спектр честно беден — так устроен голос.
  for (const midi of [57, 60, 64]) {
    const open = vocal.singSyllable({
      vowel: 'a', freq: hzOf(midi), duration: 0.6, sr: SR, random: vocal.rng(3),
    });
    const count = harmonicCount(open, SR * 0.2, hzOf(midi));
    assert.ok(count >= 3, `midi ${midi}: слышимых гармоник ${count}`);
  }
});

test('источник богат гармониками: голос, а не три синуса', () => {
  // Раньше источником были три синуса, и на ноте выше F3 формантам нечего
  // было усиливать.
  for (const midi of [45, 57, 60, 64]) {
    const syllable = vocal.singSyllable({
      vowel: 'a', freq: hzOf(midi), duration: 0.6, sr: SR, random: vocal.rng(3),
    });
    const count = harmonicCount(syllable, SR * 0.2, hzOf(midi));
    assert.ok(count >= 3, `midi ${midi}: слышимых гармоник ${count}, ожидалось не меньше 3`);
  }
});

test('огибающая: без клиппинга, но и не сплошной гул', () => {
  const line = vocal.singLine({
    text: 'я читаю твой трек наизусть', midiNotes: [57, 60, 62, 64], sr: SR, seed: 1,
  });
  const peak = dsp.peak(line.signal);
  assert.ok(peak <= 1.0001, `пик ${peak}`);
  assert.ok(peak > 0.7, `слишком тихо: пик ${peak}`);

  // Клиппинг: сэмплов на самом пределе быть не должно.
  let onLimit = 0;
  for (const value of line.signal) if (Math.abs(value) >= 0.999) onLimit += 1;
  assert.ok(onLimit / line.signal.length < 0.001, `на пределе ${((onLimit / line.signal.length) * 100).toFixed(2)}% сэмплов`);

  // Слоги: между ними есть паузы, иначе строка — непрерывный гул. «Тихо» —
  // относительно самой строки: громкость задаётся позднее, при миксе.
  const window = Math.round(SR * 0.01);
  const localPeaks = [];
  for (let start = 0; start + window <= line.signal.length; start += window) {
    let localPeak = 0;
    for (let i = start; i < start + window; i += 1) localPeak = Math.max(localPeak, Math.abs(line.signal[i]));
    localPeaks.push(localPeak);
  }
  const windows = localPeaks.length;
  const median = [...localPeaks].sort((a, b) => a - b)[Math.floor(windows / 2)];
  const quiet = localPeaks.filter((value) => value < median * 0.2).length;
  // Измерено: 11 % окон тише 20 % медианы.
  assert.ok(quiet / windows > 0.06, `тихих окон ${quiet} из ${windows} — слоги слиплись`);
  assert.ok(quiet / windows < 0.5, `тихих окон ${quiet} из ${windows} — строка почти пустая`);
});

test('длина строки следует за слогами и стилем', () => {
  const text = 'мой город спит';
  const syllables = vocal.splitSyllables(text).length;
  const sung = vocal.singLine({ text, midiNotes: [57], sr: SR, seed: 5, style: 'sung' });
  const rap = vocal.singLine({ text, midiNotes: [57], sr: SR, seed: 5, style: 'rap' });
  // sung: 0.32 с на слог (+4 % джиттера + согласные + паузы), rap: 0.19 с.
  const sungSec = sung.signal.length / SR;
  const rapSec = rap.signal.length / SR;
  assert.ok(sungSec > syllables * 0.3 && sungSec < syllables * 0.6, `${syllables} слогов → ${sungSec.toFixed(2)} с`);
  assert.ok(rapSec < sungSec * 0.8, `rap ${rapSec.toFixed(2)} с не короче sung ${sungSec.toFixed(2)} с`);
});

test('джиттер не уводит ноту: строй ровный при любом сиде', () => {
  const runs = [1, 2, 3, 4, 5].map((seed) => vocal.singSyllable({
    vowel: 'a', freq: hzOf(60), duration: 0.5, sr: SR, random: vocal.rng(seed),
  }));
  for (const signal of runs) {
    const hz = pitchOf(signal, 4000).hz;
    const cents = 1200 * Math.log2(hz / hzOf(60));
    assert.ok(Math.abs(cents) <= 60, `сид увёл ноту на ${cents.toFixed(0)} центов`);
  }
  // Повтор с тем же зерном — побитово тот же сигнал.
  const a = vocal.singLine({ text: 'мой город спит', sr: 22050, seed: 9 });
  const b = vocal.singLine({ text: 'мой город спит', sr: 22050, seed: 9 });
  assert.deepEqual(Array.from(a.signal), Array.from(b.signal));
});
