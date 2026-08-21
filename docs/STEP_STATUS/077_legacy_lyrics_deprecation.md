# PLAN_v39 — ШАГ 077: lyrics_gen_v8 deprecation и AI-first legacy adapter

`modules/lyrics_gen_v8.py` сохранён для Wizard/v8/v9 compatibility, но при import теперь выдаёт `DeprecationWarning` с указанием migration path к `modules.lyrics_gen_ai`. Функция `generate_lyrics_v8()` и её result shape не удалялись.

Фактический integration point — `app/core/orchestrator_v8_patch.py`. В нём добавлен `_generate_ai_lyrics()`: он вызывает `lyrics_gen_ai` только когда `registry.is_available("lyrics_llm")` возвращает true. Успешный current output преобразуется в legacy recipe fields `lyrics_text`, `chorus_lines`, `used_slang` и получает `lyrics_source=lyrics_gen_ai`. При role/runtime/model failure adapter возвращает `None`; только тогда импортируется и запускается v8 generator. Поэтому legacy import warning не возникает на AI-first path, а missing heavy runtime не маскируется как AI success.

Приёмка: четыре targeted tests проверили import warning, unavailable role, fake current-adapter conversion и v8 pipeline preference; real LLM inference не выполнялся. Полный `pytest tests/ -q` — **175 passed**; `compileall` успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
