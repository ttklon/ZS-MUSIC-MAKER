# PLAN_v39 — ШАГ 044: AI-first lyrics через dossier

## Runtime contract

`stage_lyrics` теперь использует `modules.lyrics_gen_ai.generate_lyrics_ai()` как основную ветвь, передавая **уже загруженный** `lyrics_llm` handle из `SequentialAIRunner`. Adapter больше не открывает вложенный `registry.use()` при наличии handle. В standalone-вызове adapter сохраняет прежнюю возможность самостоятельно получить role через registry.

| Сценарий | Результат |
|---|---|
| `lyrics_llm` доступен и output проходит gate | `source=lyrics_llm`; prompt включает тему, BPM, жанр, dossier/track reference и обязательные `user_lyrics_lines`. |
| Handle отсутствует, LLM output пустой или не проходит gate | Используется `modules.lyrics_gen.generate_lyrics`; `source=punch_lib_fallback`. |
| Любая ветвь | `lyrics.txt` сохраняется только вместе с `quality`, `reason` и явным source. |

## Release quality gate

Добавлена `validate_song_lyrics()`. Она применяет базовую lexical проверку, затем требует **200–800 слов**, минимум два `[Куплет]`/`[Verse]`, как минимум два `[Hook]`/`[Припев]`, включение всех обязательных пользовательских строк и отсутствие явных AI-заглушек (`как ии`, `as an ai` и аналогичных). Длинный структурный текст допускает vocabulary overlap до 0.08 только при соблюдении ограничения повторов строк; это исключает ложный отказ для повторяемого припева, не ослабляя обычный `validate_lyrics()`.

Punch-library fallback был измерен и скорректирован: куплет расширен до 16 строк, hook выбирается один раз и повторяется как настоящая song structure, а punch-list обходится циклически после однократного shuffle вместо случайного повторения одного бара. С двумя куплетами fallback проходит новый release contract и сохраняет `user_lyrics_lines`.

## Evidence

Добавлены регрессии: допустимый 200+ word structured lyric, отказ при неполной структуре и AI filler, а также реальный fallback без Ollama/LLM. На момент приёмки: `pytest tests/test_ai_quality.py -q` — **33 passed**; `pytest tests/ -q` — **111 passed**; `python main.py --ai --dry-run` — успешно; `compileall` — успешно; AST-аудит — **0 dead imports**.

> `lyrics_llm` weights и `llama_cpp` отсутствуют в sandbox. Реальный AI inference честно **BLOCKED**; проверены fake/adapter contract, prompt routing, release gate и работа punch-library fallback без тяжёлой роли.
