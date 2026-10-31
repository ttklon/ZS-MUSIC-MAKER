# -*- coding: utf-8 -*-
"""
modules/lyrics/memory.py — Lyric Vault: память сгенерированных текстов.

`lyric_vault/lyrics_memory.jsonl` хранит историю идей; каталог создаётся
лениво, при первой записи. Чтение никогда не падает: повреждённые строки
попадают в диагностику, а не в трек.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

VAULT_DIR = ROOT / "lyric_vault"

LYRIC_MEMORY = VAULT_DIR / "lyrics_memory.jsonl"

SLANG_FILE = VAULT_DIR / "slang.txt"


def _load_lyric_memory_with_errors() -> tuple[list, list[str]]:
    """Load valid JSONL memories while retaining line-level recovery diagnostics."""
    if not LYRIC_MEMORY.exists():
        return [], []
    memories: list = []
    errors: list[str] = []
    for line_number, line in enumerate(LYRIC_MEMORY.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            memories.append(json.loads(line))
        except json.JSONDecodeError as error:
            errors.append(f"line {line_number}: {type(error).__name__}: {error}")
    return memories, errors


def _load_lyric_memory() -> list:
    """Return valid lyric memories with the historical list-only private contract."""
    return _load_lyric_memory_with_errors()[0]


def _save_lyric_memory(entry: dict) -> None:
    entry["timestamp"] = time.time()
    with open(LYRIC_MEMORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_lyric_memory(limit: int = 20) -> list:
    """Вернуть последние валидные строки из Lyric Vault."""
    memories = _load_lyric_memory()
    return list(reversed(memories))[:limit]


def get_lyric_memory_diagnostics(limit: int = 20) -> dict:
    """Return recent valid memories together with non-fatal JSONL recovery diagnostics."""
    memories, read_errors = _load_lyric_memory_with_errors()
    return {"memories": list(reversed(memories))[:limit], "read_errors": read_errors}
