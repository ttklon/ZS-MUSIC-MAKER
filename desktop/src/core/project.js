'use strict';
/**
 * core/project.js — «модель проекта» для окна: версия, жанры, пресеты,
 * модули, досье и сохранённый отчёт готовности.
 *
 * Здесь нет ни Python, ни сети: всё читается из файлов репозитория. Отчёт
 * готовности (`data/desktop/readiness.json`) готовит `scripts/snapshot-readiness.js`,
 * который вызывает штатный `python -m tools.readiness --json`; окно только
 * читает снимок и честно говорит, если он устарел.
 */

const path = require('node:path');
const { createCatalog, parseInventoryMarkdown, summarizeInventory } = require('./catalog');
const { computeReadiness } = require('./readiness');

const SNAPSHOT_MAX_AGE_DAYS = 30;

function createProject(fsApi, root) {
  const rootPath = path.resolve(root);
  const catalog = createCatalog(fsApi, rootPath);

  function version() {
    const file = path.join(rootPath, 'version.json');
    const data = fsApi.readJson(file);
    if (data.error) return { version: null, build: null, error: `version.json: ${data.error}` };
    const value = data.value || {};
    return {
      version: value.version || null,
      build: value.build || null,
      error: null,
    };
  }

  function genres() {
    const { genres: list, categories, error } = catalog.readCatalog();
    const { presets, error: presetError } = catalog.readPresets();
    const index = catalog.indexPresets(presets);
    const cards = list.map((genre) => catalog.genreCard(genre, index.get(catalog.normalizeKey(genre.name)) || null));
    const matched = cards.filter((card) => card.hasPreset).length;
    return {
      genres: cards,
      categories,
      presetCount: Object.keys(presets).length,
      matchedPresets: matched,
      errors: [error, presetError].filter(Boolean),
    };
  }

  function modules() {
    const markdownPath = path.join(rootPath, 'data', 'desktop', 'inventory.md');
    const text = fsApi.readText(markdownPath);
    if (text.error) {
      return {
        rows: [],
        counts: {},
        total: 0,
        error: `data/desktop/inventory.md не прочитан (${text.error}). `
          + 'Сгенерируйте снимок: node scripts/snapshot-readiness.js',
      };
    }
    const { rows, errors } = parseInventoryMarkdown(text.value);
    if (!rows.length) {
      return { rows: [], counts: {}, total: 0, error: 'снимок inventory пуст — проверьте генератор' };
    }
    const summary = summarizeInventory(rows);
    return { rows, ...summary, error: errors.length ? errors.join('; ') : null };
  }

  function readiness() {
    const file = path.join(rootPath, 'data', 'desktop', 'readiness.json');
    const data = fsApi.readJson(file);
    if (data.error) {
      return {
        percent: null,
        blockScores: {},
        capsTriggered: [],
        error: `снимок готовности не прочитан (${data.error}). `
          + 'Сгенерируйте: node scripts/snapshot-readiness.js',
      };
    }
    const snapshot = data.value || {};
    const generatedAt = snapshot.generated_at ? new Date(snapshot.generated_at) : null;
    const ageDays = generatedAt ? (Date.now() - generatedAt.getTime()) / 86_400_000 : null;
    const stale = ageDays !== null && ageDays > SNAPSHOT_MAX_AGE_DAYS;
    // пересчитываем сами и сверяем: расхождение — это ошибка, а не «нюанс»
    const recomputed = computeReadiness({
      probes: snapshot.raw_probes || {},
      inventory: snapshot.module_inventory || null,
    });
    const mismatch = snapshot.percent !== undefined && snapshot.percent !== recomputed.percent;
    return {
      percent: snapshot.percent !== undefined ? snapshot.percent : null,
      recomputedPercent: recomputed.percent,
      blockScores: snapshot.block_scores || recomputed.blockScores,
      capsTriggered: snapshot.caps_triggered || recomputed.capsTriggered,
      moduleInventory: snapshot.module_inventory || null,
      generatedAt: snapshot.generated_at || null,
      ageDays: ageDays === null ? null : Math.round(ageDays * 10) / 10,
      stale,
      mismatch,
      error: mismatch
        ? `снимок ${snapshot.percent}% расходится с пересчётом ${recomputed.percent}% — перегенерируйте`
        : null,
    };
  }

  function dossiers() {
    const dir = path.join(rootPath, 'data', 'artist_dossier');
    const listing = fsApi.listDir(dir);
    if (listing.error) {
      return { artists: [], error: `data/artist_dossier: ${listing.error}` };
    }
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
        note: dossier.note || null,
      });
    }
    artists.sort((a, b) => String(a.artist).localeCompare(String(b.artist), 'ru'));
    return { artists, error: errors.length ? errors.join('; ') : null };
  }

  /** Сводка окружения: то, что окно может узнать без запуска Python. */
  function systemInfo() {
    return {
      root: rootPath,
      platform: process.platform,
      node: process.versions.node,
      electron: process.versions.electron || null,
      chrome: process.versions.chrome || null,
    };
  }

  return { version, genres, modules, readiness, dossiers, systemInfo, rootPath, catalog };
}

module.exports = { createProject, SNAPSHOT_MAX_AGE_DAYS };
