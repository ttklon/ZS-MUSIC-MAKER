# ZS Music Maker — приложение на Electron

Окно приложения — Electron. Оно не запускает Python-сервер и не ходит в сеть:
данные читаются из файлов проекта, тяжёлые операции запускаются той же
командой, что и в терминале (`python main.py …`), а вывод показывается
построчно.

```
desktop/
├── electron/
│   ├── main.js       главный процесс: окно, IPC, безопасность
│   ├── preload.js    единственный мост к системе (contextIsolation)
│   └── tasks.js      белый список задач + запуск процессов
├── src/
│   ├── index.html    разметка (CSP: без inline-скриптов и без сети)
│   ├── styles.css    оформление
│   ├── app.js        логика окна
│   └── core/
│       ├── fs-node.js  файловое API с ошибками вместо исключений
│       ├── catalog.js  жанры, пресеты, разбор inventory
│       ├── readiness.js расчёт готовности (сверен с Python)
│       └── project.js  «модель проекта» для окна
├── scripts/
│   └── snapshot-readiness.js  снимок чисел через штатный Python-инструмент
└── test/             58 тестов на `node --test`, без графической среды
```

## Запуск

```bash
cd desktop
npm install          # только для разработки: electron
npm start            # окно
npm run dev          # окно + DevTools
```

Python нужен только для раздела «Запуск» и для обновления снимка чисел:

```bash
export ZSMM_PYTHON=/путь/к/python3      # если интерпретатор не в .venv
npm run snapshot                         # обновить data/desktop/*.json|md
```

## Что действительно работает

| Раздел | Источник данных | Проверено |
|---|---|---|
| Обзор | `data/desktop/readiness.json` + inventory | да, `test/project.test.js` |
| Модули | `data/desktop/inventory.md` | да, 299 строк разбираются |
| Жанры | `config/genres_100.json`, `data/genre_presets/*.json` | да, 120 жанров |
| Досье | `data/artist_dossier/*/artist.json` | да, включая битые файлы |
| Запуск | `python main.py …` (белый список) | да, реальный процесс |
| Диагностика | версии среды + снимок | да |

Расчёт готовности в окне **сверяется с эталоном**: `tests/test_desktop_shell.py`
и `test/readiness.test.js` падают, если JS и `python -m tools.readiness`
дают разные числа.

## Чего здесь нет (честно)

- **Графическое окно не запускалось.** В окружении сборки нет
  `Xvfb`/`libgtk`/`libnss3`, поэтому Electron не стартует. Проверены:
  синтаксис всех файлов, логика (`core/*`, `tasks.js`) на настоящих данных,
  рендер `app.js` в DOM-двойнике (`test/fake-dom.js`), контракт `index.html`
  ↔ `app.js` ↔ `preload.js`. Первый реальный запуск окна — за вами:
  `cd desktop && npm install && npm start`.
- **Сборка инсталлятора (electron-builder) не выполнялась.** Конфигурация в
  `package.json` описывает AppImage/NSIS/DMG, но артефакты не собирались:
  в окружении нет сети для скачивания Electron и нет целевых платформ.
- **Аудио-движок остался на Python.** Переписаны оболочка и представление
  данных; рендер звука по-прежнему выполняет `python main.py` — окно его
  вызывает и показывает вывод. Дублировать DSP на JS никто не стал: это была
  бы вторая, непроверенная реализация.
