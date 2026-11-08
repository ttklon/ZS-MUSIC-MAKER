'use strict';
/**
 * settings.test.js — что приложение помнит между запусками.
 *
 * Файл настроек пишется на диск пользователя, поэтому проверяется и приём
 * мусора: чужие поля отбрасываются, а испорченный файл не роняет окно, а
 * возвращает значения по умолчанию и причину.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { sanitizeSettings, createSettingsStore, DEFAULTS } = require('../electron/settings');

function tempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-settings-'));
}

test('по умолчанию — рабочие параметры, а не пустой объект', () => {
  const store = createSettingsStore({ dir: tempDir() });

  assert.deepEqual(store.load().value, DEFAULTS);
});

test('настройки переживают перезапуск', () => {
  const dir = tempDir();
  createSettingsStore({ dir }).save({ genre: 'drill', bpm: 150, durationSec: 45, useBank: false });

  const again = createSettingsStore({ dir }).load();

  assert.equal(again.value.genre, 'drill');
  assert.equal(again.value.bpm, 150);
  assert.equal(again.value.durationSec, 45);
  assert.equal(again.value.useBank, false);
  assert.equal(again.error, null);
});

test('мусор в файле не ломает запуск, но назван', () => {
  const dir = tempDir();
  fs.writeFileSync(path.join(dir, 'settings.json'), '{ это не json');

  const result = createSettingsStore({ dir }).load();

  assert.deepEqual(result.value, DEFAULTS);
  assert.match(result.error, /settings\.json не прочитан/);
});

test('чужие поля не попадают в файл', () => {
  const dir = tempDir();
  createSettingsStore({ dir }).save({ genre: 'phonk', evil: 'rm -rf', shell: 'cmd.exe' });

  const saved = JSON.parse(fs.readFileSync(path.join(dir, 'settings.json'), 'utf8'));

  assert.deepEqual(Object.keys(saved).sort(), Object.keys(DEFAULTS).sort());
});

test('выход за границы откатывается к значению по умолчанию', () => {
  const { value, errors } = sanitizeSettings({ bpm: 5000, durationSec: -3, seed: 'abc', genre: 'phonk' });

  assert.equal(value.bpm, DEFAULTS.bpm);
  assert.equal(value.durationSec, DEFAULTS.durationSec);
  assert.equal(value.seed, DEFAULTS.seed);
  assert.deepEqual(errors.sort(), ['bpm', 'durationSec', 'seed']);
});

test('дробные и строковые числа приводятся к целым', () => {
  const { value } = sanitizeSettings({ bpm: '128.9', durationSec: '30', seed: '11' });

  assert.equal(value.bpm, 128);
  assert.equal(value.durationSec, 30);
  assert.equal(value.seed, 11);
});

test('жанр с путём или переводом строки не принимается', () => {
  for (const genre of ['../../etc/passwd', 'phonk\nrm', '']) {
    const { value, errors } = sanitizeSettings({ genre });

    assert.equal(value.genre, DEFAULTS.genre, `жанр «${genre}» должен быть отвергнут`);
    assert.ok(errors.includes('genre'));
  }
});

test('ошибка записи возвращается текстом, а не исключением', () => {
  const store = createSettingsStore({
    dir: '/virtual',
    fileSystem: {
      existsSync: () => false,
      readFileSync: () => '',
      mkdirSync: () => { throw new Error('EACCES'); },
      writeFileSync: () => { throw new Error('EACCES'); },
    },
  });

  const result = store.save({ bpm: 140 });

  assert.match(result.error, /EACCES/);
  assert.equal(result.value.bpm, DEFAULTS.bpm);
});
