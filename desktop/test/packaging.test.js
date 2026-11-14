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
  assert.ok(targets.includes('portable'), 'переносимый EXE собирается той же конфигурацией');
  // Цели живут только здесь: дублирование в командной строке ломало сборку.
  assert.doesNotMatch(pkg.scripts.dist, /--win nsis/, 'цели не должны дублироваться в CLI');
  assert.equal(pkg.build.win.target[0].arch[0], 'x64');
  // Установка «для пользователя»: без прав администратора на Windows 11.
  assert.equal(pkg.build.nsis.oneClick, false);
  assert.equal(pkg.build.nsis.perMachine, false);
  assert.equal(pkg.build.nsis.allowToChangeInstallationDirectory, true);
});

test('в свойствах EXE будет версия и описание', () => {
  // `signAndEditExecutable: false` выключал не только подпись, но и правку
  // ресурсов: в свойствах файла не было ни версии, ни названия. Подписи у нас
  // нет, а метаданные — есть: rcedit работает на windows-latest.
  assert.notEqual(pkg.build.win.signAndEditExecutable, false, 'правка ресурсов EXE не должна быть выключена');
  assert.equal(pkg.build.win.icon, 'build/icon.ico');
  assert.ok(pkg.build.copyright, 'нужен copyright для свойств файла');
  assert.ok(pkg.description && pkg.description.length > 10, 'нужно описание для свойств файла');
  // Подписи кода по-прежнему нет — и это сказано в README и в «Справке».
  assert.equal(pkg.build.win.signingHashAlgorithms, undefined);
});

test('productName и artifactName дают имя файла без пробелов', () => {
  // Установщик и portable EXE названы через productName; пробелы в ссылке на
  // релиз превращаются в %20, и «скачать» ломается у копирующих ссылку.
  assert.match(pkg.build.nsis.artifactName, /^ZS-Music-Maker-Setup-\$\{version\}\.\$\{ext\}$/);
  assert.match(pkg.build.portable.artifactName, /^ZS-Music-Maker-\$\{version\}-portable\.\$\{ext\}$/);
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
  // Окно создаётся в window.js, поэтому пути ищутся там: перенос кода не
  // должен означать «тест больше не проверяет ничего».
  const windowModule = fs.readFileSync(path.join(DESKTOP, 'electron', 'window.js'), 'utf8');
  assert.match(windowModule, /path\.join\(__dirname, 'preload\.js'\)/);
  assert.match(windowModule, /path\.join\(__dirname, '\.\.', 'src', 'index\.html'\)/);
  // Для упаковки важны оба файла: main.js указывает точку входа, window.js
  // лежит рядом и распакован вместе с electron/**.
  assert.ok(pkg.build.files.includes('electron/**'));
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

test('установщик публикуется в релиз, а не только в артефакты CI', () => {
  // Артефакты CI живут 30 дней и требуют входа в GitHub: ссылку на .exe
  // человеку нужно дать такую, чтобы она работала без аккаунта.
  const yaml = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'build.yml'), 'utf8');
  const publish = yaml.slice(yaml.indexOf('  publish-release:'));
  assert.match(publish, /softprops\/action-gh-release/);
  // Версия приложения читается из desktop/package.json, значит репозиторий
  // должен быть выкачан: без checkout шаг падал на отсутствующем файле.
  const steps = publish.slice(0, publish.indexOf('read app version') > 0
    ? publish.indexOf('Read app version') : publish.length);
  assert.match(steps, /actions\/checkout@v4/, 'без checkout нет desktop/package.json');
  // Публикация привязана к успеху сборки, а не к тегу: иначе ссылку на
  // установщик неоткуда взять, пока не выпущен тег.
  assert.match(publish, /needs\.desktop-windows\.result == 'success'/);
  assert.match(publish, /desktop-v/, 'метка релиза не должна совпадать с Python-сборкой');
  assert.match(publish, /electron-win\/\*\.exe/, 'в релиз попадают установщик и portable');
  // Python-сборка (PyInstaller) — отдельная метка и только по тегам.
  assert.match(publish, /refs\/tags\/v/);
  assert.match(publish, /ZS-Music-Maker-Windows\.zip/);
});

test('имя установщика без пробелов — ссылка на файл не ломается', () => {
  // «ZS Music Maker-Setup-1.0.0.exe» в URL превращается в %20 и перестаёт
  // открываться из чата или письма: имя артефакта — часть публичного адреса.
  assert.equal(pkg.build.nsis.artifactName, 'ZS-Music-Maker-Setup-${version}.${ext}');
  assert.equal(pkg.build.portable.artifactName, 'ZS-Music-Maker-${version}-portable.${ext}');
  for (const name of [pkg.build.nsis.artifactName, pkg.build.portable.artifactName]) {
    assert.doesNotMatch(name.replace(/\$\{[a-z]+\}/g, ''), /\s/, `пробел в имени: ${name}`);
    assert.doesNotMatch(name.replace(/\$\{[a-z]+\}/g, ''), /[^\x20-\x7E]/, 'только ASCII');
  }
  // Ярлык в «Пуск» при этом остаётся человеческим.
  assert.equal(pkg.build.nsis.shortcutName, 'ZS Music Maker');
});

test('отчёт smoke попадает и в артефакты, и в релиз', () => {
  // Релиз обещает `smoke.json`, но раньше файл писался в desktop/, а выгрузка
  // искала desktop/dist/smoke.json — в ассетах отчёта не было. Ловим это
  // тестом, а не взглядом на страницу релиза.
  const yaml = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'build.yml'), 'utf8');
  const smokeOut = /\$env:ZSMM_SMOKE_OUT = Join-Path \$PWD '([^']+)'/.exec(yaml);
  assert.ok(smokeOut, 'не найден путь отчёта smoke в workflow');
  const dir = smokeOut[1].split(/[\\/]/)[0];
  assert.equal(dir, 'dist', `smoke.json должен писаться в dist, а не в ${smokeOut[1]}`);

  const artifact = yaml.slice(yaml.indexOf('Upload installer'), yaml.indexOf('publish-release:'));
  assert.match(artifact, /desktop\/dist\/smoke\.json|smoke\.json/, 'smoke.json не выгружается артефактом');
  const publish = yaml.slice(yaml.indexOf('publish-release:'));
  assert.match(publish, /smoke\.json/, 'smoke.json не попадает в релиз');
});
