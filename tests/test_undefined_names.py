# -*- coding: utf-8 -*-
"""Имена, которые используются, но не определены: гейт и регрессия на дефект.

Повод. За один разбор нашлись четыре `NameError` одного класса: `_safe_print`
(`modules/video_edit/audio.py`), `_parse_lrc` (`render.py`), `asdict`
(`models.py`), `normalize_master_loudness` (`modules/mastering_reference.py`).
Все четыре выжили, потому что вызов сидел в широком `except Exception` или в
ветке, недостижимой на машине без matchering. Гейт `tools/ast_undefined_names.py`
ловит весь класс, а тест ниже — сам конкретный дефект, чтобы он не вернулся.

Проверяется именно рантайм: `master_ai` обязан доехать до DSP-фоллбека без
референса и вернуть результат, а не `NameError`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.ast_undefined_names import scan_all, scan_source  # noqa: E402


# --------------------------------------------------------------------------- #
#  Сканер
# --------------------------------------------------------------------------- #

def test_scanner_finds_missing_module_import() -> None:
    source = "import json\n\ndef f():\n    return json.dumps({})\n"
    assert scan_source(source) == []  # импорт есть — чисто

    broken = "def f():\n    return json.dumps({})\n"
    assert scan_source(broken) == [("f", "json")]


def test_scanner_ignores_local_and_nested_scopes() -> None:
    """Имя из внешней функции законно: это замыкание, а не NameError."""
    source = (
        "def outer():\n"
        "    limit = 3\n"
        "    def inner():\n"
        "        return limit\n"
        "    return inner\n"
    )
    assert scan_source(source) == []


def test_scanner_ignores_function_body_assignments_for_module_scope() -> None:
    """Присваивание внутри функции НЕ создаёт глобальное имя."""
    source = "def set_it():\n    value = 1\n\ndef get_it():\n    return value\n"
    assert scan_source(source) == [("get_it", "value")]


def test_scanner_knows_builtins_and_module_dunders() -> None:
    source = (
        "def f(items):\n"
        "    return len(items), __name__, print\n"
    )
    assert scan_source(source) == []


def test_scanner_accepts_module_level_bindings() -> None:
    source = (
        "import os\n"
        "from typing import Any\n"
        "LIMIT = 3\n"
        "def helper():\n    return None\n"
        "class Thing:\n    pass\n"
        "for i in range(2):\n    pass\n"
        "def use():\n"
        "    return os.getcwd(), Any, LIMIT, helper(), Thing, i\n"
    )
    assert scan_source(source) == []


def test_scanner_skips_star_imports_honestly() -> None:
    """`import *` делает проверку недоказуемой — файл пропускается, а не врёт."""
    source = "from os.path import *\n\ndef f():\n    return unknown_name\n"
    assert scan_source(source) == []


def test_scanner_skips_unexecuted_annotations() -> None:
    """С `from __future__ import annotations` аннотации не вычисляются."""
    source = (
        "from __future__ import annotations\n"
        "\n"
        "def f(x: NotImported) -> AlsoNotImported:\n"
        "    return x\n"
    )
    assert scan_source(source) == []


# --------------------------------------------------------------------------- #
#  Регрессия: master_ai вызывал normalize_master_loudness без импорта
# --------------------------------------------------------------------------- #

def test_dsp_fallback_reaches_normalization_and_returns(tmp_path) -> None:
    """Без референса мастеринг обязан вернуть результат, а не упасть в NameError."""
    from modules import mastering_reference

    sr = 44100
    t = np.arange(sr) / sr
    source = tmp_path / "in.wav"
    sf.write(source, 0.3 * np.sin(2 * np.pi * 220 * t), sr)

    result = mastering_reference.master_ai(
        str(source), str(tmp_path / "out.wav"), reference_wav=None
    )

    assert isinstance(result, dict)
    assert result.get("ok") is True, result
    assert Path(result["path"]).is_file()
    assert result.get("engine") == "mastering_pro"
    assert result.get("fallback_reason") == "no reference"
    assert result.get("loudness", {}).get("ok") is True


def test_reference_request_without_handle_does_not_crash(tmp_path, monkeypatch) -> None:
    """Референс есть, но движка нет: честный откат на DSP-чейн с причиной."""
    from modules import mastering_reference

    sr = 44100
    t = np.arange(sr) / sr
    source = tmp_path / "in.wav"
    sf.write(source, 0.3 * np.sin(2 * np.pi * 220 * t), sr)

    monkeypatch.setattr(mastering_reference, "MG_OK", False)

    result = mastering_reference.master_ai(
        str(source),
        str(tmp_path / "out.wav"),
        reference_wav=str(source),
    )

    assert result.get("ok") is True, result
    assert result.get("fallback_reason") == "matchering unavailable"


# --------------------------------------------------------------------------- #
#  Гейт по репозиторию
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "path,expected",
    [
        ("modules/mastering_reference.py", "normalize_master_loudness"),
        ("modules/voice_convert.py", "json"),
    ],
)
def test_known_undefined_names_are_fixed(path: str, expected: str) -> None:
    """Оба дефекта исправлены: имя либо импортировано, либо не используется."""
    found = {name for _, name in scan_all_check(path)}
    assert expected not in found


def scan_all_check(path: str) -> list[tuple[str, str]]:
    from tools.ast_undefined_names import scan_file

    return scan_file(ROOT / path)


def test_repo_has_no_undefined_names() -> None:
    report = scan_all()
    assert report == {}, f"используются неопределённые имена: {report}"


def test_registry_agreeing_with_engine_probe(tmp_path, monkeypatch) -> None:
    """Реестр без движка не должен выглядеть доступным.

    `is_available("mastering_ai")` проверяет `import matchering` здесь и сейчас,
    а `MG_OK` — при импорте модуля. Если реестр ответил «доступен», а движка
    нет, стадия падала с ModuleNotFoundError вместо честного
    `fallback_reason == "matchering unavailable"` (так падал CI).
    """
    import sys

    from modules import mastering_reference

    sr = 44100
    t = np.arange(sr) / sr
    source = tmp_path / "in.wav"
    sf.write(source, 0.3 * np.sin(2 * np.pi * 220 * t), sr)

    monkeypatch.setattr(mastering_reference, "MG_OK", False)
    # Прячем движок от реестра: он обязан ответить «недоступен», а не упасть.
    monkeypatch.setitem(sys.modules, "matchering", None)

    result = mastering_reference.master_ai(
        str(source), str(tmp_path / "out.wav"), reference_wav=str(source)
    )

    assert result.get("ok") is True, result
    assert result.get("fallback_reason") == "matchering unavailable"
