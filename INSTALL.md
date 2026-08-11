# 🛠 INSTALL — ZS Music Maker v4

## 1. Быстрый старт (Windows 11) — один клик

```
1. Распакуй ZS_Music_Maker_v4.zip в любую папку (без пробелов и кириллицы в пути!)
   Пример хорошего пути: C:\ZS_Music_Maker\
   Пример плохого пути:  C:\Мои документы\ZS Music Maker\  ← НЕ надо!

2. Двойной клик по windows_build.bat
   Первый запуск: 15–40 минут (качаются модели ~5–10 GB).
   Требуется интернет ТОЛЬКО на этапе установки.

3. Готово! Двойной клик по run.bat
   Откроется http://127.0.0.1:7860 — это твоя студия.
```

## 2. Что ставит `windows_build.bat`

- Python 3.11 (если не найден в PATH) — тихая установка в LocalAppData.
- venv в папке `venv/`.
- **Обязательные:** gradio, librosa, scipy, numpy<2, pydub, soundfile, requests, matplotlib.
- **PyTorch CPU** — стабильный fallback для RX 580 4GB.
- **torch-directml** — GPU-ускорение под AMD (опционально, тихий пропуск при провале).
- **Silero-TTS** — русский голос v3.1 (лёгкий, ~50 MB, отлично на CPU).
- **audiocraft (MusicGen)** — текстуры, работает на CPU медленно.
- **Bark, XTTS** — тяжёлые TTS (опционально).
- **rvc-python** — Retrieval-based Voice Conversion.
- **demucs** — сплиттер стемов.
- **faster-whisper** — распознавание речи.
- **matchering** — мастеринг под референс.
- **essentia** — доп. аудио-дескрипторы (опционально).
- **Ollama + llama3** — генератор текста (устанавливается системно).
- **ffmpeg** — через winget (или chocolatey / scoop).

Каждый тяжёлый пакет — со своим try/except; отсутствие одного не рушит остальное.

## 3. Проверка после установки

```
smoke_test.py          — 18/18 OK (проверка импортов + мини-тесты)
bootstrap_e2e_test.py  — сквозной прогон пайплайна без интернета
```

Оба доступны кликом из **вкладки «⑫ Диагностика»** прямо в UI.

## 4. Linux / macOS (ручная установка)

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install audiocraft --no-deps
pip install einops encodec sentencepiece hydra-core omegaconf av
pip install demucs faster-whisper matchering rvc-python
pip install git+https://github.com/suno-ai/bark.git --no-deps

# Ollama
curl https://ollama.com/install.sh | sh
ollama pull llama3

# ffmpeg (Linux)
sudo apt install ffmpeg
# ffmpeg (macOS)
brew install ffmpeg

python smoke_test.py
python main.py
```

## 5. Troubleshooting

### Ошибка «torch-directml wheel not found»
Не критично: приложение будет работать на CPU. Silero, beat_constructor и mixdown
CPU-frendly. Для MusicGen на CPU готовься к ~4-8× замедлению.

### Ошибка «No module named 'audiocraft'»
Тяжёлая либа. Пропусти генерацию текстур или установи вручную:
```
pip install audiocraft --no-deps
pip install einops encodec sentencepiece hydra-core omegaconf av
```

### Ollama не отвечает на 127.0.0.1:11434
Проверь что процесс `ollama.exe` запущен. `run.bat` пытается стартовать сам.
Если нет — установи вручную с https://ollama.com/download и выполни `ollama pull llama3`.

### FFmpeg не найден
```powershell
winget install --id=Gyan.FFmpeg -e
# или
choco install ffmpeg -y
# или
scoop install ffmpeg
```
Перезапусти терминал (обнови PATH), затем `run.bat`.

### RVC-python падает при обучении
- Убедись что записано ≥5 минут аудио (сумма всех записей в voice_vault/).
- Модель тренируется на CPU, 100 эпох ≈ 30–60 минут на 4-ядерном CPU.
- Если совсем не устанавливается — voice_convert.convert() автоматически
  переключится на offline pitch-shift fallback (не будет твоего тембра,
  но пайплайн не сломается).

### Порт 7860 занят
`run.bat` в v4 автоматически возьмёт 7861 если 7860 занят.

## 6. Полностью offline режим

После первой установки все модели закешированы. Можно отключить интернет:

- Analyzer, Groove, Beat Constructor — 100% offline.
- Silero TTS, Bark, XTTS — offline после первого запуска.
- RVC — offline.
- MusicGen — offline после первого запуска.
- Mixdown, Matchering — offline.
- **SampleHunter Online** — требует интернет (Freesound/Wikimedia).
  Используй режим **Library / Upload** для полного offline.
- **TrendScout** — требует интернет; работает и без него на локальном кэше.
- **Ollama** — offline после `ollama pull llama3`.

## 7. Обновление

Просто скачай новый ZIP, распакуй **поверх** старой папки — все твои
`voice_vault/`, `lyric_vault/`, `models/`, `samples_cache/`, `output/`
сохранятся (они в `.gitignore` и не перезапишутся).
