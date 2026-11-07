"""Документация не должна врать измеримыми числами.

Гейт T3 (`docs/IMPROVEMENT_PLAN.md`). `docs/ARCHITECTURE.md` к моменту написания
говорил про «339 строк» оркестратора (факт — 400), «9 шагов» визарда (факт — 5)
и «526 тестов» (факт — 842), а также ссылался на несуществующие каталоги
`data/genres/` и `data/schema/`.

Проверяются только числа и пути, которые можно вычислить из репозитория:
никаких «на глаз». Если текст документа меняется — тест указывает, где именно
цифра разошлась с кодом.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"
ORCHESTRATOR = ROOT / "app" / "core" / "orchestrator.py"
GUI_STEPS = 5


def _architecture() -> str:
    return ARCHITECTURE.read_text(encoding="utf-8")


def test_orchestrator_line_count_is_current() -> None:
    """"N строк" рядом с `app/core/orchestrator.py` должно совпадать с фактом."""
    match = re.search(r"app/core/orchestrator\.py[^\n]*?(\d+)\s*строк", _architecture())
    assert match, "в ARCHITECTURE.md нет строки с числом строк оркестратора"

    declared = int(match.group(1))
    actual = len(ORCHESTRATOR.read_text(encoding="utf-8").splitlines())

    assert declared == actual, f"ARCHITECTURE.md: {declared} строк, фактически {actual}"


def _wizard_steps() -> int:
    """Число шагов = длина списка `self.steps` в окне визарда."""
    source = (ROOT / "app" / "gui" / "wizard" / "window.py").read_text(encoding="utf-8")
    match = re.search(r"self\.steps = \[(.*?)\]", source, re.S)
    assert match, "не найден список шагов визарда"
    return len(re.findall(r"Step(?!Base|Result)\w+\(self\)", match.group(1)))


def test_wizard_step_count_is_current() -> None:
    match = re.search(r"wizard \((\d+) шаг", _architecture())
    assert match, "в ARCHITECTURE.md нет строки с числом шагов визарда"

    actual = _wizard_steps()
    assert int(match.group(1)) == actual, f"ARCHITECTURE.md: {match.group(1)} шагов, в коде — {actual}"


def _collected_tests() -> int:
    """Сколько тестов реально собирается (с учётом параметризации)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-p", "no:cacheprovider", "tests"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match, result.stdout[-2000:] + result.stderr[-2000:]
    return int(match.group(1))


def test_declared_test_count_is_current() -> None:
    """"N тестов" должно совпадать с числом собранных тестов, а не с памятью автора."""
    match = re.search(r"(\d+)\s+тест", _architecture())
    assert match, "в ARCHITECTURE.md нет строки с числом тестов"

    declared = int(match.group(1))
    actual = _collected_tests()

    # Допуск: документ не обязан обновляться после каждого нового теста, но не
    # может отставать на сотни — это уже неправда о проекте.
    assert abs(declared - actual) <= 50, (
        f"ARCHITECTURE.md: {declared} тестов, собирается — {actual}"
    )


def test_documented_data_paths_exist() -> None:
    """Пути из таблицы данных обязаны существовать (кроме явно помеченных как план)."""
    text = _architecture()
    declared = set(re.findall(r"`(data/[a-z_]+/)`", text))
    missing = sorted(path for path in declared if not (ROOT / path).is_dir())

    assert not missing, f"ARCHITECTURE.md ссылается на несуществующие каталоги: {missing}"


def test_declared_quality_module_is_a_package() -> None:
    """`app/ai/quality.py` — это пакет; документ не должен утверждать обратное."""
    text = _architecture()
    if "`app/ai/quality.py`" not in text:
        return

    assert (ROOT / "app" / "ai" / "quality" / "__init__.py").is_file()
    assert not (ROOT / "app" / "ai" / "quality.py").exists(), (
        "в документе `app/ai/quality.py`, а в коде это пакет app/ai/quality/"
    )


# ---------------------------------------------------------------------------
#  T19: WORKFLOW.md проверяется теми же правилами, что и ARCHITECTURE.md
# ---------------------------------------------------------------------------
WORKFLOW = ROOT / "docs" / "WORKFLOW.md"
GENRES_CATALOG = ROOT / "config" / "genres_100.json"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_does_not_reference_missing_data_dirs() -> None:
    """`data/genres/<slug>.json` не существует: каталог жанров — config/genres_100.json."""
    declared: set[str] = set()
    for line in _workflow().splitlines():
        # Прямое «такого каталога нет» — не ложное утверждение о структуре.
        if " нет" in line or "не существует" in line:
            continue
        declared.update(re.findall(r"`(data/[a-z_]+/[^`]*)`", line))
    missing = [item for item in declared if not (ROOT / item.split("<")[0]).exists()]

    assert not missing, f"WORKFLOW.md ссылается на несуществующие пути: {missing}"


def test_workflow_points_at_sources_of_truth() -> None:
    text = _workflow()

    assert GENRES_CATALOG.is_file() and "config/genres_100.json" in text
    assert "data/genre_presets/" in text
    assert "app/ai/quality/" in text, "quality — это пакет app/ai/quality/, а не quality.py"


def test_docs_cross_link_the_project_inventory() -> None:
    for doc in (ARCHITECTURE, WORKFLOW):
        assert "PROJECT_INVENTORY.md" in doc.read_text(encoding="utf-8"), doc.name
