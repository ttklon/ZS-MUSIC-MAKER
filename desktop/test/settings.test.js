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
    // Путь платформонезависимый: на Windows «/virtual» — не абсолютный путь.
    dir: path.resolve(path.sep, 'virtual', 'zsmm-settings'),
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

test('режим вокала запоминается, а звуковые данные — нет', () => {
  const dir = tempDir();
  // Ровно то, что окно отправляло после рендера с записью: параметры и
  // сами сэмплы в base64. Файл настроек не должен пухнуть от звука.
  createSettingsStore({ dir }).save({
    genre: 'phonk',
    bpm: 120,
    vocalMode: 'record',
    vocalText: 'строка',
    vocalGain: 0.5,
    vocal: { mode: 'record', pcmBase64: 'A'.repeat(700000) },
    pcmBase64: 'A'.repeat(700000),
  });

  const saved = JSON.parse(fs.readFileSync(path.join(dir, 'settings.json'), 'utf8'));

  assert.equal(saved.vocalMode, 'record');
  assert.equal(saved.vocalText, 'строка');
  assert.equal(saved.vocalGain, 0.5);
  assert.equal(saved.vocal, undefined, 'звук мелодии в настройках не хранится');
  assert.equal(saved.pcmBase64, undefined);
  // Главное: файл остался маленьким. Раньше он весил десятки мегабайт.
  const size = fs.statSync(path.join(dir, 'settings.json')).size;
  assert.ok(size < 4096, `settings.json раздулся до ${size} байт`);
});

test('чужие поля внутри вокала не проходят белый список', () => {
  const dir = tempDir();
  createSettingsStore({ dir }).save({
    vocalMode: 'файл с диска',       // не режим из списка
    vocalGain: 99,                    // вне диапазона 0…1
    vocalText: 'я'.repeat(5000),      // длиннее предела
  });

  const saved = JSON.parse(fs.readFileSync(path.join(dir, 'settings.json'), 'utf8'));

  assert.equal(saved.vocalMode, DEFAULTS.vocalMode);
  assert.equal(saved.vocalGain, DEFAULTS.vocalGain);
  assert.ok(saved.vocalText.length <= 120, `текст не обрезан: ${saved.vocalText.length}`);
});
