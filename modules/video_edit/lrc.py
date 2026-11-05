# -*- coding: utf-8 -*-
"""
modules/video_edit/lrc.py — разбор LRC-субтитров с диагностикой.

Битые строки не теряются молча: `_parse_lrc_with_diagnostics` возвращает их
список, чтобы провал оверлея был объясним.
"""

from __future__ import annotations

from modules.video_edit.console import safe_print as _safe_print


def _parse_lrc_with_diagnostics(lrc_path: str) -> dict:
    """Парсит LRC cues и раскрывает malformed timestamp/file diagnostics."""
    cues = []
    diagnostics = []
    try:
        with open(lrc_path, "r", encoding="utf-8", errors="ignore") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line or not line.startswith("["):
                    continue
                end = line.rfind("]")
                if end < 0:
                    diagnostics.append({"line": line_number, "error": "unterminated_tag"})
                    continue
                head, text = line[: end + 1], line[end + 1 :].strip()
                index = 0
                while index < len(head):
                    if head[index] != "[":
                        index += 1
                        continue
                    closing = head.find("]", index)
                    if closing < 0:
                        diagnostics.append({"line": line_number, "error": "unterminated_tag"})
                        break
                    tag = head[index + 1 : closing]
                    if ":" in tag and any(char.isdigit() for char in tag):
                        try:
                            minutes, seconds = tag.split(":", 1)
                            cues.append((float(minutes) * 60 + float(seconds), text))
                        except (TypeError, ValueError) as exc:
                            diagnostics.append({"line": line_number, "tag": tag, "error": f"{type(exc).__name__}: {exc}"})
                    index = closing + 1
    except Exception as exc:
        diagnostics.append({"error": f"{type(exc).__name__}: {exc}"})
        _safe_print(f"[video_edit] lrc parse fail: {exc}")
    cues.sort(key=lambda cue: cue[0])
    return {"cues": cues, "diagnostics": diagnostics}


def _parse_lrc(lrc_path: str) -> list[tuple[float, str]]:
    """Совместимый cue-list API для existing subtitle callers."""
    return _parse_lrc_with_diagnostics(lrc_path)["cues"]
