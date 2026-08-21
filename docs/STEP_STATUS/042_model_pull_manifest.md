# PLAN_v39 — ШАГ 042: pull weights и manifest для 13 AI-ролей

## Storage and verification contract

`tools/pull_ai_models.py` теперь использует единое, не-versioned хранилище `data/ai_models/<role>/`. Для каждого pull либо явного non-download статуса записывается `manifest.json` с источником, временем, перечнем файлов, размером и SHA-256. `--verify --role <role>` повторно вычисляет hashes и отказывает при повреждении файла. Загрузка через Hugging Face client использует его cache/resume mechanism; скрипт не реализует небезопасный самодельный HTTP downloader.

| Класс ролей | Роли | Действие pull |
|---|---|---|
| GGUF, pinned upstream identity | `lyrics_llm`, `analysis_llm`, `metadata_llm` | Скачивание одного GGUF в role directory; manifest проверяет published Hugging Face LFS SHA-256 и ожидаемый byte size. |
| Hugging Face snapshot | `music_generation`, `music_stereo`, `tts_vocal`, `asr`, `audio_tagger`, `cover_art` | `snapshot_download(..., local_dir=data/ai_models/<role>)`, per-file local SHA-256 manifest. |
| Library-managed cache | `stem_splitter` | Demucs API вызывает `get_model("htdemucs")`; manifest честно фиксирует `installed_external_cache`, не копируя cache библиотеки вслепую. |
| User-supplied | `vocal_rvc` | Записывается `user_supplied` manifest и путь `data/ai_models/vocal_rvc/`; публичные voice weights не загружаются. |
| pip-only | `essentia`, `mastering_ai` | Записывается `pip_only` manifest без выдуманных weights; требуемая зависимость остаётся в `requirements_ai.txt`. |

## Registry alignment

`MODEL_REGISTRY` и LLM loader переведены с общего `models/llm` на `data/ai_models/<role>/<file>`. Поэтому успешно скачанный GGUF является тем же физическим файлом, который проверяет `registry.is_available()` и затем открывает `llama_cpp`. Для Qwen Q4_K_M закреплены размер **8,988,110,976 bytes** и LFS SHA-256 `e47ad95d…7c008`; для Llama 3.1 8B Q5_K_M — **5,732,992,416 bytes** и `14e10feb…c69c7`.[1] [2]

## Evidence and sandbox limitation

Добавлены шесть изолированных регрессий: полный набор 13 ролей, manifest hash verification, corruption detection, pip-only manifest, CLI reject unknown role/list и registry role-directory path. В сквозной регрессии обнаружен настоящий конфликт: созданный pull manifest был ошибочно помечен неизвестным в audit **versioned** data. `audit_data_inventory` уточнён: `data/ai_models/` — runtime, .gitignored weight storage и не входит в инвентарь versioned assets; отдельный тест закрепляет это ограничение. На момент приёмки: `pytest tests/test_ai_model_pull.py -q` — **6 passed**; `pytest tests/ -q` — **106 passed**; `data inventory` — **73 managed, 0 unknown, 0 invalid**; `compileall` — успешно; AST-аудит — **0 dead imports**.

`python tools/pull_ai_models.py --role mastering_ai` и последующий `--verify` успешно записали/проверили pip-only manifest. `--role lyrics_llm` честно вернул exit 1 с причиной `huggingface_hub unavailable`; download 8.99 GB GGUF не заявляется выполненным. Ни `huggingface_hub`, ни сами тяжёлые weights не установлены в sandbox, поэтому production pull/inference остаются **BLOCKED** до установки `requirements_ai.txt` и выделения диска/сети.

## References

[1]: https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF "bartowski/Qwen2.5-14B-Instruct-GGUF"
[2]: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
