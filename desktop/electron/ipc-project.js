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

const { createNodeFs } = require('../src/core/fs-node');
const dossierEdit = require('../src/core/dossier-edit');
const dossierTracks = require('../src/core/dossier-tracks');

/**
 * Зарегистрировать каналы данных проекта.
 *
 * @param {object} params
 * @param {object} params.ipcMain     electron ipcMain (или двойник в тестах)
 * @param {Function} params.getProject текущая модель проекта либо null
 * @param {string} params.root      корень проекта (для правки досье)
 * @param {string} [params.dataDir] каталог досье для записи (установленная
 *   сборка: `resources/project` только для чтения, пишем в каталог пользователя)
 * @param {object} [params.fileSystem] файловое API (в тестах — двойник)
 * @returns {string[]} имена зарегистрированных каналов
 */
function registerProjectIpc({ ipcMain, getProject, root = null, fileSystem = null, dataDir = null }) {
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

  // Досье редактируется в окне: добавление артиста — это запись одного JSON,
  // Python для этого не нужен. Корень берём из аргумента, а не из модели,
  // чтобы каналы регистрировались даже до открытия проекта.
  if (root) {
    const fsApi = fileSystem || createNodeFs();
    // `opts.dataDir` — куда писать. В установленной сборке это каталог
    // пользователя: `resources/project` лежит в Program Files, запись туда
    // запрещена, и без этого «Добавить артиста» падало бы с EACCES.
    const opts = dataDir ? { dataDir } : {};
    ipcMain.handle('zsmm:dossier-add', (_event, payload) => dossierEdit.addArtist(
      fsApi, root, payload && typeof payload === 'object' ? payload : {}, opts,
    ));
    ipcMain.handle('zsmm:dossier-remove', (_event, payload) => dossierEdit.removeArtist(
      fsApi, root, payload && typeof payload === 'object' ? payload : {}, opts,
    ));
    // Треки досье: запись `<slug>/tracks/<id>.json` в формате Python-менеджера.
    // Анализ (bpm, тональность, разбор вокала) по-прежнему делает Python —
    // окно только заводит трек и честно ставит статус `pending`.
    ipcMain.handle('zsmm:dossier-tracks', (_event, payload) => {
      const { slug } = payload && typeof payload === 'object' ? payload : {};
      const clean = String(slug || '').trim();
      if (!clean) return { ok: false, error: 'не указан артист' };
      const list = dossierTracks.listTracks(fsApi, root, clean, opts);
      return {
        ok: true,
        data: { slug: clean, tracks: list.tracks, errors: list.errors },
      };
    });
    ipcMain.handle('zsmm:dossier-track-add', (_event, payload) => dossierTracks.addTrack(
      fsApi, root, payload && typeof payload === 'object' ? payload : {}, opts,
    ));
    registered.push(
      'zsmm:dossier-add', 'zsmm:dossier-remove',
      'zsmm:dossier-tracks', 'zsmm:dossier-track-add',
    );
  }
  return registered;
}

module.exports = { registerProjectIpc };
