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
// Окно разбито на app.js + sections/*.js — контракт проверяется по всем
// скриптам вместе: иначе правило легко обойти, перенеся код в раздел.
const { windowScripts } = require('./fake-dom');
const appJs = windowScripts(SRC).map((script) => script.source).join('\n');
const preload = fs.readFileSync(path.join(ELECTRON, 'preload.js'), 'utf8');

/** Исходники главного процесса: main.js сам тонкий, IPC живёт рядом. */
function readElectron(names) {
  return names.map((name) => fs.readFileSync(path.join(ELECTRON, name), 'utf8')).join('\n');
}

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
  // Раньше здесь стоял запрет на child_process: оболочка была без Python.
  // Задачи проекта запускают `python main.py …` осознанно и только через
  // `electron/tasks.js`; прямой spawn в main.js по-прежнему запрещён.
  assert.doesNotMatch(main, /child_process/, 'главный процесс не запускает процессы сам');
  assert.doesNotMatch(main, /spawn\(/, 'запуск процессов живёт в electron/tasks.js');
});

test('в стилях нет внешних шрифтов и картинок', () => {
  const css = fs.readFileSync(path.join(SRC, 'styles.css'), 'utf8');

  assert.doesNotMatch(css, /@import|url\(https?:/);
});

test('бит рендерится в главном процессе, а не в странице', () => {
  const main = readElectron(['main.js', 'beat-service.js']);
  const pipeline = fs.readFileSync(path.join(ELECTRON, 'pipeline.js'), 'utf8');

  assert.match(main, /zsmm:beat-render/, 'нет IPC-канала рендера бита');
  assert.match(pipeline, /sanitizeBeatOptions/, 'параметры из окна должны проверяться');
  assert.match(main, /renderInWorker/, 'рендер должен уходить в отдельный поток');
  assert.match(main, /zsmm:beat-save/, 'нет канала сохранения WAV');
  // Движок тянет fs/Buffer — в окне ему не место.
  assert.doesNotMatch(appJs, /require\(/, 'страница не должна получать require');
  assert.match(appJs, /window\.zsmm\.renderBeat/, 'окно должно звать мост рендера');
});

test('настройки и окружение приложения доходят до окна', () => {
  const main = readElectron(['main.js', 'beat-service.js', 'settings.js']);

  for (const channel of ['zsmm:settings-load', 'zsmm:settings-save', 'zsmm:environment', 'zsmm:save-copy']) {
    assert.match(main, new RegExp(channel), `нет канала ${channel}`);
  }
  assert.match(appJs, /rememberBeatOptions/, 'параметры бита должны запоминаться');
  assert.match(appJs, /saveReport/, 'отчёт должен сохраняться, а не только показываться');
});

test('окно работает без Python: рендер бита идёт через worker', () => {
  const main = fs.readFileSync(path.join(ELECTRON, 'main.js'), 'utf8');
  const host = fs.readFileSync(path.join(ELECTRON, 'render-host.js'), 'utf8');

  // Задачи пайплайна — единственное место, где нужен Python, и он ищется
  // отдельно (runtime.js), а не предполагается на месте.
  assert.match(main, /resolvePython/);
  assert.match(host, /renderInMain/, 'без worker_threads должен быть запасной путь');
});

test('меню приложения не отдаёт «перезагрузить» в релизной сборке', () => {
  const main = fs.readFileSync(path.join(ELECTRON, 'main.js'), 'utf8');

  assert.match(main, /buildMenu/, 'меню должно собираться кодом');
  assert.match(main, /isDev \? \[/, 'reload и DevTools — только в режиме разработки');
});
