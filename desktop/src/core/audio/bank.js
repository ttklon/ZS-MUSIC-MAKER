'use strict';
/**
 * core/audio/bank.js — сэмпловый банк в окне: манифест, лицензии, выбор.
 *
 * Порт `app/audio/samples.py` (часть, которая нужна движку бита). Живой
 * one-shot лучше синтеза, поэтому банк читается первым, а синтез остаётся
 * запасным путём — и отчёт обязан сказать, чем именно сыгран трек.
 *
 * Отличия от Python, о которых нужно помнить:
 *
 *  * SHA-256 не пересчитывается на каждый удар (это чтение всего файла);
 *    проверка целостности остаётся в Python-инструментах и в тестах;
 *  * `pitch_shift` тот же по смыслу — пересчёт скорости линейной
 *    интерполяцией, без сохранения длины: так делает драм-машина.
 */

const path = require('node:path');
const crypto = require('node:crypto');

const { decodeWav } = require('./wav-decode');
const { Rng } = require('./rng');

const SCHEMA = 'zsmm.sample-bank.v1';
const ALLOWED_LICENSES = ['CC0-1.0', 'CC0', 'PUBLIC-DOMAIN', 'CC-BY-4.0', 'CC-BY-3.0'];
const INSTRUMENTS = ['kick', 'snare', 'clap', 'hat', 'open_hat', '808', 'bass', 'melody', 'fx', 'foley'];
const DRUM_INSTRUMENTS = ['kick', 'snare', 'clap', 'hat', 'open_hat', '808'];

const licenseAllowed = (license) => ALLOWED_LICENSES.includes(String(license || '').toUpperCase());

/**
 * Прочитать манифест и разложить записи по инструментам.
 *
 * @param {object} fileSystem — `src/core/fs-node.js` (readJson/readBinary/exists)
 * @param {string} rootDir — корень проекта
 * @returns {{entries: object, warnings: string[], velocityMode: string, empty: boolean}}
 */
function loadBank(fileSystem, rootDir, { manifestPath = 'data/samples/manifest.json' } = {}) {
  const warnings = [];
  const entries = {};
  const result = {
    entries,
    warnings,
    velocityMode: 'layers',
    empty: true,
    schema: null,
    total: 0,
  };

  const absolute = path.join(rootDir, manifestPath);
  if (!fileSystem.exists(absolute)) {
    warnings.push(`манифест банка не найден: ${manifestPath}`);
    return result;
  }
  const read = fileSystem.readJson(absolute);
  if (read.error) {
    warnings.push(`манифест не прочитан: ${read.error}`);
    return result;
  }
  const manifest = read.value || {};
  result.schema = manifest.schema || null;
  if (manifest.schema && manifest.schema !== SCHEMA) {
    warnings.push(`неожиданная схема манифеста: ${manifest.schema}`);
  }
  if (typeof manifest.velocity_mode === 'string') result.velocityMode = manifest.velocity_mode;

  const samplesDir = path.dirname(absolute);
  for (const [instrument, rows] of Object.entries(manifest.instruments || {})) {
    if (!Array.isArray(rows)) continue;
    const usable = [];
    for (const row of rows) {
      if (!row || typeof row.file !== 'string') continue;
      const problems = [];
      if (!licenseAllowed(row.license)) problems.push(`лицензия ${row.license} не разрешена`);
      // Путь из манифеста может быть записан по-виндовому (`kick\\x.wav`):
      // на Linux такой файл «не находится», хотя лежит рядом. Разделители
      // приводятся к текущей платформе — это данные, а не код.
      const file = path.join(samplesDir, ...String(row.file).split(/[\\/]+/).filter(Boolean));
      if (!fileSystem.exists(file)) problems.push('файла нет на диске');
      usable.push({
        instrument,
        file,
        // В отчётах путь всегда в одну форму: иначе один и тот же сэмпл
        // называется по-разному на Windows и Linux.
        relative: String(row.file).split(/[\\/]+/).filter(Boolean).join('/'),
        license: row.license,
        source: row.source || '',
        sha256: row.sha256 || '',
        velocity: typeof row.velocity === 'number' ? row.velocity : 1.0,
        roundRobin: Number.isInteger(row.round_robin) ? row.round_robin : 0,
        tuningHz: typeof row.tuning_hz === 'number' ? row.tuning_hz : 0,
        problems,
        allowed: problems.length === 0,
      });
    }
    entries[instrument] = usable;
    for (const entry of usable) {
      if (!entry.allowed) warnings.push(`${instrument}: ${entry.relative} — ${entry.problems.join('; ')}`);
    }
  }

  result.empty = !INSTRUMENTS.some((name) => (entries[name] || []).some((entry) => entry.allowed));
  result.total = Object.values(entries)
    .flat()
    .filter((entry) => entry.allowed).length;
  return result;
}

/** Записи инструмента, которые можно брать в трек. */
function usable(bank, instrument) {
  return (bank.entries[instrument] || []).filter((entry) => entry.allowed);
}

/** Отчёт «чем играем»: те же поля, что `capability()` в Python. */
function capability(bank) {
  const covered = INSTRUMENTS.filter((name) => usable(bank, name).length > 0);
  const drumsCovered = DRUM_INSTRUMENTS.filter((name) => usable(bank, name).length > 0);
  return {
    status: covered.length >= 6 ? 'REAL_PASS' : covered.length ? 'PARTIAL' : 'FALLBACK',
    engine: 'app.audio.samples (js port)',
    instruments_with_samples: covered,
    instruments_on_synth: INSTRUMENTS.filter((name) => !covered.includes(name)),
    drum_instruments_with_samples: drumsCovered,
    total_samples: bank.total,
    velocity_mode: bank.velocityMode,
    warnings: bank.warnings.slice(),
  };
}

/**
 * Выбор записи: ближайший velocity-слой, затем round-robin.
 *
 * `rng` — `Rng` из `rng.js`: выбор детерминирован seed'ом, а не временем.
 */
function chooseEntry(bank, instrument, rng = null, velocity = 1.0) {
  const candidates = usable(bank, instrument);
  if (!candidates.length) return null;
  const layers = [...new Set(candidates.map((entry) => Math.round(entry.velocity * 1000) / 1000))].sort(
    (a, b) => a - b,
  );
  const nearest = layers.reduce(
    (best, layer) => (Math.abs(layer - velocity) < Math.abs(best - velocity) ? layer : best),
    layers[0],
  );
  const inLayer = candidates.filter((entry) => Math.round(entry.velocity * 1000) / 1000 === nearest);
  if (!rng || inLayer.length === 1) {
    return inLayer.slice().sort((a, b) => a.roundRobin - b.roundRobin)[0];
  }
  return inLayer[rng.int(inLayer.length)];
}

/** Изменение скорости как питч-шифт one-shot'а (длина меняется). */
function pitchShift(signal, semitones) {
  if (!signal || !signal.length || semitones === 0) return signal;
  const ratio = Math.pow(2, semitones / 12);
  const target = Math.max(2, Math.round(signal.length / ratio));
  const out = new Float32Array(target);
  for (let i = 0; i < target; i += 1) {
    const position = (i * (signal.length - 1)) / Math.max(1, target - 1);
    const low = Math.floor(position);
    const high = Math.min(signal.length - 1, low + 1);
    out[i] = signal[low] + (signal[high] - signal[low]) * (position - low);
  }
  return out;
}

/**
 * Банк как источник звука для `VoiceEngine`.
 *
 * Кэш держит уже декодированные сэмплы: один и тот же one-shot играет
 * десятки раз за такт, декодировать его каждый раз — впустую жечь время.
 */
class SampleSource {
  constructor({ fileSystem, rootDir, sampleRate = 44100, manifestPath } = {}) {
    this.fileSystem = fileSystem;
    this.rootDir = rootDir;
    this.sampleRate = sampleRate;
    this.manifestPath = manifestPath;
    this.bank = null;
    this.cache = new Map();
    this.errors = [];
    this.loaded = 0;
  }

  ensure() {
    if (!this.bank) {
      if (!this.fileSystem || !this.rootDir) {
        this.bank = { entries: {}, warnings: ['банк не подключён'], velocityMode: 'layers', empty: true, total: 0 };
      } else {
        this.bank = loadBank(this.fileSystem, this.rootDir, { manifestPath: this.manifestPath || undefined });
      }
      this.errors = this.bank.warnings.slice();
    }
    return this.bank;
  }

  get empty() {
    return this.ensure().empty;
  }

  /** Тот же контракт, что `_bank_audio` в Python: сэмпл или null. */
  audio(instrument, rng, velocity = 1.0) {
    const bank = this.ensure();
    const entry = chooseEntry(bank, instrument, rng, velocity);
    if (!entry) return null;

    const key = entry.relative;
    let audio = this.cache.get(key);
    if (!audio) {
      const read = this.fileSystem.readBinary(entry.file);
      if (read.error) {
        this.errors.push(`${entry.relative}: ${read.error}`);
        return null;
      }
      try {
        audio = decodeWav(read.value, { sampleRate: this.sampleRate }).audio;
      } catch (err) {
        this.errors.push(`${entry.relative}: ${err.message}`);
        return null;
      }
      this.cache.set(key, audio);
      this.loaded += 1;
    }
    if (entry.tuningHz && (instrument === 'kick' || instrument === '808')) {
      const ratio = Math.min(2, Math.max(0.5, (this.rootHz || 440) / entry.tuningHz));
      audio = pitchShift(audio, 12 * Math.log2(ratio));
    }
    return audio;
  }

  report() {
    const bank = this.ensure();
    const report = capability(bank);
    report.loaded_samples = this.loaded;
    if (this.errors.length) report.errors = this.errors.slice();
    return report;
  }
}

/** Проверка целостности банка: отдельная утилита, не часть рендера. */
function verifyChecksums(fileSystem, rootDir) {
  const bank = loadBank(fileSystem, rootDir);
  const checked = [];
  for (const entries of Object.values(bank.entries)) {
    for (const entry of entries) {
      if (!entry.allowed || !entry.sha256) continue;
      const read = fileSystem.readBinary(entry.file);
      if (read.error) {
        checked.push({ file: entry.relative, ok: false, error: read.error });
        continue;
      }
      const digest = crypto.createHash('sha256').update(read.value).digest('hex');
      checked.push({ file: entry.relative, ok: digest === entry.sha256 });
    }
  }
  return checked;
}

module.exports = {
  SCHEMA,
  ALLOWED_LICENSES,
  INSTRUMENTS,
  DRUM_INSTRUMENTS,
  hasRng: () => typeof Rng === 'function',
  licenseAllowed,
  loadBank,
  usable,
  capability,
  chooseEntry,
  pitchShift,
  SampleSource,
  verifyChecksums,
};
