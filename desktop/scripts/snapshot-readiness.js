'use strict';
/**
 * scripts/snapshot-readiness.js — снимок честных чисел проекта.
 *
 * Вызывается вручную (или в CI) и делает две вещи:
 *  1. `python -m tools.readiness --json` → `data/desktop/readiness.json`;
 *  2. `python -m tools.readiness --inventory-markdown` → `data/desktop/inventory.md`.
 *
 * Окно не запускает Python: оно читает эти файлы. Такой снимок — это данные,
 * а не пересказ, и он помечен датой, чтобы окно могло сказать «устарел».
 */

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..', '..');
const OUT_DIR = path.join(ROOT, 'data', 'desktop');

function resolvePython(env = process.env) {
  const candidates = [env.ZSMM_PYTHON, path.join(ROOT, '.venv', 'bin', 'python3'),
    path.join(ROOT, '.venv', 'Scripts', 'python.exe'), '/usr/bin/python3', '/usr/local/bin/python3'];
  for (const candidate of candidates.filter(Boolean)) {
    if (fs.existsSync(candidate)) return candidate;
  }
  throw new Error('Python не найден: укажите ZSMM_PYTHON=/путь/к/python3');
}

function run(python, args) {
  const result = spawnSync(python, args, { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`python ${args.join(' ')} → код ${result.status}: ${(result.stderr || '').slice(-500)}`);
  }
  return result.stdout;
}

function snapshot({ python = null, now = new Date() } = {}) {
  const interpreter = python || resolvePython();
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const readinessRaw = run(interpreter, ['-m', 'tools.readiness', '--json']);
  const payload = JSON.parse(readinessRaw);
  const withDate = { generated_at: now.toISOString(), ...payload };
  fs.writeFileSync(path.join(OUT_DIR, 'readiness.json'), JSON.stringify(withDate, null, 2), 'utf8');

  const inventory = run(interpreter, ['-m', 'tools.readiness', '--inventory-markdown']);
  fs.writeFileSync(path.join(OUT_DIR, 'inventory.md'), inventory, 'utf8');

  return {
    percent: payload.percent,
    modules: (payload.module_inventory || {}).tracked_modules,
    caps: payload.caps_triggered || [],
    files: [path.join(OUT_DIR, 'readiness.json'), path.join(OUT_DIR, 'inventory.md')],
  };
}

if (require.main === module) {
  try {
    const info = snapshot();
    console.log(`готовность: ${info.percent}%, модулей: ${info.modules}`);
    for (const [value, reason] of info.caps) console.log(`  потолок ${value}%: ${reason}`);
    for (const file of info.files) console.log(`  записан ${path.relative(ROOT, file)}`);
  } catch (err) {
    console.error(`ошибка снимка: ${err.message}`);
    process.exitCode = 1;
  }
}

module.exports = { snapshot, resolvePython, OUT_DIR, ROOT };
