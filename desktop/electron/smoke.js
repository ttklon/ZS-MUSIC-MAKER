'use strict';
/**
 * smoke.js — проверка упакованного приложения без окна (`--smoke`).
 *
 * Зачем отдельным модулем: собрать установщик и не проверить, что он читает
 * свои данные, — значит узнать о сломанных путях от пользователя. Здесь нет
 * ни `electron`, ни сети: только чтение проекта и короткий рендер, поэтому
 * проверка прогоняется и в CI на Windows, и обычным `node --test`.
 */

const path = require('node:path');

const { renderBeatPayload } = require('./pipeline');
const { createBankProvider } = require('./pipeline');
const { resolvePython } = require('./runtime');

/**
 * Собрать отчёт о состоянии приложения.
 *
 * @param {object} params
 * @param {string|null} params.root      корень проекта
 * @param {string|null} params.rootError причина, если корень не найден
 * @param {Function} params.createProject фабрика модели проекта
 * @param {object} [params.env]
 * @param {boolean} [params.packaged]
 * @param {string} [params.electron]
 * @returns {Promise<{ok: boolean, checks: Array<{name: string, ok: boolean, detail: string}>}>}
 */
async function runSmoke({
  root,
  rootError = null,
  createProject,
  env = process.env,
  packaged = false,
  electron = null,
}) {
  const checks = [];
  const push = (name, ok, detail) => checks.push({ name, ok: Boolean(ok), detail: String(detail ?? '') });

  push('корень проекта найден', Boolean(root), root || rootError || 'путь не найден');

  if (root) {
    try {
      const project = createProject();
      const version = project.version();
      push('version.json', Boolean(version.version), version.version || version.error);

      const genres = project.genres();
      push('каталог жанров', genres.genres.length >= 100, `${genres.genres.length} жанров`);

      const modules = project.modules();
      push('inventory', modules.total > 0, `${modules.total} модулей`);

      const readiness = project.readiness();
      push('снимок готовности', readiness.percent !== null && readiness.percent !== undefined, `${readiness.percent}%`);

      const bank = createBankProvider({ rootDir: root }).bank();
      const bankReport = bank.report();
      push(
        'банк сэмплов',
        bankReport.status === 'REAL_PASS',
        `${bankReport.status}, ${bankReport.total_samples} сэмплов`,
      );

      const beat = await renderBeatPayload(
        { bpm: 140, genre: 'phonk', seed: 7, durationSec: 2 },
        { rootDir: root },
      );
      push(
        'рендер бита',
        beat.ok === true && beat.data.wavBase64.length > 1000,
        beat.ok === true ? `${beat.data.report.total_bars} тактов, ${beat.data.report.duration_sec} с` : beat.error,
      );

      // Вокал в собранном приложении: движок в asar, поэтому проверяем именно
      // упакованный путь. Тестовый дубль обязан приехать помеченным как
      // имитация — иначе окно может выдать его за запись.
      const withVocal = await renderBeatPayload(
        { bpm: 120, genre: 'phonk', seed: 3, durationSec: 2, vocal: { mode: 'test' } },
        { rootDir: root },
      );
      const vocal = withVocal.ok === true ? withVocal.data.report.vocal : null;
      push(
        'вокал (тестовый дубль)',
        Boolean(vocal && vocal.source === 'test' && vocal.simulated === true && withVocal.data.vocalWavBase64),
        vocal ? `${vocal.label}, ${vocal.mixed_seconds} с в миксе` : (withVocal.error || 'вокала нет в отчёте'),
      );

      // Куда приложение пишет досье. В установленной сборке это обязан быть
      // каталог пользователя: `resources/project` лежит в Program Files.
      const writable = require('./writable-data');
      const plan = writable.dossierWriteDir({
        packaged,
        projectRoot: root,
        userData: process.env.APPDATA || require('node:os').tmpdir(),
      });
      push(
        'каталог досье для записи',
        packaged ? plan.source === 'user' : plan.source === 'project',
        `${plan.source}: ${plan.dir}`,
      );

      // Задачи без Python: раздел «Запуск» должен уметь хоть что-то в
      // установленном приложении, где интерпретатора нет.
      const nativeTasks = require('./native-tasks');
      const files = nativeTasks.runNativeTask({ key: 'native-files', project, root });
      push('проверка файлов без Python', files.ok === true, files.lines.at(-1) || 'нет вывода');

      // Досье читается и правится тем же кодом, что в окне. Пишем во
      // временный каталог: у установленного приложения `resources` может быть
      // только для чтения, и smoke не должен ничего ломать.
      const dossier = require('../src/core/dossier-edit');
      const list = project.dossiers();
      push('досье читается', Array.isArray(list.artists), `${list.artists.length} артист(ов)`);
      const tmp = require('node:fs').mkdtempSync(require('node:path').join(require('node:os').tmpdir(), 'zsmm-smoke-'));
      const { createNodeFs } = require('../src/core/fs-node');
      const added = dossier.addArtist(createNodeFs(), tmp, { artist: 'Smoke Artist' });
      // Трек заводится тем же кодом, что в разделе «Треки»: проверяем, что
      // запись создаётся и читается, и что статус не выдуман («не разобран»).
      const tracks = require('../src/core/dossier-tracks');
      const track = added.ok
        ? tracks.addTrack(createNodeFs(), tmp, { slug: added.data.slug, title: 'Smoke Track' })
        : { ok: false, error: 'артист не добавлен' };
      const trackList = added.ok ? tracks.listTracks(createNodeFs(), tmp, added.data.slug) : { tracks: [] };
      const removed = added.ok ? dossier.removeArtist(createNodeFs(), tmp, { slug: added.data.slug }) : { ok: false };
      push(
        'досье правится без Python',
        added.ok === true && track.ok === true && trackList.tracks.length === 1
          && trackList.tracks[0].status === 'pending' && removed.ok === true,
        added.ok
          ? `артист и трек ${track.ok ? track.data.track_id : track.error} добавлены и удалены`
          : added.error,
      );
      try {
        require('node:fs').rmSync(tmp, { recursive: true, force: true });
      } catch {
        /* временный каталог мог остаться — это не провал проверки */
      }
    } catch (err) {
      push('чтение проекта', false, err.message);
    }
  }

  const python = resolvePython({ root, env });
  // Python в собранном приложении не обязателен: это не провал сборки,
  // а состояние, о котором говорит «Диагностика».
  push('Python для задач', true, python.python || 'не найден (не обязателен)');

  return {
    ok: checks.every((check) => check.ok),
    packaged,
    electron,
    root,
    checks,
  };
}

/** Куда писать отчёт: CI читает файл, а не stdout (у GUI нет консоли). */
function smokeOutputPath(env = process.env, tmpdir = require('node:os').tmpdir()) {
  return env.ZSMM_SMOKE_OUT || path.join(tmpdir, 'zsmm-smoke.json');
}

/**
 * Напечатать отчёт и сохранить его в файл.
 *
 * Файл нужен CI: консольный вывод запущенного через `Start-Process` процесса
 * перехватить нельзя, а прочитать JSON после выхода — можно. Если записать
 * не удалось, это не ошибка проверки: отчёт уже напечатан.
 *
 * @param {object} report
 * @param {object} [params]
 * @param {object} [params.env]
 * @param {Function} [params.writeFile]
 * @param {{write: Function}} [params.out]
 * @returns {string} путь к файлу отчёта
 */
function writeReport(report, { env = process.env, writeFile = null, out = process.stdout } = {}) {
  const text = `${JSON.stringify(report, null, 2)}\n`;
  out.write(text);
  const file = smokeOutputPath(env);
  if (!writeFile) return file;
  try {
    writeFile(file, text, 'utf8');
    out.write(`smoke: ${file}\n`);
  } catch (err) {
    out.write(`smoke: файл не записан (${err.message})\n`);
  }
  return file;
}

module.exports = { runSmoke, smokeOutputPath, writeReport };
