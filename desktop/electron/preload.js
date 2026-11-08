'use strict';
/**
 * preload.js — единственный мост между окном и системой.
 *
 * Контекст изоляции включён: страница не получает ни `require`, ни
 * `ipcRenderer`. Наружу отдаются только готовые функции, без объекта IPC.
 */

const { contextBridge, ipcRenderer } = require('electron');

async function section(name) {
  const reply = await ipcRenderer.invoke(`zsmm:${name}`);
  if (!reply || reply.error) {
    return { ok: false, error: (reply && reply.error) || 'нет ответа от главного процесса' };
  }
  return { ok: true, data: reply.data };
}

// Обёртки держат `ipcRenderer` внутри preload: страница получает только
// готовые функции, а не объект IPC.
/** Запуск задач проекта: есть события, поэтому отдельный канал. */
async function listTasks() {
  const reply = await ipcRenderer.invoke('zsmm:tasks');
  return reply && reply.ok ? reply.data : reply;
}

async function startTask(key, options) {
  return ipcRenderer.invoke('zsmm:task-start', { key, options });
}

async function stopTask() {
  return ipcRenderer.invoke('zsmm:task-stop');
}

/** Подписка на поток вывода. Возвращает функцию отписки. */
function onTaskEvent(callback) {
  if (typeof callback !== 'function') return () => {};
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on('zsmm:task-event', listener);
  return () => ipcRenderer.removeListener('zsmm:task-event', listener);
}

function onTaskDone(callback) {
  if (typeof callback !== 'function') return () => {};
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on('zsmm:task-done', listener);
  return () => ipcRenderer.removeListener('zsmm:task-done', listener);
}

/** Собрать бит в главном процессе: движок живёт там, странице он не виден. */
function renderBeat(options) {
  return ipcRenderer.invoke('zsmm:beat-render', options);
}

/** Прервать идущий рендер бита. */
function cancelBeat() {
  return ipcRenderer.invoke('zsmm:beat-cancel');
}

/** Что за банк сэмплов подключён к движку (REAL_PASS/PARTIAL/FALLBACK). */
function beatBank() {
  return ipcRenderer.invoke('zsmm:beat-bank');
}

/** Подписка на прогресс рендера бита. Возвращает функцию отписки. */
function onBeatProgress(callback) {
  if (typeof callback !== 'function') return () => {};
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on('zsmm:beat-progress', listener);
  return () => ipcRenderer.removeListener('zsmm:beat-progress', listener);
}

/** Добавить артиста в досье (запись artist.json в data/artist_dossier). */
function dossierAdd(payload) {
  return ipcRenderer.invoke('zsmm:dossier-add', payload);
}

/** Удалить артиста вместе с его каталогом досье. */
function dossierRemove(payload) {
  return ipcRenderer.invoke('zsmm:dossier-remove', payload);
}

/** Диалог выбора WAV для вокала. Возвращает `{path}` или `{path: null}`. */
function pickVocalFile() {
  return ipcRenderer.invoke('zsmm:vocal-pick');
}

/** Состояние входа записи: есть ли захват с микрофона (сейчас — нет). */
function vocalInput() {
  return ipcRenderer.invoke('zsmm:vocal-input');
}

/** Открыть готовый WAV в системном плеере (двойной щелчок по файлу). */
function openBeatExternal(wavBase64) {
  return ipcRenderer.invoke('zsmm:beat-open-external', wavBase64);
}

/** Сохранить вокальный дубль отдельным WAV через диалог. */
function exportVocalTake(payload) {
  return ipcRenderer.invoke('zsmm:vocal-export', payload);
}

/** Сохранить готовый WAV через диалог сохранения. */
function saveBeat(wavBase64) {
  return ipcRenderer.invoke('zsmm:beat-save', wavBase64);
}

/** Сохранить текстовый отчёт (JSON/MD) через диалог сохранения. */
function saveReport(name, text) {
  return ipcRenderer.invoke('zsmm:save-copy', { name, text });
}

/** Настройки окна: переживают перезапуск (userData/settings.json). */
function loadSettings() {
  return ipcRenderer.invoke('zsmm:settings-load');
}

function saveSettings(patch) {
  return ipcRenderer.invoke('zsmm:settings-save', patch);
}

/** Где работает приложение: пути, версии, есть ли Python. Для «Диагностики». */
function environment() {
  return ipcRenderer.invoke('zsmm:environment');
}

function revealRoot() {
  return ipcRenderer.invoke('zsmm:reveal-root');
}

function openExternal(url) {
  return ipcRenderer.invoke('zsmm:open-external', url);
}

contextBridge.exposeInMainWorld('zsmm', {
  version: () => section('version'),
  genres: () => section('genres'),
  modules: () => section('modules'),
  readiness: () => section('readiness'),
  dossiers: () => section('dossiers'),
  system: () => section('system'),
  listTasks,
  startTask,
  stopTask,
  onTaskEvent,
  onTaskDone,
  renderBeat,
  cancelBeat,
  beatBank,
  onBeatProgress,
  saveBeat,
  saveReport,
  openBeatExternal,
  exportVocalTake,
  pickVocalFile,
  vocalInput,
  dossierAdd,
  dossierRemove,
  loadSettings,
  saveSettings,
  environment,
  revealRoot,
  openExternal,
});
