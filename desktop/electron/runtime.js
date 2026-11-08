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
function resolvePython({ root = null, env = process.env, platform = process.platform, exists = (p) => fs.existsSync(p) } = {}) {
  const candidates = [
    env.ZSMM_PYTHON,
    root && platform === 'win32' ? path.join(root, '.venv', 'Scripts', 'python.exe') : null,
    root ? path.join(root, '.venv', 'bin', 'python3') : null,
    root ? path.join(root, '.venv', 'Scripts', 'python.exe') : null,
    platform === 'win32' ? 'python.exe' : null,
    platform === 'win32' ? 'py.exe' : null,
    '/usr/bin/python3',
    '/usr/local/bin/python3',
  ].filter(Boolean);

  for (const candidate of candidates) {
    // Короткое имя (`python.exe`) ищется в PATH, а не как путь от cwd.
    if (!candidate.includes(path.sep)) return { python: candidate, error: null, source: 'PATH' };
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

module.exports = { ROOT_MARKERS, hasMarkers, rootCandidates, resolveRoot, resolvePython };
