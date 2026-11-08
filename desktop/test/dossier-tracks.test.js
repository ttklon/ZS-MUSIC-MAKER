'use strict';
/**
 * test/dossier-tracks.test.js — трек добавляется в досье без Python.
 *
 * Проверяется главное: файл трека совпадает по формату с тем, что пишет
 * `modules/artist_dossier` (идентификатор, поля `TrackEntry`, строка в
 * `artist.json`), а анализ не выдумывается — `status` остаётся `pending`.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');
const dossier = require('../src/core/dossier-edit');
const tracks = require('../src/core/dossier-tracks');

function makeRoot() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-tracks-'));
  fs.mkdirSync(path.join(root, 'data', 'artist_dossier'), { recursive: true });
  return root;
}

test('идентификатор трека совпадает с Python-формулой', () => {
  // Значения посчитаны `modules/artist_dossier/schema.py::_track_id`:
  // `<slug>_<первые 8 hex md5(название|ссылка)>`. Если окно разойдётся с
  // Python, один и тот же трек получит два разных файла.
  assert.equal(tracks.trackId('Intro Track'), 'intro_track_223d85c6');
  assert.equal(tracks.trackId('Мой трек'), 'мой_трек_eb49e9ad');
  assert.equal(tracks.trackId('demo 01'), 'demo_01_8f1f9480');
});

test('трек пишется в формате TrackEntry и попадает в artist.json', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  const added = dossier.addArtist(fsApi, root, { artist: 'Тест Артист' });
  assert.equal(added.ok, true, added.error);

  const track = tracks.addTrack(fsApi, root, {
    slug: added.data.slug,
    title: 'Intro Track',
    lyrics: 'первая строка\nвторая строка',
  });
  assert.equal(track.ok, true, track.error);
  assert.equal(track.data.status, 'pending', 'анализ не выполнялся — статус не может быть «разобран»');
  assert.equal(track.data.hasLyrics, true);

  const file = path.join(root, 'data', 'artist_dossier', added.data.slug, 'tracks', 'intro_track_223d85c6.json');
  assert.ok(fs.existsSync(file), 'файл трека не создан');
  const stored = JSON.parse(fs.readFileSync(file, 'utf8'));
  for (const key of [
    'track_id', 'title', 'artist', 'audio_path', 'external_url', 'lyrics',
    'audio_copy', 'features', 'dossier', 'status', 'added_at',
  ]) {
    assert.ok(key in stored, `в записи трека нет поля ${key}`);
  }
  assert.equal(stored.artist, 'Тест Артист', 'в треке должно быть имя артиста, как у Python-менеджера');
  assert.deepEqual(stored.features, {}, 'анализ не выполнялся — features пустой');

  const artist = JSON.parse(
    fs.readFileSync(path.join(root, 'data', 'artist_dossier', added.data.slug, 'artist.json'), 'utf8'),
  );
  assert.deepEqual(artist.tracks, ['intro_track_223d85c6']);

  const lyricsFile = path.join(root, 'data', 'artist_dossier', added.data.slug, 'lyrics', 'intro_track_223d85c6.txt');
  assert.ok(fs.existsSync(lyricsFile), 'текст трека не сохранён');
  assert.match(fs.readFileSync(lyricsFile, 'utf8'), /вторая строка/);

  fs.rmSync(root, { recursive: true, force: true });
});

test('список треков читается: название, статус, наличие текста', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  const added = dossier.addArtist(fsApi, root, { artist: 'Список' });
  tracks.addTrack(fsApi, root, { slug: added.data.slug, title: 'Второй трек' });
  tracks.addTrack(fsApi, root, { slug: added.data.slug, title: 'Первый трек', externalUrl: 'https://example.com/t' });

  const list = tracks.listTracks(fsApi, root, added.data.slug);
  assert.deepEqual(list.errors, []);
  assert.deepEqual(list.tracks.map((t) => t.title), ['Второй трек', 'Первый трек']);
  assert.equal(list.tracks[0].status, 'pending');
  assert.equal(list.tracks[1].externalUrl, 'https://example.com/t');

  fs.rmSync(root, { recursive: true, force: true });
});

test('повтор, пустое название и чужая ссылка отклоняются текстом', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  const added = dossier.addArtist(fsApi, root, { artist: 'Отказы' });
  const slug = added.data.slug;
  assert.equal(tracks.addTrack(fsApi, root, { slug, title: 'Один трек' }).ok, true);

  const again = tracks.addTrack(fsApi, root, { slug, title: 'Один трек' });
  assert.equal(again.ok, false);
  assert.match(again.error, /уже есть/);

  assert.match(tracks.addTrack(fsApi, root, { slug, title: 'Я' }).error, /короче/);
  assert.match(
    tracks.addTrack(fsApi, root, { slug, title: 'Ссылка', externalUrl: 'ftp://x' }).error,
    /http/,
  );
  assert.match(
    tracks.addTrack(fsApi, root, { slug: '../..', title: 'Побег' }).error,
    /каталога/,
  );
  assert.match(
    tracks.addTrack(fsApi, root, { slug: 'нет_такого', title: 'Чужой' }).error,
    /сначала добавьте/,
  );
  fs.rmSync(root, { recursive: true, force: true });
});

test('битый файл трека не прячет остальные', () => {
  const root = makeRoot();
  const fsApi = createNodeFs();
  const added = dossier.addArtist(fsApi, root, { artist: 'Битый' });
  tracks.addTrack(fsApi, root, { slug: added.data.slug, title: 'Живой трек' });
  fs.writeFileSync(
    path.join(root, 'data', 'artist_dossier', added.data.slug, 'tracks', 'сломанный.json'),
    '{ не json',
  );

  const list = tracks.listTracks(fsApi, root, added.data.slug);
  assert.equal(list.tracks.length, 1);
  assert.equal(list.errors.length, 1);
  assert.match(list.errors[0], /сломанный\.json/);
  fs.rmSync(root, { recursive: true, force: true });
});
