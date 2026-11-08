'use strict';
/**
 * ipc-project.js — IPC вокруг данных проекта.
 *
 * Шесть каналов `zsmm:version|genres|modules|readiness|dossiers|system` — это
 * чтение файлов проекта и ничего больше. Вынесено из `main.js` ради правила
 * «≤ 400 строк» и ради теста: загрузчики проверяются на настоящем проекте
 * без Electron.
 *
 * Правило ответа одно: либо `{data}`, либо `{error}` — исключение наружу не
 * уходит, иначе окно получит голый `Error` вместо текста для человека.
 */

/**
 * Зарегистрировать каналы данных проекта.
 *
 * @param {object} params
 * @param {object} params.ipcMain     electron ipcMain (или двойник в тестах)
 * @param {Function} params.getProject текущая модель проекта либо null
 * @returns {string[]} имена зарегистрированных каналов
 */
function registerProjectIpc({ ipcMain, getProject }) {
  const registered = [];
  // Загрузчики берутся из актуального проекта: окно может открыться до того,
  // как проект прочитан, и это не должно ломать регистрацию каналов.
  const loaders = {
    version: (p) => p.version(),
    genres: (p) => p.genres(),
    modules: (p) => p.modules(),
    readiness: (p) => p.readiness(),
    dossiers: (p) => p.dossiers(),
    system: (p) => p.systemInfo(),
  };

  for (const [name, loader] of Object.entries(loaders)) {
    const channel = `zsmm:${name}`;
    ipcMain.handle(channel, () => {
      const active = getProject();
      if (!active) return { error: 'проект не открыт' };
      try {
        return { data: loader(active) };
      } catch (err) {
        return { error: err && err.message ? err.message : String(err) };
      }
    });
    registered.push(channel);
  }
  return registered;
}

module.exports = { registerProjectIpc };
