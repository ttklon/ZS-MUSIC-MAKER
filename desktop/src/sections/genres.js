'use strict';
/**
 * sections/genres.js — раздел «Жанры»: каталог из `config/genres_100.json` и пресеты.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

(function () {
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

      // Жанр — это не только справка: по клику он подставляется в раздел
      // «Бит» вместе с темпом пресета. Раньше 120 жанров были мёртвым списком,
      // из которого нельзя было ничего собрать.
      const send = el('button', 'ghost chip-send', 'Собрать бит');
      send.addEventListener('click', () => {
        const bpm = $('beat-bpm');
        const name = $('beat-genre');
        if (name) name.value = genre.name;
        if (bpm && genre.bpm && genre.bpm.length) {
          // Пресет даёт диапазон темпа — берём нижнюю границу как рабочую.
          bpm.value = String(Number(genre.bpm[0]) || bpm.value);
        }
        state.genreSent = genre.name;
        W.switchView('beat');
      });
      li.append(send);
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
  // В браузере все `<script>` делят одну глобальную область: второй
  // верхнеуровневый `const` с тем же именем роняет файл целиком
  // (`Identifier 'W' has already been declared`). Поэтому код раздела
  // живёт в своей функции, а наружу отдаёт только одно имя.
  window.ZSMM_SECTIONS.initGenres = function () {
    W.loadGenres = loadGenres;
  };
})();
