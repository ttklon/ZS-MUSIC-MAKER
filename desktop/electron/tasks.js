'use strict';
/**
 * tasks.js — длинные операции проекта, запущенные из окна.
 *
 * Принцип: окно не переписывает движок на JS. Тяжёлая работа (рендер, досье,
 * проверка окружения) остаётся в Python, а Electron запускает ту же команду,
 * что и человек в терминале (`python main.py …`), и показывает её вывод
 * построчно. Так не бывает «в окне одно, в консоли другое».
 *
 * Разрешён белый список команд: окно не может выполнить произвольный процесс.
 */

const { spawn } = require('node:child_process');
const path = require('node:path');

const { nativeTaskList } = require('./native-tasks');

/**
 * Разрешённые задачи. `args` — фиксированные флаги; пользователь может задать
 * только жанр/тему/сид, и они проходят проверку формата.
 */
const TASKS = {
  'dry-run': {
    label: 'Пробный прогон пайплайна',
    args: () => ['--run', '--dry-run'],
    accepts: ['genre', 'theme', 'seed'],
    timeoutMs: 30 * 60_000,
  },
  run: {
    label: 'Полный прогон пайплайна',
    args: () => ['--run'],
    accepts: ['genre', 'theme', 'seed'],
    timeoutMs: 6 * 60 * 60_000,
  },
  health: {
    label: 'Проверка окружения',
    args: () => ['--health'],
    accepts: [],
    timeoutMs: 15 * 60_000,
  },
  // Полная сборка досье: биография, темы, разбор вокала и треков. Именно то,
  // что окно не умеет само и о чём честно пишет в разделе «Досье».
  'dossier-build': {
    label: 'Собрать досье артиста',
    args: () => ['--dossier-build'],
    accepts: ['artist'],
    timeoutMs: 4 * 60 * 60_000,
  },
  'self-diag': {
    label: 'Самодиагностика',
    args: () => ['--self-diag'],
    accepts: [],
    timeoutMs: 30 * 60_000,
  },
  readiness: {
    label: 'Готовность',
    args: () => ['--readiness'],
    accepts: [],
    timeoutMs: 15 * 60_000,
  },
  // Агентик: 4 ответа → трек. Отдельная задача, потому что это единственная
  // кнопка, после которой человек ждёт «готовый трек», а не отчёт: таймаут
  // больше, и первый запуск сам докачивает тяжёлые движки.
  'agent-hit': {
    label: 'Сделать хит (агентик: 4 вопроса → трек)',
    args: () => ['--agent-hit'],
    accepts: ['mood', 'artist', 'refs', 'voice'],
    timeoutMs: 12 * 60 * 60_000,
  },
  'ai-status': {
    label: 'Статус AI-моделей',
    args: () => ['--ai-status'],
    accepts: [],
    timeoutMs: 10 * 60_000,
  },
  smoke: {
    label: 'Смоук-тесты звука',
    args: () => ['--smoke'],
    accepts: [],
    timeoutMs: 30 * 60_000,
  },
};

class TaskError extends Error {}

/** Проверить, что значение безопасно как аргумент командной строки. */
function sanitizeOptions(options = {}) {
  const genre = options.genre === undefined || options.genre === null ? null : String(options.genre);
  const theme = options.theme === undefined || options.theme === null ? null : String(options.theme);
  const seed = options.seed === undefined || options.seed === null ? null : options.seed;
  const artist = options.artist === undefined || options.artist === null ? null : String(options.artist);
  // Ответы агентика: тема и референсы — свободный текст, но без переводов
  // строк и кавычек shell-уровня: они уходят одним аргументом (`spawn` без
  // оболочки), поэтому запрещаем только то, что ломает формат отчёта.
  const mood = cleanText(options.mood, 300, 'настроение');
  const refs = cleanRefs(options.refs);
  const voice = cleanText(options.voice, 260, 'голос');

  // Имя артиста уходит аргументом в Python: только буквы, цифры, пробел, «-» и
  // «_». Это же имя Python превращает в slug каталога, поэтому `..` и слэши
  // здесь запрещены.
  if (artist !== null && !/^[\w \-А-Яа-яЁё]{2,80}$/u.test(artist)) {
    throw new TaskError(`недопустимое имя артиста: ${artist}`);
  }

  if (genre !== null && !/^[\w \-]{1,64}$/u.test(genre)) {
    throw new TaskError(`недопустимый жанр: ${genre}`);
  }
  if (theme !== null && !/^[\w \-]{1,64}$/u.test(theme)) {
    throw new TaskError(`недопустимая тема: ${theme}`);
  }
  let seedValue = null;
  if (seed !== null && seed !== '') {
    // Только десятичные цифры: `Number("1e5")` дало бы 100000, а `" 5"`
    // и `"0x10"` — значения, которые пользователь не имел в виду.
    if (typeof seed === 'number') {
      seedValue = seed;
    } else if (/^\d+$/.test(String(seed).trim())) {
      seedValue = Number.parseInt(String(seed).trim(), 10);
    } else {
      seedValue = Number.NaN;
    }
    if (!Number.isInteger(seedValue) || seedValue < 0) {
      throw new TaskError(`сид должен быть неотрицательным целым: ${seed}`);
    }
  }
  return { genre, theme, seed: seedValue, artist, mood, refs, voice };
}

/**
 * Свободный текст из вопроса агентика: без переводов строк и управляющих
 * символов, с ограничением длины. Пустая строка — это «пусто», а не null:
 * агент сам решит, брать ли значение из трендов.
 */
function cleanText(value, limit, label) {
  if (value === undefined || value === null) return '';
  const text = String(value).replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim();
  if (text.length > limit) throw new TaskError(`${label} длиннее ${limit} символов`);
  return text;
}

/**
 * Референсы: список путей/ссылок через запятую. Кавычки и переводы строк
 * запрещены — это единственный символ, который мог бы «склеить» аргументы.
 */
function cleanRefs(value) {
  if (value === undefined || value === null || value === '') return '';
  const text = String(value).replace(/["'`\r\n]/g, '').trim();
  if (text.length > 1200) throw new TaskError('слишком много референсов');
  return text;
}

/**
 * Проверить, что задача принимает переданные ей параметры.
 *
 * Раньше неизвестный параметр молча игнорировался: окно считало, что ответ
 * агентика ушёл в Python, а тот его просто не получал. Теперь это ошибка с
 * именем параметра — её видно в отчёте, а не в пустом результате.
 */
function assertAccepted(key, task, options = {}) {
  const known = ['genre', 'theme', 'seed', 'artist', 'mood', 'refs', 'voice'];
  for (const name of Object.keys(options || {})) {
    if (options[name] === undefined || options[name] === null || options[name] === '') continue;
    if (!known.includes(name)) throw new TaskError(`неизвестный параметр: ${name}`);
    // Задача без такого флага просто его не получает (`buildCommand` ниже
    // проверяет `accepts`): это старое поведение, и менять его нельзя —
    // раздел «Запуск» передаёт общий набор полей любой задаче.
  }
}

/**
 * Аргументы артиста.
 *
 * У «досье» артист обязателен, у агентика — нет: пусто означает «из трендов».
 * Флаг разный: `--dossier-artist` запускает сборку досье, а не трек.
 */
function appendArtist(argv, key, safe) {
  if (!safe.artist) {
    if (key === 'dossier-build') throw new TaskError('для этой задачи нужно имя артиста');
    return;
  }
  argv.push(key === 'agent-hit' ? '--agent-artist' : '--dossier-artist', safe.artist);
}

/** Собрать argv для задачи: только разрешённые флаги, без оболочки. */
function buildCommand(key, options = {}) {
  const task = TASKS[key];
  if (!task) throw new TaskError(`неизвестная задача: ${key}`);
  // Всё, что вернул `sanitizeOptions`, должно быть явно разрешено задачей:
  // иначе параметр молча терялся бы, и окно думало бы, что ответ ушёл.
  assertAccepted(key, task, options);
  const safe = sanitizeOptions(options);
  const argv = [...task.args(safe)];
  if (safe.genre !== null && task.accepts.includes('genre')) argv.push('--genre', safe.genre);
  if (safe.theme !== null && task.accepts.includes('theme')) argv.push('--theme', safe.theme);
  if (safe.seed !== null && task.accepts.includes('seed')) argv.push('--seed', String(safe.seed));
  if (task.accepts.includes('mood') && safe.mood) argv.push('--agent-mood', safe.mood);
  if (task.accepts.includes('refs') && safe.refs) argv.push('--agent-refs', safe.refs);
  if (task.accepts.includes('voice') && safe.voice) argv.push('--agent-voice', safe.voice);
  if (task.accepts.includes('artist')) appendArtist(argv, key, safe);
  return argv;
}

/**
 * Запустить задачу. `onEvent` получает {type, ...}: start, stdout, stderr,
 * timeout, exit. Возвращает handle с `stop()` и `done` (Promise).
 */
function runTask({ key, options = {}, python, root, env = process.env, onEvent = () => {} }) {
  if (!python) throw new TaskError('не указан интерпретатор Python');
  const argv = buildCommand(key, options);
  const task = TASKS[key];
  const script = path.join(root, 'main.py');

  let timedOut = false;
  let settled = false;
  const child = spawn(python, [script, ...argv], {
    cwd: root,
    env: { ...env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  const timer = setTimeout(() => {
    timedOut = true;
    onEvent({ type: 'timeout', timeoutMs: task.timeoutMs });
    child.kill('SIGKILL');
  }, task.timeoutMs);

  const emitLines = (stream, kind) => {
    let buffer = '';
    stream.on('data', (chunk) => {
      buffer += chunk.toString();
      let index = buffer.indexOf('\n');
      while (index !== -1) {
        const line = buffer.slice(0, index);
        buffer = buffer.slice(index + 1);
        onEvent({ type: kind, line });
        index = buffer.indexOf('\n');
      }
    });
    stream.on('end', () => {
      if (buffer.length) onEvent({ type: kind, line: buffer });
    });
  };

  emitLines(child.stdout, 'stdout');
  emitLines(child.stderr, 'stderr');
  onEvent({ type: 'start', command: ['main.py', ...argv], label: task.label });

  const done = new Promise((resolve) => {
    child.on('error', (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      onEvent({ type: 'error', error: err.message });
      resolve({ ok: false, code: null, timedOut, error: err.message });
    });
    child.on('exit', (code, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      onEvent({ type: 'exit', code, signal, timedOut });
      resolve({ ok: code === 0 && !timedOut, code, signal, timedOut });
    });
  });

  return {
    done,
    pid: child.pid,
    command: ['main.py', ...argv],
    stop() {
      if (settled) return false;
      child.kill('SIGTERM');
      return true;
    },
  };
}

/**
 * Полный список задач для окна: сначала те, что считает само окно, потом
 * вызовы Python. `native: true` — окну не нужен интерпретатор, и оно не
 * должно показывать рядом с ними предупреждение про Python.
 */
function taskList() {
  const pythonTasks = Object.entries(TASKS).map(([key, task]) => ({
    key,
    label: task.label,
    accepts: [...task.accepts],
    native: false,
  }));
  return [...nativeTaskList(), ...pythonTasks];
}

module.exports = { TASKS, TaskError, runTask, buildCommand, sanitizeOptions, taskList };
