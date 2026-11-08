'use strict';
/**
 * core/fs-node.js — файловое API для Node/Electron.
 *
 * Ошибки не бросаются наружу без нужды: каждый метод возвращает
 * `{value}` либо `{error}`, чтобы вызывающий код мог показать причину, вместо
 * того чтобы молча получить пустой результат. Единственное исключение —
 * `listDir`: его `entries` всегда массив (пустой при ошибке).
 */

const fs = require('node:fs');
const path = require('node:path');

function createNodeFs(fileSystem = fs) {
  return {
    exists(target) {
      try {
        return fileSystem.existsSync(target);
      } catch {
        return false;
      }
    },

    listDir(target) {
      try {
        const entries = fileSystem.readdirSync(target).sort();
        return { entries };
      } catch (err) {
        return { entries: [], error: err.code || err.message };
      }
    },

    readText(target) {
      try {
        return { value: fileSystem.readFileSync(target, 'utf8') };
      } catch (err) {
        return { error: `${err.code || 'ERR'}: ${err.message}` };
      }
    },

    readJson(target) {
      const text = this.readText(target);
      if (text.error) return text;
      try {
        return { value: JSON.parse(text.value) };
      } catch (err) {
        return { error: `битый JSON: ${err.message}` };
      }
    },

    /** Записать файл, создав родительские каталоги. */
    writeText(target, contents) {
      try {
        fileSystem.mkdirSync(path.dirname(target), { recursive: true });
        fileSystem.writeFileSync(target, contents, 'utf8');
        return { value: target };
      } catch (err) {
        return { error: `${err.code || 'ERR'}: ${err.message}` };
      }
    },
  };
}

module.exports = { createNodeFs };
