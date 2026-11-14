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
const { resolvePython, resolvePipelineRoot } = require('./runtime');

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

/**
 * 4. Самодиагностика окна: то, что зависит от машины, а не от проекта.
 *
 * Python-«--self-diag» проверяет библиотеки пайплайна. Но у окна свой набор
 * условий: можно ли писать настройки и досье, есть ли поток рендера, полон ли
 * банк, найдены ли движок и каталог. Раньше эти пункты проверялись только
 * глазами в «Диагностике».
 */
function selfCheck({ root, project, fsApi = createNodeFs(), dossierDir = null, userData = null }) {
  const lines = [];
  const problems = [];

  // 1. Ядро окна: движок, каталог, модель проекта подключены.
  try {
    require('../src/core/audio/engine');
    lines.push(line('OK движок бита: src/core/audio/engine'));
  } catch (err) {
    problems.push('движок бита не подключён');
    lines.push(line(`ПРОБЛЕМА движок бита: ${err.message}`));
  }

  // 2. Проект читается: версия и жанры — то, без чего окно пустое.
  const version = project.version();
  if (version.version) lines.push(line(`OK версия приложения: ${version.version}`));
  else {
    problems.push('версия не прочитана');
    lines.push(line(`ПРОБЛЕМА версия: ${version.error || 'нет значения'}`));
  }
  const genres = project.genres();
  if (genres.genres && genres.genres.length) {
    lines.push(line(`OK каталог жанров: ${genres.genres.length}`));
  } else {
    problems.push('каталог жанров пуст');
    lines.push(line('ПРОБЛЕМА каталог жанров пуст'));
  }

  // 3. Куда приложение пишет: без этого досье и настройки не сохранятся.
  const writeDir = dossierDir || path.join(root, 'data', 'artist_dossier');
  const probeFile = path.join(writeDir, '.write-probe');
  const written = fsApi.writeText(probeFile, 'probe');
  if (written.error) {
    problems.push('каталог досье недоступен для записи');
    lines.push(line(`ПРОБЛЕМА запись в досье: ${writeDir} (${written.error})`));
  } else {
    lines.push(line(`OK запись в досье: ${writeDir}`));
    // Пробный файл убираем: иначе он попадёт в список «артистов».
    if (typeof fsApi.removeDir === 'function') {
      // removeDir удаляет каталог; для файла используем его же аккуратно —
      // пробный файл лежит в каталоге досье и не должен там остаться.
      fsApi.removeDir(probeFile);
    }
  }
  if (userData) {
    const settingsProbe = path.join(userData, '.settings-probe');
    const settingsWritten = fsApi.writeText(settingsProbe, 'probe');
    if (settingsWritten.error) {
      problems.push('каталог настроек недоступен для записи');
      lines.push(line(`ПРОБЛЕМА запись в настройки: ${userData} (${settingsWritten.error})`));
    } else {
      lines.push(line(`OK запись в настройки: ${userData}`));
      if (typeof fsApi.removeDir === 'function') fsApi.removeDir(settingsProbe);
    }
  }

  // 4. Поток рендера: без него бит считается в главном процессе (медленнее,
  // но окно отвечает). Это не ошибка — это состояние, и оно названо.
  let worker = false;
  try {
    require('node:worker_threads').Worker;
    worker = true;
  } catch {
    worker = false;
  }
  lines.push(line(worker
    ? 'OK поток рендера: worker_threads доступны'
    : 'поток рендера недоступен: бит считается в главном процессе'));

  // 5. Банк сэмплов: REAL_PASS — живые записи, иначе честный FALLBACK.
  try {
    const { SampleSource } = require('../src/core/audio/bank');
    const report = new SampleSource({ fileSystem: fsApi, rootDir: root }).report();
    if (report.status === 'REAL_PASS') {
      lines.push(line(`OK банк сэмплов: ${report.status}, ${report.total_samples} one-shot`));
    } else {
      lines.push(line(`банк неполный: ${report.status}, ${report.total_samples} one-shot — `
        + 'часть инструментов синтезируется'));
    }
  } catch (err) {
    problems.push('банк сэмплов не читается');
    lines.push(line(`ПРОБЛЕМА банк сэмплов: ${err.message}`));
  }

  // 6. Python и пайплайн: окно работает и без них, поэтому это не проблема,
  // но человек должен видеть, чего именно не будет. Проверка не запускает
  // процесс — только ищет файлы (`runtime.js`).
  const python = resolvePython({ root });
  const pipeline = resolvePipelineRoot({ root });
  lines.push(line(`Python: ${python.python || 'не найден'} — без него задачи с main.py не запустятся`));
  lines.push(line(`Пайплайн: ${pipeline.root
    ? `${pipeline.root}`
    : 'в поставку не входит, нужен ZSMM_PIPELINE_ROOT'}`));

  lines.push(line(problems.length ? `итог: проблем ${problems.length}` : 'итог: проблем нет'));
  return { ok: problems.length === 0, lines };
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
  'native-selfcheck': {
    label: 'Самодиагностика окна (без Python)',
    accepts: [],
    run: selfCheck,
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
 * @param {string} [params.userData] каталог настроек (проверка записи)
 * @param {object} [params.fileSystem]
 * @param {Function} [params.onEvent] получает `{type: 'stdout'|'stderr'}`
 * @returns {{ok: boolean, lines: string[], error?: string}}
 */
function runNativeTask({
  key, project, root, fileSystem = createNodeFs(), dossierDir = null, userData = null,
  onEvent = () => {},
}) {
  const task = NATIVE_TASKS[key];
  if (!task) return { ok: false, lines: [], error: `неизвестная задача: ${key}` };
  let result;
  try {
    result = task.run({ root, project, fsApi: fileSystem, dossierDir, userData });
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
  selfCheck,
};
