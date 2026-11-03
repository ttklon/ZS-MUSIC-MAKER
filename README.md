# ZS Music Maker — «Hit Locked Pro»

> **Версия:** `41.0.0-alpha.15` (источник правды — [`version.json`](version.json))
> **Платформа:** Windows 11, локально, без облака и платных сервисов
> **Состояние:** идёт рефакторинг v41 — см. [`docs/PLAN_v41_MASTER.md`](docs/PLAN_v41_MASTER.md)

Локальная студия одного трека: из жанра, темы и референсов собирает бит,
вокал (своя запись или TTS), микс, мастеринг под 8 стендов, обложку, тексты,
метаданные и релиз-пакет — целиком на твоём ПК.

## Быстрый старт (Windows 11)

```bat
scripts\setup.cmd            :: один раз: проверка Python, venv, зависимости, health-check
scripts\run_silent.cmd       :: запуск мастера без окна консоли (как обычное приложение)
scripts\run.cmd              :: то же, но с консолью (видно прогресс и ошибки)
scripts\build_exe.cmd        :: собрать exe (PyInstaller, onedir) в dist\
scripts\verify.cmd           :: полная проверка: тесты, смоуки, аудиты
python main.py --console     :: консольный режим
```

Мастер — пять шагов: **жанр и тема → материал → голос → тонкая настройка → запуск**.
Своя запись голоса с микрофона — основной путь; синтез и RVC помечаются как FALLBACK.
Журналы и крэш-репорты лежат в `%LOCALAPPDATA%\ZS Music Maker\logs`.

Полезные режимы:

```bat
python main.py --version
python main.py --list-genres
python main.py --god                 :: полный пайплайн одной командой
python main.py --dry-run             :: прогон без тяжёлых моделей
python main.py --health              :: что реально работает на этой машине
python main.py --readiness           :: честный процент готовности
python main.py --ai-status           :: доступность AI-ролей без загрузки весов
python main.py --score output\master.wav   :: hit-score + разбор по метрикам
python main.py --smoke               :: smoke-набор (God Mode + аудио-качество)
```

## Что честно работает

| Слой | Статус |
|---|---|
| CLI, визард, оркестратор | работает |
| Анализ/грув/бит (librosa + процедурный синтез) | работает |
| Микс + сайдчейн, мастеринг 8 стендов, true-peak −1 dBTP | работает |
| Запись и обработка своего вокала (микрофон, чистка, дабл, ad-libs) | работает |
| Обложка (Pillow), ISRC, релиз-пакет, тексты/LRC | работает |
| TTS-вокал (Silero/XTTS/bark/pyttsx3) | работает при наличии движка, иначе BLOCKED |
| RVC (свой голос модели) | BLOCKED без `.pth` модели |
| MusicGen / Demucs / SDXL / CLAP / LLM-веса | BLOCKED без пакетов и весов — не имитируются |

Отсутствующая зависимость всегда даёт `BLOCKED` с причиной, а не фейковый успех.

## Документация

| Файл | О чём |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | слои, стадии, контракты |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | как добавить стадию, жанр, сэмпл |
| [`docs/PLAN_v41_MASTER.md`](docs/PLAN_v41_MASTER.md) | план рефакторинга 2026 |
| [`CHANGELOG.md`](CHANGELOG.md) | история изменений |
| [`INSTALL.md`](INSTALL.md) | установка и зависимости |

## Проверки

```bash
python -m pytest tests/          # полный набор, см. PROJECT_STATE.md
python tools/smoke_audio.py      # 6/6 (стерео, громкость, drop)
python tools/smoke_god.py        # 8/8 (God Mode E2E → master 120 с)
python tools/fallback_audit.py   # fallback-пути
python -m tools.audit_honesty   # фейковые успехи и немые except
python -m tools.readiness
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
