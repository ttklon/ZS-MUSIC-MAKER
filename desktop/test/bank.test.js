'use strict';
/**
 * bank.test.js — сэмпловый банк в окне: манифест, лицензии, выбор, отчёт.
 *
 * Живой one-shot лучше синтеза, но только если банк действительно прочитан и
 * лицензия позволяет. Поэтому проверяется не «функция вернула объект», а:
 * манифест разбирается на настоящих файлах, запрещённая лицензия не попадает
 * в трек, SHA-256 совпадает, а отчёт честно переключается между
 * REAL_PASS/PARTIAL/FALLBACK.
 */

const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');
const bank = require('../src/core/audio/bank');
const { Rng } = require('../src/core/audio/rng');

const ROOT = path.resolve(__dirname, '..', '..');
const fs = createNodeFs();

/** Манифест из памяти: проверки на «плохих» данных без правки файлов проекта. */
function fakeFs(files) {
  return {
    exists: (target) => Object.prototype.hasOwnProperty.call(files, target),
    readJson: (target) => ({ value: JSON.parse(files[target]) }),
    readBinary: (target) => ({ value: Buffer.from(files[target], 'binary') }),
  };
}

test('настоящий банк проекта читается: 32 one-shot, REAL_PASS', () => {
  const loaded = bank.loadBank(fs, ROOT);
  assert.strictEqual(loaded.empty, false);
  assert.strictEqual(loaded.total, 32);
  assert.deepStrictEqual(loaded.warnings, []);

  const report = bank.capability(loaded);
  assert.strictEqual(report.status, 'REAL_PASS');
  assert.deepStrictEqual(report.drum_instruments_with_samples, [
    'kick', 'snare', 'clap', 'hat', 'open_hat', '808',
  ]);
  assert.strictEqual(report.velocity_mode, 'engine-gain');
  assert.ok(report.instruments_on_synth.includes('melody'), 'мелодии в банке нет — синтез');
});

test('SHA-256 всех файлов банка совпадает с манифестом', () => {
  const checked = bank.verifyChecksums(fs, ROOT);
  assert.strictEqual(checked.length, 32);
  const broken = checked.filter((item) => !item.ok);
  assert.deepStrictEqual(broken, [], `не сходятся хэши: ${JSON.stringify(broken)}`);
});

test('запрещённая лицензия не попадает в трек и видна в предупреждениях', () => {
  const manifest = {
    schema: 'zsmm.sample-bank.v1',
    instruments: {
      kick: [
        { file: 'kick/ok.wav', license: 'CC0-1.0', round_robin: 0, velocity: 1.0 },
        { file: 'kick/bad.wav', license: 'ALL-RIGHTS-RESERVED', round_robin: 1, velocity: 1.0 },
      ],
    },
  };
  // Корень строится на месте: на Windows путь с ведущим «/» превращается
  // в «\\virtual\\...», и манифест «не находится» — тест падал не по делу.
  const root = path.resolve(path.sep, 'virtual', 'zsmm-bank');
  const sampleFile = (name) => path.join(root, 'data', 'samples', name);
  const fake = fakeFs({
    [path.join(root, 'data', 'samples', 'manifest.json')]: JSON.stringify(manifest),
    [sampleFile('kick/ok.wav')]: '',
    [sampleFile('kick/bad.wav')]: '',
  });
  const loaded = bank.loadBank(fake, root);
  const usable = bank.usable(loaded, 'kick');
  assert.strictEqual(usable.length, 1);
  assert.strictEqual(usable[0].relative, 'kick/ok.wav');
  assert.ok(loaded.warnings.some((warning) => warning.includes('ALL-RIGHTS-RESERVED')));

  const report = bank.capability(loaded);
  assert.strictEqual(report.status, 'PARTIAL');
  assert.deepStrictEqual(report.instruments_with_samples, ['kick']);
});

test('отсутствующий файл не считается покрытием', () => {
  const manifest = {
    schema: 'zsmm.sample-bank.v1',
    instruments: { snare: [{ file: 'snare/ghost.wav', license: 'CC0-1.0' }] },
  };
  const loaded = bank.loadBank(
    fakeFs({ '/v/data/samples/manifest.json': JSON.stringify(manifest) }),
    '/v',
  );
  assert.strictEqual(bank.usable(loaded, 'snare').length, 0);
  assert.ok(loaded.warnings.some((warning) => warning.includes('файла нет на диске')));
  assert.strictEqual(bank.capability(loaded).status, 'FALLBACK');
});

test('пустой манифест и его отсутствие — FALLBACK с причиной', () => {
  const noManifest = bank.loadBank({ exists: () => false, readJson: () => ({}) }, ROOT);
  assert.strictEqual(noManifest.empty, true);
  assert.ok(noManifest.warnings[0].includes('манифест банка не найден'));
  assert.strictEqual(bank.capability(noManifest).status, 'FALLBACK');

  const broken = bank.loadBank(
    { exists: () => true, readJson: () => ({ error: 'битый JSON: Unexpected token' }) },
    ROOT,
  );
  assert.strictEqual(broken.empty, true);
  assert.ok(broken.warnings[0].includes('битый JSON'));
});

test('выбор сэмпла: слой по velocity, затем round-robin, детерминированно', () => {
  const loaded = bank.loadBank(fs, ROOT);
  const kicks = bank.usable(loaded, 'kick');
  const picked = new Set();
  const rng = new Rng(5);
  for (let i = 0; i < 40; i += 1) picked.add(bank.chooseEntry(loaded, 'kick', rng).relative);
  assert.ok(picked.size > 1, 'round-robin должен давать разные файлы, а не один и тот же');
  assert.ok(picked.size <= kicks.length);

  // Без RNG берётся запись с наименьшим round_robin — предсказуемо.
  const fixed = bank.chooseEntry(loaded, 'kick', null);
  assert.strictEqual(fixed.roundRobin, 0);

  assert.strictEqual(bank.chooseEntry(loaded, 'foley', null), null, 'нет инструмента — нет сэмпла');
});

test('питч-шифт меняет длину и сохраняет форму', () => {
  const signal = new Float32Array(1000);
  for (let i = 0; i < signal.length; i += 1) signal[i] = Math.sin((2 * Math.PI * 20 * i) / 1000);
  const up = bank.pitchShift(signal, 12);
  assert.ok(up.length < signal.length, 'на октаву выше — короче');
  const down = bank.pitchShift(signal, -12);
  assert.ok(down.length > signal.length, 'на октаву ниже — длиннее');
  assert.strictEqual(bank.pitchShift(signal, 0), signal);
  let peak = 0;
  for (const value of up) peak = Math.max(peak, Math.abs(value));
  assert.ok(peak > 0.5 && peak <= 1.0001, 'шифт не должен раздувать пик');
});

test('источник сэмплов кэширует декодирование и отдаёт сэмпл банка', () => {
  const source = new bank.SampleSource({ fileSystem: fs, rootDir: ROOT });
  assert.strictEqual(source.empty, false);
  source.rootHz = 440;
  const first = source.audio('kick', new Rng(1), 1.0);
  assert.ok(first && first.length > 1000);
  assert.strictEqual(source.loaded, 1);
  source.audio('kick', new Rng(2), 1.0);
  assert.strictEqual(source.loaded, 1, 'повторный удар не должен перечитывать файл');

  const report = source.report();
  assert.strictEqual(report.status, 'REAL_PASS');
  assert.strictEqual(report.loaded_samples, 1);
});

test('источник без банка не падает и честно пустой', () => {
  const source = new bank.SampleSource({ fileSystem: fs, rootDir: path.join(ROOT, 'нет-такого') });
  assert.strictEqual(source.empty, true);
  assert.strictEqual(source.audio('kick', new Rng(1)), null);
  assert.strictEqual(source.report().status, 'FALLBACK');
});
