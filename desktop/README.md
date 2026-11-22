# Разработка основного окна ZS Music Maker

Основной продукт — Electron, Windows 11 x64, стартовый экран «Создание трека».
Поставка включает код Python-пайплайна; релизные сборки также включают Python.
Тяжёлые backend и веса не считаются установленными по факту установки EXE.

Сценарии и ограничения: [спецификация](../docs/PRODUCT.md). Источник, используемый
также в справке окна: `src/core/product-contract.js`. Версия: `../version.json`.

## Локальная разработка

Из `desktop/`:

```sh
npm install
npm run verify
npm start
npm run preview
```

Preview работает с браузерным мостом и не доказывает Electron/Python inference.
`npm run dist` собирает Windows NSIS и portable; релизный workflow дополнительно
готовит встроенный Python. Обычная локальная сборка без runtime не эквивалентна релизу.

После изменения контракта:

```sh
node scripts/product-spec.js
node scripts/product-spec.js --check
```

Не редактировать сгенерированные части README и `docs/PRODUCT.md` независимо от контракта.
Проверка документации должна падать при рассогласовании, а не автоматически скрывать его.

Исторические сведения и старое описание дерева:
[архив](../docs/history/desktop-README-before-product-contract.md). Архив не является
источником текущих возможностей. Сквозная приёмка — [EXECUTION](../docs/plan/EXECUTION.md).
