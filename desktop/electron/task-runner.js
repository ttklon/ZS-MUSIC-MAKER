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
/**
 * Окружение процесса Python: галочка «сеть» из окна должна до него доходить.
 *
 * Раньше `networkOnline` жила только в настройках Electron: пользователь
 * включал сеть в приложении, а `python main.py --rvc-setup` всё равно отвечал
 * `network disabled`, потому что `app/core/net_policy.py` смотрит либо на
 * `allow_online`, либо на `data/settings.json`. Явная переменная окружения —
 * самый узкий мост: она действует ровно на запущенную задачу и не пишет
 * чужой конфиг за спиной у пользователя.
 */
function taskEnv(networkOnline, base = process.env, python = null, userBase = null) {
  const env = { ...base };
  if (networkOnline === true) env.ZSMM_ONLINE = '1';
  else delete env.ZSMM_ONLINE;
  if (python && userBase && path.basename(path.dirname(python)) === '.python') {
    env.PYTHONUSERBASE = userBase;
    env.PIP_USER = '1';
    delete env.PIP_TARGET;
    delete env.PIP_PREFIX;
    delete env.PYTHONNOUSERSITE;
  }
  return env;
}

function registerTaskIpc({
  ipcMain,
  root = null,
  pythonUserBase = null,
  workspaceRoot = null,
  getProject,
  getWindows = () => null,
  getSettings = () => null,
  state = { activeTask: null },
}) {
  let preparing = false;
  ipcMain.handle('zsmm:tasks', () => ({ ok: true, data: tasks.taskList() }));

  const start = async (key, options = {}, sender = null) => {
    if (state.activeTask || preparing) {
      return { ok: false, error: 'уже выполняется другая задача: сначала остановите её' };
    }
    const windows = getWindows && getWindows();
    const send = (channel, payload) => {
      if (sender && !sender.isDestroyed()) sender.send(channel, payload);
    };

    // Задачи без Python считает сам главный процесс: это чтение файлов и
    // пересчёт готовности, а не движок. Поток событий тот же, что у задач
    // Python, — окну не нужно знать разницу.
    const native = nativeTasks.NATIVE_TASKS[key];
    if (native) {
      const project = getProject && getProject();
      if (!project) return { ok: false, error: 'проект не открыт' };
      const start = { type: 'start', command: [native.label], label: native.label };
      // Индикатор на кнопке панели задач нужен и здесь: «Проверка файлов»
      // щёлкает мгновенно, а самодиагностика пишет на диск, и окно в это
      // время не должно выглядеть занятым без причины.
      if (windows) windows.showTaskProgress(start);
      send('zsmm:task-event', start);
      try {
        const result = nativeTasks.runNativeTask({
          key,
          project,
          root: root || path.resolve(__dirname, '..', '..'),
          dossierDir: state.dossierDir || null,
          userData: state.userData || null,
          onEvent: (payload) => send('zsmm:task-event', payload),
        });
        const exit = { type: 'exit', code: result.ok ? 0 : 1, signal: null, timedOut: false };
        if (windows) windows.showTaskProgress(exit);
        send('zsmm:task-event', exit);
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
      preparing = true;
      const runRoot = workspaceRoot
        ? await require('./pipeline-workspace').prepareWorkspace(pipeline.root, workspaceRoot)
        : pipeline.root;
      const settingsValue = (getSettings && getSettings()) || {};
      state.activeTask = tasks.runTask({
        key,
        options: options || {},
        python,
        root: runRoot,
        env: taskEnv(settingsValue.networkOnline === true, process.env, python, pythonUserBase),
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
    } finally { preparing = false; }
  };

  ipcMain.handle('zsmm:task-start', (event, payload = {}) =>
    start(payload.key, payload.options || {}, event.sender));

  ipcMain.handle('zsmm:task-stop', () => {
    if (!state.activeTask) return { ok: false, error: 'нет запущенной задачи' };
    return { ok: true, data: { stopped: state.activeTask.stop() } };
  });

  // `start` отдаётся наружу: агентик запускает ту же задачу, а не вторую
  // копию лаунчера — иначе белый список команд легко обойти.
  return { handlers: ['zsmm:tasks', 'zsmm:task-start', 'zsmm:task-stop'], start };
}

module.exports = { registerTaskIpc, taskEnv };
