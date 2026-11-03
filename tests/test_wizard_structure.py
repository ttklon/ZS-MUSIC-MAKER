# -*- coding: utf-8 -*-
"""Мастер: пять шагов, честные импорты Qt и полный словарь строк.

GUI нельзя поднять в headless-CI (нет libGL), поэтому проверки статические — но
именно они ловят класс ошибок, который до этого жил в мастере:

* `QTimer` использовался без импорта → мастер падал на старте (NameError);
* шагов было девять, хотя по плану пять;
* строки интерфейса писались мимо словаря i18n;
* ключи рецепта писались вразнобой (`artist` vs `artist_name`).

AST-проверки дешёвые и не требуют ни дисплея, ни шрифтов.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.core.i18n_data import TRANSLATIONS

ROOT = Path(__file__).resolve().parents[1]
WIZARD = ROOT / "app" / "gui" / "wizard"
WIZARD_MODULES = sorted(path for path in WIZARD.glob("*.py") if path.name != "__init__.py")

RECIPE_SOURCE = (ROOT / "app" / "core" / "recipe.py").read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
    return names


def _top_level_class_bases(tree: ast.Module) -> dict[str, ast.Module]:
    return {
        node.name: tree
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def test_wizard_has_exactly_five_steps_plus_result() -> None:
    """План 5.2: девять экранов сведены к пяти шагам (+ экран результата)."""
    window = _tree(WIZARD / "window.py")
    steps_assignment = None
    for node in ast.walk(window):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Attribute) and target.attr == "steps"
            for target in node.targets
        ):
            steps_assignment = node.value
    assert steps_assignment is not None, "список шагов мастера не найден"
    assert isinstance(steps_assignment, ast.List)
    step_classes = [
        call.func.id
        for call in steps_assignment.elts
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    ]
    assert step_classes == [
        "StepBrief",
        "StepMaterial",
        "StepVoice",
        "StepTuning",
        "StepRun",
    ]
    # экран результата создаётся отдельно и в счётчик шагов не входит
    assert "StepResult(" in (WIZARD / "window.py").read_text(encoding="utf-8")


def test_no_removed_legacy_step_modules_left() -> None:
    """Старые модули шагов удалены, а не оставлены «на всякий случай»."""
    for name in ("steps_intro.py", "steps_creative.py"):
        assert not (WIZARD / name).exists(), f"{name} должен быть удалён (слит в новые шаги)"


@pytest.mark.parametrize("module", WIZARD_MODULES, ids=lambda p: p.name)
def test_every_qt_name_is_imported(module: Path) -> None:
    """Использованное имя Qt обязано быть импортировано (ловит NameError вроде QTimer)."""
    tree = _tree(module)
    imported = _imported_names(tree)
    used = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id.startswith("Q")
        and node.id[:2] == "Q"
        and node.id[1:2].isupper()
    }
    missing = sorted(name for name in used if name not in imported)
    assert not missing, f"{module.name}: не импортированы {missing}"


@pytest.mark.parametrize("module", WIZARD_MODULES, ids=lambda p: p.name)
def test_no_bare_except_and_no_print(module: Path) -> None:
    """В GUI не должно быть `except:` без типа и отладочных print."""
    source = module.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module))
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            assert node.type is not None, f"{module.name}: голый except"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "print", f"{module.name}: print в GUI-коде"


def test_step_classes_implement_commit_and_help() -> None:
    """Каждый шаг умеет отдать рецепт и текст помощи."""
    expected = ["StepBrief", "StepMaterial", "StepVoice", "StepTuning", "StepRun", "StepResult"]
    found: dict[str, set[str]] = {}
    for module in WIZARD_MODULES:
        for name, tree in _top_level_class_bases(_tree(module)).items():
            if name in expected:
                found[name] = {
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                }
    missing_classes = [name for name in expected if name not in found]
    assert not missing_classes, f"не найдены шаги: {missing_classes}"
    for name, methods in found.items():
        assert "commit" in methods, f"{name}: нет commit()"
        assert "help_text" in methods, f"{name}: нет help_text()"


def test_wizard_recipe_keys_are_known() -> None:
    """Ключи, которые пишет мастер, понимает `app/core/recipe.py` (без опечаток)."""
    keys: set[str] = set()
    for module in WIZARD_MODULES:
        for node in ast.walk(_tree(module)):
            if not isinstance(node, ast.Assign):
                continue
            targets = [
                target
                for target in node.targets
                if isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "recipe"
            ]
            for target in targets:
                slice_node = target.slice
                if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                    keys.add(slice_node.value)
    assert keys, "мастер ничего не пишет в рецепт"
    unknown = sorted(key for key in keys if f'"{key}"' not in RECIPE_SOURCE)
    assert not unknown, f"ключи рецепта не обрабатываются recipe.py: {unknown}"


def test_all_wizard_strings_live_in_the_dictionary() -> None:
    """Ни одной строки мимо словаря: каждый t("…") существует в ru и en."""
    used: set[str] = set()
    for module in WIZARD_MODULES:
        for node in ast.walk(_tree(module)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "t"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                used.add(node.args[0].value)
    assert len(used) > 40, "ожидалось много ключей — проверь, что строки идут через t()"
    for language in ("ru", "en"):
        missing = sorted(key for key in used if key not in TRANSLATIONS.get(language, {}))
        assert not missing, f"нет перевода ({language}): {missing}"


def test_dictionary_has_no_empty_or_duplicate_conflicts() -> None:
    """Все ключи заполнены, наборы ключей ru и en совпадают."""
    ru = set(TRANSLATIONS["ru"])
    en = set(TRANSLATIONS["en"])
    assert ru == en, f"расхождение ключей: {sorted(ru ^ en)}"
    for language, table in TRANSLATIONS.items():
        empty = [key for key, value in table.items() if not str(value).strip()]
        assert not empty, f"{language}: пустые строки {empty}"


def test_wizard_uses_single_genre_source() -> None:
    """Жанры берутся из StyleRegistry, а не из списка, зашитого в GUI."""
    source = (WIZARD / "steps_brief.py").read_text(encoding="utf-8")
    assert "StyleRegistry" in source
    assert "drift_phonk" in source  # дефолт, если движок недоступен
