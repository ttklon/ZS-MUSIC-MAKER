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
│       ├── project.js  «модель проекта» для окна
│       ├── beat-options.js  границы рендера бита (общие с предпросмотром)
│       └── audio/      движок бита на JavaScript (порт modules/beat)
│           ├── rng.js          mulberry32: seed → одинаковый трек
│           ├── dsp.js          фильтры Баттерворта (сверены со scipy), огибающие
│           ├── instruments.js  синтез kick/snare/clap/hat/808/impact
│           ├── pattern-data.js ритм и акценты (сгенерировано из Python)
│           ├── patterns.js     жанр → семейство, velocity-карты
│           ├── humanize.js     микротайминг и «человечная» громкость
│           ├── variation.js    вариативность такта (пропуски, ghost-ноты)
│           ├── harmony.js      аккорды, голосоведение, пэд, стабы
│           ├── voices.js       голоса: ударные, бас, суб, гармония, FX
│           ├── arrangement.js  драматургия: секции, энергия, слои
│           ├── engine.js       сборка трека + «человечность» + стерео
│           └── wav.js          запись WAV (PCM 16 / float32)
├── scripts/
│   └── snapshot-readiness.js  снимок чисел через штатный Python-инструмент
└── test/             122 теста на `node --test`, без графической среды
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
| Бит | движок `src/core/audio/*` прямо в приложении | да, WAV собирается и играется |
| Досье | `data/artist_dossier/*/artist.json` | да, включая битые файлы |
| Запуск | `python main.py …` (белый список) | да, реальный процесс |
| Диагностика | версии среды + снимок | да |

Расчёт готовности в окне **сверяется с эталоном**: `tests/test_desktop_shell.py`
и `test/readiness.test.js` падают, если JS и `python -m tools.readiness`
дают разные числа.

## Бит собирается внутри окна

Раздел «Бит» рендерит трек в главном процессе (`zsmm:beat-render`) и отдаёт
окну готовый WAV в base64: страница ничего не считает и не получает `fs`.
Тот же движок крутится в `npm run preview`, поэтому предпросмотр в браузере
не «рисует заглушку».

Что уже перенесено из Python (`modules/beat/`, 2779 строк):

| Python | JS | Состояние |
|---|---|---|
| `drums.py` (синтез ударных) | `audio/instruments.js` | формулы и гейны те же |
| `dsp`-фильтры scipy | `audio/dsp.js` | АЧХ сверена с `scipy.signal.butter` до 0.8 дБ |
| `patterns.py` (ритм, акценты) | `audio/patterns.js` + `pattern-data.js` | таблицы сверяются тестом |
| `humanize.py` | `audio/humanize.js` | порт целиком |
| `variation.py` (`bar_variant`) | `audio/variation.js` | порт; метрика повторяемости — нет |
| `harmony.py` | `audio/harmony.js` | порт целиком |
| `voices.py` | `audio/voices.js` | без сэмплового банка |
| `dramaturgy.py` | `audio/arrangement.js` | план секций совпадает с Python |
| `arrangement.py`, `track_assembly.py` | `audio/engine.js` | дроп, мотив, ширина, длина |
| `microtime.py` | `audio/engine.js` | дрейф темпа и шум комнаты |
| запись WAV (soundfile) | `audio/wav.js` | PCM 16 бит, тот же формат |

Проверки, которые держат совпадение с Python:

- `node --test test/patterns.test.js` — ритм и акценты по всем семействам;
- `node --test test/dsp.test.js` — АЧХ фильтров против чисел из scipy;
- `node --test test/engine.test.js` — 20 с бита, пик ≤ 0.98, тот же seed →
  тот же WAV, куплет тише хука;
- `pytest tests/test_desktop_audio_port.py` — таблицы JS против
  `modules/beat/patterns.py`, проекция 120 жанров, WAV читается `soundfile`.

Замер: 20 секунд бита (140 BPM, phonk, seed 7) собираются за **≈1.5 с** в
процессе Node; Python-версия тратит на тот же рендер ≈1.0 с. Разница — цена
отсутствия numpy, а не другой алгоритм: громкость секций и спектр совпадают
с эталоном в пределах 1–2 дБ.

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
- **Сэмплового банка в окне нет.** `data/samples/` не читается: в приложении
  нет декодера WAV с диска. Движок честно помечает себя `FALLBACK` и
  синтезирует one-shot'ы — ровно как Python-версия с пустым банком.
  С банком кик/снейр/хэт были бы настоящими сэмплами и статус стал бы
  `REAL_PASS`.
- **Метрика «формульности» (`repetition_report`) осталась в Python.** Ей нужен
  FFT по тактам и отчёт, а не звук. В окне её нет — и это написано здесь, а
  не подразумевается.
- **Длинные треки рендерятся медленнее реального времени.** 3 минуты бита в
  окне — это десятки секунд работы главного процесса; индикатор прогресса
  пока не сделан, кнопка просто ждёт ответа.
