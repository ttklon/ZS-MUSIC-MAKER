'use strict';
/**
 * render-host.test.js — рендер в отдельном потоке и откат в главный процесс.
 *
 * Главное, что здесь проверяется: пользователь получает бит даже там, где
 * `worker_threads` недоступны (часть упакованных сборок), а отчёт честно
 * говорит, каким путём считали. И наоборот: при живом потоке главный процесс
 * не считает ничего.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { EventEmitter } = require('node:events');

const { renderInWorker, createCancelSignal } = require('../electron/render-host');

const ROOT = path.resolve(__dirname, '..', '..');
const OPTIONS = { bpm: 140, genre: 'phonk', seed: 7, durationSec: 2 };

/** Заглушка Worker: ведёт себя как настоящий поток, но без счёта. */
function fakeWorker(script) {
  return class FakeWorker extends EventEmitter {
    constructor() {
      super();
      this.terminated = false;
      setTimeout(() => script(this), 0);
    }

    terminate() {
      this.terminated = true;
      return Promise.resolve(0);
    }
  };
}

test('поток отдаёт результат и прогресс, главный процесс не считает', async () => {
  let mainCalled = false;
  const progress = [];
  const Worker = fakeWorker((worker) => {
    worker.emit('message', { type: 'progress', progress: { phase: 'section', percent: 20 } });
    worker.emit('message', { type: 'result', payload: { report: { bpm: 140 }, wavBase64: 'UklGRg==' } });
  });

  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    onProgress: (event) => progress.push(event),
    renderInMain: async () => {
      mainCalled = true;
      return { ok: true, data: {} };
    },
    Worker,
  });

  assert.equal(result.ok, true);
  assert.equal(result.renderer, 'worker');
  assert.equal(result.data.report.bpm, 140);
  assert.equal(mainCalled, false, 'при живом потоке главный процесс не рендерит');
  assert.deepEqual(progress, [{ phase: 'section', percent: 20 }]);
});

test('ошибка в потоке переходит в откат, а не в пустой экран', async () => {
  const Worker = fakeWorker((worker) => worker.emit('error', new Error('нет файла потока')));

  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    renderInMain: async () => ({ ok: true, data: { wavBase64: 'UklGRg==', report: { bpm: 140 } } }),
    Worker,
  });

  assert.equal(result.ok, true, 'бит должен собраться, даже если поток не поднялся');
  assert.equal(result.renderer, 'main');
  assert.match(result.fallbackReason, /нет файла потока/);
});

test('без worker_threads работает запасной путь', async () => {
  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    renderInMain: async () => ({ ok: true, data: { wavBase64: 'UklGRg==' } }),
    Worker: null,
  });

  assert.equal(result.ok, true);
  assert.equal(result.renderer, 'main');
  assert.match(result.fallbackReason, /worker_threads/);
});

test('ошибка самого рендера не маскируется откатом', async () => {
  // `fatal` так помечает конвейер ошибку самих параметров (см. pipeline.js).
  const Worker = fakeWorker((worker) => {
    worker.emit('message', { type: 'error', error: 'BPM вне диапазона', fatal: true });
  });

  const result = await renderInWorker({
    options: { bpm: 5000 },
    rootDir: ROOT,
    renderInMain: async () => assert.fail('неверные параметры не должны идти в запасной путь'),
    Worker,
  });

  assert.equal(result.ok, false);
  assert.match(result.error, /BPM/);
  assert.equal(result.renderer, 'worker');
});

test('зависший поток обрывается по таймауту с внятной причиной', async () => {
  const Worker = fakeWorker(() => { /* молчит */ });

  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    renderInMain: async () => ({ ok: true, data: { wavBase64: 'UklGRg==' } }),
    Worker,
    timeoutMs: 30,
  });

  assert.equal(result.ok, true, 'таймаут тоже уходит в запасной путь');
  assert.equal(result.renderer, 'main');
  assert.match(result.fallbackReason, /не уложился/);
});

test('настоящий поток действительно считает бит', async () => {
  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    renderInMain: async () => assert.fail('настоящий worker должен справиться сам'),
  });

  assert.equal(result.ok, true, result.error);
  assert.equal(result.renderer, 'worker');
  assert.equal(Buffer.from(result.data.wavBase64, 'base64').toString('ascii', 0, 4), 'RIFF');
  assert.equal(result.data.report.bpm, 140);
});

test('отмена снимает поток и не уходит в запасной путь', async () => {
  let mainCalled = false;
  const signal = createCancelSignal();
  const Worker = fakeWorker((worker) => {
    // Поток «работает», но пользователь нажал «Отменить».
    setTimeout(() => signal.abort(), 5);
    setTimeout(() => worker.emit('message', { type: 'result', payload: {} }), 50);
  });

  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    renderInMain: async () => {
      mainCalled = true;
      return { ok: true, data: {} };
    },
    Worker,
    signal,
  });

  assert.equal(result.ok, false);
  assert.equal(result.cancelled, true);
  assert.match(result.error, /отменён/);
  assert.equal(mainCalled, false, 'отменённый рендер не должен переезжать в главный процесс');
});

test('отмена до старта возвращает «отменён», не запуская ничего', async () => {
  const signal = createCancelSignal();
  signal.abort();
  let started = false;

  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    renderInMain: async () => {
      started = true;
      return { ok: true, data: {} };
    },
    Worker: fakeWorker(() => {}),
    signal,
  });

  assert.equal(result.cancelled, true);
  assert.equal(started, false);
});

test('запасной путь тоже уважает отмену', async () => {
  const signal = createCancelSignal();
  const Worker = null; // как будто worker_threads недоступны

  const result = await renderInWorker({
    options: OPTIONS,
    rootDir: ROOT,
    Worker,
    signal,
    renderInMain: async (_options, ctx) => {
      // Главный процесс обязан получить проверку отмены, а не только флаг.
      assert.equal(typeof ctx.isCancelled, 'function');
      signal.abort();
      assert.equal(ctx.isCancelled(), true);
      return { ok: false, error: 'рендер отменён', cancelled: true };
    },
  });

  assert.equal(result.cancelled, true);
  assert.equal(result.renderer, 'main');
});

test('сигнал отмены срабатывает один раз и не падает без подписчиков', () => {
  const signal = createCancelSignal();

  assert.equal(signal.aborted, false);
  assert.equal(signal.abort(), true);
  assert.equal(signal.abort(), false, 'повторная отмена — не событие');
  assert.equal(signal.aborted, true);
  signal.offAbort(() => {});
});
