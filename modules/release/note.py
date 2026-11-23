# -*- coding: utf-8 -*-
"""modules/release/note.py — человеческая записка внутри релизного пакета.

Пакет уходит человеку (а иногда и на площадку), поэтому рядом с файлами
должно быть сказано, что это за релиз и чего в нём заведомо нет. Пустой
`lyrics.txt` без пояснения читается как ошибка сборки, а не как
«инструментал по решению автора».
"""

from __future__ import annotations

from typing import Any


def _release_readme(meta: dict[str, Any], lyrics_text: str, files: dict[str, str]) -> str:
    """Что лежит в пакете и чего в нём нет — словами, а не догадками."""
    title = str(meta.get("title") or "Untitled")
    lines = [
        f"{title} — {meta.get('artist') or 'unknown artist'}",
        "",
        "Что в пакете:",
    ]
    for name in sorted(files):
        if name in {"README.txt"}:
            continue
        lines.append(f"  - {name}")
    lines += ["", "Заметки:"]
    if lyrics_text.strip():
        lines.append("  - текст приложен в lyrics.txt (без привязки к таймлайну)")
    else:
        lines.append(
            "  - это инструментал: текст не сгенерирован (нужна локальная LLM, "
            "см. docs/ в исходниках — модель не входит в пакет)"
        )
    lines.append(
        "  - ISRC/ISWC не выданы: это делают регистраторы, приложение их не "
        "придумывает"
    )
    lines.append("  - обложка и промо-материалы — отдельными файлами в корне проекта")
    lines.append("")
    return "\n".join(lines)


def write_release_readme(release_dir, meta: dict[str, Any], lyrics_text: str, files: dict[str, str]) -> None:
    """Положить README.txt в пакет и зарегистрировать его в списке файлов.

    Вызывается последней: иначе список в записке неполный (проверено на живом
    прогоне — в нём оказались только lyrics.txt и master.wav).
    """
    from pathlib import Path

    folder = Path(release_dir)
    (folder / "README.txt").write_text(
        _release_readme(meta, lyrics_text, files), encoding="utf-8"
    )
    files["README.txt"] = str(folder / "README.txt")
