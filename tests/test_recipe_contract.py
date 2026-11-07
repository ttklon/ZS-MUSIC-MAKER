"""Контракт рецепта: каждое поле, которое пишет `build_recipe`, имеет читателя.

Гейт T2 (`docs/IMPROVEMENT_PLAN.md`). На момент написания теста он падал на
`quality_profile`: режим Fast/Quality/Max сохранялся в рецепт и не читался нигде,
то есть переключатель в визарде ни на что не влиял.

Проверка статическая (AST + текстовый поиск по прод-коду), потому что «мёртвое
поле» — это отсутствие ссылок, а не ошибка исполнения.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "app" / "core" / "recipe.py"
PRODUCTION_DIRS = ("app", "modules", "agents", "tools", "updater", "ui")

# Поля, которым отдельный читатель не нужен: значение уже израсходовано.
# Исключение должно быть обосновано, иначе гейт превращается в формальность.
ALLOWED_WITHOUT_READER = {
    # пишется в отчёт как идентификатор прогона, настройкой пайплайна не является
    "project_id",
    # склеивается в `theme` внутри build_recipe (см. test_extra_prompt_reaches_theme):
    # дальше по пайплайну едет объединённая тема, а не отдельное поле
    "extra_prompt",
}


def _recipe_keys() -> list[str]:
    tree = ast.parse(RECIPE.read_text(encoding="utf-8"))
    build = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_recipe"
    )
    keys: list[str] = []
    for node in ast.walk(build):
        if isinstance(node, ast.Dict):
            keys.extend(
                key.value for key in node.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            )
    return keys


def _production_sources() -> dict[str, str]:
    files = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    sources: dict[str, str] = {}
    for rel in files:
        if not (ROOT / rel).is_file():
            continue
        if not (rel.split("/", 1)[0] in PRODUCTION_DIRS or rel in ("main.py", "install.py")):
            continue
        sources[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    return sources


def _without_build_recipe(source: str) -> str:
    """Вернуть файл без тела `build_recipe` — объявление поля не считается чтением."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_recipe":
            lines = source.splitlines()
            return "\n".join(
                line for index, line in enumerate(lines, 1)
                if not (node.lineno <= index <= node.end_lineno)
            )
    return source


def _readers(key: str, sources: dict[str, str]) -> list[str]:
    hits: list[str] = []
    for rel, source in sources.items():
        if rel == "app/core/recipe.py":
            source = _without_build_recipe(source)
        if f'"{key}"' in source or f"'{key}'" in source:
            hits.append(rel)
    return hits


def test_recipe_keys_are_discovered() -> None:
    """Самопроверка парсера: если найдено <10 ключей, тест бесполезен."""
    keys = _recipe_keys()
    assert len(keys) >= 30, keys
    assert "quality_mode" in keys


def test_every_recipe_field_has_a_reader() -> None:
    sources = _production_sources()
    orphans = [
        key for key in _recipe_keys()
        if key not in ALLOWED_WITHOUT_READER and not _readers(key, sources)
    ]

    assert not orphans, (
        "поля рецепта пишутся, но нигде не читаются (настройка не влияет на результат): "
        + ", ".join(sorted(orphans))
    )


def test_extra_prompt_reaches_theme() -> None:
    """Освобождение `extra_prompt` из гейта опирается именно на этот merge."""
    from app.core.recipe import build_recipe

    recipe = build_recipe({"theme": "night drive", "user_extra_prompt": "late rain"})

    assert recipe["extra_prompt"] == "late rain"
    assert "late rain" in recipe["theme"], recipe["theme"]
    assert recipe["theme"].startswith("night drive")


def test_quality_profile_is_read_by_the_pipeline() -> None:
    """Точечная проверка того самого дефекта: режим качества должен иметь читателя."""
    sources = _production_sources()
    readers = [rel for rel in _readers("quality_profile", sources) if rel.startswith(("app/", "modules/"))]

    assert readers, "quality_profile не читается ни одним модулем пайплайна"
