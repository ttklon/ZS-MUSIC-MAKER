'use strict';
/**
 * runtime.js — где окно берёт данные: корень проекта, Python, каталоги.
 *
 * В репозитории всё лежит рядом: `desktop/` внутри корня, рядом `config/`,
 * `data/samples/`, `data/desktop/`. В установленном приложении (AppImage,
 * NSIS-инсталлятор) кода репозитория вокруг нет — есть `resources/app.asar`
 * и распакованные данные в `resources/`. Поэтому корень не «вычисляется из
 * `__dirname`, и всё», а ищется по списку кандидатов, и первый, где есть
 * `version.json`, считается корнем проекта.
 *
 * Вынесено из `main.js` отдельным модулем, чтобы это проверялось обычным
 * `node --test` без графической среды: ошибка в путях видна только в
 * собранном приложении, и ловить её там дорого.
 */

const fs = require('node:fs');
const path = require('node:path');

/** Файлы, по которым корень опознаётся как проект, а не как пустой каталог. */
const ROOT_MARKERS = ['version.json', path.join('config', 'genres_100.json')];

function hasMarkers(dir) {
  try {
    return ROOT_MARKERS.some((marker) => fs.existsSync(path.join(dir, marker)));
  } catch {
    return false;
  }
}

/**
 * Кандидаты в корень проекта, в порядке приоритета.
 *
 * `appPath` — каталог с `package.json` приложения (`app.getAppPath()`),
 * `resourcesPath` — `process.resourcesPath` в упакованной сборке.
 * Дубли не страшны: список всё равно проверяется по маркерам.
 */
function rootCandidates({ appPath, resourcesPath, env = process.env } = {}) {
  const list = [];
  if (env.ZSMM_ROOT) list.push(env.ZSMM_ROOT);
  if (resourcesPath) {
    list.push(path.join(resourcesPath, 'project'));
    list.push(resourcesPath);
  }
  if (appPath) {
    list.push(path.resolve(appPath, '..', '..'));
    list.push(path.resolve(appPath, '..'));
    list.push(appPath);
  }
  // Без дублей: список попадает в текст ошибки, и повтор одного пути дважды
  // читается как «здесь что-то есть, но не подошло».
  return [...new Set(list.filter(Boolean).map((candidate) => path.resolve(candidate)))];
}

/**
 * Найти корень проекта и честно сказать, если не нашли.
 *
 * @returns {{root: string|null, error: string|null, candidates: string[]}}
 */
function resolveRoot({ appPath, resourcesPath, env } = {}) {
  const candidates = rootCandidates({ appPath, resourcesPath, env });
  for (const candidate of candidates) {
    if (hasMarkers(candidate)) return { root: candidate, error: null, candidates };
  }
  return {
    root: null,
    error: 'Корень проекта не найден: нет version.json ни в одном из каталогов '
      + `(${candidates.join('; ') || 'список пуст'}). Задайте ZSMM_ROOT.`,
    candidates,
  };
}

/**
 * Найти Python для задач пайплайна.
 *
 * В собранном приложении Python нет — и это не ошибка сборки, а её свойство:
 * раздел «Запуск» тогда честно отключается, а рендер бита работает, потому
 * что движок на JavaScript. Windows-кандидаты идут первыми.
 */
/**
 * Найти команду в PATH.
 *
 * Спрашивать ОС «есть ли python.exe» из главного процесса нельзя: это либо
 * запуск процесса, либо гадание. Поэтому PATH просматривается по каталогам —
 * результат один и тот же в тестах и в приложении.
 */
function findInPath(command, env = process.env, exists = (p) => fs.existsSync(p)) {
  const pathValue = env.PATH || env.Path || '';
  const dirs = String(pathValue).split(path.delimiter).filter(Boolean);
  const names = process.platform === 'win32'
    ? [command, `${command}.exe`, `${command}.bat`, `${command}.cmd`]
    : [command];
  for (const dir of dirs) {
    for (const name of names) {
      const candidate = path.join(dir, name);
      try {
        if (exists(candidate)) return candidate;
      } catch {
        /* недоступный каталог — идём дальше */
      }
    }
  }
  return null;
}

function resolvePython({ root = null, env = process.env, platform = process.platform, exists = (p) => fs.existsSync(p) } = {}) {
  // `viaPath` — имя команды, которое ищет сама ОС. Раньше это угадывалось по
  // отсутствию `path.sep`, и на Windows «/usr/bin/python3» (без обратных
  // слэшей) считался командой из PATH — то есть «Python найден» там, где его
  // нет. Признак задаётся явно.
  const candidates = [
    { value: env.ZSMM_PYTHON, viaPath: false },
    { value: root && platform === 'win32' ? path.join(root, '.venv', 'Scripts', 'python.exe') : null, viaPath: false },
    { value: root ? path.join(root, '.venv', 'bin', 'python3') : null, viaPath: false },
    { value: root ? path.join(root, '.venv', 'Scripts', 'python.exe') : null, viaPath: false },
    { value: platform === 'win32' ? 'python.exe' : null, viaPath: true },
    { value: platform === 'win32' ? 'py.exe' : null, viaPath: true },
    { value: platform !== 'win32' ? 'python3' : null, viaPath: true },
    { value: '/usr/bin/python3', viaPath: false },
    { value: '/usr/local/bin/python3', viaPath: false },
  ].filter((entry) => entry.value);

  for (const { value: candidate, viaPath } of candidates) {
    if (viaPath) {
      const found = findInPath(candidate, env, exists);
      if (found) return { python: found, error: null, source: 'PATH' };
      continue;
    }
    try {
      if (exists(candidate)) return { python: candidate, error: null, source: candidate };
    } catch {
      /* недоступный путь — пробуем следующий */
    }
  }
  return {
    python: null,
    error: 'Python не найден. Раздел «Запуск» без него не работает (рендер бита '
      + 'работает всегда: движок внутри приложения). Укажите ZSMM_PYTHON=путь '
      + 'к python.exe или создайте .venv в корне проекта.',
    source: null,
  };
}

module.exports = { ROOT_MARKERS, hasMarkers, rootCandidates, resolveRoot, resolvePython, findInPath };
