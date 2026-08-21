# -*- coding: utf-8 -*-
"""Аудит versioned-данных ZS Music Maker.

Инструмент читает каждый файл из ``data/``, валидирует его формат и относит
к явной категории жизненного цикла. Это предотвращает незаметное накопление
нечитаемых seed-ов, тестовых manifest-ов и кэшей между релизами.

Запуск:
    python tools/audit_data_inventory.py
    python tools/audit_data_inventory.py --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

# Каталоги содержат versioned assets, которые загружаются по glob или служат
# проверяемыми seed/fixture-данными для соответствующих runtime-компонентов.
MANAGED_DIRECTORIES = {
    "genre_presets": "genre preset catalog",
    "kpi_history_seed": "KPI schema seed",
    "prompts": "prompt catalog",
    "reference_cache": "reference-analysis cache fixture",
    "sample_manifests": "sample manifest fixture",
}
# Runtime weights и их integrity manifests создаются pull-инструментом, находятся
# под .gitignore и не входят в инвентарь versioned data-assets.
RUNTIME_DIRECTORIES = {"ai_models", "artist_dossier"}

MANAGED_FILES = {
    "README.md": "data catalog documentation",
    "tutorial_settings.json": "onboarding settings",
    "hw_profile.json": "hardware profile seed",
    ".gitkeep": "directory retention marker",
}


def classify_data_file(path: Path, data_dir: Path = DATA_DIR) -> str | None:
    """Вернуть назначение versioned data-файла или ``None`` для неизвестного."""
    relative = path.relative_to(data_dir)
    if relative.name in MANAGED_FILES:
        return MANAGED_FILES[relative.name]
    if relative.parts and relative.parts[0] in MANAGED_DIRECTORIES:
        return MANAGED_DIRECTORIES[relative.parts[0]]
    return None


def _validate_jsonl(path: Path) -> tuple[bool, str | None]:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            return False, f"line {number}: {exc.msg}"
    return True, None


def validate_data_file(path: Path) -> tuple[bool, str | None]:
    """Проверить кодировку и формат поддерживаемого versioned data-файла."""
    try:
        if path.name == ".gitkeep":
            return True, None
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".jsonl":
            return _validate_jsonl(path)
        else:
            if not path.read_text(encoding="utf-8").strip():
                return False, "empty text asset"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, str(exc)
    return True, None


def scan_data(data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """Прочитать все файлы data/ и вернуть машиночитаемый инвентаризационный отчёт."""
    entries: list[dict[str, Any]] = []
    unknown: list[str] = []
    invalid: list[dict[str, str]] = []

    if not data_dir.exists():
        return {"data_dir": str(data_dir), "files": entries, "unknown": [], "invalid": []}

    for path in sorted(item for item in data_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(data_dir)
        if relative.parts and relative.parts[0] in RUNTIME_DIRECTORIES:
            continue
        purpose = classify_data_file(path, data_dir)
        valid, error = validate_data_file(path)
        relative = relative.as_posix()
        entry = {
            "path": relative,
            "purpose": purpose,
            "bytes": path.stat().st_size,
            "valid": valid,
            "error": error,
        }
        entries.append(entry)
        if purpose is None:
            unknown.append(relative)
        if not valid:
            invalid.append({"path": relative, "error": error or "invalid"})

    return {
        "data_dir": str(data_dir),
        "files": entries,
        "managed_count": len(entries) - len(unknown),
        "unknown": unknown,
        "invalid": invalid,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and inventory versioned data assets")
    parser.add_argument("--json", action="store_true", help="print the complete report as JSON")
    args = parser.parse_args(argv)
    report = scan_data()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "data inventory: "
            f"files={len(report['files'])} managed={report['managed_count']} "
            f"unknown={len(report['unknown'])} invalid={len(report['invalid'])}"
        )
        for entry in report["invalid"]:
            print(f"INVALID {entry['path']}: {entry['error']}")
        for path in report["unknown"]:
            print(f"UNKNOWN {path}")

    return 0 if not report["unknown"] and not report["invalid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
