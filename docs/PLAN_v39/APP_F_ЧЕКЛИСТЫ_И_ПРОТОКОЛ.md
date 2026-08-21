================================================================================
APP_F. ЧЕКЛИСТЫ САМОПРОВЕРКИ И GIT-ПРОТОКОЛ
================================================================================

GIT-ПРОТОКОЛ (обязателен на каждом шаге):
  1. git pull origin main
  2. правки (только файлы шага)
  3. python -m compileall -q app agents modules tools updater ui main.py
  4. python -m pytest tests/ -q
  5. python main.py --help (быстрый smoke)
  6. git add -A && git commit -m "ШАГ NNN: <суть>"
  7. git push origin main
  8. git ls-remote origin main == git rev-parse HEAD

ЧЕКЛИСТ НОВОГО КОДА:
  [ ] типизация (from __future__ import annotations)
  [ ] логи через app_logger, не print
  [ ] пути через Path(__file__).resolve().parents[1] / ROOT
  [ ] no shell=True
  [ ] no secrets в коде
  [ ] registry.use() в with-блоке
  [ ] try/except c reason, без except:
  [ ] тест добавлен в tests/
  [ ] доки обновлены
  [ ] откат: git revert HEAD
