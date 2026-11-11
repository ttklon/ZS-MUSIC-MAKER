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
    // Атрибуты нужны там, где окно спрашивает о разметке: `tabindex="-1"` у
    // заголовка раздела или `aria-label` у кнопки без текста.
    this.attributes = {};
    this.tabIndex = -1;
  }

  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null;
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    // `tabindex="-1"` — элемент не попадает в обход Tab, но принимает фокус
    // программно. Именно так заголовок раздела забирает фокус у меню.
    if (name === 'tabindex') this.tabIndex = Number(value);
  }

  hasAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name);
  }

  /**
   * Программный фокус — как в браузере.
   *
   * Двойник DOM его не поддерживал, поэтому проверка «после переключения
   * фокус ушёл из меню в заголовок раздела» была невозможна: вызов молча
   * ничего не делал, и любой код прошёл бы её.
   */
  focus() {
    const doc = this.ownerDocument;
    if (doc && doc !== this) doc.activeElement = this;
  }

  blur() {
    const doc = this.ownerDocument;
    if (doc && doc !== this && doc.activeElement === this) doc.activeElement = null;
  }

  get className() {
    return this.classList.toString();
  }

  /**
   * `<option>` внутри `<select>` — как в браузере.
   *
   * Без этого раздел «Треки» на пустом списке артистов не мог отличить «нет
   * из чего выбирать» от «выбирать не стал», и подсказка была бы неверной.
   */
  get options() {
    return this.children.filter((child) => child.tagName === 'OPTION');
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
    // Настоящий `<select>` после замены пунктов сам выбирает первый: без
    // этого окно в тесте видело пустое значение там, где у человека уже
    // стоит артист, и «Добавить» отвечало «выберите артиста» на ровном месте.
    if (this.tagName === 'SELECT' && !this.value && this.options.length) {
      this.value = this.options[0].value;
    }
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

  /** Поддержаны только те селекторы, которые реально использует окно. */
  matches(selector) {
    if (selector === '[data-view]') return this.dataset.view !== undefined;
    if (selector.startsWith('.')) {
      return this.classList.contains(selector.slice(1));
    }
    // Селектор по тегу (`select`, `audio`): без него нельзя ни собрать все
    // списки разметки, ни проверить, что пункт попал в свой `<select>`.
    if (/^[a-zA-Z][\w-]*$/.test(selector)) return this.tagName === selector.toUpperCase();
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
    // Куда ушёл фокус: без этого нельзя проверить, что после переключения
    // раздела клавиши прокрутки относятся к содержимому, а не к меню.
    this.activeElement = null;
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
  // Какой `<select>` открыт прямо сейчас: `<option>` обязан попасть внутрь
  // него, иначе `select.value` в тесте не выставляется, а настоящий браузер
  // показывает выбранный режим. Без этого проверка «сохранённый режим вокала
  // вернулся» проходила бы на пустом значении.
  let openSelect = null;

  // `textarea` в списке: без него раздел, где есть поле текста, падал бы в
  // тесте на «нет элемента», хотя в настоящем окне поле есть. `audio` — по
  // той же причине: рендер в двойнике падал на `#beat-audio`, и проверка
  // настроек не доходила до сохранения вовсе.
  for (const match of html.matchAll(/<(button|section|div|span|p|ul|tbody|pre|h1|h2|h3|input|textarea|table|select|option|code|audio)\b([^>]*)>/g)) {
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
    // `tabindex` из разметки: заголовок раздела помечен `-1`, чтобы принимать
    // фокус программно и не попадать в обход Tab.
    const tabIndexMatch = /\stabindex="(-?\d+)"/.exec(attributes);
    if (tabIndexMatch) element.setAttribute('tabindex', tabIndexMatch[1]);
    if (hasBooleanAttribute(attributes, 'disabled')) element.disabled = true;
    if (hasBooleanAttribute(attributes, 'checked')) element.checked = true;

    // Вложенность для `<option>`: только внутри своего `<select>`.
    if (tag === 'option' && openSelect) {
      openSelect.append(element);
      continue;
    }
    body.append(element);
    if (tag === 'select') {
      openSelect = element;
      // Настоящий `<select>` показывает первый пункт. Это видно только после
      // разбора пунктов, поэтому выбор откладывается до конца функции.
    } else if (tag === 'div' || tag === 'section' || tag === 'fieldset') {
      // Разметка полей идёт блоками: новый блок закрывает предыдущий список.
      // Для `option` это неважно, а для `select` важно не «прилипнуть» к
      // чужому `<select>` из предыдущего блока.
      openSelect = null;
    }
  }

  // `<select>` без выбранного пункта в браузере показывает первый. Делаем это
  // после разбора всех `<option>`: раньше пунктов ещё не было.
  for (const select of doc.querySelectorAll('select')) {
    if (!select.value && select.options.length) select.value = select.options[0].value;
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
