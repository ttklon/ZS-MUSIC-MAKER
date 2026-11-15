# ПРОМТ ДЛЯ НЕЙРОСЕТИ — ZS-MUSIC-MAKER: автономный хит-мейкер «скачал → хит готов»

Скопируй весь промт ниже в ChatGPT / Claude / Gemini / локальную LLM — он заставит агента сделать **полный redo** проекта из одного файла, без заглушек, как реальный пользователь Win11.

---

## РОЛЬ

Ты — senior full-stack + ML engineer. Твоя задача — довести репозиторий `ttklon/ZS-MUSIC-MAKER` до состояния **fully-ready автономного хит-завода**: один Portable/Setup, после первой тихой докачки (если сеть есть) офлайн `readiness 90-100%`, каждая кнопка работает без `heavy engines unavailable` и без fallback-заглушек.

## КОНТЕКСТ ПРОЕКТА

- Репо: `ttklon/ZS-MUSIC-MAKER`, ветка `main` (HEAD `46a1795` `41.4.0`), теги `v41.3.0`/`v41.4.0` уже в `main`.
- Стек: Python 3.10+ / Electron (Node 20.19+) / PyTorch 2.5.1 CPU / audiocraft / demucs / faster-whisper / rvc-python / Ollama.
- Сейчас `readiness 65%` — кап `musicgen_runtime/demucs_runtime` до `main --bootstrap --online`. `audit_honesty CLEAN (301 файл)`, `check_snapshot_freshness 0`, `desktop npm run check` OK, `node --test --test-concurrency=1` 445/445 (156s). Требует добить до 90-100% офлайн.

## ЦЕЛЬ (критерий приёмки пользователя)

> Скачал один `ZS-Music-Maker-Windows-Portable.zip` / `Setup.exe` → двойной клик → всё делается ВНУТРИ программы, звучит так, будто пользователь сам спел/сделал: готовый трек (текст связный актуальный, голос не Windows TTS, бит качественный сгенерированный).

## ЖЁСТКИЕ ТРЕБОВАНИЯ (не обсуждаются)

1. **Одна программа, без отдельных скачиваний.** `scripts/setup.cmd` тихо делает `python main.py --bootstrap --online` + `main.py --readiness`. Дальше офлайн.
2. **Bootstrap `all_heavy`** — докачать всё тяжёлое: `HEAVY_PIP` torch 2.5.1 CPU + audiocraft 1.3.0 + demucs 4.0.1 + faster-whisper + rvc-python, `tools/pull_ai_models.py --all` (13 ролей), RVC base `hubert_base.pt (353MB) + rmvpe.pt`, `ollama pull qwen3:4b (2.5GB)`, дефолтная RVC-модель. Итого ~6-10 ГБ, gate `network_allowed(allow_online)`.
3. **Hardware silent auto** — детектор железа тихий, без бейджа/визарда/настроек ("Показывать ничего не надо, он сам должен всё понимать").
4. **Genre AI `full_agents`** — жанр авто по анализу референс-трека через `trend_scout.scout + sample_hunter + sequential_runner` везде, не ручной выбор.
5. **RVC обязательно внутри**: запись микрофона → клонирование голоса пользователя, предустановленные качественные модели, обучение ≤10 мин, инференс CPU-онли, `weights_only` safe load. Голос НЕ Windows TTS.
6. **Бит = MusicGen/AudioCraft** — `facebook/musicgen-small 300M` (или medium 1.5B опционально), EnCodec 32kHz 4 codebooks, CPU-чанки 30с, `generate`/`generate_with_chroma`.
7. **Текст = локальный LLM** — только `LLMRouter → Ollama qwen3:4b` (endpoint `http://127.0.0.1:11434/v1` OpenAI-совместим), без шаблонного `lyrics/generator.py` fallback. Если Ollama недоступен — честный `BLOCKED` без заглушки.
8. **Транскрибация = Whisper** (faster-whisper), **стемы = Demucs**.
9. **Все ИИ-агенты автономно в каждой функции**: `trend_scout`, `sample_hunter`, `hit_factory`, `sequential_runner` — `wire_full_agents()` в `modules/hit_factory/generator.py`.
10. **Ведущий ИИ-агентик-проводник**: диалог 4 вопроса (муд/артист/референсы/голос) → `Сделать хит автономно` → `window.zsmm.hitFactory.makeOne` иначе fallback `engine.js` + `switchView('beat')`. Отдельно: вкладки референсов по категориям + досье на артиста/трек + главное окно генерации текста/трека.
11. **Ни одной заглушки/нерабочей кнопки.** Каждый компонент `REAL_PASS`. `tools/audit_honesty.py` должен быть `CLEAN`.

## ЧТО УЖЕ СДЕЛАНО (не ломай)

- `app/core/bootstrap.py` — `ensure_models` разбит на `_pull_missing_roles / _ensure_rvc_base / _ensure_ollama_qwen` (≤60 строк), silent `all_heavy`.
- `modules/hit_factory/generator.py` — `wire_full_agents`, `_maybe_auto_genre` (trend_scout авто-жанр).
- `main.py` — `_maybe_silent_bootstrap`, `app/cli/commands.py:run_bootstrap(allow_online)`.
- `desktop/src/sections/agent.js` (123 строки) + `desktop/src/index.html` nav `agent` + `desktop/src/app.js` LOADERS agent + `desktop/package.json` check — вкладка Агент 4 вопроса.
- `data/desktop/readiness.json` 321 tracked 281 REAL_PASS.

## ЧТО ДОДЕЛАТЬ (чек-лист)

- [ ] **RVC fully-autonomous**: `.venv-rvc` auto-create, `rvc-python` pip, `hubert_base.pt/rmvpe.pt` автокачка, дефолтная модель предустановлена, UI запись микрофона (`ZSMM_FAKE_MIC` симуляция для тестов), клонирование ≤10 мин, инференс через `rvc_python`.
- [ ] **MusicGen CPU-чанки**: `MusicGen.get_pretrained('facebook/musicgen-small')`, 30с чанки, сшивка, fallback только честный BLOCKED (не заглушка).
- [ ] **LLM только Ollama**: убрать `lyrics/generator.py` шаблон-фолбэк, оставить `LLMRouter → ollama qwen3:4b`, `ollama serve` auto-check.
- [ ] **Demucs + Whisper** — проверить `demucs_runtime/faster-whisper` в `readiness` ≥90% после `bootstrap --online`.
- [ ] **Full agents везде**: `sample_hunter`/`sequential_runner` не только в hit_factory, но и в `beat/vocal` пайплайнах.
- [ ] **Агент-гид**: доработать `desktop/src/sections/agent.js` — 4 вопроса → хит, кнопка `Показать референсы по категориям` → `switchView('dossiers')`, прогресс-бар, `ZSMM_FAKE_MIC` toggle.
- [ ] **Убрать заглушки**: `tools/audit_honesty.py` CLEAN, `tools/check_snapshot_freshness.py 0`, `smoke_god/smoke_audio/fallback_audit` зелёные.
- [ ] **Тесты как реальный Win11-пользователь**: `scripts/setup.cmd` → `bootstrap --online` → Agent 4 вопроса → `hit_factory full_agents` → `beat + vocal` с симуляцией микрофона, `desktop --test --test-concurrency=1` 445/445, `pytest test_function_length_budget 3 passed`.

## ПРИЁМКА (авто-проверка)

```bash
python tools/audit_honesty.py  # → CLEAN (301+ файлов)
python tools/check_snapshot_freshness.py  # → 0
python main.py --readiness  # → 90-100% (после --bootstrap --online), нет heavy engines unavailable
python main.py --bootstrap --online  # → докачивает 6-10GB без ошибок, silent
python -m pytest tests/test_function_length_budget.py -q  # → 3 passed
cd desktop && npm run check  # → OK (incl. agent.js)
cd desktop && node --test --test-concurrency=1  # → 445/445 156s (без concurrency — таймаут/race, фиксить workflow)
# Ручной smoke: открыть Portable → вкладка Агент → 4 вопроса → Сделать хит → получается wav/mp3: текст связный, голос клон, бит MusicGen
```

## ИССЛЕДОВАНИЕ (обязательно перед кодом)

Проведи web_search по:
- `RVC voice conversion GitHub rvc-python 2024` → `RVC-Project/Retrieval-based-Voice-Conversion-WebUI` 32.7k stars, `rvc-python`, `Applio`, `OpenVoiceChanger` — VITS+ContentVec+RMVPE, `hubert_base.pt/rmvpe.pt`, Python 3.10+ Node 20.19+.
- `MusicGen audiocraft Hugging Face text to music 2024` → `facebook/musicgen-small 300M/medium 1.5B/melody/large 3.3B` stereo, `audiocraft` torch>=2.0, `MusicGen.get_pretrained/generate/generate_with_chroma`.
- `Ollama qwen local LLM Hugging Face 2024` → `qwen3:0.6b/4b/8b` (2.5GB/5.2GB), `ollama pull/run`, `http://127.0.0.1:11434/v1`, GGUF Q4_K_M.
Сравни форки, выбери CPU-рабочие, зафиксируй ссылки в `PLAN_FULL_REDO.md`.

## ОГРАНИЧЕНИЯ КОДА

- Функции ≤60 строк (SLACK 3), иначе `test_function_length_budget` падает → сплитуй хелперами (`_pull_missing_roles` etc.).
- Не используй `except Exception: pass` — только `_LOG.debug`.
- Один файл Portable — всё внутри, без внешних скачиваний после первого bootstrap.

## ВЫВОД

В конце: `git add -A && git commit -m "feat: fully-autonomous hit factory RVC+MusicGen+Qwen 42.x"` + `git push origin main` + `git tag v42.x` + `gh release` 6 assets. Приложи `PROMPT_FOR_NEURAL_NETWORK.md` в корень.

---

## КОМАНДЫ ДЛЯ СТАРТА (скопируй агенту)

```bash
git clone https://github.com/ttklon/ZS-MUSIC-MAKER && cd ZS-MUSIC-MAKER
cat PLAN_FULL_REDO.md
python tools/audit_honesty.py; python tools/check_snapshot_freshness.py; python main.py --readiness
# затем выполняй чек-лист выше по очереди, после каждого шага — тесты из раздела ПРИЁМКА
```
