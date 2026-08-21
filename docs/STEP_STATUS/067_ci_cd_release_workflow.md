# PLAN_v39 — ШАГ 067: CI/CD binary artifacts и tagged release

`build.yml` уже собирал Windows `ZS-Music-Maker.exe`, smoke-тестировал `--version` и сохранял artifact 30 дней. Workflow расширен trigger-ом `v*` tags и `publish-release` job: после успешной Windows build job скачивает artifact, архивирует его и создаёт GitHub Release с generated release notes через `softprops/action-gh-release`.

Публикация выполняется **только** для `refs/tags/v*`; обычный push в `main` продолжает выполнять build/artifact без выпуска Release. Локально Windows/PyInstaller/GitHub Actions не исполнялись; проверены workflow whitespace и весь Python regression suite.

На момент приёмки: полный `pytest tests/ -q` — **137 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
