'use strict';
/**
 * smoke.test.js — проверка упакованного приложения (`--smoke`).
 *
 * Это последний рубеж: если сборка потеряла `data/samples/` или не нашла
 * корень проекта, CI должен узнать об этом сам, без человека за экраном.
 * Поэтому проверяется и успешный путь, и то, что поломка даёт `ok: false`,
 * а не «зелёный» отчёт.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { runSmoke, smokeOutputPath, writeReport } = require('../electron/smoke');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');

function projectFor(root) {
  return () => createProject(createNodeFs(), root);
}

test('на репозитории проверка проходит целиком', async () => {
  const report = await runSmoke({ root: ROOT, createProject: projectFor(ROOT), packaged: false });

  assert.equal(report.ok, true, JSON.stringify(report.checks.filter((c) => !c.ok), null, 2));
  const names = report.checks.map((check) => check.name);
  for (const expected of [
    'version.json', 'каталог жанров', 'inventory', 'банк сэмплов', 'рендер бита',
    // Новые проверки упакованного приложения: вокал и правка досье без Python.
    'вокал (тестовый дубль)', 'досье читается', 'досье правится без Python',
  ]) {
    assert.ok(names.includes(expected), `нет проверки «${expected}»`);
  }
  assert.match(report.checks.find((c) => c.name === 'рендер бита').detail, /такт/);
  // Тестовый дубль в smoke обязан быть помечен как имитация, а не «записью».
  const vocal = report.checks.find((c) => c.name === 'вокал (тестовый дубль)');
  assert.match(vocal.detail, /не с микрофона/);
});

test('потерянный корень проекта — провал, а не пустой отчёт', async () => {
  const report = await runSmoke({
    root: null,
    rootError: 'Корень проекта не найден',
    createProject: () => {
      throw new Error('не должно вызываться');
    },
  });

  assert.equal(report.ok, false);
  assert.equal(report.checks[0].ok, false);
  assert.match(report.checks[0].detail, /не найден/);
});

test('проект без данных валит проверку с названной причиной', async () => {
  const empty = path.join(require('node:os').tmpdir(), 'zsmm-smoke-empty');
  const report = await runSmoke({ root: empty, createProject: projectFor(empty) });

  assert.equal(report.ok, false);
  const failed = report.checks.filter((check) => !check.ok).map((check) => check.name);
  assert.ok(failed.includes('каталог жанров'), `провалы: ${failed.join(', ')}`);
});

test('отсутствие Python не считается провалом сборки', async () => {
  const report = await runSmoke({
    root: ROOT,
    createProject: projectFor(ROOT),
    env: {},
    packaged: true,
  });

  const python = report.checks.find((check) => check.name === 'Python для задач');
  assert.equal(python.ok, true);
  assert.match(python.detail, /не найден|python/);
});

test('путь отчёта берётся из ZSMM_SMOKE_OUT, иначе из temp', () => {
  assert.equal(smokeOutputPath({ ZSMM_SMOKE_OUT: 'C:\\out\\smoke.json' }), 'C:\\out\\smoke.json');
  assert.match(smokeOutputPath({}, 'C:\\Temp'), /zsmm-smoke\.json$/);
});

test('отчёт печатается и пишется в файл даже без доступа к temp', () => {
  const written = [];
  const lines = [];
  const out = { write: (text) => lines.push(String(text)) };
  const report = { ok: true, checks: [] };

  const file = writeReport(report, {
    env: { ZSMM_SMOKE_OUT: 'C:\\out\\smoke.json' },
    writeFile: (target, text) => written.push({ target, text }),
    out,
  });

  assert.equal(file, 'C:\\out\\smoke.json');
  assert.equal(written.length, 1);
  assert.equal(written[0].target, file);
  assert.deepEqual(JSON.parse(written[0].text), report);
  assert.match(lines.join(''), /smoke: C:\\out\\smoke\.json/);
});

test('не удалось записать файл — отчёт всё равно напечатан, причина названа', () => {
  const lines = [];
  const out = { write: (text) => lines.push(String(text)) };
  writeReport(
    { ok: false },
    {
      env: { ZSMM_SMOKE_OUT: 'C:\\out\\smoke.json' },
      writeFile: () => {
        throw new Error('нет прав');
      },
      out,
    },
  );

  const text = lines.join('');
  assert.match(text, /"ok": false/, 'JSON должен уйти в консоль до записи файла');
  assert.match(text, /файл не записан \(нет прав\)/);
});
