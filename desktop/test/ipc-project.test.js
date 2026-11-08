'use strict';
/**
 * ipc-project.test.js — каналы данных проекта на настоящем проекте.
 *
 * Проверяется не «канал зарегистрирован», а ответ: окно получает `{data}`
 * либо `{error}` с текстом, и отсутствие проекта — это `{error}`, а не
 * исключение внутри главного процесса.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { registerProjectIpc } = require('../electron/ipc-project');
const { createProject } = require('../src/core/project');
const { createNodeFs } = require('../src/core/fs-node');

const ROOT = path.resolve(__dirname, '..', '..');

/** Двойник ipcMain: запоминает обработчики и умеет их вызывать. */
function fakeIpc() {
  const handlers = new Map();
  return {
    handlers,
    handle(channel, fn) {
      handlers.set(channel, fn);
    },
    call(channel, ...args) {
      const fn = handlers.get(channel);
      assert.ok(fn, `нет канала ${channel}`);
      return fn(...args);
    },
  };
}

test('все шесть каналов данных регистрируются', () => {
  const ipcMain = fakeIpc();
  const project = createProject(createNodeFs(), ROOT);
  const channels = registerProjectIpc({ ipcMain, getProject: () => project });

  assert.deepEqual(channels, [
    'zsmm:version',
    'zsmm:genres',
    'zsmm:modules',
    'zsmm:readiness',
    'zsmm:dossiers',
    'zsmm:system',
  ]);
  for (const channel of channels) assert.ok(ipcMain.handlers.has(channel), channel);
});

test('каналы отдают настоящие данные проекта', () => {
  const ipcMain = fakeIpc();
  const project = createProject(createNodeFs(), ROOT);
  registerProjectIpc({ ipcMain, getProject: () => project });

  const version = ipcMain.call('zsmm:version');
  assert.ok(version.data && typeof version.data.version === 'string', 'нет версии');

  const genres = ipcMain.call('zsmm:genres');
  assert.ok(genres.data.genres.length >= 100, `жанров: ${genres.data.genres.length}`);

  const readiness = ipcMain.call('zsmm:readiness');
  assert.ok(typeof readiness.data.percent === 'number');
});

test('без проекта канал отвечает ошибкой, а не падает', () => {
  const ipcMain = fakeIpc();
  registerProjectIpc({ ipcMain, getProject: () => null });

  assert.deepEqual(ipcMain.call('zsmm:genres'), { error: 'проект не открыт' });
});

test('исключение загрузчика превращается в текст для окна', () => {
  const ipcMain = fakeIpc();
  const broken = {
    version() {
      throw new Error('version.json испорчен');
    },
  };
  registerProjectIpc({ ipcMain, getProject: () => broken });

  assert.deepEqual(ipcMain.call('zsmm:version'), { error: 'version.json испорчен' });
  // Без сообщения в ошибке всё равно нужен текст, а не «undefined».
  const silent = {
    version() {
      throw 'строка вместо ошибки';
    },
  };
  const ipc2 = fakeIpc();
  registerProjectIpc({ ipcMain: ipc2, getProject: () => silent });
  assert.deepEqual(ipc2.call('zsmm:version'), { error: 'строка вместо ошибки' });
});
