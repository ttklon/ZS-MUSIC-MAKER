'use strict';
/**
 * sections/overview.js — раздел «Обзор»: готовность, счётчики модулей, потолки.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

async function loadOverview() {
  const [version, readiness, modules] = await Promise.all([ask('version'), ask('readiness'), ask('modules')]);

  $('version').textContent = version.version ? `v${version.version}` : 'версия неизвестна';
  if (version.error) showError(version.error);

  const caps = readiness.capsTriggered || [];
  const percent = readiness.percent === null || readiness.percent === undefined ? '—' : `${readiness.percent}%`;
  const inventory = readiness.moduleInventory || {};
  const cards = [
    card('Готовность', percent, readiness.stale ? `снимок ${readiness.ageDays} дн. назад` : 'по probes, с потолками'),
    card('Модулей', String(modules.total || 0), `${(modules.counts || {}).REAL_PASS || 0} достижимы`),
    card('Мёртвый код', String((modules.counts || {}).DEPRECATED || 0), 'не удалён, помечен в плане'),
    card('Потолки', String(caps.length), 'причины ниже 100 %'),
  ];
  $('overview-cards').replaceChildren(...cards);

  // причина отказа важнее любых цифр: сначала показываем её
  $('readiness-note').textContent = readiness.error
    ? readiness.error
    : caps.length
      ? 'Готовность ограничена потолками — они перечислены ниже, а не спрятаны.'
      : 'Потолков нет.';
  $('caps').replaceChildren(
    ...caps.map(([value, reason]) => {
      const item = el('li', null, `${value}% — ${reason}`);
      return item;
    }),
  );

  const stale = [];
  if (readiness.stale) stale.push(`снимок готовности сделан ${readiness.ageDays} дн. назад`);
  if (readiness.mismatch) stale.push('снимок расходится с пересчётом');
  if (stale.length) showError(`Данные устарели: ${stale.join('; ')}. Запустите node scripts/snapshot-readiness.js`);
  if (modules.error) showError(modules.error);
}

// ----------------------------------------------------------------- модули
async function loadModules() {
  const data = await ask('modules');
  state.modules = data;
  renderModules();
}

/** Перерисовать таблицу модулей по сохранённым данным и текущему фильтру. */
function renderModules() {
  const data = state.modules || {};
  if (data.error) showError(data.error);
  const counts = data.counts || {};
  $('modules-summary').textContent = data.total
    ? `${data.total} модулей: ` + Object.entries(counts).map(([k, v]) => `${k} — ${v}`).join(', ')
    : 'нет данных';

  const filter = ($('module-filter').value || '').trim().toLowerCase();
  const rows = (data.rows || [])
    .filter((row) => !filter || row.path.toLowerCase().includes(filter))
    .map((row) => {
      const tr = document.createElement('tr');
      const syntax = el('td', null, row.syntaxOk ? 'да' : 'нет');
      tr.append(
        el('td', null, row.path),
        (() => {
          const td = document.createElement('td');
          td.append(statusTag(row.status));
          return td;
        })(),
        el('td', null, row.reachable ? 'да' : 'нет'),
        el('td', null, String(row.productionReferences)),
        syntax,
      );
      return tr;
    });
  $('modules-body').replaceChildren(...rows);
  // Сколько нашлось по фильтру — видно сразу: «нет строк» иначе выглядит как
  // сломанная таблица, а не как пустой результат поиска.
  $('modules-found').textContent = filter
    ? `найдено ${rows.length} из ${(data.rows || []).length}`
    : '';
}

W.loadOverview = loadOverview;
W.loadModules = loadModules;
W.renderModules = renderModules;
