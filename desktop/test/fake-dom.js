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
    if (this.children.length) return this.children.map((child) => child.textContent).join('');
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

  dispatch(event) {
    for (const handler of this.listeners.get(event) || []) handler({ type: event, target: this });
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
function documentFromHtml(html) {
  const doc = new FakeDocument();
  const body = doc.createElement('body');
  doc.append(body);

  for (const match of html.matchAll(/<(button|section|div|span|p|ul|tbody|pre|h1|h2|h3|input|table|select|option|code)\b([^>]*)>/g)) {
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
    if (tag === 'input') element.value = '';
    body.append(element);
  }
  return doc;
}

module.exports = { FakeDocument, FakeElement, documentFromHtml };
