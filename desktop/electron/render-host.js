'use strict';
/**
 * render-host.js — запуск рендера в отдельном потоке с честным откатом.
 *
 * Зачем отдельный поток: рендер 3 минут бита — это секунды счёта. Даже с
 * пошаговой отдачей управления окно дёргается, а прочие IPC-вызовы ждут.
 *
 * Почему откат: в некоторых окружениях `worker_threads` недоступны или
 * упаковка запрещает запуск файла рядом с `app.asar`. Тогда рендер идёт в
 * главном процессе — тот же код (`pipeline.js`), тот же WAV. Отчёт говорит,
 * каким путём считали: `report.renderer` = `worker` или `main`.
 *
 * Отмена. Долгий бит нужно уметь прервать: «Собрать бит» на 5 минут — это
 * секунды счёта, и ждать их без выхода из положения неправильно. Поток
 * снимается `terminate()`, запасной путь проверяет `isCancelled()` между
 * секциями (сам рендер режется по секциям, см. `engine.renderBeatInSteps`).
 */

const path = require('node:path');

/**
 * @param {object} params
 * @param {object} params.options      параметры из окна
 * @param {string} params.rootDir      корень проекта (банк сэмплов)
 * @param {Function} [params.onProgress] прогресс рендера
 * @param {Function} [params.renderInMain] запасной путь (pipeline.renderBeatPayload)
 * @param {Function} [params.Worker]   подмена worker_threads.Worker в тестах
 * @param {string} [params.workerPath]
 * @param {object} [params.signal]     { aborted, onAbort(fn) } — отмена извне
 * @returns {Promise<{ok: boolean, data?: object, error?: string, renderer: string, fallbackReason?: string, cancelled?: boolean}>}
 */
async function renderInWorker({
  options,
  rootDir,
  onProgress,
  renderInMain,
  Worker = loadWorker(),
  workerPath = path.join(__dirname, 'render-worker.js'),
  timeoutMs = 30 * 60_000,
  signal = null,
}) {
  const cancelled = () => Boolean(signal && signal.aborted);

  const fallback = async (reason) => {
    if (cancelled()) return { ok: false, error: 'рендер отменён', renderer: 'none', cancelled: true };
    if (typeof renderInMain !== 'function') {
      return { ok: false, error: reason, renderer: 'none', fallbackReason: reason };
    }
    const result = await renderInMain(options, {
      rootDir,
      onProgress,
      // Запасной путь живёт в главном процессе и обязан сам проверять отмену:
      // иначе кнопка «Отменить» ничего не делает там, где нет потока.
      isCancelled: cancelled,
    });
    return { ...result, renderer: 'main', fallbackReason: reason };
  };

  if (cancelled()) return { ok: false, error: 'рендер отменён', renderer: 'none', cancelled: true };
  if (typeof Worker !== 'function') {
    return fallback('worker_threads недоступны в этом окружении');
  }

  let worker;
  try {
    worker = new Worker(workerPath, { workerData: { options, rootDir } });
  } catch (err) {
    return fallback(`поток не запустился: ${err && err.message ? err.message : err}`);
  }

  return new Promise((resolve) => {
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (signal && typeof signal.offAbort === 'function') signal.offAbort(onAbort);
      worker.terminate().catch(() => {});
      resolve(value);
    };
    const onAbort = () => finish({ ok: false, error: 'рендер отменён', renderer: 'worker', cancelled: true });
    if (signal && typeof signal.onAbort === 'function') signal.onAbort(onAbort);

    const timer = setTimeout(() => {
      finish({ ok: false, error: `рендер не уложился в ${Math.round(timeoutMs / 1000)} с`, renderer: 'worker' });
    }, timeoutMs);

    worker.on('message', (message) => {
      if (!message || typeof message !== 'object') return;
      if (message.type === 'progress' && typeof onProgress === 'function') onProgress(message.progress);
      else if (message.type === 'result') finish({ ok: true, data: message.payload, renderer: 'worker' });
      else if (message.type === 'error') {
        finish({ ok: false, error: message.error, renderer: 'worker', fatal: message.fatal === true });
      }
    });
    worker.on('error', (err) => {
      // Поток упал (нет файла, запрет упаковки) — считаем в главном процессе.
      // Уже отправленный прогресс не откатываем: окно само перезапишет статус.
      finish({ ok: false, error: err && err.message ? err.message : String(err), renderer: 'worker' });
    });
    worker.on('exit', (code) => {
      if (!settled && code !== 0) {
        finish({ ok: false, error: `поток рендера завершился с кодом ${code}`, renderer: 'worker' });
      }
    });
  }).then(async (result) => {
    // Отмену не «спасаем» запасным путём: пользователь именно этого и просил.
    if (result.cancelled === true) return result;
    // Падение потока — не повод отказывать пользователю в бите. А вот
    // неверные параметры — повод: их не надо пересчитывать ещё раз.
    if (result.ok === false && result.renderer === 'worker' && result.fatal !== true
      && typeof renderInMain === 'function') {
      return fallback(`поток рендера упал: ${result.error}`);
    }
    return result;
  });
}

/**
 * Сигнал отмены: один флаг и подписчики.
 *
 * Сделан руками, а не через `AbortController`, чтобы одинаково работать в
 * Electron, в предпросмотре (обычный Node) и в тестах без polyfill.
 */
function createCancelSignal() {
  const listeners = new Set();
  const signal = {
    aborted: false,
    onAbort(fn) {
      if (typeof fn === 'function') listeners.add(fn);
    },
    offAbort(fn) {
      listeners.delete(fn);
    },
    abort() {
      if (signal.aborted) return false;
      signal.aborted = true;
      for (const listener of [...listeners]) {
        try {
          listener();
        } catch {
          /* подписчик не должен ломать отмену */
        }
      }
      listeners.clear();
      return true;
    },
  };
  return signal;
}

function loadWorker() {
  try {
    // eslint-disable-next-line global-require
    return require('node:worker_threads').Worker;
  } catch {
    return null;
  }
}

module.exports = { renderInWorker, createCancelSignal };
