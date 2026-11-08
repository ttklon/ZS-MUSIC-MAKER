'use strict';
/**
 * Контракт интерфейса без графической среды.
 *
 * Тест проверяет то, что обычно ломается незаметно: ссылки на несуществующие
 * элементы, файлы, которых нет на диске, и вызовы моста, которых нет в
 * preload. Такой тест ловит ошибку до запуска окна, а не после.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const SRC = path.resolve(__dirname, '..', 'src');
const ELECTRON = path.resolve(__dirname, '..', 'electron');

const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
const appJs = fs.readFileSync(path.join(SRC, 'app.js'), 'utf8');
const preload = fs.readFileSync(path.join(ELECTRON, 'preload.js'), 'utf8');

function ids() {
  const found = new Set();
  for (const match of html.matchAll(/\sid="([^"]+)"/g)) found.add(match[1]);
  return found;
}

test('index.html ссылается только на существующие файлы', () => {
  for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const target = match[1];
    if (/^https?:/.test(target) || target.startsWith('data:')) continue;
    assert.ok(fs.existsSync(path.join(SRC, target)), `нет файла: ${target}`);
  }
});

test('CSP запрещает сеть и inline-скрипты', () => {
  const csp = /content="([^"]*default-src[^"]*)"/.exec(html);
  assert.ok(csp, 'в index.html нет Content-Security-Policy');

  assert.match(csp[1], /connect-src 'none'/, 'окно не должно ходить в сеть');
  assert.doesNotMatch(csp[1], /unsafe-inline/, 'inline-скрипты запрещены');
});

test('все id, к которым обращается app.js, есть в разметке', () => {
  const known = ids();
  const used = new Set();
  for (const match of appJs.matchAll(/\$\('([^']+)'\)/g)) used.add(match[1]);

  const missing = [...used].filter((id) => !known.has(id));
  assert.deepEqual(missing, [], `app.js ищет несуществующие элементы: ${missing.join(', ')}`);
});

test('все разделы навигации имеют панель и заголовок', () => {
  const views = [...html.matchAll(/data-view="([^"]+)"/g)].map((m) => m[1]);
  assert.ok(views.length >= 5);

  for (const view of views) {
    assert.match(html, new RegExp(`id="view-${view}"`), `нет панели для ${view}`);
    assert.match(appJs, new RegExp(`${view}:`), `нет загрузчика для ${view}`);
  }
});

test('app.js вызывает только то, что отдаёт preload', () => {
  // берём ровно тело `exposeInMainWorld('zsmm', {...})`, а не весь файл
  const block = preload.slice(preload.indexOf("exposeInMainWorld('zsmm'"));
  const exposed = new Set();
  for (const match of block.matchAll(/^\s{2}(\w+)\s*[:,]/gm)) exposed.add(match[1]);
  for (const match of block.matchAll(/^\s{2}(\w+),$/gm)) exposed.add(match[1]);
  for (const match of block.matchAll(/^\s{2}(\w+):\s/gm)) exposed.add(match[1]);

  const used = new Set();
  for (const match of appJs.matchAll(/window\.zsmm\.(\w+)/g)) used.add(match[1]);

  const unknown = [...used].filter((name) => !exposed.has(name));
  assert.deepEqual(unknown, [], `app.js зовёт несуществующие методы: ${unknown.join(', ')}`);
  assert.ok(exposed.size >= 6, `preload отдаёт слишком мало: ${[...exposed].join(', ')}`);
});

test('app.js не содержит сетевых вызовов', () => {
  for (const pattern of [/fetch\(/, /XMLHttpRequest/, /new WebSocket/, /https?:\/\//]) {
    assert.doesNotMatch(appJs, pattern, `сеть в окне недопустима: ${pattern}`);
  }
});

test('preload не отдаёт странице require и ipcRenderer напрямую', () => {
  assert.match(preload, /contextBridge\.exposeInMainWorld/);
  assert.doesNotMatch(preload, /exposeInMainWorld\('zsmm',\s*\{[^}]*ipcRenderer\b/);
  const exposedBlock = preload.slice(preload.indexOf('exposeInMainWorld'));
  assert.doesNotMatch(exposedBlock, /\brequire\(/, 'require не должен попадать в окно');
});

test('main.js держит изоляцию контекста включённой', () => {
  const main = fs.readFileSync(path.join(ELECTRON, 'main.js'), 'utf8');

  assert.match(main, /contextIsolation:\s*true/);
  assert.match(main, /nodeIntegration:\s*false/);
  assert.match(main, /setWindowOpenHandler/, 'всплывающие окна должны блокироваться');
  assert.doesNotMatch(main, /child_process|spawn\(/, 'Python-процессов в оболочке нет');
});

test('в стилях нет внешних шрифтов и картинок', () => {
  const css = fs.readFileSync(path.join(SRC, 'styles.css'), 'utf8');

  assert.doesNotMatch(css, /@import|url\(https?:/);
});
