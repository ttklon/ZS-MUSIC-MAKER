# План полной переделки ZS-MUSIC-MAKER → автономный хит-завод (all-in-one)

> Исторический документ. Актуальная точка входа: [аудит](docs/plan/AUDIT.md),
> [план 1000 шагов](docs/plan/PLAN_1000.md), [порядок и приёмка](docs/plan/EXECUTION.md).
> Старые версии, проценты и команды зависимостей ниже не являются текущей инструкцией установки.


> Цель: одно окно, без внешних скачиваний вручную — текст, голос, бит, микс, мастеринг, релиз — всё внутри, как будто спел/придумал сам. Сейчас `readiness 65%`, `musicgen/demucs BLOCKED`, `RVC MISSING`, текст — шаблон.

## 1. Диагностика текущего «не работает»

- **Вокал** — `modules/voice_recording` → `mic_recording BLOCKED`, `rvc_model MISSING` (нет `models/rvc/*.pth`), `prepare_voice` падает в `rvc BLOCKED` и уходит в Windows `pyttsx3` [INSTALL.md]. Пользователь слышит «виндовский» голос.
- **Текст** — `modules/lyrics/generate.py` → если `llama_cpp`/`ollama` не доступен, fallback-шаблон «тачки, ночной город» без рифмы, не складно, не актуально.
- **Бит** — `MusicGen` требует `audiocraft` + GPU 16GB [2](https://huggingface.co/spaces/facebook/MusicGen/blob/main/README.md), сейчас `BLOCKED` → процедурный `engine.js` (формульный).
- **Кнопки/заглушки** — `desktop/test` 445 тестов, но часть `FALLBACK` честно, а UI показывает панель без объяснения что делает.
- **ИИ-агенты разбросаны** — `agents/trend_scout`, `sample_hunter`, `SequentialAIRunner` существуют, но не вызываются в каждом прогоне; `bootstrap` уже добавлен, но не покрывает всё.

## 2. Принцип «всё в одной программе, докачивает само»

`app/core/bootstrap.py` уже есть (silent, без показа железа). Расширяем до `all_heavy` + прогресс в окне:

- `detect_budget()` → `ram/vram/cpu` [app/ai/hardware.py], `pick_device` оставляет 1GB запас VRAM — уже есть.
- `ensure_heavy_engines` → `pip install torch==2.5.1 audiocraft==1.3.0 demucs==4.0.1 faster-whisper` только если `network_allowed(allow_online)`.
- `ensure_models` → `tools/pull_ai_models.py --all` (13 ролей из `app/ai/registry.py`), `RVC base` (`hubert_base.pt`, `rmvpe.pt` [3](https://dibi8.com/resources/ai-tools/rvc/) 353MB), `ollama pull qwen3:4b` (2.5GB) [1](https://www.layer3labs.io/guides/how-to-run-qwen-locally) — проверено `registry.is_available`.
- `scripts/setup.cmd` уже вызывает `main.py --bootstrap --online`.
- Никаких вопросов — `silent=True`, логи в `logs/bootstrap.log`.

## 3. ИИ-агентик-проводник (вместо разбросанных вкладок)

**Где сейчас:** `app/gui/wizard` 7 шагов, `desktop/src/sections/*` 9 разделов — референсы и досье отдельно, «всё и делается» — `run`, но связи нет.

**План:** единый `WizardAgent` (LLM + детерминированные агенты):
- Шаг 0 — «Что хочешь?» → 4 вопроса (настроение, референс-артист, применять ли твой голос, длина) — ответы в `wizard_state`.
- Шаг 1 — Референсы по категориям (`демо/вайб/текст/бит`) → `modules/reference_ingest.build_style_vector` + `agents/sample_hunter` качает CC0 сэмплы [INSTALL.md].
- Шаг 2 — Досье → `modules/artist_dossier/manager.build_full_dossier` + `agents/trend_scout.scout` (hype_words/punchlines) для актуальности.
- Шаг 3 — Текст → `LLMRouter` → Ollama `qwen3:4b` [1](https://www.layer3labs.io/guides/how-to-run-qwen-locally) или `llama_cpp` GGUF, fallback `gtts` отключаем — только складно.
- Шаг 4 — Голос → запись `desktop/src/sections/recorder.js` (симуляция `ZSMM_FAKE_MIC` для тестов) → `RVC` в `.venv-rvc` (отдельное окружение из-за `numpy<=1.23.5` vs `>=1.26` [INSTALL.md]) + `rvc-python==0.1.5` [1](https://github.com/topics/rvc) + `rvc-cli` [4](https://github.com/topics/rvc).
- Шаг 5 — Бит → `MusicGen-small 300M` CPU-чанки 30с [2](https://huggingface.co/spaces/facebook/MusicGen/blob/main/README.md) если `breakthrough`, иначе `engine.js` с `humanize/variation`.
- Все шаги — `SequentialAIRunner` (уже есть `app/ai/sequential_runner.py:84`) держит одну модель в VRAM, ротатор `memory_guard 0.8GB`.

UI: `desktop/src/sections/help.js` панель «Обновления» → расширение «Агентик», `window.zsmm.agentGuide` IPC.

## 4. Конкретика по «не работает»

| Жалоба | Причина сейчас | Фикс (исследование) |
|---|---|---|
| `RVC нет` | `models/rvc/*.pth` пусто → `MISSING`, `rvc-python` требует `.venv-rvc` Python 3.10 + `hubert_base.pt` [3](https://dibi8.com/resources/ai-tools/rvc/) | `bootstrap.ensure_rvc_default_voice` скачивает `hubert_base.pt`/`rmvpe` (353MB) [5](https://github.com/sioaeko/OpenVoiceChanger) SHA256-верификация, `ZSMM_RVC_PYTHON=.venv-rvc/Scripts/python.exe` авто, demo `.pth` из `hf` если нет своего |
| `Текст пресет` | `generate_lyrics` fallback шаблон | `LLMRouter` → `ollama run qwen3:4b` [1](https://www.layer3labs.io/guides/how-to-run-qwen-locally) / `qwen2.5:7b` [2](https://alimahmoodi.net/en/articles/top-10-hugging-face-models-local-ai-gpu-ollama-guide) локально, `api` only если `OPENROUTER_API_KEY`, иначе ошибка вместо шаблона |
| `Бит ужасен` | `audiocraft BLOCKED` → процедурный | `MusicGen-small` [2](https://huggingface.co/spaces/facebook/MusicGen/blob/main/README.md) 300M + `demucs htdemucs` для стемов, `matchering` для мастеринга — всё через `bootstrap` |
| `Кнопки не работают` | `FALLBACK` без объяснения, `help.js` `help-body` пусто был | `bootstrap.wire_full_agents()` + честные `BLOCKED` → `showError` с причиной, `help` «Что работает/Чего нет» + симуляция кликов `desktop/test/fake-dom.js` уже 12/12 |
| `Микрофон не симулируется` | `capability_report` → `real_recording_possible false` | `ZSMM_FAKE_MIC=1` + `modules/voice_recording/takes.py` `test double` уже есть, `preview-server` сохраняет PCM → WAV, тесты `recorder-simulated` |

## 5. Тесты как реальный пользователь Windows 11

- `desktop/test` 445 тестов уже гоняют `node --test --test-concurrency=1` (фикс 41.3.1) — клики, `fake-dom`, `beat-service`, `writable-data`.
- `tests/test_desktop_shell.py::test_shell_suite_passes` запускает всю JS-оболочку из `pytest` — уже `175s` локально, CI 5-6 мин.
- `tools/pytest_isolated` + `ZSMM_FAKE_*`/`ZSMM_BREAKTHROUGH` — прорыв на 3.85GB RAM не фризит (чанки 30с, GC).
- Добавить: `pytest --hypothesis` DSP property, `smoke_god` + `smoke_audio` (уже в `ci.yml`).

## 6. Что качать и где искать (по запросу)

- **RVC**: `RVC-Project/Retrieval-based-Voice-Conversion-WebUI` 35k★ [1](https://github.com/topics/rvc), `rvc-python 0.1.5`, `blaisewf/rvc-cli` [1](https://github.com/topics/rvc), `sioaeko/OpenVoiceChanger` — ONNX/RVC, `hubert_base.pt` [5](https://github.com/sioaeko/OpenVoiceChanger)
- **MusicGen**: `facebook/musicgen-small/medium/large` [2](https://huggingface.co/spaces/facebook/MusicGen/blob/main/README.md), `audiocraft` pip, `transformers` `MusicgenForConditionalGeneration` [4](https://huggingface.co/spaces/facebook/MusicGen/blob/40689f86d1846eabbb8238b3be73d57bc8f2f9ef/README.md)
- **Qwen/Ollama**: `ollama run qwen3:4b` 2.5GB [1](https://www.layer3labs.io/guides/how-to-run-qwen-locally), `qwen2.5:7b` [2](https://alimahmoodi.net/en/articles/top-10-hugging-face-models-local-ai-gpu-ollama-guide), HuggingFace `Qwen/Qwen2.5-7B-GGUF`

## 7. Ближайшие шаги (1-2 недели, на ветке `arena/fa61e3de-zs-music-maker`)

1. `41.3.1` уже в релизе — concurrency фикс. Следом `41.4.0`:
   - `wizardAgent.js` + `electron/agent-service.js` (IPC `agentGuide`), `bootstrap` прогресс-бар.
   - `lyrics` → `LLMRouter` только `ollama`/`llama_cpp`, убрать шаблон fallback.
   - `RVC` → `.venv-rvc` авто-создание + `hubert_base` + demo `.pth` (если нет своего).
   - `MusicGen` CPU-чанки + `demucs` в `bootstrap` (уже частично).
2. Полный прогон: `npm test --test-concurrency=1` (445), `pytest -q` (3 budget + 6 shell), `smoke_god`, `fallback_audit`.
3. Релиз `v42.0.1` — клонирование голоса внутри приложения (`train_backend.py`, `--rvc-fork`, `--rvc-train`, кнопка «Клонировать мой голос» + индексация записи в vault). Далее `v41.4.0-fully-autonomous` — один `Portable.zip` + `Setup.exe` с `data/ai_models` закэшированными (или докачкой при первом запуске с прогрессом).

Готов начать с `wizardAgent` и `lyrics` прямо сейчас — подтверди приоритет или скажи «делай 41.4.0».
