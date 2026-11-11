# -*- coding: utf-8 -*-
"""
Шаблонный текст: одинаковый вход даёт одинаковый текст, строки не повторяются.

Живой прогон `--god --genre phonk --theme "ночная трасса"` дал куплет, где
одна и та же строка шла дважды подряд («Клуб гудит, басы качают» ×2), а два
запуска с теми же параметрами давали разные тексты: сид считался через
`hash(...)`, а хеш строк в Python рандомизирован между процессами. Текст —
falsy-fallback, но «тот же вход, другой результат» ломает обещание
детерминизма из README (`--seed`: «same seed => identical beat/artefacts»).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.llm.fallback import local_fallback_lyrics

ROOT = Path(__file__).resolve().parents[1]


def _blocks(text: str) -> dict[str, list[str]]:
    """Разбить текст на блоки по маркерам `[verse 1]` / `[hook]`."""
    blocks: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped
            blocks[current] = []
        elif current is not None:
            blocks[current].append(stripped)
    return blocks


def test_same_input_gives_same_lyrics() -> None:
    first = local_fallback_lyrics("ночная трасса", "phonk")
    second = local_fallback_lyrics("ночная трасса", "phonk")
    assert first == second


def test_lyrics_are_stable_across_processes() -> None:
    """Главная причина: `hash()` строк меняется от процесса к процессу."""
    code = (
        "import hashlib;"
        "from modules.llm.fallback import local_fallback_lyrics;"
        "print(hashlib.sha256(local_fallback_lyrics('ночная трасса','phonk').encode()).hexdigest())"
    )
    digests = set()
    for seed in ("0", "1", "12345"):
        out = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
            check=True,
        )
        digests.add(out.stdout.strip())
    assert len(digests) == 1, f"текст зависит от процесса: {digests}"


def test_no_line_repeats_inside_a_block() -> None:
    for theme, genre in (("ночная трасса", "phonk"), ("лето", "pop"), ("дождь", "lo-fi")):
        blocks = _blocks(local_fallback_lyrics(theme, genre))
        for name, lines in blocks.items():
            assert len(lines) == len(set(lines)), f"{name}: строки повторяются — {lines}"


def test_hook_repeats_but_verses_differ() -> None:
    blocks = _blocks(local_fallback_lyrics("ночная трасса", "phonk"))
    # Припев повторяется намеренно — это припев; куплеты обязаны отличаться.
    assert blocks["[verse 1]"] != blocks["[verse 2]"]
