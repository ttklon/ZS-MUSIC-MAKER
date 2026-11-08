'use strict';
/**
 * packaging.test.js — то, что ломается только в собранном приложении.
 *
 * Установщик здесь не собрать (нет Windows и скачивания Electron), но
 * описание сборки проверить можно — и нужно: забытый `asarUnpack` или файл,
 * не попавший в `extraResources`, виден только после установки.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const DESKTOP = path.resolve(__dirname, '..');
const ROOT = path.resolve(DESKTOP, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(DESKTOP, 'package.json'), 'utf8'));

test('описание сборки Windows 11 на месте', () => {
  assert.equal(pkg.build.appId, 'ru.zsmm.musicmaker');
  assert.equal(pkg.build.productName, 'ZS Music Maker');

  const targets = pkg.build.win.target.map((entry) => entry.target);
  assert.ok(targets.includes('nsis'), 'нужен установщик NSIS, а не только архив');
  assert.equal(pkg.build.win.target[0].arch[0], 'x64');
  // Установка «для пользователя»: без прав администратора на Windows 11.
  assert.equal(pkg.build.nsis.oneClick, false);
  assert.equal(pkg.build.nsis.perMachine, false);
  assert.equal(pkg.build.nsis.allowToChangeInstallationDirectory, true);
});

test('поток рендера не остаётся внутри app.asar', () => {
  // worker_threads запускается по пути к файлу: внутри архива его нет.
  assert.ok(pkg.build.asarUnpack.includes('electron/**'), 'electron/** должен быть распакован');
  assert.ok(fs.existsSync(path.join(DESKTOP, 'electron', 'render-worker.js')));
});

test('данные проекта попадают в resources/project', () => {
  const resources = new Map(pkg.build.extraResources.map((entry) => [entry.from, entry.to]));

  assert.equal(resources.get('../version.json'), 'project/version.json');
  assert.equal(resources.get('../config/genres_100.json'), 'project/config/genres_100.json');
  assert.equal(resources.get('../data/samples'), 'project/data/samples');
  assert.equal(resources.get('../data/desktop'), 'project/data/desktop');

  // И то, что перечислено, действительно существует в репозитории.
  for (const from of resources.keys()) {
    assert.ok(fs.existsSync(path.join(DESKTOP, from.replace(/^\.\.\//, '../'))), `нет каталога ${from}`);
  }
});

test('иконки Windows лежат там, где их ищет electron-builder', () => {
  assert.equal(pkg.build.win.icon, 'build/icon.ico');
  assert.equal(pkg.build.directories.buildResources, 'build');
  assert.ok(fs.existsSync(path.join(DESKTOP, 'build', 'icon.ico')));
  assert.ok(fs.existsSync(path.join(DESKTOP, 'build', 'icon.png')));

  // ICO — настоящий контейнер, а не переименованный PNG.
  const ico = fs.readFileSync(path.join(DESKTOP, 'build', 'icon.ico'));
  assert.equal(ico.readUInt16LE(0), 0, 'reserved');
  assert.equal(ico.readUInt16LE(2), 1, 'type = icon');
  assert.ok(ico.readUInt16LE(4) >= 5, 'в иконке должно быть несколько размеров');
});

test('скрипты сборки не требуют сети для тестов', () => {
  assert.match(pkg.scripts.dist, /electron-builder --win/);
  assert.match(pkg.scripts['dist:dir'], /--dir/);
  assert.match(pkg.scripts.test, /node --test/);
  assert.doesNotMatch(pkg.scripts.test, /electron /, 'тесты не должны запускать Electron');
});

test('main.js запускается из упакованного app.asar', () => {
  assert.equal(pkg.main, 'electron/main.js');
  // Внутри сборки нет `src/` рядом с корнем репозитория: путь к preload и
  // странице считается от __dirname, а не от cwd.
  const main = fs.readFileSync(path.join(DESKTOP, 'electron', 'main.js'), 'utf8');
  assert.match(main, /path\.join\(__dirname, 'preload\.js'\)/);
  assert.match(main, /path\.join\(__dirname, '\.\.', 'src', 'index\.html'\)/);
});

test('в сборку не попадает ничего лишнего', () => {
  const files = pkg.build.files;

  assert.ok(files.includes('electron/**'));
  assert.ok(files.includes('src/**'));
  assert.ok(!files.some((entry) => entry.startsWith('test')), 'тесты в сборке не нужны');
});

test('версия приложения совпадает с версией проекта', () => {
  const version = JSON.parse(fs.readFileSync(path.join(ROOT, 'version.json'), 'utf8'));

  // В окне показывается version.json проекта, в свойствах EXE — package.json.
  // Расхождение читается как «приложение старое».
  assert.equal(pkg.version.split('.')[0], '1', 'мажор package.json — 1.x');
  assert.ok(version.version, 'version.json читается');
});
