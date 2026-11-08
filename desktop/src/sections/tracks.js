'use strict';
/**
 * sections/tracks.js — раздел «Треки»: досье артиста ведётся из окна.
 *
 * Раньше трек можно было завести только через `python main.py --dossier-add`.
 * Здесь то же самое делает окно: выбор артиста, название, необязательные
 * ссылка и текст. Запись создаётся в формате Python-менеджера
 * (`core/dossier-tracks.js`), а разбор трека (темп, тональность, вокал)
 * остаётся за Python — до него статус честно «не разобран».
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

const W = window.ZSMM_UI;
const { $, el, showError, state } = W;

const STATUS_TEXT = {
  pending: 'не разобран',
  partial: 'разобран частично',
  analyzed: 'разобран',
};

/** Подпись трека: что известно и чего ещё нет. */
function trackLine(track) {
  const status = STATUS_TEXT[track.status] || track.status;
  const facts = [status];
  if (track.bpm) facts.push(`${track.bpm} BPM`);
  if (track.key) facts.push(track.key);
  if (track.hasLyrics) facts.push('есть текст');
  if (track.hasAudio) facts.push('есть аудио');
  if (track.externalUrl) facts.push(track.externalUrl);
  return `${track.title} — ${facts.join(', ')}`;
}

function renderTracks(tracks, errors) {
  $('tracks-status').textContent = tracks.length
    ? `Треков: ${tracks.length}. Разбор выполняет Python при сборке досье.`
    : 'У этого артиста треков пока нет: добавьте название выше.';
  $('tracks-list').replaceChildren(
    ...tracks.map((track) => {
      const item = el('li', 'row', trackLine(track));
      return item;
    }),
  );
  if (errors && errors.length) showError(`Треки прочитаны не полностью: ${errors.join('; ')}`);
}

/** Заполнить список артистов, сохранив текущий выбор. */
function fillArtists(artists) {
  const select = $('tracks-artist');
  const previous = select.value || state.trackArtist || null;
  select.replaceChildren(
    ...artists.map((artist) => {
      const option = document.createElement('option');
      option.value = artist.slug;
      option.textContent = artist.demo ? `${artist.artist} [демо]` : artist.artist;
      return option;
    }),
  );
  if (previous && artists.some((artist) => artist.slug === previous)) select.value = previous;
  state.trackArtist = select.value || null;
}

async function loadArtistTracks() {
  const select = $('tracks-artist');
  const slug = select.value;
  state.trackArtist = slug || null;
  if (!slug) {
    renderTracks([], []);
    return;
  }
  const reply = await W.askWith('dossierTracks', slug);
  if (!reply || reply.ok !== true) {
    renderTracks([], []);
    showError(`Треки не прочитаны: ${(reply && reply.error) || 'нет ответа'}`);
    return;
  }
  renderTracks(reply.data.tracks, reply.data.errors);
}

async function loadTracks() {
  const data = await W.ask('dossiers');
  const artists = data.artists || [];
  if (data.error) showError(data.error);
  fillArtists(artists);
  if (!artists.length) {
    $('tracks-status').textContent = 'Артистов нет: добавьте имя в разделе «Досье», трек заводится у артиста.';
    $('tracks-list').replaceChildren();
    return;
  }
  await loadArtistTracks();

  if (loadTracks.wired) return;
  loadTracks.wired = true;

  $('tracks-artist').addEventListener('change', () => {
    loadArtistTracks().catch((err) => showError(`Треки: ${err.message}`));
  });

  $('tracks-add').addEventListener('click', async () => {
    const slug = $('tracks-artist').value;
    const title = ($('tracks-title').value || '').trim();
    if (!slug) {
      showError('Сначала выберите артиста');
      return;
    }
    if (!title) {
      showError('Введите название трека');
      return;
    }
    const button = $('tracks-add');
    button.disabled = true;
    try {
      const reply = await W.askWith('dossierTrackAdd', {
        slug,
        title,
        externalUrl: ($('tracks-url').value || '').trim() || null,
        lyrics: ($('tracks-lyrics').value || '').trim() || null,
      });
      if (!reply || reply.ok !== true) {
        // Отказ («такой трек уже есть») — текст для человека, а не повод
        // очищать форму: пусть поправит название.
        showError(`Трек не добавлен: ${(reply && reply.error) || 'нет ответа'}`);
        return;
      }
      $('tracks-title').value = '';
      $('tracks-url').value = '';
      $('tracks-lyrics').value = '';
      state.lastTrack = reply.data;
      await loadArtistTracks();
    } catch (err) {
      showError(`Трек не добавлен: ${err.message}`);
    } finally {
      button.disabled = false;
    }
  });
}

W.loadTracks = loadTracks;
