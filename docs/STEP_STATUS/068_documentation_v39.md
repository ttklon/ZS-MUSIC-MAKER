# PLAN_v39 — ШАГ 068: документация v39

README, INSTALL и CHANGELOG синхронизированы с `version.json` (v39.9.0). README документирует проверенные CLI-контракты `--ai-status`, `--ai --dry-run`, dossier commands, `--score`, read-only `--update` и installer `--dry-run --ai`. INSTALL подчёркивает, что AI install/model pull являются opt-in; отсутствие runtime или weights не объявляется работающей генерацией.

Добавлен `docs/DEVELOPER_GUIDE.md`: workflow разработки, правила добавления AI-ролей, sequential runner/quality gates, session security, tests и release boundary. `CHANGELOG.md` получил v39.9 summary, включая tag-gated release workflow.

Приёмка: `python main.py --help`, `python main.py --ai-status` и `python tools/pull_ai_models.py --help` успешно выполнены. Все относительные README links проверены: **2/2 существуют**. Полный `pytest tests/ -q` — **137 passed**; `compileall` успешно; AST-аудит — **0 dead imports**.
