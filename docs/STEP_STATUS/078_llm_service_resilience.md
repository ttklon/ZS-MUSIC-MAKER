# PLAN_v39 — ШАГ 078: общий LLM client retry/timeout/circuit breaker

`app/ai/llm_service.py` заменён на общий устойчивый service для llama-cpp-compatible handles. Он сохраняет string API `complete()` и добавляет `complete_with_report()` с structured metadata. Контракт: default timeout **600 s**, `retries=2` (до трёх попыток), daemon-thread bounded wait для зависшего handle, и process-local circuit breaker после трёх consecutive failed requests. Timeout, empty completion, missing handle и open circuit возвращают честный empty text/report вместо поддельного content.

Chat completion interface по-прежнему поддерживается; при его ошибке service сохраняет прежнюю совместимость с callable llama interface. `modules/llm_clients_v15.py` получил `complete_local_handle()`, который делегирует local handle shared service и возвращает router-style dict без local-template подмены. Cloud provider router не менялся.

Приёмка на fake handles: retry recovery именно на третьей попытке, bounded timeout, circuit open на третьем failed request, chat→callable fallback и идентичный text shared service/v15 wrapper. Реальный llama-cpp/model/network run не выполнялся. Полный `pytest tests/ -q` — **180 passed**; `compileall` успешно; AST-аудит — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
