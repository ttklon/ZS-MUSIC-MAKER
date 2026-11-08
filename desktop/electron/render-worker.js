'use strict';
/**
 * render-worker.js — рендер бита в отдельном потоке.
 *
 * Раньше рендер шёл в главном процессе: окно отвечало (секции отдают
 * управление в цикл событий), но на длинном бите подтормаживали анимации и
 * любые другие IPC-вызовы ждали своей очереди. Здесь та же работа живёт в
 * отдельном потоке: главный процесс только пересылает прогресс.
 *
 * Отдельный файл обязателен — `worker_threads` запускает поток по пути к
 * скрипту, а не по функции. Поэтому в Electron он лежит вне `app.asar`
 * (`asarUnpack`), см. `desktop/package.json`.
 */

const { parentPort, workerData } = require('node:worker_threads');

const { renderBeatPayload } = require('./pipeline');

async function main() {
  const { options, rootDir } = workerData || {};

  const result = await renderBeatPayload(options, {
    rootDir,
    onProgress: (progress) => {
      if (parentPort) parentPort.postMessage({ type: 'progress', progress });
    },
  });

  if (!parentPort) return;
  if (result.ok === true) {
    parentPort.postMessage({ type: 'result', payload: result.data });
  } else {
    parentPort.postMessage({ type: 'error', error: result.error, fatal: result.fatal === true });
  }
}

main().catch((err) => {
  if (parentPort) parentPort.postMessage({ type: 'error', error: err && err.message ? err.message : String(err) });
});
