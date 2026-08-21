# PLAN_v39 — ШАГ 064: path validation и secrets

В `app.core.security_utils` добавлены `safe_identifier`, `safe_child_path` и `redact_secrets`. Identifier rejects empty, absolute, separator-containing и traversal-shaped values; generated child paths остаются непосредственно под trusted root. Redaction заменяет token-shaped GitHub/API/Bearer values до попадания в logs/UI.

Центральный `app.core.logger` получил `_SecretRedactingFilter` на file и console handlers. Он редактирует final formatted message и очищает logging args перед emission. Добавлены fuzz-like traversal tests и token redaction regression.

На момент приёмки: security tests — **2 passed**; полный `pytest tests/ -q` — **134 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**; scoped Python PAT-pattern audit — **0 matches**.
