'use strict';
/**
 * task-runner.js — IPC-каналы запуска задач: «Запустить», «Остановить».
 *
 * Почему отдельным модулем: `main.js` отвечает за окно, меню и регистрацию
 * каналов, а здесь живёт логика запуска — выбор между задачей без Python
 * (`native-tasks.js`) и `python main.py …` (`tasks.js`), проверка окружения,
 * поток событий и одна активная задача на окно.
 *
 * Два условия должны выполняться вместе, и раньше проверялось только первое:
 *   - интерпретатор найден (`resolvePython`);
 *   - в поставке есть сам пайплайн (`resolvePipelineRoot`): в установщике
 *     лежит только data-часть проекта, и `python main.py` там запускать
 *     нечего. Окно, которое говорит «Python найден», но не может запустить
 *     ни одной задачи, — это ложь в интерфейсе.
 */

const path = require('node:path');

const nativeTasks = require('./native-tasks');
const tasks = require('./tasks');
const { resolvePython, resolvePipelineRoot } = require('./runtime');

/**
 * Зарегистрировать каналы задач.
 *
 * @param {object} params
 * @param {object} params.ipcMain     electron ipcMain (или двойник в тестах)
 * @param {string|null} params.root   корень проекта (данные)
 * @param {Function} params.getProject текущая модель проекта
 * @param {Function} [params.getWindows] менеджер окна (прогресс в панели задач)
 * @param {object} [params.state]     `{ activeTask }` — общее состояние с main.js
 * @param {Function} [params.onTaskStarted] вызывается после старта (для quit)
 * @returns {{handlers: string[]}}
 */
function registerTaskIpc({
  ipcMain,
  root = null,
  getProject,
  getWindows = () => null,
  state = { activeTask: null },
}) {
  ipcMain.handle('zsmm:tasks', () => ({ ok: true, data: tasks.taskList() }));

  ipcMain.handle('zsmm:task-start', async (event, { key, options } = {}) => {
    if (state.activeTask) {
      return { ok: false, error: 'уже выполняется другая задача: сначала остановите её' };
    }
    const windows = getWindows && getWindows();
    const sender = event.sender;
    const send = (channel, payload) => {
      if (!sender.isDestroyed()) sender.send(channel, payload);
    };

    // Задачи без Python считает сам главный процесс: это чтение файлов и
    // пересчёт готовности, а не движок. Поток событий тот же, что у задач
    // Python, — окну не нужно знать разницу.
    const native = nativeTasks.NATIVE_TASKS[key];
    if (native) {
      const project = getProject && getProject();
      if (!project) return { ok: false, error: 'проект не открыт' };
      send('zsmm:task-event', { type: 'start', command: [native.label], label: native.label });
      try {
        const result = nativeTasks.runNativeTask({
          key,
          project,
          root: root || path.resolve(__dirname, '..', '..'),
          dossierDir: state.dossierDir || null,
          userData: state.userData || null,
          onEvent: (payload) => send('zsmm:task-event', payload),
        });
        send('zsmm:task-event', { type: 'exit', code: result.ok ? 0 : 1, signal: null, timedOut: false });
        send('zsmm:task-done', {
          ok: result.ok, code: result.ok ? 0 : 1, signal: null, timedOut: false,
        });
        return { ok: true, data: { pid: null, command: [native.label], native: true } };
      } catch (err) {
        send('zsmm:task-done', { ok: false, code: null, signal: null, timedOut: false });
        return { ok: false, error: err.message };
      }
    }

    const { python, error } = resolvePython({ root, env: process.env });
    if (!python) return { ok: false, error };
    const pipeline = resolvePipelineRoot({ root: root || path.resolve(__dirname, '..', '..') });
    if (!pipeline.root) return { ok: false, error: pipeline.error };

    try {
      state.activeTask = tasks.runTask({
        key,
        options: options || {},
        python,
        root: pipeline.root,
        onEvent: (payload) => {
          if (windows) windows.showTaskProgress(payload);
          send('zsmm:task-event', payload);
        },
      });
      state.activeTask.done.then((result) => {
        state.activeTask = null;
        send('zsmm:task-done', result);
      });
      return {
        ok: true,
        data: { pid: state.activeTask.pid, command: state.activeTask.command },
      };
    } catch (err) {
      state.activeTask = null;
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle('zsmm:task-stop', () => {
    if (!state.activeTask) return { ok: false, error: 'нет запущенной задачи' };
    return { ok: true, data: { stopped: state.activeTask.stop() } };
  });

  return { handlers: ['zsmm:tasks', 'zsmm:task-start', 'zsmm:task-stop'] };
}

module.exports = { registerTaskIpc };
