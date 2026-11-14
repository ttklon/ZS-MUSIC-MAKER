'use strict';
/**
 * app-paths.js — куда приложение сохраняет файлы на Windows 11.
 *
 * Вынесено из `main.js`, потому что это единственное место, где нужен
 * `app.getPath`, и потому что ошибку здесь видно только на установленной
 * сборке: в репозитории каталог «Музыка» есть всегда, а в урезанном профиле
 * Windows его может не быть вовсе.
 *
 * Правило: если системного каталога нет, приложение не падает и не пишет в
 * `C:\` — оно уходит во временный каталог и говорит об этом в «Диагностике».
 */

const path = require('node:path');
const os = require('node:os');

/**
 * @param {{getPath?: Function}} electronApp объект `app` из Electron
 * @returns {string} существующий или запасной каталог для WAV и отчётов
 */
function musicDir(electronApp) {
  try {
    const dir = electronApp && typeof electronApp.getPath === 'function'
      ? electronApp.getPath('music')
      : null;
    if (dir) return dir;
  } catch {
    /* без графической среды системных путей может не быть */
  }
  return path.join(os.tmpdir(), 'zsmm');
}

module.exports = { musicDir };
