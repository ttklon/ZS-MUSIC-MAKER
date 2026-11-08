'use strict';
/**
 * sections/genres.js — раздел «Жанры»: каталог из `config/genres_100.json` и пресеты.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

// ------------------------------------------------------------------ жанры
function renderGenres() {
  const needle = ($('genre-filter').value || '').trim().toLowerCase();
  const list = state.genres.filter(
    (genre) => !needle || genre.name.toLowerCase().includes(needle)
      || genre.category.toLowerCase().includes(needle),
  );
  $('genre-list').replaceChildren(
    ...list.map((genre) => {
      const li = el('li', genre.hasPreset ? 'chip has-preset' : 'chip');
      li.append(el('span', 'chip-name', genre.name));
      const meta = genre.hasPreset
        ? `${genre.category} · ${genre.bpm ? genre.bpm.join('–') + ' BPM' : 'BPM нет'}`
        : `${genre.category} · без пресета`;
      li.append(el('span', 'chip-meta', meta));
      return li;
    }),
  );
  $('genre-count').textContent = `${list.length} из ${state.genres.length}`;
}

async function loadGenres() {
  const data = await ask('genres');
  state.genres = data.genres || [];
  for (const error of data.errors || []) showError(error);
  $('genres-summary').textContent =
    `каталог: ${state.genres.length} жанров, пресетов: ${data.presetCount || 0}`;
  renderGenres();
}

W.loadGenres = loadGenres;
W.renderGenres = renderGenres;
