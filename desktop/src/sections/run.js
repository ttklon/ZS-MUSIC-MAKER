'use strict';
/**
 * sections/run.js — раздел «Запуск»: `python main.py …` с живым выводом.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

(function () {
const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

// ------------------------------------------------------------------ запуск
function renderTaskOutput() {
  // держим последние 2000 строк: полный вывод рендера может быть огромным
  const tail = state.taskLines.slice(-2000);
  const out = $('task-output');
  out.textContent = tail.join('\n');
  out.scrollTop = out.scrollHeight;
}

function setTaskStatus(text, running) {
  state.taskRunning = running;
  $('task-status').textContent = text;
  $('task-start').disabled = running;
  $('task-stop').disabled = !running;
}

function appendTaskLine(line) {
  state.taskLines.push(line);
  renderTaskOutput();
}

async function loadRun() {
  // Есть ли Python — выясняем до первой кнопки: иначе пользователь нажимает
  // «Запустить», получает отказ и не понимает, что чинить.
  if (typeof window.zsmm.environment === 'function') {
    try {
      const reply = await window.zsmm.environment();
      if (reply && reply.ok === true) {
        state.python = reply.data.python || null;
        state.pythonError = reply.data.python_error || null;
        // Пайплайн и интерпретатор — разные условия: в установщике есть
        // только данные проекта, и `python main.py` там просто нет.
        state.pipeline = reply.data.pipeline_root || null;
        state.pipelineError = reply.data.pipeline_error || null;
      }
    } catch (err) {
      state.pythonError = `окружение недоступно: ${err.message}`;
    }
  }

  const reply = await window.zsmm.listTasks();
  if (!reply || reply.ok === false) {
    throw new Error((reply && reply.error) || 'список задач недоступен');
  }
  // preload отдаёт массив задач, предпросмотр и тесты — `{data}`. Принимаем
  // оба вида: раньше `tasks.map` падал на объекте, и раздел оставался пустым.
  const tasks = Array.isArray(reply) ? reply : reply.data;
  if (!Array.isArray(tasks)) {
    throw new Error(`список задач пришёл в неожиданном виде: ${typeof tasks}`);
  }
  state.tasks = tasks;
  $('task-select').replaceChildren(
    ...tasks.map((task) => {
      const option = document.createElement('option');
      option.value = task.key;
      option.textContent = task.label;
      return option;
    }),
  );
  updatePythonNote();
  setTaskStatus('Задача не запущена', false);

  if (!loadRun.wired) {
    loadRun.wired = true;
    $('task-start').addEventListener('click', startTask);
    // Подпись про Python зависит от выбранной задачи: окно умеет четыре задачи
    // само, и предупреждение не должно висеть над ними.
    $('task-select').addEventListener('change', () => updatePythonNote());
    $('task-stop').addEventListener('click', () => {
      window.zsmm.stopTask().then((reply) => {
        if (!reply || reply.ok !== true) showError((reply && reply.error) || 'не удалось остановить');
      });
    });
    window.zsmm.onTaskEvent((event) => {
      if (!event) return;
      if (event.type === 'start') {
        state.taskLines = [];
        setTaskStatus(`Выполняется: ${event.label} (${event.command.join(' ')})`, true);
      } else if (event.type === 'stdout') {
        appendTaskLine(event.line);
      } else if (event.type === 'stderr') {
        appendTaskLine(`[stderr] ${event.line}`);
      } else if (event.type === 'timeout') {
        appendTaskLine(`[таймаут] задача превысила ${Math.round(event.timeoutMs / 60000)} мин и остановлена`);
      }
    });
    window.zsmm.onTaskDone((result) => {
      if (!result) return;
      if (result.timedOut) {
        setTaskStatus('Остановлено по таймауту — это не успех', false);
      } else if (result.ok) {
        setTaskStatus('Завершено успешно', false);
      } else {
        setTaskStatus(`Завершено с ошибкой (код ${result.code}${result.signal ? `, сигнал ${result.signal}` : ''})`, false);
      }
    });
  }
}

/**
 * Подпись про Python: пока его нет, «Запустить» остаётся доступной, но рядом
 * написано, что произойдёт. Прятать кнопку хуже — пользователь не поймёт,
 * почему раздел пустой.
 */
function updatePythonNote() {
  const note = $('task-python-note');
  if (!note) return;
  // Задачи без Python (файлы, готовность, досье, самодиагностика)
  // считает само окно: предупреждение к ним не относится, иначе человек
  // решит, что не работает вообще ничего.
  const selected = Array.isArray(state.tasks)
    ? state.tasks.find((task) => task && task.key === $('task-select').value)
    : null;
  if (selected && selected.native) {
    note.textContent = 'Эту задачу считает само окно: Python не нужен.';
    return;
  }
  if (state.python && !state.pipeline) {
    // Худший случай для доверия: интерпретатор есть, а запускать нечего.
    note.textContent = `Python найден (${state.python}), но ${(state.pipelineError || 'пайплайн не найден')
      .replace(/\.$/, '')
      .replace(/^П/, 'п')}`;
    return;
  }
  if (state.python) {
    note.textContent = `Python найден: ${state.python}. Задача запускается тем же CLI, что в терминале.`;
    return;
  }
  // `python_error` уже содержит человеческий текст («Python не найден»),
  // поэтому не повторяем его дважды — один раз причину, один раз последствия.
  const reason = state.pythonError || 'Python не найден';
  note.textContent = `${reason.replace(/\.$/, '')}: задачи раздела не запустятся. `
    + 'Рендер бита, жанры и досье работают без него.';
}

async function startTask() {
  const key = $('task-select').value;
  const genre = ($('task-genre').value || '').trim();
  const seed = ($('task-seed').value || '').trim();
  // Артист нужен задачам досье и не мешает остальным: tasks.js сам решает,
  // какие параметры принимает выбранная задача.
  const artist = ($('task-artist').value || '').trim();
  const options = {};
  if (genre) options.genre = genre;
  if (seed) options.seed = seed;
  if (artist) options.artist = artist;

  state.taskLines = [];
  renderTaskOutput();
  // Пустой список задач — единственный случай, когда запускать нечего: имя
  // задачи приходит из `<select>`, и проверять его здесь незачем (это делает
  // tasks.js и отвечает текстом).
  if (!Array.isArray(state.tasks) || state.tasks.length === 0) {
    showError('Нет доступных задач: список пуст');
    return;
  }
  const reply = await window.zsmm.startTask(key, options);
  if (!reply || reply.ok !== true) {
    setTaskStatus('Не запущено', false);
    showError((reply && reply.error) || 'задача не запустилась');
    return;
  }
  const pid = reply.data.pid ? ` (pid ${reply.data.pid})` : '';
  setTaskStatus(`Запущено: ${reply.data.command.join(' ')}${pid}`, true);
}

W.loadRun = loadRun;
  // В браузере все `<script>` делят одну глобальную область: второй
  // верхнеуровневый `const` с тем же именем роняет файл целиком
  // (`Identifier 'W' has already been declared`). Поэтому код раздела
  // живёт в своей функции, а наружу отдаёт только одно имя.
  window.ZSMM_SECTIONS.initRun = function () {
    W.loadRun = loadRun;
  };
})();
