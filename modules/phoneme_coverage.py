"""
ZS Music Maker v10 — Phoneme Coverage Analyzer
================================================
Voice Vault: покрытие фонем/сочетаний (ТЗ 3.8).

Считает какие фонемы/дифоны русского и английского уже записаны
пользователем в Voice Vault, и рекомендует какие короткие фразы
записать чтобы покрыть недостающие.

Не требует нейросети — работает на транскрипте (Whisper выход
или ручной ввод текста) через словарь звуков.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

# Русские фонемы (упрощённо, IPA-подобно)
RU_PHONEMES = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
# Англ фонемы (по буквенным группам)
EN_PHONEMES = list("abcdefghijklmnopqrstuvwxyz")
DIPHTHONGS = [
    "ая",
    "ое",
    "ый",
    "уй",
    "ай",
    "ой",
    "ei",
    "ai",
    "ou",
    "au",
    "th",
    "sh",
    "ch",
]

VAULT_DIR = Path("voice_vault")
COVERAGE_FILE = VAULT_DIR / "phoneme_coverage.json"


def _collect_transcripts_with_errors() -> tuple[list[str], list[str]]:
    """Collect Voice Vault transcripts and retain non-fatal read diagnostics."""
    texts: list[str] = []
    errors: list[str] = []
    for path in VAULT_DIR.rglob("*.txt"):
        try:
            texts.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{path.name}: {type(error).__name__}: {error}")
    for path in VAULT_DIR.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "transcript" in data:
                texts.append(str(data["transcript"]))
            elif isinstance(data, list):
                texts.extend(str(item["transcript"]) for item in data if isinstance(item, dict) and "transcript" in item)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            errors.append(f"{path.name}: {type(error).__name__}: {error}")
    return texts, errors


def _collect_transcripts() -> list[str]:
    """Return transcripts with the historical list-only private helper contract."""
    return _collect_transcripts_with_errors()[0]


def compute_coverage() -> dict[str, Any]:
    """
    Пересчитывает покрытие. Возвращает и сохраняет в JSON.
    """
    texts, transcript_read_errors = _collect_transcripts_with_errors()
    joined = " ".join(texts).lower()

    ru_c = Counter(ch for ch in joined if ch in RU_PHONEMES)
    en_c = Counter(ch for ch in joined if ch in EN_PHONEMES)
    di_c = Counter(d for d in DIPHTHONGS if d in joined)

    ru_missing = [p for p in RU_PHONEMES if ru_c[p] < 3]
    en_missing = [p for p in EN_PHONEMES if en_c[p] < 3]
    di_missing = [d for d in DIPHTHONGS if di_c[d] < 1]

    total_ru = sum(ru_c.values())
    total_en = sum(en_c.values())

    ru_cov_pct = round((len(RU_PHONEMES) - len(ru_missing)) / len(RU_PHONEMES) * 100, 1)
    en_cov_pct = round((len(EN_PHONEMES) - len(en_missing)) / len(EN_PHONEMES) * 100, 1)

    suggestions = _make_suggestions(ru_missing, en_missing, di_missing)

    report = {
        "ru_coverage_pct": ru_cov_pct,
        "en_coverage_pct": en_cov_pct,
        "ru_missing": ru_missing,
        "en_missing": en_missing,
        "diphthongs_missing": di_missing,
        "total_ru_chars": total_ru,
        "total_en_chars": total_en,
        "suggested_phrases": suggestions,
        "transcript_count": len(texts),
        "transcript_read_errors": transcript_read_errors,
    }

    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    COVERAGE_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def _make_suggestions(ru_missing, en_missing, di_missing) -> list[str]:
    """
    Простые пангаммы под недостающие звуки.
    """
    pool = []
    if "ъ" in ru_missing or "ы" in ru_missing:
        pool.append("Съешь ещё этих мягких французских булок, да выпей чаю")
    if "ж" in ru_missing or "щ" in ru_missing:
        pool.append("Широкая электрификация южных губерний даст мощный толчок подъёму")
    if "х" in ru_missing:
        pool.append("В чащах юга жил бы цитрус? Да, но фальшивый экземпляр!")
    if "ц" in ru_missing:
        pool.append("Цапля целый день сидела на цветущем цветке")
    if any(x in en_missing for x in "xzqj"):
        pool.append("The quick brown fox jumps over the lazy dog")
    if "th" in di_missing:
        pool.append("Three thin thieves thought a thousand thoughts")
    if "sh" in di_missing:
        pool.append("She sells seashells by the sea shore")
    if not pool:
        pool = ["Запись выглядит достаточной. Можно двигаться к RVC-тренингу."]
    return pool[:5]


if __name__ == "__main__":
    r = compute_coverage()
    print(json.dumps(r, ensure_ascii=False, indent=2))
