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
  // Режим вокала запоминается названием, а не данными: сам дубль живёт в
  // памяти окна и в файл настроек попадать не должен (см. sanitizeSettings).
  vocalMode: 'none',
  vocalText: 'я читаю твой трек наизусть',
  vocalGain: 0.5,
  // Размер окна: на Windows 11 пользователь разворачивает окно под свой
  // монитор, и каждый запуск с 1280×820 выглядит как сброс настроек.
  windowWidth: 1280,
  windowHeight: 820,
  // Позиция окна. `null` — «куда положит Windows»: выдумывать координаты
  // хуже, чем открыть окно по центру экрана по умолчанию.
  windowX: null,
  windowY: null,
};

/** Координаты окна: экраны бывают и с отрицательным началом (монитор слева). */
const POSITION_LIMITS = {
  windowX: [-32000, 32000],
  windowY: [-32000, 32000],
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

/**
 * Режимы вокала, которые имеет смысл помнить между запусками.
 *
 * `record` помнится как НАЗВАНИЕ режима: самого дубля в новом запуске нет,
 * и окно возвращает «без вокала», объясняя это подписью. `file` не помнится
 * намеренно: файл мог исчезнуть, а молча рендерить «тишину» хуже, чем
 * попросить выбрать файл заново.
 */
const VOCAL_MODES = ['none', 'synth', 'test'];
const VOCAL_TEXT_MAX = 120;

/**
 * Разделы окна. Список нужен, чтобы `settings.json` не открывал окно на
 * несуществующем разделе (тогда экран был бы пустым без объяснения).
 */
const VIEWS = ['overview', 'modules', 'genres', 'beat', 'dossiers', 'tracks', 'run', 'health', 'help'];

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

  for (const [field, [min, max]] of Object.entries(POSITION_LIMITS)) {
    // `null` — законное значение: позиция не запоминалась.
    if (value[field] === null) {
      out[field] = null;
      continue;
    }
    const number = Number(value[field]);
    if (Number.isFinite(number) && number >= min && number <= max) out[field] = Math.trunc(number);
    else if (value[field] !== undefined) errors.push(field);
  }

  if (typeof value.useBank === 'boolean') out.useBank = value.useBank;
  if (typeof value.view === 'string' && VIEWS.includes(value.view)) out.view = value.view;
  else if (value.view !== undefined) errors.push('view');

  // Вокал: режим, текст и уровень — настройки; сэмплы — нет. Поле `vocal`
  // целиком (в нём окно раньше присылало `pcmBase64`) не сохраняется никогда:
  // это не «потеря поля», а защита файла настроек от десятков мегабайт звука.
  if (typeof value.vocalMode === 'string') {
    // `record` — законный режим, но помнится только как напоминание о нём:
    // дубля в новом запуске нет, и applyBeatSettings вернёт «без вокала».
    const mode = value.vocalMode.trim();
    if (mode === 'record') out.vocalMode = 'record';
    else if (VOCAL_MODES.includes(mode)) out.vocalMode = mode;
    else errors.push('vocalMode');
  } else if (value.vocalMode !== undefined) {
    errors.push('vocalMode');
  }

  if (typeof value.vocalText === 'string') {
    out.vocalText = value.vocalText.trim().slice(0, VOCAL_TEXT_MAX);
  } else if (value.vocalText !== undefined) {
    errors.push('vocalText');
  }

  {
    const gain = Number(value.vocalGain);
    if (Number.isFinite(gain) && gain >= 0 && gain <= 1) out.vocalGain = Math.round(gain * 100) / 100;
    else if (value.vocalGain !== undefined) errors.push('vocalGain');
  }

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

module.exports = {
  DEFAULTS, LIMITS, POSITION_LIMITS, GENRE_RE, VIEWS, VOCAL_MODES, VOCAL_TEXT_MAX,
  sanitizeSettings, createSettingsStore,
};
