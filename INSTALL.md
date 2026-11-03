# 🛠 INSTALL — ZS Music Maker v41

> Актуальная версия: **41.0.0-alpha.16**. Единый источник правды — `version.json`.

## 1. Быстрый старт (Windows 11)

```
1. Распакуй ZIP / склонируй репозиторий в папку БЕЗ пробелов и кириллицы в пути.
   Хорошо:  C:\ZS_Music_Maker\
   Плохо:   C:\Мои документы\ZS Music Maker\

2. Установи Python 3.10+ (https://www.python.org/downloads/),
   при установке отметь «Add python.exe to PATH».

3. Открой терминал в папке проекта и выполни:
       python install.py
   Время зависит от сети и компьютера; тяжёлые модели не устанавливаются автоматически.
   Доступ к сети может также понадобиться при первом использовании или cloud-сервисам.

4. Запуск — двойной клик по `scripts\run.cmd` (или: python main.py)
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
python main.py --ai-status   # наличие зависимостей/части файлов, не тест inference
python main.py --ai --dry-run --genre phonk --theme "night"  # безопасный AI pipeline dry-run
python install.py --dry-run --ai  # показать opt-in план core+AI установки без изменений
python tools/pull_ai_models.py --help  # сверка/pull role-scoped model artifacts
```


### Модели и проверка ограничений

`python main.py --ai-status` показывает определённый бюджет оборудования и
проверки наличия, но не доказывает успешное inference; для большинства ролей
проверяется только Python-зависимость. Укажите `ZSMM_RAM_GB` и `ZSMM_VRAM_GB`
вручную, если детектор не может измерить память GPU. Список источников:
`python tools/pull_ai_models.py --list`; загрузка отдельной роли:
`python tools/pull_ai_models.py --role lyrics_llm`; проверка записанного
манифеста: `python tools/pull_ai_models.py --verify --role lyrics_llm`.

`--all` может потребовать десятки гигабайт и доступа к Hugging Face. Не
запускайте его без проверки свободного места, лицензий и совместимости ПК.
RVC требует собственной обученной модели `.pth`, которую можно выбрать в мастере
или разместить в `models/rvc/my_voice/my_voice.pth`;
загрузчик не скачивает и не проверяет пользовательский голос. Установка весов не подтверждает
качество или работу всей цепочки. Файлы моделей не входят в репозиторий.
Проверка Windows и полное AI-воспроизведение пользовательского сценария
пока не проведены: см. `PROJECT_STATE.md`.

## AMD 8 ГБ: экспериментальные локальные модели

Установленные 8 ГБ VRAM и 16 ГБ RAM — не свободная память. Закройте лишние
приложения, начинайте с 10–30 секунд и одной генерации; большой контекст,
вторая модель и длинный трек увеличивают расход памяти. CPU/offload может
помочь, но не гарантирует запуск: память, драйвер и конкретная видеокарта
остаются ограничением. Приложение проверяет свободную VRAM PyTorch перед
автовыбором CUDA/ROCm с запасом 1 ГиБ; другие процессы и серверы не входят
в управление реестра и могут продолжать занимать память.

Узнать точную модель Radeon в PowerShell:

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
```

**Текст: Ollama + Qwen3.5 4B.** Это кандидат 2026 года для сравнения, не
гарантия качества русской лирики. Установите актуальную Ollama и модель
отдельно, затем перед запуском ZS Music Maker в том же окне CMD:

```bat
ollama pull qwen3.5:4b
set ZSMM_OLLAMA_MODEL=qwen3.5:4b
set ZSMM_OLLAMA_TIMEOUT=600
scripts\run.cmd
```

Маршрутизатор ограничивает контекст 4096, ждёт локальную модель дольше и
просит Ollama выгрузить её после ответа. `ollama ps` показывает фактическое
распределение CPU/GPU во время работы. Поддержка ROCm/Vulkan зависит от
модели Radeon и версии драйвера; ускорение не подтверждено на вашем ПК. Если
модель отсутствует, в отчёте будет fallback и ошибка провайдера. Указание
`ZSMM_OLLAMA_MODEL` отключает приоритет встроенного GGUF для текстовой стадии;
если заданы облачные ключи, роутер всё ещё может выбрать облако первым. Для совместимой
сборки llama-cpp-python можно вручную задать `ZSMM_LLAMA_GPU_LAYERS` (0 —
CPU, положительное число — попытка частичного переноса слоёв, -1 — все).
Проверяйте свободную память: это не гарантия успешной GPU-загрузки.

**Инструментал: ACE-Step 1.5.** В мастере выберите «ACE-Step 1.5»; нужен
отдельно установленный и запущенный локальный API на `127.0.0.1:8001`.
По [инструкции проекта](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md#amd--rocm-gpus)
для Windows ROCm нужен Python 3.12 и отдельная ROCm-среда; не устанавливайте
CUDA PyTorch поверх неё. Сверьте свою карту с [поддержкой AMD](https://rocm.docs.amd.com/projects/install-on-windows/en/latest/reference/system-requirements.html).
У проекта также есть CPU-режим, но скорость и объём RAM нужно проверять.
Установите и запустите сервер по официальной инструкции. Для экономии памяти
используйте 2B turbo, batch 1, offload; наш запрос отключает `thinking` и
не требует второго генеративного LM для формирования аудиокодов. Например,
для совместимого сервера можно перед запуском установить переменные
`ACESTEP_OFFLOAD_TO_CPU=true`, `ACESTEP_OFFLOAD_DIT_TO_CPU=true` и
`ACESTEP_INIT_LLM=false` (способ запуска зависит от установки ACE-Step).

Это *инструментал*, не собственный голос и не разделённые стемы. При выборе
ACE-Step недоступность сервера, ошибки, пустой или неподходящий WAV приводят
к ошибке стадии, а не замене на процедурный бит. Тайм-аут по умолчанию —
7200 с (`ZSMM_ACESTEP_TIMEOUT`); после тайм-аута сервер может продолжать
генерацию. Серверы ACE-Step и Ollama работают независимо и могут занимать
память одновременно; закрывайте неиспользуемые приложения. Адаптер проверен
только на тестовом HTTP-сервере, реальные веса и Windows не проверены.
Проверьте лицензию конкретных весов и права на материалы перед публикацией;
веса MusicGen распространяются с некоммерческим ограничением.

**Свой голос.** Сначала сделайте или выберите инструментал. В окне записи
выберите этот же файл как минус и запишитесь в наушниках; файл попадёт в
Voice Vault. Для последующего полного прогона выберите в первом шаге
«Свой инструментал из файла» и тот же минус: программа не заменит его новым
битом. При импорте используется фактическая длина файла, а не ползунок.
Флажок RVC включает преобразование своей записи,
сдвиг в полутонах меняет высоту, но не создаёт эмоциональную подачу: её нужно
исполнить в исходном дубле. Выберите в шаге «Голос» свою или разрешённую
совместимую модель `.pth` и при наличии соответствующий `.index`. Если файлы
не выбраны, используются `models\rvc\my_voice\my_voice.pth` и необязательный
`my_voice.index`. Выбранный индекс не игнорируется при ошибке. Загружайте
`.pth` только из доверенного источника: загрузка весов PyTorch может выполнять
код. Нужен установленный `rvc-python` и его вспомогательные
веса. Встроенное обучение сейчас **не подключено**: внешний RVC-тренер и
полученная в нём модель должны быть проверены отдельно. Ни обучение на
вашем голосе, ни inference RVC на Windows не подтверждены. Ручной сдвиг вокала
в миллисекундах помогает подогнать дубль к минусу: плюс — позже, минус — раньше.
Автоматическая калибровка задержки устройств пока не реализована.

Во втором шаге можно вручную добавить тексты референсов и свои заметки о
сленге/темах. Выполняется только подсчёт слов и строк; полный текст референса
не передаётся LLM, но частые слова и заметки могут уйти настроенному облачному
провайдеру. Это не расшифровка аудио и не исследование актуальных трендов.
При своих готовых строках или шаблонном fallback этот контекст не используется
для генерации. Режимы качества в мастере временно отключены, поскольку пока
не управляют рендером.

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
scripts\verify.cmd         # Windows: pytest + smoke_audio + smoke_god + fallback_audit
scripts\setup.cmd          # Windows: venv + зависимости одной командой

# Или вручную (кросс-платформенно):
python -m pytest tests/                    # полный unit/regression suite
python tools/smoke_audio.py                  # аудио-качество
python tools/smoke_god.py                  # God Mode E2E
python tools/fallback_audit.py             # аудит fallback-путей
python main.py --health                    # общее здоровье системы
```

## 4. Linux / macOS (ручная установка)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# v35: ВАЖНО — ставить согласованную пару torch+torchaudio С ОДНОГО индекса.
# Нельзя смешивать torch (pytorch-индекс) и torchaudio (PyPI): бинарники ABI
# несовместимы → OSError «Could not load _torchaudio.abi3.so». Берём оба с
# pytorch-индекса с зафиксированной парой версий (проверено на Silero TTS):
pip install "torch==2.5.1" "torchaudio==2.5.1" --index-url https://download.pytorch.org/whl/cpu
# Зависимости Silero TTS (русский голос, ~50MB, CPU-friendly, REAL_PASS v35):
pip install omegaconf soundfile

# ffmpeg
sudo apt install ffmpeg        # Linux
brew install ffmpeg            # macOS

# Для тестов (нужны только разработке, на Windows для работы программы не нужны):
pip install -r requirements_dev.txt

python -m pytest tests/
python main.py --health
python main.py                 # запуск
```

## 5. Troubleshooting

### «torch-directml wheel not found»
Часть DSP-пайплайна может работать на CPU. Для MusicGen и других тяжёлых
моделей понадобятся достаточная RAM и совместимые зависимости; время и
работоспособность на конкретном компьютере не гарантируются.

### «No module named 'audiocraft'»
Тяжёлая опциональная либа для текстур. Пропусти её или установи вручную
(см. раздел 2). Без неё стадия текстур честно помечается BLOCKED, пайплайн
не ломается.

### FFmpeg не найден
```powershell
winget install --id=Gyan.FFmpeg -e    # или: choco install ffmpeg -y
```
Перезапусти терминал (обновится PATH), затем снова `scripts\run.cmd`.

### TTS / вокал недоступен (vocal_status = BLOCKED)
Вокальная стадия работает через цепочку движков: silero → xtts → bark →
pyttsx3 → gtts. Если ни один не установлен — пайплайн честно продолжает
без вокала и пишет причину в отчёт проекта.

Пример установки зависимостей Silero TTS (речь, а не проверенное пение):
```bash
pip install "torch==2.5.1" "torchaudio==2.5.1" --index-url https://download.pytorch.org/whl/cpu
pip install omegaconf soundfile
```
Первый вызов скачает веса (~59MB) в кэш torch.hub, дальше — локально.
Выбор пола: `synth(text, gender="female")` (male=aidar / female=kseniya).

Минимальный вариант (если torch не влезает): `pip install pyttsx3 gtts`
(pyttsx3 offline но роботичный; gtts требует сеть).

### RVC-конверсия тембра
RVC требует установленного `rvc-python` и обученной `.pth`-модели.
Если RVC недоступен — конверсия **не подменяется** pitch-shift'ом
(это осознанный запрет по ТЗ: честность важнее фальшивого результата);
стадия вернёт честный BLOCKED/RuntimeError с объяснением.

## 6. Полностью offline режим

Offline возможен только после отдельной установки и проверки необходимых весов;
обычная установка Python-пакетов не скачивает все модели:

- Analyzer, Groove, Beat Constructor, Mixdown, Mastering — 100% offline.
- TTS (pyttsx3/gtts) — pyttsx3 offline; gtts требует сеть (Google).
- SampleHunter Online — требует интернет (Freesound/Wikimedia);
  для полного offline используй локальную библиотеку сэмплов.
- Локальная GGUF-модель lyrics_llm требует отдельно установленных весов и
  llama-cpp-python. При её отсутствии роутер может использовать API/Ollama
  или шаблонный fallback; fallback не является LLM.

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
