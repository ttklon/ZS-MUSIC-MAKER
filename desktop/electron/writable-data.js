'use strict';
/**
 * writable-data.js — куда приложение пишет досье в установленной сборке.
 *
 * Проблема, которую видно только на Windows: установщик NSIS кладёт данные в
 * `C:\Program Files\ZS Music Maker\resources\project`, а этот каталог обычному
 * пользователю недоступен для записи. Окно писало досье прямо туда — значит,
 * «Добавить артиста» и «Добавить трек» падали бы с `EACCES` у всех, кто
 * поставил приложение.
 *
 * Правило:
 *  - в репозитории (`npm start`) пишем в корень проекта — как читаем;
 *  - в установленной сборке пишем в каталог пользователя
 *    (`%APPDATA%\zs-music-maker-desktop\artist_dossier`), а поставку
 *    (`demo_artist`, `schema.json`) докладываем из `resources` только на
 *    чтение, если своего файла ещё нет.
 *
 * Слияние описано данными, а не кодом в `main.js`: `plan()` принимает списки
 * файлов и говорит, что копировать и что писать, поэтому проверяется без
 * графической среды и без установщика.
 */

const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');

/**
 * Маркер первого запуска. Без него удалённый пользователем демо-артист
 * возвращался бы при каждом старте: «нет файла — скопируем» не отличает
 * первый запуск от намеренного удаления.
 */
const SEED_MARKER = '.seeded.json';

/** Файлы поставки, которые копируются в каталог пользователя. */
const SEED_FILES = [
  { from: 'schema.json', to: 'schema.json' },
  { from: path.join('demo_artist', 'artist.json'), to: path.join('demo_artist', 'artist.json') },
];

/**
 * Каталог досье для записи.
 *
 * @param {object} params
 * @param {boolean} params.packaged   `app.isPackaged`
 * @param {string} params.projectRoot корень проекта (может быть read-only)
 * @param {string} params.userData    `app.getPath('userData')`
 * @returns {{dir: string, source: 'project'|'user', projectDir: string}}
 */
function dossierWriteDir({ packaged, projectRoot, userData }) {
  const projectDir = path.join(projectRoot, 'data', 'artist_dossier');
  if (!packaged) return { dir: projectDir, source: 'project', projectDir };
  if (!userData) return { dir: projectDir, source: 'project', projectDir };
  return { dir: path.join(userData, 'artist_dossier'), source: 'user', projectDir };
}

/**
 * Что скопировать из поставки в каталог пользователя.
 *
 * @param {object} params
 * @param {string[]} params.userEntries    уже существующие записи в user-каталоге
 * @param {string[]} params.projectEntries имена папок/файлов в поставке
 * @returns {Array<{from: string, to: string}>} план копирования (только недостающее)
 */
function seedPlan({ userEntries = [], projectEntries = [] } = {}) {
  const have = new Set(userEntries);
  const available = new Set(projectEntries);
  return SEED_FILES
    .filter((file) => available.has(file.from.split(path.sep)[0]))
    .filter((file) => !have.has(file.from.split(path.sep)[0]))
    .map((file) => ({ ...file }));
}

/**
 * Подготовить хранилище досье к работе.
 *
 * Возвращает куда писать и что уже скопировано. Ошибка копирования не роняет
 * окно: раздел «Досье» просто откроется пустым, а причина попадёт в `error`.
 *
 * @param {object} params
 * @param {boolean} params.packaged
 * @param {string} params.projectRoot
 * @param {string|null} params.userData
 * @param {object} [params.fileSystem]
 * @returns {{dir: string, source: 'project'|'user', projectDir: string,
 *            seeded: string[], error: string|null}}
 */
function prepareDossierStore({ packaged, projectRoot, userData, fileSystem = createNodeFs() }) {
  const plan = dossierWriteDir({ packaged, projectRoot, userData });
  if (plan.source !== 'user') return { ...plan, seeded: [], error: null };
  const marker = path.join(plan.dir, SEED_MARKER);
  if (fileSystem.exists(marker)) return { ...plan, seeded: [], error: null };
  try {
    const listing = fileSystem.listDir(plan.projectDir);
    const existing = fileSystem.listDir(plan.dir);
    if (listing.error) {
      // Поставка не читается — маркер не ставим: при следующем запуске
      // попробуем снова, а не оставим раздел пустым навсегда.
      return { ...plan, seeded: [], error: `досье: поставка не читается (${listing.error})` };
    }
    const copy = seedPlan({
      userEntries: existing.entries || [],
      projectEntries: listing.entries || [],
    });
    const seeded = [];
    for (const file of copy) {
      const data = fileSystem.readText(path.join(plan.projectDir, file.from));
      if (data.error) continue;
      const written = fileSystem.writeText(path.join(plan.dir, file.to), data.value);
      if (!written.error) seeded.push(file.to);
    }
    fileSystem.writeText(marker, `${JSON.stringify({ seeded, at: new Date().toISOString() }, null, 2)}\n`);
    return { ...plan, seeded, error: null };
  } catch (err) {
    return { ...plan, seeded: [], error: `досье: ${err.message}` };
  }
}

module.exports = {
  SEED_FILES, SEED_MARKER, dossierWriteDir, seedPlan, prepareDossierStore,
};
