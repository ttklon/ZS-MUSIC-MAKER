# ПРОМТ ДЛЯ НЕЙРОСЕТИ — ZS-MUSIC-MAKER: автономный хит-мейкер «скачал → хит готов»

Скопируй весь промт ниже в ChatGPT / Claude / Gemini / локальную LLM — он заставит агента сделать **полный redo** проекта из одного файла, без заглушек, как реальный пользователь Win11.

---

## РОЛЬ

Ты — senior full-stack + ML engineer. Твоя задача — довести репозиторий `ttklon/ZS-MUSIC-MAKER` до состояния **fully-ready автономного хит-завода**: один Portable/Setup, после первой тихой докачки (если сеть есть) офлайн `readiness 90-100%`, каждая кнопка работает без `heavy engines unavailable` и без fallback-заглушек.

## КОНТЕКСТ ПРОЕКТА

- Репо: `ttklon/ZS-MUSIC-MAKER`, ветка `main`, текущая версия `42.0.36` (`version.json`), теги `v41.3.0`/`v41.4.0` уже в `main`.
- Стек: Python 3.10+ / Electron (Node 20.19+) / PyTorch 2.5.1 CPU / audiocraft / demucs / faster-whisper / rvc-python / Ollama.
- Сейчас `readiness 65%` в песочнице без тяжёлых пакетов (кап `musicgen_runtime/demucs_runtime` до `main --bootstrap --online`), `weighted_sum 83.93`; с `ZSMM_FAKE_HEAVY=1` — `90.18 %` (остаётся кап микрофона). `audit_honesty CLEAN (310 файлов)`, `check_snapshot_freshness 0`, `desktop npm run check` OK, `node --test --test-concurrency=1` 456/456 (147s), `pytest` `2096 passed, 2 skipped`.

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

- `app/core/bootstrap.py` — `ensure_models` разбит на `_pull_missing_roles / _ensure_rvc_base / _ensure_ollama_qwen` (≤60 строк), silent `all_heavy`; `OLLAMA_TEXT_MODEL = qwen3:4b` (был несуществующий `qwen3.5:4b`, override `ZSMM_OLLAMA_PULL_MODEL`), `ensure_rvc_default_voice()` реально качает `f0G40k.pth` в `models/rvc/zs_default_female/` через `hf_hub_download`.
- `modules/hit_factory/generator.py` — `wire_full_agents`, `_maybe_auto_genre` (trend_scout авто-жанр).
- `app/core/agent_wiring.py` + `app/core/agent_context.py` — `wire_full_agents()/trend_context()/sample_context()/prepare_run_context()`; оркестратор один раз за прогон подмешивает тренды и сэмплы, отказ агента → строка `blocked`, трек не падает.
- `modules/beat_gen_musicgen.py` — `render_musicgen_beat()` (`facebook/musicgen-small`, EnCodec 32 кГц / 4 книги, CPU-чанки 30 с, `get_model()`→`get_pretrained`), `_pick_beat_engine` → `ace_step → musicgen → процедурка`.
- `app/core/stages/{lyrics,vocal,vocal_synth}.py` — шаблонный текст убран (без Ollama `provider="BLOCKED"`, `fallback_used=False`, `error.action` с `ollama pull qwen3:4b`); Windows TTS не подставляется (`engine="BLOCKED"`), `pyttsx3` только `ZSMM_ALLOW_SYSTEM_TTS=1`.
- `modules/agent_guide/` + `app/cli/agent_task.py` + `desktop/electron/agent-service.js` — 4 вопроса → план → `hit_factory` → отчёт `HIT/PARTIAL/FAILED` с причинами; `main.py --agent-hit`.
- `desktop/src/sections/agent.js` (123 строки) + `desktop/src/index.html` nav `agent` + `desktop/src/app.js` LOADERS agent + `desktop/package.json` check — вкладка Агент 4 вопроса.
- `data/desktop/readiness.json` 321 tracked 281 REAL_PASS.

## ЧТО ДОДЕЛАТЬ (чек-лист)

- [x] **RVC fully-autonomous**: `hubert_base.pt/rmvpe.pt` автокачка в bootstrap, дефолтная модель `f0G40k.pth`, запись микрофона в окне, **обучение через `train_backend.py`** (`ZSMM_RVC_TRAIN_CMD` или форк из `models/rvc_forks/`, успех = код 0 + непустой `.pth`), инференс через `rvc_python`. Окружение: `.venv-rvc` создаётся само (`modules/rvc_manager/venv.py`, `--rvc-setup`, кнопка «Подготовить голосовой движок»).
- [x] **MusicGen CPU-чанки**: `MusicGen.get_pretrained('facebook/musicgen-small')`, 30с чанки, сшивка, fallback только честный BLOCKED (не заглушка).
- [x] **LLM только Ollama**: убрать `lyrics/generator.py` шаблон-фолбэк, оставить `LLMRouter → ollama qwen3:4b`, `ollama serve` auto-check.
- [~] **Demucs + Whisper** — проверить `demucs_runtime/faster-whisper` в `readiness` ≥90% после `bootstrap --online`.
- [~] **Full agents везде**: `sample_hunter`/`sequential_runner` не только в hit_factory, но и в `beat/vocal` пайплайнах.
- [~] **Агент-гид**: доработать `desktop/src/sections/agent.js` — 4 вопроса → хит, кнопка `Показать референсы по категориям` → `switchView('dossiers')`, прогресс-бар, `ZSMM_FAKE_MIC` toggle.
- [x] **Убрать заглушки**: `tools/audit_honesty.py` CLEAN, `tools/check_snapshot_freshness.py 0`, `smoke_god/smoke_audio/fallback_audit` зелёные.
- [x] **Тесты как реальный Win11-пользователь**: `scripts/setup.cmd` → `bootstrap --online` → Agent 4 вопроса → `hit_factory full_agents` → `beat + vocal` с симуляцией микрофона, `desktop --test --test-concurrency=1` 445/445, `pytest test_function_length_budget 3 passed`.

## ПРИЁМКА (авто-проверка)

```bash
python tools/audit_honesty.py  # → CLEAN (310 файлов, проверено)
python tools/check_snapshot_freshness.py  # → 0
python main.py --readiness  # → 90-100% (после --bootstrap --online), нет heavy engines unavailable
python main.py --bootstrap --online  # → докачивает 6-10GB без ошибок, silent
python -m pytest tests/test_function_length_budget.py -q  # → 3 passed (проверено)
python -m pytest tests -q -k "not test_desktop"  # → 2096 passed, 2 skipped (проверено)
python main.py --agent-hit --agent-mood "ночной город"  # → мастер + честный PARTIAL без Ollama/голоса (проверено)
cd desktop && npm run check  # → OK (incl. agent.js)
cd desktop && node --test --test-concurrency=1  # → 456/456 147s (проверено; без concurrency — таймаут/race)
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

## ОТКРЫТЫЕ ПУНКТЫ (честно, для следующего прогона)

- В песочнице без сети `.venv-rvc` не создаётся (`network disabled`) — это проверяется только на машине с сетью: `python main.py --rvc-setup`.
- Обучение идёт через подтянутый форк (`--rvc-fork applio`) или `ZSMM_RVC_TRAIN_CMD`; без них честный `blocked_backend` с командой.
- `musicgen`/`demucs` требуют `--bootstrap --online`; в этой песочнице (2 CPU / 3 ГБ RAM, без torch) они `BLOCKED`, поэтому `readiness` упирается в кап 65 %.
- Микрофон в CI не проверяется физически: `mic_recording` = `BLOCKED`, пока окно не получит доступ к устройству (`ZSMM_FAKE_MIC=1` — только для тестов).
- `MusicGen` вызывается из `beat`-стадии; стемы `demucs` и `faster-whisper` подключены, но качество на CPU не измерялось (нет пакетов в песочнице).

---

## КОМАНДЫ ДЛЯ СТАРТА (скопируй агенту)

```bash
git clone https://github.com/ttklon/ZS-MUSIC-MAKER && cd ZS-MUSIC-MAKER
cat PLAN_FULL_REDO.md
python tools/audit_honesty.py; python tools/check_snapshot_freshness.py; python main.py --readiness
# затем выполняй чек-лист выше по очереди, после каждого шага — тесты из раздела ПРИЁМКА
```
