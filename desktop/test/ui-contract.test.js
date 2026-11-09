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
  // `blob:` нужен для проигрывания готового WAV. С `data:`-адресом плеер
  // молчал в собранном приложении: CSP блокировал источник, а DOM-двойник
  // CSP не применяет — это увидел только настоящий браузер.
  assert.match(csp[1], /media-src 'self' blob:/, 'плееру нужен blob:, иначе бит не играется');
  assert.doesNotMatch(csp[1], /media-src[^;]*\bdata:/, 'data: в media не нужен и опаснее blob:');
  assert.doesNotMatch(csp[1], /script-src[^;]*blob:/, 'blob: не должен попадать в script-src');
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
  assert.ok(views.length >= 6, 'в навигации должно быть не меньше шести разделов');

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

test('скрипты окна делят одну глобальную область и не конфликтуют именами', () => {
  // В браузере все `<script>` из index.html исполняются в одной глобальной
  // области. Раньше каждый раздел объявлял верхнеуровневый `const W`, и
  // второй файл падал с «Identifier 'W' has already been declared» — то есть
  // из девяти разделов работал только первый. DOM-двойник этого не видел,
  // потому что грузил каждый скрипт отдельной функцией.
  const scripts = windowScripts(SRC);
  const sources = scripts.map((script) => script.source).join('\n;\n');
  assert.doesNotThrow(
    () => new Function('window', 'document', 'setTimeout', 'clearTimeout', sources),
    'скрипты не собираются в одну область видимости',
  );

  // Каждый раздел обёрнут в функцию: только так он не выбрасывает свои имена
  // в общую область. Проверяем структурно, а не по отступам.
  for (const { name, source } of scripts) {
    if (name === 'app.js' || name === 'sections/recorder.js') continue;
    const live = source
      .replace(/^\s*\/\*[\s\S]*?\*\//gm, '')
      .split('\n')
      .filter((line) => line.trim() && !line.trim().startsWith('//'))
      .join('\n');
    assert.match(live, /^\(function \(\) \{/m, `${name} не обёрнут в функцию: его имена попадут в общую область`);
    assert.match(live, /window\.ZSMM_SECTIONS\.init\w+ = function/, `${name} не регистрирует инициализатор`);
  }
});

test('каждый раздел отдаёт ровно один инициализатор, и все они на месте', () => {
  // Раздел, упавший при разборе, не оставит инициализатора — тогда `app.js`
  // скажет причину, вместо пустой панели. Проверяем, что список совпадает
  // с файлами в index.html (vocal.js своей панели не имеет).
  const html = fs.readFileSync(path.join(SRC, 'index.html'), 'utf8');
  const files = [...html.matchAll(/<script src="(sections\/[^"]+)\.js"><\/script>/g)]
    .map((match) => match[1].replace('sections/', ''))
    .filter((name) => name !== 'recorder' && name !== 'vocal');
  const expected = files.map((name) => `init${name[0].toUpperCase()}${name.slice(1)}`);

  const combined = windowScripts(SRC).map((script) => script.source).join('\n');
  for (const init of expected) {
    assert.match(combined, new RegExp(`ZSMM_SECTIONS\\.${init}\\s*=`), `нет инициализатора ${init}`);
  }
  // Каждый файл регистрирует свой инициализатор ровно один раз.
  const registrations = [...combined.matchAll(/ZSMM_SECTIONS\.(init\w+)\s*=/g)].map((m) => m[1]);
  assert.equal(new Set(registrations).size, registrations.length, `повтор инициализатора: ${registrations}`);
});

test('каждый файл окна и главного процесса не длиннее 400 строк', () => {
  // Правило проекта: длинные файлы не читаются. Раньше оно проверялось
  // только для Python, и `engine.js` успел вырасти до 843 строк при лимите
  // 400 — то есть правило нарушалось, но никто об этом не узнал.
  const MAX_LINES = 400;
  const tooLong = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith('.js')) {
        const lines = fs.readFileSync(full, 'utf8').split('\n').length;
        if (lines > MAX_LINES) tooLong.push(`${path.relative(path.resolve(__dirname, '..'), full)}: ${lines}`);
      }
    }
  };
  walk(SRC);
  walk(ELECTRON);
  assert.deepEqual(tooLong, [], `файлы длиннее ${MAX_LINES} строк: ${tooLong.join(', ')}`);
});

test('страница зовёт только существующие методы моста, включая правку данных', () => {
  // Проверяются все скрипты окна, а не только app.js: разделы зовут мост сами
  // (вокал, досье) и могут сослаться на канал, которого нет в preload.
  const block = preload.slice(preload.indexOf("exposeInMainWorld('zsmm'"));
  const exposed = new Set();
  for (const match of block.matchAll(/^\s{2}(\w+)\s*[:,]/gm)) exposed.add(match[1]);
  const used = new Set();
  for (const match of appJs.matchAll(/window\.zsmm\.(\w+)/g)) used.add(match[1]);
  // `askWith` берёт имя метода строкой: собираем и такие обращения.
  for (const match of appJs.matchAll(/askWith\('(\w+)'/g)) used.add(match[1]);
  const unknown = [...used].filter((name) => !exposed.has(name));
  assert.deepEqual(unknown, [], `окно зовёт несуществующие методы: ${unknown.join(', ')}`);
});

test('готовый WAV отдаётся плееру через blob, а не через data:', () => {
  // Регрессия: `audio.src = data:audio/wav;base64,…` не работает в собранном
  // приложении из-за CSP. Проверяем на уровне исходников, потому что
  // DOM-двойник политику безопасности не применяет.
  const beat = fs.readFileSync(path.join(SRC, 'sections', 'beat.js'), 'utf8');
  assert.doesNotMatch(beat, /data:audio\//, 'источник плеера не должен быть data:-адресом');
  assert.match(beat, /W\.blobUrl\(wavBase64\)/, 'WAV должен превращаться в blob-адрес');
  assert.match(beat, /revokeObjectURL/, 'прошлый blob надо освобождать, иначе мегабайты копятся');
  // И сам помощник действительно делает Blob из байтов.
  const app = fs.readFileSync(path.join(SRC, 'app.js'), 'utf8');
  assert.match(app, /new Blob\(\[bytes\], \{ type: mime \}\)/);
  assert.match(app, /URL\.createObjectURL/);
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
  const options = require('../electron/window-policy').windowOptions();

  // Настройки окна живут в window-policy.js: проверяем значения, а не текст
  // main.js, иначе перенос строки ломает «зелёный» тест без поломки окна.
  assert.equal(options.webPreferences.contextIsolation, true);
  assert.equal(options.webPreferences.nodeIntegration, false);
  const windowModule = fs.readFileSync(path.join(ELECTRON, 'window.js'), 'utf8');
  assert.match(windowModule, /policy\.windowOptions\(/, 'окно должно собираться по этой политике');
  assert.match(windowModule, /setWindowOpenHandler/, 'всплывающие окна должны блокироваться');
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
  const main = readElectron(['main.js', 'app-menu.js']);
  const { menuTemplate } = require('../electron/app-menu');

  assert.match(main, /buildMenu/, 'меню должно собираться кодом');
  // Проверяем сам шаблон: в сборке пунктов разработчика быть не должно.
  const roles = menuTemplate({ isDev: false }).flatMap((item) => (item.submenu || []).map((sub) => sub.role));
  assert.ok(!roles.includes('reload'), 'reload и DevTools — только в режиме разработки');
  assert.ok(!roles.includes('toggleDevTools'));
  const devRoles = menuTemplate({ isDev: true }).flatMap((item) => (item.submenu || []).map((sub) => sub.role));
  assert.ok(devRoles.includes('reload') && devRoles.includes('toggleDevTools'));
});

test('каждое поле ввода названо словами, а не только подсказкой', () => {
  // Placeholder исчезает при вводе, и Narrator в Windows 11 читает поле как
  // «поле ввода» без имени. У всех полей должна быть подпись.
  const fields = html.match(/<(input|select|textarea)\b[^>]*>/g) || [];
  const nameless = fields.filter((tag) => {
    if (/type="checkbox"/.test(tag)) return false;
    return !/aria-label=/.test(tag) && !/aria-labelledby=/.test(tag) && !/\bid="[^"]+"/.test(tag.replace(/aria-label[^>]*/, ''));
  });
  assert.deepEqual(nameless, [], 'поля без доступного имени');
  const labelled = fields.filter((tag) => /aria-label=/.test(tag));
  // Минус флажок «банк сэмплов»: он подписан текстом в <label>.
  assert.equal(labelled.length, fields.length - 1, 'имя должно быть у каждого поля, а не у половины');
  // Флажок «банк сэмплов» подписан текстом внутри <label> — это допустимо.
  assert.match(html, /<label class="muted check"><input type="checkbox" id="beat-use-bank"/);
});

test('сообщения об ошибке и о ходе работы объявлены живыми областями', () => {
  // Иначе человек с экранным диктором не узнает, что нажатие привело к
  // отказу: баннер появляется молча.
  assert.match(html, /id="error-banner"[^>]*role="alert"/);
  for (const id of ['beat-status', 'tracks-status', 'task-status']) {
    const tag = (html.match(new RegExp(`<[^>]*id="${id}"[^>]*>`)) || [])[0] || '';
    assert.match(tag, /role="status"/, `${id} должен объявлять изменения`);
    assert.match(tag, /aria-live="polite"/, `${id} должен быть вежливой живой областью`);
  }
});

test('фокус клавиатуры виден, движение отключаемо', () => {
  const css = fs.readFileSync(path.join(SRC, 'styles.css'), 'utf8');
  assert.match(css, /:focus-visible/, 'без видимой рамки фокуса Tab теряется');
  assert.match(css, /outline:\s*2px/, 'рамка фокуса должна быть видимой');
  assert.match(css, /prefers-reduced-motion/, 'анимация должна отключаться по настройке системы');
});
