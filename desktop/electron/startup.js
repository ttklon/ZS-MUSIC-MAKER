'use strict';
/**
 * startup.js — шаги запуска, которые видно только на Windows 11.
 *
 * Здесь нет `require('electron')`: объект `app` приходит аргументом. Поэтому
 * замок единственного экземпляра и идентификатор панели задач проверяются
 * обычным `node --test`, а не только руками на Windows.
 *
 * Порядок важен: замок берётся до `whenReady`, иначе второй процесс успевает
 * подняться и прочитать настройки; `AppUserModelId` — до создания окна,
 * иначе первое окно попадает в чужую группу панели задач.
 */

const policy = require('./window-policy');

/**
 * Взять замок единственного экземпляра и повесить обработчик второго запуска.
 *
 * @param {object} params
 * @param {object} params.app          Electron `app` (нужны requestSingleInstanceLock, on, quit)
 * @param {Function} params.getWindow  вернуть текущее окно
 * @returns {boolean} true — можно продолжать запуск
 */
function installSingleInstance({ app, getWindow }) {
  const gotLock = app.requestSingleInstanceLock();
  if (!policy.shouldContinueStartup({ gotLock })) {
    // Окно живёт в первом процессе: этому остаётся только выйти.
    app.quit();
    return false;
  }
  app.on('second-instance', () => {
    policy.focusExisting(getWindow());
  });
  return true;
}

/**
 * Идентификатор для панели задач Windows 11.
 *
 * Ставится только у собранного приложения: в разработке `electron.exe`
 * группируется по своему пути, и смешивать группы не нужно.
 *
 * @param {object} params
 * @param {object} params.app
 * @param {string} [params.platform]
 * @returns {string|null} поставленный идентификатор либо null
 */
function installAppUserModelId({ app, platform = process.platform }) {
  const id = policy.appUserModelId({ isPackaged: app.isPackaged, platform });
  if (!id) return null;
  try {
    app.setAppUserModelId(id);
    return id;
  } catch {
    return null;
  }
}

module.exports = { installSingleInstance, installAppUserModelId };
