# PLAN_v39 — ШАГ 063: безопасная проверка обновлений

Добавлен `updater.check_git_update_status()`: он читает current branch/HEAD, porcelain status и remote branch revision через `git ls-remote`, затем возвращает `up_to_date`, `update_available` или `unknown`. В report явно присутствует `working_tree_clean` и `apply_performed=false`.

`python main.py --update` подключён к этому status-only API. Он **не** запускает `fetch`, `pull`, `reset`, `checkout`, установку ZIP или rollback; применение обновления остаётся отдельной явной операцией updater-а с backup/verification.

На момент приёмки: `main.py --update` — успешно; read-only updater regression — **1 passed**; полный `pytest tests/ -q` — **132 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
