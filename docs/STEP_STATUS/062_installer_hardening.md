# PLAN_v39 — ШАГ 062: installer и dependency setup

`install.py` переписан как безопасный idempotent installer. Команды исполняются только как explicit argument lists через `subprocess` без `shell=True`; прежняя строка с `apt-get ... && ...` больше не передаётся ошибочно как один argv. Core dependencies устанавливаются по умолчанию, AI manifest — только через явный `--ai`, Linux system packages — только через `--system-deps`.

Команда `python install.py --dry-run --ai` создаёт требуемые runtime directories, при наличии копирует `.env.example` в отсутствующий `.env`, печатает core/AI installation plan и ничего не устанавливает. Unit tests фиксируют opt-in AI plan и dry-run отсутствие installer commands.

На момент приёмки: CLI dry-run — успешно; `pytest tests/test_installer.py -q` — **2 passed**; полный `pytest tests/ -q` — **131 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
