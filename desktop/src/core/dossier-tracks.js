'use strict';
/**
 * core/dossier-tracks.js — добавить трек в досье артиста без Python.
 *
 * Раньше «Добавить» умело только создавать артиста: у записи всегда было
 * `tracks: []`, и единственным способом завести трек был `python main.py
 * --dossier-add`. Но трек — это два файла (`tracks/<id>.json` и строка в
 * `artist.json`), так что окно делает это само.
 *
 * Формат повторяет `modules/artist_dossier`:
 *   - `<id>` = `<slug названия>_<первые 8 hex md5(название|ссылка)>`
 *     (`schema.py::_track_id`). Идентификатор считается здесь же: одинаковое
 *     название и ссылка дают тот же id, поэтому повтор не плодит дубли;
 *   - `tracks/<id>.json` — запись `TrackEntry` со `status: "pending"`;
 *   - анализ (`bpm`, тональность, тексты) выполняет Python при сборке досье,
 *     и здесь он не выдумывается: `features` пустой, `status` честный.
 *
 * Копирование аудиофайла сюда не входит: это отдельный шаг с диалогом выбора
 * файла, и притворяться, что трек «уже разобран», нельзя.
 */

const crypto = require('node:crypto');
const path = require('node:path');

const { dossierDir, slugify } = require('./dossier-edit');

/** Допустимые статусы записи — те же, что в Python-менеджере. */
const STATUSES = ['pending', 'partial', 'analyzed'];

/**
 * Идентификатор трека — копия `modules/artist_dossier/schema.py::_track_id`.
 *
 * @param {string} title
 * @param {string} [url]
 * @returns {string}
 */
function trackId(title, url = '') {
  const base = `${title || ''}|${url || ''}`;
  const hash = crypto.createHash('md5').update(base, 'utf8').digest('hex').slice(0, 8);
  return `${slugify(title).slice(0, 32)}_${hash}`;
}

/** Каталог `tracks/` конкретного артиста внутри `data/artist_dossier`. */
function tracksDir(root, slug, dataDir = null) {
  return path.join(dossierDir(root, dataDir), slug, 'tracks');
}

/**
 * Список треков артиста. Читаются только файлы `<id>.json`; битый файл — это
 * строка в `errors`, а не пустой список без объяснения.
 *
 * @returns {{tracks: Array<object>, errors: string[]}}
 */
function listTracks(fsApi, root, slug, opts = {}) {
  const dir = tracksDir(root, slug, opts.dataDir);
  const listing = fsApi.listDir(dir);
  if (listing.error) {
    // Каталога `tracks/` может не быть просто потому, что у артиста ещё нет
    // треков: это не «ошибка чтения», и пугать ею в окне нельзя — иначе
    // красный баннер висит на каждом свежем досье.
    const missing = fsApi.exists ? !fsApi.exists(dir) : listing.error === 'ENOENT';
    return { tracks: [], errors: missing ? [] : [`tracks/: ${listing.error}`] };
  }
  const tracks = [];
  const errors = [];
  for (const entry of listing.entries) {
    if (!entry.endsWith('.json')) continue;
    const data = fsApi.readJson(path.join(dir, entry));
    if (data.error) {
      errors.push(`${entry}: ${data.error}`);
      continue;
    }
    const value = data.value || {};
    tracks.push({
      track_id: value.track_id || entry.replace(/\.json$/, ''),
      title: value.title || entry,
      status: STATUSES.includes(value.status) ? value.status : 'pending',
      hasAudio: Boolean(value.audio_path),
      hasLyrics: Boolean(value.lyrics),
      externalUrl: value.external_url || null,
      // Поля анализа читаются, но не выдумываются: их заполняет Python.
      bpm: value.features && value.features.bpm ? value.features.bpm : null,
      key: value.features && value.features.key ? value.features.key : null,
    });
  }
  tracks.sort((a, b) => String(a.title).localeCompare(String(b.title), 'ru'));
  return { tracks, errors };
}

/**
 * Добавить трек.
 *
 * @param {object} fsApi
 * @param {string} root
 * @param {object} params `{ slug, title, externalUrl, lyrics }`
 * @returns {{ok: true, data: object} | {ok: false, error: string}}
 */
function addTrack(fsApi, root, { slug, title, externalUrl = null, lyrics = null } = {}, opts = {}) {
  const cleanSlug = String(slug || '').trim();
  if (!cleanSlug || cleanSlug !== slugify(cleanSlug)) {
    return { ok: false, error: 'некорректное имя каталога артиста' };
  }
  const dir = dossierDir(root, opts.dataDir);
  const artistFile = path.join(dir, cleanSlug, 'artist.json');
  if (!fsApi.exists(artistFile)) {
    return { ok: false, error: `артиста «${cleanSlug}» нет — сначала добавьте его` };
  }
  const name = String(title || '').trim();
  if (name.length < 2) return { ok: false, error: 'название трека короче двух символов' };
  if (name.length > 120) return { ok: false, error: 'название трека длиннее 120 символов' };
  const url = externalUrl === null || externalUrl === undefined ? '' : String(externalUrl).trim();
  if (url && !/^https?:\/\/[^\s]{4,300}$/i.test(url)) {
    return { ok: false, error: 'ссылка должна начинаться с http:// или https://' };
  }

  const id = trackId(name, url);
  const trackFile = path.join(dir, cleanSlug, 'tracks', `${id}.json`);
  if (fsApi.exists(trackFile)) {
    return { ok: false, error: `трек «${name}» уже есть у этого артиста` };
  }

  // Имя артиста берём из его записи: Python-менеджер пишет в трек
  // `artist` = имя, а не slug, и окно не должно создавать другой формат.
  const artist = fsApi.readJson(artistFile);
  if (artist.error) return { ok: false, error: `artist.json: ${artist.error}` };
  const record = artist.value || {};

  const text = lyrics === null || lyrics === undefined ? '' : String(lyrics);
  const payload = {
    track_id: id,
    title: name,
    artist: record.artist || cleanSlug,
    audio_path: null,
    external_url: url || null,
    lyrics: text.trim() ? text.slice(0, 20000) : null,
    audio_copy: {},
    // Пустые features — это не «нет данных», а «анализ ещё не выполнялся»:
    // так запись и читается (status: pending).
    features: {},
    dossier: {},
    status: 'pending',
    added_at: Date.now() / 1000,
  };
  const written = fsApi.writeText(trackFile, `${JSON.stringify(payload, null, 2)}\n`);
  if (written.error) return { ok: false, error: `не удалось записать трек: ${written.error}` };

  if (payload.lyrics) {
    const saved = fsApi.writeText(path.join(dir, cleanSlug, 'lyrics', `${id}.txt`), payload.lyrics);
    if (saved.error) return { ok: false, error: `не удалось сохранить текст: ${saved.error}` };
  }

  const tracks = Array.isArray(record.tracks) ? record.tracks : [];
  if (!tracks.includes(id)) tracks.push(id);
  record.tracks = tracks;
  record.updated_at = Date.now() / 1000;
  const resaved = fsApi.writeText(artistFile, `${JSON.stringify(record, null, 2)}\n`);
  if (resaved.error) return { ok: false, error: `не удалось обновить artist.json: ${resaved.error}` };

  return {
    ok: true,
    data: {
      track_id: id,
      title: name,
      hasLyrics: Boolean(payload.lyrics),
      externalUrl: payload.external_url,
      status: 'pending',
      tracks: tracks.length,
    },
  };
}

/**
 * Удалить трек у артиста.
 *
 * Зачем: трек заводят руками, и опечатка в названии — обычное дело. Пока
 * удаления не было, единственным способом исправить ошибку было лезть в
 * `data/artist_dossier` проводником.
 *
 * Удаляются `<id>.json`, `<id>.txt` (текст) и запись в `artist.json`. Каталог
 * `tracks/` не трогается: у артиста могут быть другие треки. Имя `id`
 * проверяется по разрешённому пути, как у удаления артиста.
 *
 * @param {object} fsApi файловое API проекта (нужен `removeFile`)
 * @param {string} root
 * @param {object} params `{ slug, trackId }`
 * @param {object} [opts] `{ dataDir }`
 * @returns {{ok: true, data: object} | {ok: false, error: string}}
 */
function removeTrack(fsApi, root, { slug, trackId: id } = {}, opts = {}) {
  const cleanSlug = String(slug || '').trim();
  if (!cleanSlug || cleanSlug !== slugify(cleanSlug)) {
    return { ok: false, error: 'некорректное имя каталога артиста' };
  }
  const cleanId = String(id || '').trim();
  // Идентификатор трека — `<slug названия>_<8 hex>`. Разрешаем только буквы,
  // цифры и подчёркивание (названия бывают русскими), но не `.` и не `/`:
  // иначе через `trackId` можно попросить удалить файл вне каталога треков.
  if (!/^[\p{L}\p{N}_]{2,40}_[0-9a-f]{8}$/u.test(cleanId)) {
    return { ok: false, error: 'некорректный идентификатор трека' };
  }
  if (typeof fsApi.removeFile !== 'function') {
    return { ok: false, error: 'файловое API не умеет удалять файлы' };
  }
  const dir = dossierDir(root, opts.dataDir);
  const artistDir = path.join(dir, cleanSlug);
  const artistFile = path.join(artistDir, 'artist.json');
  const trackFile = path.join(artistDir, 'tracks', `${cleanId}.json`);
  const allowed = path.resolve(path.join(artistDir, 'tracks'));
  if (path.dirname(path.resolve(trackFile)) !== allowed) {
    return { ok: false, error: 'путь вне каталога треков' };
  }
  if (!fsApi.exists(trackFile)) {
    return { ok: false, error: `трека «${cleanId}» у артиста нет` };
  }
  const artist = fsApi.readJson(artistFile);
  if (artist.error) return { ok: false, error: `artist.json: ${artist.error}` };

  // Сначала запись в artist.json, потом файлы: если второй шаг сорвётся,
  // трек останется сиротой в `tracks/`, а не «битой» ссылкой в досье.
  const record = artist.value || {};
  const tracks = Array.isArray(record.tracks) ? record.tracks.filter((item) => item !== cleanId) : [];
  record.tracks = tracks;
  record.updated_at = Date.now() / 1000;
  const resaved = fsApi.writeText(artistFile, `${JSON.stringify(record, null, 2)}\n`);
  if (resaved.error) return { ok: false, error: `не удалось обновить artist.json: ${resaved.error}` };

  const removed = fsApi.removeFile(trackFile);
  if (removed && removed.error) return { ok: false, error: `не удалось удалить трек: ${removed.error}` };
  const lyricsFile = path.join(artistDir, 'lyrics', `${cleanId}.txt`);
  if (fsApi.exists(lyricsFile)) fsApi.removeFile(lyricsFile);

  return { ok: true, data: { slug: cleanSlug, trackId: cleanId, tracks: tracks.length } };
}

module.exports = { STATUSES, trackId, tracksDir, listTracks, addTrack, removeTrack };
