'use strict';
/** Generate/check product documentation from the same contract shipped to the UI. */
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '../..');
const contract = require('../src/core/product-contract');

function summary(c) {
  return [
    '<!-- product-contract:start -->',
    `**Основной продукт:** ${c.name} · ${c.platform}.`,
    `**Вход:** ${c.entry}. **Статус:** ${c.state}`,
    '', c.delivery, '', c.network, '', c.rights, '',
    ...c.scenarios.map(s => `- **${s.name} — ${s.accepted ? 'принят' : 'не принят'}.** ${s.result} ${s.blocker}`),
    '', ...c.notEquivalent.map(s => '- ' + s),
    '<!-- product-contract:end -->'
  ].join('\n');
}

function document(c) {
  return ['# Спецификация поддерживаемого продукта', '',
    '> Пакет T0001–T0010. Нормативная граница продукта, не сертификат готовности.',
    '> Источник: desktop/src/core/product-contract.js; версия приложения: version.json.', '',
    summary(c), '', '## Поставка и совместимость', '',
    `- Идентификатор: \`${c.id}\`, схема контракта: ${c.schema}.`,
    `- Установщик: \`${c.installer}\`; версия берётся из \`${c.versionSource}\`.`,
    '- NSIS x64, per-user; административные права не являются условием обычного запуска.',
    '- Portable — альтернативная упаковка того же Electron-продукта, не другая студия.',
    '- Статус подписи определяется конкретной сборкой, а не этим документом.',
    '- Изменения ветки разработки не означают, что уже опубликован новый установщик.',
    '', c.hardware, '', '## Входы и ожидаемые результаты', '',
    'Это целевые сценарии, а не обещание уже реализованного recipe API:', '',
    '1. Тема «ночной город», режим instrumental → музыка, WAV, отчёт и прослушивание; без статуса песни с вокалом.',
    '2. Своя спетая запись и инструментал → согласованный микс; исходник не изменяется.',
    '3. Текст и мелодия в режиме singing → спетый вокал; без singing backend результат BLOCKED, не TTS под видом пения.',
    '4. Изменение куплета → новая версия с сохранением предыдущего результата.',
    '', '## Ошибки и восстановление', '', c.recovery,
    '- Повреждённый или отсутствующий контракт: явная ошибка справки, без оптимистичного списка функций.',
    '- Несовпадение версии package.json и version.json: проверка поставки должна завершиться ошибкой.',
    '', '## Дополнительные входы', '', c.legacy,
    '', '## Условие финального выпуска', '', c.releaseGate,
    '', 'Подробная приёмка: [plan/EXECUTION.md](plan/EXECUTION.md).', ''
  ].join('\n');
}

function checkMetadata(c, root = ROOT) {
  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'desktop/package.json'), 'utf8'));
  const version = JSON.parse(fs.readFileSync(path.join(root, c.versionSource), 'utf8')).version;
  if (pkg.version !== version) throw new Error('Product version mismatch');
  if (pkg.build.productName !== c.name) throw new Error('Product name mismatch');
  const nsis = pkg.build.win.target.find(t => t.target === 'nsis');
  if (!nsis?.arch.includes('x64') || pkg.build.nsis.perMachine !== false) throw new Error('Installer target mismatch');
  const expected = c.installer.replace('<version>', '${version}').replace('.exe', '.${ext}');
  if (pkg.build.nsis.artifactName !== expected) throw new Error('Installer name mismatch');
  return { version, product: c.id, installer: c.installer.replace('<version>', version) };
}

function run(check = false) {
  const metadata = checkMetadata(contract);
  const readmePath = path.join(ROOT, 'README.md');
  const readme = fs.readFileSync(readmePath, 'utf8');
  const pattern = /<!-- product-contract:start -->[\s\S]*?<!-- product-contract:end -->/;
  if (!pattern.test(readme)) throw new Error('README contract markers missing');
  const outputs = [[path.join(ROOT, 'docs/PRODUCT.md'), document(contract)],
    [readmePath, readme.replace(pattern, summary(contract))]];
  for (const [file, content] of outputs) {
    if (check) {
      if (fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n') !== content.replace(/\r\n/g, '\n')) throw new Error('Stale product documentation: ' + file);
    } else fs.writeFileSync(file, content);
  }
  console.log(JSON.stringify({ ...metadata, specification_checked: true, song_generation_verified: false }));
}
if (require.main === module) run(process.argv.includes('--check'));
module.exports = { summary, document, checkMetadata };
