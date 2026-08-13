# 🛠 INSTALL — ZS Music Maker v33

> Актуальная версия: **v33.0.0** (2026-08-13). Единый источник правды о версии — `version.json`.

## 1. Быстрый старт (Windows 11)

```
1. Распакуй ZIP / склонируй репозиторий в папку БЕЗ пробелов и кириллицы в пути.
   Хорошо:  C:\ZS_Music_Maker\
   Плохо:   C:\Мои документы\ZS Music Maker\

2. Установи Python 3.10+ (https://www.python.org/downloads/),
   при установке отметь «Add python.exe to PATH».

3. Открой терминал в папке проекта и выполни:
       python install.py
   Первый запуск: 10–40 минут (качаются зависимости; тяжёлые модели — опционально).
   Интернет нужен ТОЛЬКО на этапе установки.

4. Запуск — двойной клик по run.bat (или: python main.py)
   Без аргументов откроется desktop-GUI (PySide6). Если PySide6 не установлен —
   автоматически откроется Gradio-веб-интерфейс или консольный режим.
```

Полезные режимы запуска:

```
python main.py --desktop     # PySide6 desktop-окно
python main.py --gradio      # веб-интерфейс (Gradio)
python main.py --console     # консольный режим
python main.py --god         # God Mode: полный пайплайн одной командой (CLI)
python main.py --health      # проверка здоровья системы
python main.py --readiness   # чек-лист готовности по ТЗ
```

## 2. Что ставит `install.py`

- **Обязательные зависимости** из `requirements.txt` (PySide6, gradio, librosa,
  scipy, numpy, pydub, soundfile, matplotlib, mido, pyloudnorm, pedalboard,
  pyttsx3, gtts, sounddevice, Pillow, mutagen, requests и др.).
- **PyTorch CPU** — стабильный fallback для RX 580 4GB (опционально).
- Создание рабочих каталогов (`output/`, `models/`, `samples_cache/`, `checkpoints/`).
- Проверку GPU/CPU и базовых моделей.

Каждый тяжёлый пакет ставится с отдельной обработкой ошибок — отсутствие
одного не рушит остальное.

### Опциональные тяжёлые пакеты (ставятся вручную при необходимости)

```bash
# AMD DirectML (только если у тебя AMD GPU на Windows)
pip install torch-directml==0.2.5

# MusicGen (текстуры) — тяжёлый, на CPU медленно
pip install audiocraft --no-deps
pip install einops encodec sentencepiece hydra-core omegaconf av

# Дополнительно: сплиттер стемов, распознавание речи, мастеринг под референс
pip install demucs faster-whisper matchering

# Тяжёлые TTS (опционально): XTTS, Bark
pip install TTS
pip install git+https://github.com/suno-ai/bark.git --no-deps

# ffmpeg (нужен pydub/demucs)
winget install --id=Gyan.FFmpeg -e     # Windows
```

## 3. Проверка после установки

```
verify.bat                 # Windows: pytest + smoke_v26 + smoke_v29
run_all_smoke.bat          # Windows: прогон всех tools/smoke_v*.py

# Или вручную (кросс-платформенно):
python -m pytest tests/                    # юнит-тесты DSP
python tools/smoke_v26.py                  # аудио-качество
python tools/smoke_v29.py                  # God Mode E2E
python tools/fallback_audit.py             # аудит fallback-путей
python main.py --health                    # общее здоровье системы
```

## 4. Linux / macOS (ручная установка)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# ffmpeg
sudo apt install ffmpeg        # Linux
brew install ffmpeg            # macOS

python -m pytest tests/
python main.py --health
python main.py                 # запуск
```

## 5. Troubleshooting

### «torch-directml wheel not found»
Не критично: приложение работает на CPU. Beat constructor, mixdown и
mastering — CPU-friendly. MusicGen на CPU — примерно 4–8× медленнее.

### «No module named 'audiocraft'»
Тяжёлая опциональная либа для текстур. Пропусти её или установи вручную
(см. раздел 2). Без неё стадия текстур честно помечается BLOCKED, пайплайн
не ломается.

### FFmpeg не найден
```powershell
winget install --id=Gyan.FFmpeg -e    # или: choco install ffmpeg -y
```
Перезапусти терминал (обновится PATH), затем снова `run.bat`.

### TTS / вокал недоступен (vocal_status = BLOCKED)
Вокальная стадия работает через цепочку движков: silero → xtts → bark →
pyttsx3 → gtts. Если ни один не установлен — пайплайн честно продолжает
без вокала и пишет причину в отчёт проекта. Минимальный вариант:
`pip install pyttsx3 gtts` (лёгкие, CPU).

### RVC-конверсия тембра
RVC требует установленного `rvc-python` и обученной `.pth`-модели.
Если RVC недоступен — конверсия **не подменяется** pitch-shift'ом
(это осознанный запрет по ТЗ: честность важнее фальшивого результата);
стадия вернёт честный BLOCKED/RuntimeError с объяснением.

## 6. Полностью offline режим

После первой установки модели закешированы, интернет можно отключить:

- Analyzer, Groove, Beat Constructor, Mixdown, Mastering — 100% offline.
- TTS (pyttsx3/gtts) — pyttsx3 offline; gtts требует сеть (Google).
- SampleHunter Online — требует интернет (Freesound/Wikimedia);
  для полного offline используй локальную библиотеку сэмплов.
- LLM-генерация текстов — требует API-ключи (см. ниже); без ключей
  работает встроенный офлайн-генератор лирики.

### Переменные окружения (опционально)

| Переменная | Назначение |
|---|---|
| `OPENROUTER_API_KEY` | LLM-тексты через OpenRouter |
| `XAI_API_KEY` / `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Альтернативные LLM-провайдеры |
| `ZSMM_NO_CHECKPOINTS=1` | Отключить чекпоинты пайплайна |
| `ZSMM_PROGRAM_DIR` / `ZSMM_USER_DIR` | Переопределить каталоги updater'а |

## 7. Обновление

Скачай новый ZIP / сделай `git pull` — твои `voice_vault/`, `lyric_vault/`,
`models/`, `samples_cache/`, `output/` сохранятся (они в `.gitignore`).
