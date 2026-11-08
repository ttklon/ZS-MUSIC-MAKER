'use strict';
/**
 * sections/run.js — раздел «Запуск»: `python main.py …` с живым выводом.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

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
  setTaskStatus('Задача не запущена', false);

  if (!loadRun.wired) {
    loadRun.wired = true;
    $('task-start').addEventListener('click', startTask);
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
  setTaskStatus(`Запущено: ${reply.data.command.join(' ')} (pid ${reply.data.pid})`, true);
}

W.loadRun = loadRun;
