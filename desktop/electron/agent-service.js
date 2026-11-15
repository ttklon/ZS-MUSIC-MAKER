'use strict';
/**
 * agent-service.js — «Сделать хит»: кнопка агентика → задача → готовый трек.
 *
 * Зачем отдельный канал, а не обычный `task-start`: агентику нужно вернуть не
 * поток лога, а **результат** — путь к мастеру и вердикт, который Python
 * печатает последней строкой в JSON. Окно иначе показало бы «задача
 * завершилась», а человек так и не узнал бы, где файл.
 *
 * Канал намеренно тонкий: запуск процесса, проверка аргументов и построчный
 * вывод остаются в `tasks.js` / `task-runner.js`. Здесь только разбор отчёта
 * и открытие мастера в системном плеере — то, что уже умеет главный процесс.
 *
 * Тест: `test/agent-bridge.test.js` (без Electron — двойники ipcMain и окна).
 */

const path = require('node:path');

/** Последняя строка отчёта агентика — JSON (его печатает `app/cli/agent_task.py`). */
const REPORT_PREFIX = '[agent-hit]';

/**
 * Найти путь к мастеру в выводе задачи.
 *
 * Python печатает `{"verdict": …, "master_path": …}` в конце. Разбираем любую
 * строку с `master_path`, а не только последнюю: между отчётом и итогом может
 * оказаться строка предупреждения, и терять из-за неё результат нельзя.
 */
function parseMasterPath(lines) {
  if (!Array.isArray(lines)) return { masterPath: null, verdict: null };
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    const line = String(lines[index] || '');
    const start = line.indexOf('{');
    if (start === -1 || !line.includes('master_path')) continue;
    try {
      const payload = JSON.parse(line.slice(start));
      if (payload && typeof payload.master_path === 'string' && payload.master_path) {
        return { masterPath: payload.master_path, verdict: payload.verdict || null };
      }
      // Мастера нет, но отчёт есть: вердикт важнее пустого пути.
      if (payload && payload.verdict) return { masterPath: null, verdict: payload.verdict };
    } catch (err) {
      // Строка лога, а не отчёт: идём дальше вверх. Ошибка разбора здесь
      // ожидаема и не является ошибкой задачи.
      void err;
    }
  }
  return { masterPath: null, verdict: null };
}

/** Проверить, что мастер существует на диске: путь из отчёта — не гарантия. */
function masterExists(masterPath, fsApi) {
  if (!masterPath || typeof masterPath !== 'string') return false;
  if (!path.isAbsolute(masterPath)) return false;
  try {
    return Boolean(fsApi && fsApi.existsSync && fsApi.existsSync(masterPath));
  } catch (err) {
    void err;
    return false;
  }
}

/**
 * @param {object} params
 * @param {object} params.ipcMain        electron ipcMain (или двойник)
 * @param {Function} params.startAgent   `(options) => {ok, error?}` — запуск задачи
 * @param {object} [params.fsApi]        файловое API (`existsSync`)
 * @param {Function} [params.openPath]   открыть файл в системном плеере
 * @returns {{handlers: string[]}}
 */
function registerAgentIpc({ ipcMain, startAgent, fsApi = require('node:fs'), openPath = null }) {
  // Запуск: ответ приходит сразу (задача идёт минутами), а результат окно
  // получает из общего потока `zsmm:task-done` и само разбирает лог.
  ipcMain.handle('zsmm:agent-hit', async (_event, options) => {
    if (typeof startAgent !== 'function') return { ok: false, error: 'запуск задач недоступен' };
    try {
      return await startAgent(options || {});
    } catch (err) {
      return { ok: false, error: err && err.message ? err.message : String(err) };
    }
  });

  // Готовый мастер → системный плеер. Окно присылает путь, который само
  // прочитало из лога; главный процесс проверяет, что файл существует,
  // и только тогда открывает. Путь приходит от Python, а не от пользователя.
  ipcMain.handle('zsmm:agent-open', async (_event, payload = {}) => {
    const masterPath = payload && payload.masterPath;
    if (!masterExists(masterPath, fsApi)) {
      return { ok: false, error: 'мастер не найден на диске' };
    }
    if (typeof openPath !== 'function') return { ok: false, error: 'системное открытие недоступно' };
    const error = await openPath(masterPath);
    return error ? { ok: false, error: `плеер не открылся: ${error}` } : { ok: true, data: { path: masterPath } };
  });

  return { handlers: ['zsmm:agent-hit', 'zsmm:agent-open'] };
}

module.exports = { registerAgentIpc, parseMasterPath, masterExists, REPORT_PREFIX };
