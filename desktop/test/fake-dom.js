'use strict';
/**
 * Очень маленький DOM-двойник для проверки `src/app.js` без браузера.
 *
 * Он не пытается быть браузером: поддерживается ровно то, что использует
 * окно — createElement, append, replaceChildren, classList, textContent,
 * addEventListener и простой поиск по `[data-view]`. Это позволяет поймать
 * реальные ошибки рендера (обращение к null, неверный id), не ставя jsdom
 * (в офлайн-сборке его нет).
 */

class FakeClassList {
  constructor(element) {
    this.element = element;
    this.set = new Set();
  }
  add(...names) {
    for (const name of names) this.set.add(name);
  }
  remove(...names) {
    for (const name of names) this.set.delete(name);
  }
  toggle(name, force) {
    const enabled = force === undefined ? !this.set.has(name) : Boolean(force);
    if (enabled) this.set.add(name);
    else this.set.delete(name);
    return enabled;
  }
  contains(name) {
    return this.set.has(name);
  }
  toString() {
    return [...this.set].join(' ');
  }
}

class FakeElement {
  constructor(tagName, ownerDocument) {
    this.tagName = String(tagName).toUpperCase();
    this.ownerDocument = ownerDocument;
    this.children = [];
    this.parent = null;
    this.classList = new FakeClassList(this);
    this.dataset = {};
    this._text = '';
    this.id = '';
    this.value = '';
    this.listeners = new Map();
  }

  get className() {
    return this.classList.toString();
  }

  set className(value) {
    this.classList.set = new Set(String(value).split(/\s+/).filter(Boolean));
  }

  get textContent() {
    // Текст, заданный через `textContent = '…'`, и добавленные после него
    // узлы живут вместе — как в браузере. Раньше потомки полностью вытесняли
    // текст, и двойник расходился с настоящим DOM там, где к готовой строке
    // пририсовывают кнопку («трек — не разобран [Удалить]»).
    if (this.children.length) return this._text + this.children.map((child) => child.textContent).join('');
    return this._text;
  }

  set textContent(value) {
    this.children = [];
    this._text = value === null || value === undefined ? '' : String(value);
  }

  append(...nodes) {
    for (const node of nodes) {
      if (node === null || node === undefined) continue;
      const child = typeof node === 'string' ? this.ownerDocument.createTextNode(node) : node;
      child.parent = this;
      this.children.push(child);
    }
  }

  replaceChildren(...nodes) {
    this.children = [];
    this._text = '';
    this.append(...nodes);
  }

  appendChild(node) {
    this.append(node);
    return node;
  }

  addEventListener(event, handler) {
    if (!this.listeners.has(event)) this.listeners.set(event, []);
    this.listeners.get(event).push(handler);
  }

  dispatch(event, payload = {}) {
    // `payload` передаёт поля события: `key` для клавиатуры, `dataset` для
    // клика по кнопке. Без этого обработчик Esc нельзя было проверить.
    for (const handler of this.listeners.get(event) || []) {
      handler({ type: event, target: this, ...payload });
    }
  }

  /** Все потомки (depth-first), включая сам элемент. */
  *walk() {
    yield this;
    for (const child of this.children) {
      if (child instanceof FakeElement) yield* child.walk();
    }
  }

  /** Поддержаны только те селекторы, которые реально использует app.js. */
  matches(selector) {
    if (selector === '[data-view]') return this.dataset.view !== undefined;
    if (selector.startsWith('.')) {
      return this.classList.contains(selector.slice(1));
    }
    return false;
  }

  querySelectorAll(selector) {
    return [...this.walk()].filter((node) => node !== this && node.matches(selector));
  }
}

class FakeDocument extends FakeElement {
  constructor() {
    super('#document', null);
    this.ownerDocument = this;
    this.byId = new Map();
    this.readyState = 'loading';
  }

  createElement(tag) {
    return new FakeElement(tag, this);
  }

  createTextNode(text) {
    const node = new FakeElement('#text', this);
    node._text = String(text);
    return node;
  }

  getElementById(id) {
    const found = [...this.walk()].find((node) => node.id === id);
    if (!found) throw new Error(`FakeDocument: нет элемента #${id}`);
    return found;
  }

  hasId(id) {
    return [...this.walk()].some((node) => node.id === id);
  }
}

/** Собрать документ из index.html: только id, data-view и поля ввода. */
/**
 * Есть ли булев атрибут в строке атрибутов.
 *
 * `hasBooleanAttribute(' id="x" disabled', 'disabled')` → true,
 * а `' data-disabled="1"'` → false. Именно на этой разнице всё и держится.
 */
function hasBooleanAttribute(attributes, name) {
  return new RegExp(`(^|\\s)${name}(\\s|=|$)`).test(attributes);
}

function documentFromHtml(html) {
  const doc = new FakeDocument();
  const body = doc.createElement('body');
  doc.append(body);

  // `textarea` в списке: без него раздел, где есть поле текста, падал бы в
  // тесте на «нет элемента», хотя в настоящем окне поле есть.
  for (const match of html.matchAll(/<(button|section|div|span|p|ul|tbody|pre|h1|h2|h3|input|textarea|table|select|option|code)\b([^>]*)>/g)) {
    const tag = match[1];
    const attributes = match[2];
    const element = doc.createElement(tag);
    const idMatch = /\sid="([^"]+)"/.exec(attributes);
    if (idMatch) element.id = idMatch[1];
    const viewMatch = /data-view="([^"]+)"/.exec(attributes);
    if (viewMatch) {
      element.dataset.view = viewMatch[1];
      element.classList.add('nav-item');
    }
    // Как в браузере: value из разметки — начальное значение поля, иначе
    // тест видит пустые поля там, где у пользователя уже стоит «140».
    if (tag === 'input' || tag === 'textarea') {
      const valueMatch = /\svalue="([^"]*)"/.exec(attributes);
      element.value = valueMatch ? valueMatch[1] : '';
    }
    // `<option value="record">`: без этого тест не смог бы выбрать режим,
    // который есть в разметке, и «режима нет» проходило бы незамеченным.
    if (tag === 'option') {
      const valueMatch = /\svalue="([^"]*)"/.exec(attributes);
      if (valueMatch) element.value = valueMatch[1];
    }
    // Булевы атрибуты разметки: без них тест не отличит изначально
    // заблокированную кнопку от доступной. Границу слова проверяем явно:
    // `(?=[\s>/])` не срабатывает в конце строки, а атрибут может быть
    // последним (`... id="x" disabled`).
    if (hasBooleanAttribute(attributes, 'disabled')) element.disabled = true;
    if (hasBooleanAttribute(attributes, 'checked')) element.checked = true;
    body.append(element);
  }
  return doc;
}

module.exports = { FakeDocument, FakeElement, documentFromHtml };

/**
 * Все скрипты окна в порядке подключения (см. `index.html`).
 *
 * Окно разбито на `sections/*.js`; тест рендера обязан исполнять их так же,
 * как браузер, иначе «раздел пустой» пройдёт незамеченным.
 */
function windowScripts(srcDir) {
  const fs = require('node:fs');
  const path = require('node:path');
  const html = fs.readFileSync(path.join(srcDir, 'index.html'), 'utf8');
  return [...html.matchAll(/<script src="([^"]+)"><\/script>/g)]
    .map((match) => match[1])
    // шим предпросмотра подаётся сервером, а не файлом
    .filter((name) => name !== 'preview-shim.js')
    .map((name) => ({ name, source: fs.readFileSync(path.join(srcDir, name), 'utf8') }));
}

module.exports.windowScripts = windowScripts;

/**
 * Загрузить всё окно (`app.js` + `sections/*.js`) в поддельный документ.
 *
 * @param {object} params
 * @param {string} params.srcDir  каталог `src/`
 * @param {string} params.html    содержимое index.html
 * @param {object} params.bridge  объект `window.zsmm`
 * @returns {{document: object, window: object}}
 */
function bootWindow({ srcDir, html, bridge }) {
  const document = documentFromHtml(html);
  const window = document.createElement('window');
  window.zsmm = bridge;

  // Таймеры остаются настоящими: окно ждёт таймаутов (складка настроек,
  // автоскрытие баннера), и подменять их заглушкой — значит проверять не то.
  const nativeSetTimeout = global.setTimeout;
  const nativeClearTimeout = global.clearTimeout;
  window.setTimeout = (fn, ms) => nativeSetTimeout(fn, ms);
  window.clearTimeout = (handle) => nativeClearTimeout(handle);
  global.window = window;
  global.document = document;

  // Разбор как в браузере: все `<script>` делят одну глобальную область, и
  // второй `const` с тем же именем роняет файл целиком. Раньше каждый скрипт
  // шёл отдельной функцией, поэтому ошибка «Identifier 'W' has already been
  // declared» не ловилась в тестах 3 дня — а в настоящем окне она означала,
  // что из девяти разделов работал только первый.
  const scripts = windowScripts(srcDir);
  const parse = new Function('window', 'document', 'setTimeout', 'clearTimeout',
    scripts.map((script) => script.source).join('\n;\n'));
  parse(window, document, window.setTimeout, window.clearTimeout);

  // Инициализаторы разделов — как в `app.js`: раздел, упавший при разборе,
  // не оставляет после себя инициализатора, и это видно списком.
  window.ZSMM_SECTIONS = window.ZSMM_SECTIONS || {};
  for (const init of Object.values(window.ZSMM_SECTIONS)) init();

  document.dispatch('DOMContentLoaded');
  return { document, window };
}

module.exports.bootWindow = bootWindow;
