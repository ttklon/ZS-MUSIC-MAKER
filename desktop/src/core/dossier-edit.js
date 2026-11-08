'use strict';
/**
 * core/dossier-edit.js — досье артистов: список, создание, удаление.
 *
 * Раньше пустой раздел «Досье» предлагал уйти в терминал и запустить
 * `python main.py --dossier-add`. Но добавление артиста — это запись одного
 * JSON-файла, никакого Python для этого не нужно. Здесь то же самое делает
 * окно: создаёт `data/artist_dossier/<slug>/artist.json` в том же формате,
 * что и `modules/artist_dossier` (поля `artist`, `slug`, `tracks`,
 * `dossier`, `added_at`, `updated_at`), чтобы Python потом прочитал файл без
 * сюрпризов.
 *
 * Удаление трогает только каталог артиста внутри `data/artist_dossier` и
 * отказывается работать со схемой и с путями за пределами корня.
 */

const path = require('node:path');

/** Артисты, которые приходят вместе с приложением (демонстрация раздела). */
const DEMO_SLUGS = new Set(['demo_artist']);

/** Каталог досье внутри корня проекта. */
function dossierDir(root) {
  return path.join(root, 'data', 'artist_dossier');
}

/**
 * Slug в том же виде, что `modules/artist_dossier/schema.py::_slug`.
 *
 * Кириллица сохраняется, пробелы и пунктуация становятся `_`, регистр
 * приводится к нижнему. Пустое имя недопустимо: иначе все «безымянные»
 * артисты попали бы в один каталог.
 *
 * @param {string} name
 * @returns {string}
 */
function slugify(name) {
  const cleaned = String(name || '')
    .trim()
    .replace(/[^0-9A-Za-zА-Яа-яЁё_-]+/g, '_')
    .replace(/^_+|_+$/g, '');
  return cleaned.toLowerCase();
}

/** Список артистов в том же виде, что отдаёт `project.dossiers()`. */
function dossiers(fsApi, root) {
  const dir = dossierDir(root);
  const listing = fsApi.listDir(dir);
  if (listing.error) return { artists: [], error: `data/artist_dossier: ${listing.error}` };
  const artists = [];
  const errors = [];
  for (const entry of listing.entries) {
    const artistFile = path.join(dir, entry, 'artist.json');
    if (!fsApi.exists(artistFile)) continue;
    const data = fsApi.readJson(artistFile);
    if (data.error) {
      errors.push(`${entry}: ${data.error}`);
      continue;
    }
    const value = data.value || {};
    const tracks = Array.isArray(value.tracks) ? value.tracks : [];
    const dossier = value.dossier && typeof value.dossier === 'object' ? value.dossier : {};
    artists.push({
      artist: value.artist || entry,
      slug: value.slug || entry,
      tracks: tracks.length,
      hasDossier: Boolean(dossier.bio),
      deferred: Boolean(dossier.note) && !dossier.bio,
      // Демо-артист помечен отдельно: пустой раздел выглядит как поломка, а
      // пример в разделе объясняет формат. Подпись говорит, что это демо.
      demo: DEMO_SLUGS.has(value.slug || entry),
      note: value.note || dossier.note || null,
    });
  }
  artists.sort((a, b) => String(a.artist).localeCompare(String(b.artist), 'ru'));
  return { artists, error: errors.length ? errors.join('; ') : null };
}

/**
 * Создать артиста.
 *
 * @param {object} fsApi файловое API проекта
 * @param {string} root  корень проекта
 * @param {object} params `{ artist, note }`
 * @returns {{ok: true, data: object} | {ok: false, error: string}}
 */
function addArtist(fsApi, root, { artist, note = null } = {}) {
  const name = String(artist || '').trim();
  if (name.length < 2) return { ok: false, error: 'имя артиста короче двух символов' };
  if (name.length > 80) return { ok: false, error: 'имя артиста длиннее 80 символов' };
  const slug = slugify(name);
  if (!slug) return { ok: false, error: 'из этого имени не получается имя каталога' };

  const dir = dossierDir(root);
  const artistDir = path.join(dir, slug);
  const artistFile = path.join(artistDir, 'artist.json');
  if (fsApi.exists(artistFile)) {
    return { ok: false, error: `артист «${name}» уже есть (${slug})` };
  }

  const now = Date.now() / 1000;
  const payload = {
    artist: name,
    slug,
    added_at: now,
    updated_at: now,
    tracks: [],
    dossier: {},
    // Заметка видна в окне: пустое досье — не ошибка, а состояние.
    note: typeof note === 'string' && note.trim() ? note.trim().slice(0, 300) : null,
  };
  const written = fsApi.writeText(artistFile, `${JSON.stringify(payload, null, 2)}\n`);
  if (written.error) return { ok: false, error: `не удалось записать ${artistFile}: ${written.error}` };
  return {
    ok: true,
    data: { artist: name, slug, path: artistFile, tracks: 0, hasDossier: false },
  };
}

/**
 * Удалить артиста вместе с его каталогом.
 *
 * Схема (`schema.json`) и сам каталог досье не трогаются: проверка идёт по
 * реальному пути, а не по строке, которую прислало окно.
 *
 * @param {object} fsApi  файловое API проекта (нужен `removeDir`)
 * @param {string} root
 * @param {object} params `{ slug }`
 * @returns {{ok: true, data: object} | {ok: false, error: string}}
 */
function removeArtist(fsApi, root, { slug } = {}) {
  const clean = String(slug || '').trim();
  if (!clean || clean !== slugify(clean)) {
    return { ok: false, error: 'некорректное имя каталога артиста' };
  }
  if (typeof fsApi.removeDir !== 'function') {
    return { ok: false, error: 'файловое API не умеет удалять каталоги' };
  }
  const dir = dossierDir(root);
  const target = path.join(dir, clean);
  // Проверка по разрешённому пути: «..» и абсолютные пути отсекаются здесь,
  // даже если окно когда-нибудь будет взломано.
  if (path.dirname(target) !== path.resolve(dir)) {
    return { ok: false, error: 'путь вне каталога досье' };
  }
  if (!fsApi.exists(path.join(target, 'artist.json'))) {
    return { ok: false, error: `артиста «${clean}» нет` };
  }
  const removed = fsApi.removeDir(target);
  if (removed && removed.error) return { ok: false, error: removed.error };
  return { ok: true, data: { slug: clean, removed: true } };
}

module.exports = { DEMO_SLUGS, dossierDir, slugify, dossiers, addArtist, removeArtist };
