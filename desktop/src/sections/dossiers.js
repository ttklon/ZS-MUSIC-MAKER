'use strict';
/**
 * sections/dossiers.js — раздел «Досье»: артисты из `data/artist_dossier/`.
 *
 * Раньше здесь был только список, а на пустом каталоге — совет идти в
 * терминал. Теперь артиста можно добавить и удалить прямо в окне: это
 * запись одного `artist.json` в том же формате, что у Python-менеджера
 * (`core/dossier-edit.js`). Сборка самого досье (bio, темы, анализ треков)
 * по-прежнему требует Python и честно названа в подписи.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

(function () {
const W = window.ZSMM_UI;
const { $, ask, showError, state } = W;

const EMPTY_TEXT = 'Артистов пока нет. Добавьте имя выше — окно само создаст запись в data/artist_dossier.';

/**
 * Отправить собранное имя в раздел «Запуск» и запустить сборку досье.
 *
 * Тяжёлую работу делает Python (`--dossier-build`), поэтому честный путь —
 * не притворяться, что окно считает само, а передать задачу туда, где она
 * выполняется, и показать её вывод.
 */
function runDossierBuild(artist) {
  const field = $('task-artist');
  if (field) field.value = artist;
  const select = $('task-select');
  if (select && [...select.options].some((option) => option.value === 'dossier-build')) {
    select.value = 'dossier-build';
  }
  W.switchView('run');
  // Запуск происходит уже в разделе «Запуск»: там видно команду, вывод и
  // кнопку «Остановить». Здесь только переключаем и ждём.
  setTimeout(() => {
    const start = $('task-start');
    if (start && !start.disabled) start.click();
  }, 0);
}

/** Нарисовать список артистов с кнопками удаления. */
function renderArtists(artists) {
  $('dossier-empty').textContent = artists.length
    ? `${artists.length} артист(ов) в досье. Полная сборка досье (биография, темы, разбор треков) `
      + 'требует Python: кнопка «Досье» запускает её в разделе «Запуск».'
    : EMPTY_TEXT;

  $('dossier-list').replaceChildren(
    ...artists.map((artist) => {
      const status = artist.hasDossier ? 'досье собрано' : artist.deferred ? 'отложено' : 'не собрано';
      const demo = artist.demo ? '[демо из поставки] ' : '';
      const note = artist.note ? ` — ${artist.note}` : '';
      // «Треки» — рядом с артистом: заводить трек логично там, где видишь
      // артиста, а не искать его в другом разделе по имени.
      const tracks = document.createElement('button');
      tracks.className = 'ghost';
      tracks.textContent = 'Треки';
      tracks.addEventListener('click', () => W.openArtistTracks(artist.slug));
      const build = document.createElement('button');
      build.className = 'ghost';
      build.textContent = 'Собрать досье';
      build.addEventListener('click', () => runDossierBuild(artist.artist));
      const remove = document.createElement('button');
      remove.className = 'ghost';
      remove.textContent = 'Удалить';
      remove.addEventListener('click', async () => {
        try {
          const reply = await W.askWith('dossierRemove', { slug: artist.slug });
          if (!reply || reply.ok !== true) {
            showError(`Не удалено: ${(reply && reply.error) || 'нет ответа'}`);
            return;
          }
          await W.loadDossiers();
        } catch (err) {
          showError(`Не удалено: ${err.message}`);
        }
      });
      const item = document.createElement('li');
      item.className = 'row';
      const text = document.createElement('span');
      text.textContent = `${demo}${artist.artist} — треков: ${artist.tracks}, ${status}${note}`;
      // Сборка досье идёт через Python: кнопка активна всегда, но текст
      // подписи раздела говорит, что для неё нужен Python.
      item.append(text, tracks, build, remove);
      return item;
    }),
  );
}

async function loadDossiers() {
  const data = await ask('dossiers');
  if (data.error) showError(data.error);
  const artists = data.artists || [];
  renderArtists(artists);

  const addButton = $('dossier-add');
  if (!addButton || addButton.dataset.wired === '1') return;
  addButton.dataset.wired = '1';

  addButton.addEventListener('click', async () => {
    const name = ($('dossier-name').value || '').trim();
    if (!name) {
      showError('Введите имя артиста');
      return;
    }
    addButton.disabled = true;
    try {
      const reply = await W.askWith('dossierAdd', {
        artist: name,
        note: ($('dossier-note').value || '').trim(),
      });
      if (!reply || reply.ok !== true) {
        // Отказ сервиса («артист уже есть») — это текст для пользователя, а не
        // повод ронять раздел: форму оставляем заполненной.
        showError(`Артист не добавлен: ${(reply && reply.error) || 'нет ответа'}`);
        return;
      }
      $('dossier-name').value = '';
      $('dossier-note').value = '';
      state.lastArtist = reply.data;
      await loadDossiers();
    } catch (err) {
      showError(`Артист не добавлен: ${err.message}`);
    } finally {
      addButton.disabled = false;
    }
  });
}

W.loadDossiers = loadDossiers;
  // В браузере все `<script>` делят одну глобальную область: второй
  // верхнеуровневый `const` с тем же именем роняет файл целиком
  // (`Identifier 'W' has already been declared`). Поэтому код раздела
  // живёт в своей функции, а наружу отдаёт только одно имя.
  window.ZSMM_SECTIONS.initDossiers = function () {
    W.loadDossiers = loadDossiers;
  };
})();
