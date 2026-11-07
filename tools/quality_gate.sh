#!/usr/bin/env bash
# tools/quality_gate.sh — неактуален (T21).
#
# Скрипт требовал `mypy` и `pylint`, которых нет ни в одном requirements, а при
# их отсутствии печатал сообщение о полном успехе, то есть объявлял победу,
# ничего не проверив. Это ровно тот тип ложного успеха,
# который проект запрещает.
#
# Замены (реальные и запускаемые):
#   python -m pytest tests/ -q          # полный набор
#   python tools/fallback_audit.py      # честность fallback
#   python tools/ast_dead_imports.py    # мёртвые импорты
#   python -m tools.audit_honesty       # фейковые успехи и немые except
#   python -m tools.readiness           # процент готовности и матрица модулей
#
# Скрипт оставлен как заглушка, а не удалён: на него могут ссылаться привычки и
# внешние инструкции. Он честно сообщает об отказе и выходит с кодом 2.
set -u

cat <<'MSG'
tools/quality_gate.sh is retired: it required mypy/pylint (absent from every
requirements file) and printed a perfect score without running them.

Use instead:
  python -m pytest tests/ -q
  python tools/fallback_audit.py
  python tools/ast_dead_imports.py
  python -m tools.audit_honesty
  python -m tools.readiness
MSG
exit 2
