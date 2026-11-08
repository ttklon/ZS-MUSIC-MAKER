'use strict';
/**
 * sections/dossiers.js — раздел «Досье»: артисты из `data/artist_dossier/`.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

// ------------------------------------------------------------------ досье
async function loadDossiers() {
  const data = await ask('dossiers');
  if (data.error) showError(data.error);
  const artists = data.artists || [];
  $('dossier-empty').textContent = artists.length
    ? `${artists.length} артист(ов) в досье`
    : 'Досье пусто. Это не ошибка окна: артист добавляется командой python main.py --dossier-add.';
  $('dossier-list').replaceChildren(
    ...artists.map((artist) => {
      const state_ = artist.hasDossier ? 'досье собрано' : artist.deferred ? 'отложено' : 'не собрано';
      return el('li', null, `${artist.artist} — треков: ${artist.tracks}, ${state_}`);
    }),
  );
}

W.loadDossiers = loadDossiers;
