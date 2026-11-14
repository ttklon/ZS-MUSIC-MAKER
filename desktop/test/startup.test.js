'use strict';
/**
 * startup.test.js — шаги запуска на двойнике `app`.
 *
 * Замок единственного экземпляра и `AppUserModelId` видно только на Windows,
 * поэтому проверяются на объекте-двойнике: важно, что вызвано, в каком
 * порядке и что второй запуск не продолжает инициализацию.
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const startup = require('../electron/startup');
const policy = require('../electron/window-policy');

/** Двойник Electron `app`: записывает вызовы и ведёт себя как настоящий. */
function fakeApp({ gotLock = true, isPackaged = true, failSetId = false } = {}) {
  const calls = [];
  const handlers = {};
  return {
    calls,
    handlers,
    isPackaged,
    requestSingleInstanceLock: () => {
      calls.push(['lock']);
      return gotLock;
    },
    quit: () => calls.push(['quit']),
    on: (name, fn) => {
      calls.push(['on', name]);
      handlers[name] = fn;
    },
    setAppUserModelId: (id) => {
      calls.push(['setAppUserModelId', id]);
      if (failSetId) throw new Error('нет AppUserModelId в этой версии Electron');
    },
  };
}

test('первый запуск берёт замок и подписывается на второй экземпляр', () => {
  const app = fakeApp({ gotLock: true });
  const ok = startup.installSingleInstance({ app, getWindow: () => null });

  assert.equal(ok, true);
  assert.deepEqual(app.calls, [['lock'], ['on', 'second-instance']]);
});

test('второй запуск выходит и ничего больше не настраивает', () => {
  const app = fakeApp({ gotLock: false });
  const ok = startup.installSingleInstance({ app, getWindow: () => null });

  assert.equal(ok, false);
  assert.deepEqual(app.calls, [['lock'], ['quit']]);
  assert.equal(app.handlers['second-instance'], undefined, 'обработчик нужен только первому процессу');
});

test('второй запуск поднимает окно первого процесса', () => {
  const shown = [];
  const window = {
    isMinimized: () => true,
    isVisible: () => true,
    restore: () => shown.push('restore'),
    focus: () => shown.push('focus'),
  };
  const app = fakeApp({ gotLock: true });
  startup.installSingleInstance({ app, getWindow: () => window });
  app.handlers['second-instance']();

  assert.deepEqual(shown, ['restore']);
});

test('AppUserModelId ставится у собранного Windows-приложения', () => {
  const app = fakeApp({ isPackaged: true });
  const id = startup.installAppUserModelId({ app, platform: 'win32' });

  assert.equal(id, policy.APP_USER_MODEL_ID);
  assert.deepEqual(app.calls, [['setAppUserModelId', 'ru.zsmm.musicmaker']]);
});

test('в разработке и не на Windows идентификатор не ставится', () => {
  const dev = fakeApp({ isPackaged: false });
  assert.equal(startup.installAppUserModelId({ app: dev, platform: 'win32' }), null);
  assert.deepEqual(dev.calls, []);

  const linux = fakeApp({ isPackaged: true });
  assert.equal(startup.installAppUserModelId({ app: linux, platform: 'linux' }), null);
  assert.deepEqual(linux.calls, []);
});

test('старая версия Electron без setAppUserModelId не роняет запуск', () => {
  const app = fakeApp({ isPackaged: true, failSetId: true });
  assert.equal(startup.installAppUserModelId({ app, platform: 'win32' }), null);
});
