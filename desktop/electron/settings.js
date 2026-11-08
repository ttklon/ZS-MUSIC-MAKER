'use strict';
/**
 * settings.js — что приложение помнит между запусками.
 *
 * Хранилище — обычный JSON в каталоге пользователя (`app.getPath('userData')`,
 * на Windows 11 это `%APPDATA%\zs-music-maker-desktop`). Никаких внешних
 * зависимостей и никакой сети.
 *
 * Правила:
 *  - битый или чужой файл не роняет окно: возвращаются значения по умолчанию
 *    и причина (`error`), которую окно показывает;
 *  - сохраняется только белый список полей — файл настроек не должен стать
 *    способом дописать в приложение что угодно.
 */

const path = require('node:path');

const DEFAULTS = {
  genre: 'phonk',
  bpm: 140,
  seed: 7,
  durationSec: 20,
  useBank: true,
  view: 'overview',
  // Размер окна: на Windows 11 пользователь разворачивает окно под свой
  // монитор, и каждый запуск с 1280×820 выглядит как сброс настроек.
  windowWidth: 1280,
  windowHeight: 820,
};

const LIMITS = {
  bpm: [40, 300],
  seed: [0, 2 ** 31 - 1],
  durationSec: [1, 600],
  // Границы, а не размеры: окно больше монитора Windows 11 сам не покажет.
  windowWidth: [960, 10000],
  windowHeight: [600, 10000],
};

const GENRE_RE = /^[\w .+-]{1,40}$/;

/** Привести произвольный объект к известным полям. */
function sanitizeSettings(raw) {
  const value = raw && typeof raw === 'object' ? raw : {};
  const out = { ...DEFAULTS };
  const errors = [];

  if (typeof value.genre === 'string' && GENRE_RE.test(value.genre.trim())) {
    out.genre = value.genre.trim();
  } else if (value.genre !== undefined) {
    errors.push('genre');
  }

  for (const [field, [min, max]] of Object.entries(LIMITS)) {
    const number = Number(value[field]);
    if (Number.isFinite(number) && number >= min && number <= max) out[field] = Math.trunc(number);
    else if (value[field] !== undefined) errors.push(field);
  }

  if (typeof value.useBank === 'boolean') out.useBank = value.useBank;
  if (typeof value.view === 'string' && /^[a-z]{1,20}$/.test(value.view)) out.view = value.view;

  return { value: out, errors };
}

/**
 * Хранилище настроек.
 *
 * @param {object} params
 * @param {string} params.dir     каталог пользователя (userData)
 * @param {object} [params.fileSystem] подмена fs в тестах
 */
function createSettingsStore({ dir, fileSystem = require('node:fs') } = {}) {
  if (!dir) throw new Error('createSettingsStore: нужен каталог');
  const file = path.join(dir, 'settings.json');

  return {
    file,

    load() {
      try {
        if (!fileSystem.existsSync(file)) return { value: { ...DEFAULTS }, errors: [], error: null };
        const parsed = JSON.parse(fileSystem.readFileSync(file, 'utf8'));
        const { value, errors } = sanitizeSettings(parsed);
        return {
          value,
          errors,
          error: errors.length ? `в settings.json поправлены поля: ${errors.join(', ')}` : null,
        };
      } catch (err) {
        // Битый файл — не повод терять настройки пользователя молча.
        return {
          value: { ...DEFAULTS },
          errors: [],
          error: `settings.json не прочитан (${err.message}); взяты значения по умолчанию`,
        };
      }
    },

    save(patch) {
      const current = this.load().value;
      // `invalid` — какие поля не приняты: окно говорит об этом, а не молчит.
      const { value, errors } = sanitizeSettings({ ...current, ...(patch && typeof patch === 'object' ? patch : {}) });
      try {
        fileSystem.mkdirSync(dir, { recursive: true });
        fileSystem.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
        return { value, invalid: errors, error: null };
      } catch (err) {
        return { value: current, invalid: [], error: `settings.json не записан: ${err.message}` };
      }
    },
  };
}

module.exports = { DEFAULTS, LIMITS, GENRE_RE, sanitizeSettings, createSettingsStore };
