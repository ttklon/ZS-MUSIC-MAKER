'use strict';
/**
 * native-tasks.js — задачи раздела «Запуск», которые окно считает само.
 *
 * Раньше весь раздел «Запуск» требовал Python: даже «проверить, что файлы на
 * месте» вызывало `python main.py --health`. Но эти три проверки — чтение
 * файлов и арифметика, а не движок: их честно делает главный процесс.
 *
 * Правила те же, что у Python-задач (`tasks.js`):
 *   - белый список ключей, произвольный процесс запустить нельзя;
 *   - вывод строится построчно (`OK`/`ПРОБЛЕМА`), а не «всё хорошо»;
 *   - `ok` в конце — это результат проверки, а не «функция отработала».
 *
 * Здесь нет ни `electron`, ни сети: только файлы проекта. Поэтому модуль
 * проверяется обычным `node --test` на настоящем репозитории.
 */

const path = require('node:path');

const { createNodeFs } = require('../src/core/fs-node');

const MAX_LINE = 400;

/** Одна строка вывода: длинные пути не должны ломать окно. */
function line(text) {
  const value = String(text ?? '');
  return value.length > MAX_LINE ? `${value.slice(0, MAX_LINE)}…` : value;
}

/**
 * Проверка файла: существует, читается, содержит то, что нужно.
 *
 * `format` важен: `inventory.md` — markdown, и `readJson` на нём отвечает
 * «битый JSON», что выглядело бы как поломка данных вместо неверного чтения.
 */
function checkFile(fsApi, root, relative, label, validate, format = 'json') {
  const file = path.join(root, relative);
  if (!fsApi.exists(file)) return { ok: false, line: `ПРОБЛЕМА ${label}: нет ${relative}` };
  const data = format === 'text' ? fsApi.readText(file) : fsApi.readJson(file);
  if (data.error) return { ok: false, line: `ПРОБЛЕМА ${label}: ${relative} не читается (${data.error})` };
  if (typeof validate === 'function') {
    const verdict = validate(data.value);
    if (verdict) return { ok: false, line: `ПРОБЛЕМА ${label}: ${relative} — ${verdict}` };
  }
  return { ok: true, line: `OK ${label}: ${relative}` };
}

/** 1. Файлы, без которых окно показывает пустые разделы. */
function projectCheck({ root, fsApi = createNodeFs(), dossierDir = null }) {
  const lines = [];
  const results = [
    checkFile(fsApi, root, 'version.json', 'версия', (value) => (value && value.version ? null : 'нет поля version')),
    checkFile(fsApi, root, 'config/genres_100.json', 'каталог жанров', (value) => {
      const count = Object.values(value || {}).reduce((sum, list) => sum + (Array.isArray(list) ? list.length : 0), 0);
      return count >= 100 ? null : `жанров ${count}, ожидалось не меньше 100`;
    }),
    // Манифест банка: `instruments` — карта инструмент → список one-shot'ов.
    checkFile(fsApi, root, 'data/samples/manifest.json', 'манифест сэмплов', (value) => {
      const instruments = value && value.instruments && typeof value.instruments === 'object'
        ? value.instruments
        : null;
      if (!instruments) return 'нет карты instruments';
      const total = Object.values(instruments)
        .reduce((sum, list) => sum + (Array.isArray(list) ? list.length : 0), 0);
      return total > 0 ? null : 'ни одного сэмпла';
    }),
    checkFile(fsApi, root, 'data/desktop/inventory.md', 'снимок модулей', (text) => {
      const rows = String(text || '').split('\n').filter((row) => row.startsWith('|')).length;
      return rows > 10 ? null : `строк таблицы ${rows}, ожидалось больше 10`;
    }, 'text'),
  ];
  for (const item of results) lines.push(line(item.line));

  // Каталоги: наличие проверяется отдельно, потому что это не JSON.
  const presets = fsApi.listDir(path.join(root, 'data', 'genre_presets'));
  if (presets.error) lines.push(line(`ПРОБЛЕМА пресеты жанров: нет data/genre_presets (${presets.error})`));
  else lines.push(line(`OK пресеты жанров: data/genre_presets, файлов ${presets.entries.length}`));

  // Каталог досье в установленной сборке лежит не в проекте, а в каталоге
  // пользователя: проверяем именно тот, куда приложение пишет.
  const dossiers = fsApi.listDir(dossierDir || path.join(root, 'data', 'artist_dossier'));
  const where = dossierDir ? 'каталог пользователя' : 'data/artist_dossier';
  if (dossiers.error) lines.push(line(`ПРОБЛЕМА каталог досье: ${where} (${dossiers.error})`));
  else lines.push(line(`OK каталог досье: ${where}, записей ${dossiers.entries.length}`));

  const failed = lines.filter((text) => text.startsWith('ПРОБЛЕМА')).length;
  lines.push(line(failed ? `итог: проблем ${failed}` : 'итог: проблем нет'));
  return { ok: failed === 0, lines };
}

/** 2. Готовность: пересчёт против снимка — то же число или расхождение. */
function readinessCheck({ project }) {
  const lines = [];
  const data = project.readiness();
  if (data.error) lines.push(line(`ПРОБЛЕМА ${data.error}`));
  lines.push(line(`снимок: ${data.percent === null ? 'нет' : `${data.percent}%`}`));
  lines.push(line(`пересчёт окна: ${data.recomputedPercent}%`));
  for (const [block, value] of Object.entries(data.blockScores || {})) {
    lines.push(line(`  ${block}: ${value}%`));
  }
  for (const cap of data.capsTriggered || []) {
    lines.push(line(`потолок ${cap[0]}%: ${cap[1]}`));
  }
  if (data.generatedAt) lines.push(line(`снимок от ${data.generatedAt}`));
  if (data.stale) lines.push(line('ПРОБЛЕМА снимок старше 30 дней — перегенерируйте (npm run snapshot)'));
  const ok = !data.error && data.mismatch !== true;
  lines.push(line(ok ? 'итог: снимок и пересчёт совпадают' : 'итог: числа расходятся'));
  return { ok, lines };
}

/** 3. Досье: артисты, треки, что ещё не разобрано. */
function dossierCheck({ root, project, fsApi = createNodeFs(), dossierDir = null }) {
  const lines = [];
  const dossierTracks = require('../src/core/dossier-tracks');
  const list = project.dossiers();
  if (list.error) lines.push(line(`ПРОБЛЕМА ${list.error}`));
  if (!list.artists.length) lines.push(line('артистов нет: раздел «Досье» пуст, это состояние, а не ошибка'));

  let pending = 0;
  let analyzed = 0;
  for (const artist of list.artists) {
    const read = dossierTracks.listTracks(fsApi, root, artist.slug, dossierDir ? { dataDir: dossierDir } : {});
    // Отсутствие `tracks/` — не поломка: каталог создаётся при первом треке
    // (так же ведёт себя Python-менеджер). Проблема — нечитаемый файл.
    for (const message of read.errors) {
      if (/ENOENT/.test(message)) continue;
      lines.push(line(`ПРОБЛЕМА ${artist.slug}: ${message}`));
    }
    const counts = { pending: 0, partial: 0, analyzed: 0 };
    for (const track of read.tracks) counts[track.status] = (counts[track.status] || 0) + 1;
    pending += counts.pending;
    analyzed += counts.analyzed;
    lines.push(line(
      `${artist.demo ? '[демо] ' : ''}${artist.artist}: треков ${read.tracks.length}, `
      + `не разобрано ${counts.pending}, частично ${counts.partial}, разобрано ${counts.analyzed}`,
    ));
  }
  lines.push(line(`итог: артистов ${list.artists.length}, разобрано треков ${analyzed}, ждут разбора ${pending}`));
  // Неразобранные треки — не ошибка проверки: разбор делает Python, и окно об
  // этом говорит. Ошибкой считается только нечитаемый файл.
  return { ok: lines.every((text) => !text.startsWith('ПРОБЛЕМА')), lines };
}

const NATIVE_TASKS = {
  'native-files': {
    label: 'Проверка файлов проекта (без Python)',
    accepts: [],
    run: projectCheck,
  },
  'native-readiness': {
    label: 'Готовность: снимок против пересчёта (без Python)',
    accepts: [],
    run: readinessCheck,
  },
  'native-dossier': {
    label: 'Сводка по досье (без Python)',
    accepts: [],
    run: dossierCheck,
  },
};

/** Список нативных задач — в том же виде, что `taskList()` из tasks.js. */
function nativeTaskList() {
  return Object.entries(NATIVE_TASKS).map(([key, task]) => ({
    key,
    label: task.label,
    accepts: [...task.accepts],
    native: true,
  }));
}

/**
 * Выполнить нативную задачу с тем же потоком событий, что у Python-задач.
 *
 * @param {object} params
 * @param {string} params.key
 * @param {object} params.project  модель проекта (`src/core/project`)
 * @param {string} params.root
 * @param {string} [params.dossierDir] каталог досье для записи (установленная сборка)
 * @param {object} [params.fileSystem]
 * @param {Function} [params.onEvent] получает `{type: 'stdout'|'stderr'}`
 * @returns {{ok: boolean, lines: string[], error?: string}}
 */
function runNativeTask({
  key, project, root, fileSystem = createNodeFs(), dossierDir = null, onEvent = () => {},
}) {
  const task = NATIVE_TASKS[key];
  if (!task) return { ok: false, lines: [], error: `неизвестная задача: ${key}` };
  let result;
  try {
    result = task.run({ root, project, fsApi: fileSystem, dossierDir });
  } catch (err) {
    const message = err && err.message ? err.message : String(err);
    onEvent({ type: 'stderr', line: message });
    return { ok: false, lines: [], error: message };
  }
  for (const text of result.lines) onEvent({ type: 'stdout', line: text });
  return result;
}

module.exports = {
  NATIVE_TASKS,
  nativeTaskList,
  runNativeTask,
  projectCheck,
  readinessCheck,
  dossierCheck,
};
