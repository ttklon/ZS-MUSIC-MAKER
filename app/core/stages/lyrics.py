# -*- coding: utf-8 -*-
"""
app/core/stages/lyrics.py — Текст: структура куплет/припев, LLM/шаблоны, честный fallback.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

from app.core.lyric_context import MAX_REFERENCE_CHARS, build_lyric_context
from app.core.pipeline_runtime import _output, _timed
# `LLMRouter` реэкспортируется: тесты и эксперименты подменяют его именно на
# этом модуле, как и реализации стадий на фасаде оркестратора.
from app.core.stages.lyrics_providers import (  # noqa: F401
    LLMRouter,
    _build_lyrics_prompt,
    _discover_auto_model,
    _try_llm_router,
    _try_local_lyrics_model,
)
from app.core.stages.lyrics_templates import LYRICS_TEMPLATES
from app.pipeline import StageResult, StageStatus

try:  # локальный LLM-роутер опционален: без него работает шаблонный текст
    from modules.llm import LLMRouter
except Exception:  # noqa: BLE001
    LLMRouter = None


def _looks_like_a_title(line: str, genre: str) -> bool:
    """Первая содержательная строка — кандидат в название, но не «скаффолд».

    Шаблонный текст начинается со строки «тема, жанр, время идёт». Такая
    строка — служебная связка, а не название: раньше она уезжала в теги
    релиза (`title` == `album` == «тема, drift_phonk, время идёт»).
    """
    if not line or len(line) > 60 or line[0] in "[(":
        return False
    if line.endswith((",", ":", "—", "-")):
        return False
    # Скаффолд: несколько фрагментов через запятую и упоминание жанра.
    if line.count(",") >= 2 and (genre or "").strip().lower() in line.lower():
        return False
    return True


def _text_to_struct(text: str, genre: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    title = ""
    chorus: list[str] = []
    verses: dict[str, list[str]] = {}
    current = "verse1"
    for ln in lines:
        low = ln.lower()
        if low.startswith("[") and low.endswith("]"):
            if "hook" in low or "chorus" in low or "припев" in low:
                current = "chorus"
            elif "intro" in low:
                current = "intro"
            else:
                # Номер куплета любой: `[verse 3]`, `[куплет 3]`, `[verse3]`.
                # Раньше распознавался только второй, и третий куплет
                # молча приклеивался к первому.
                match = re.search(r"(?:verse|куплет)\s*(\d+)", low)
                number = int(match.group(1)) if match else 1
                current = f"verse{max(1, number)}"
                verses.setdefault(current, [])
            continue
        if not title and _looks_like_a_title(ln, genre):
            title = ln
        if current == "chorus":
            chorus.append(ln)
        elif current.startswith("verse"):
            verses.setdefault(current, []).append(ln)
    if not title:
        title = f"ZS Track ({genre})"
    ordered = [verses[key][:8] for key in _verse_keys(verses)]
    return {
        "title": title,
        # legacy-ключи остаются: их читают отчёт и старые потребители
        "verse1": verses.get("verse1", [])[:8] or [],
        "chorus": chorus[:6] or [],
        "verse2": verses.get("verse2", [])[:8] or [],
        "verses": [block for block in ordered if block],
        "language": "ru+en",
    }


def _verse_keys(source: dict[str, Any]) -> list[str]:
    """Ключи куплетов в порядке номеров: `verse1`, `verse2`, … `verse10`.

    Сортировка строкой поставила бы `verse10` перед `verse2`.
    """
    keys = [key for key in source if re.fullmatch(r"verse\d+", str(key))]
    return sorted(keys, key=lambda key: int(str(key)[5:]))


def _struct_to_text(struct: dict[str, Any]) -> str:
    """Отрендерить структуру в текст: любой набор куплетов в порядке номеров."""
    parts: list[str] = []
    if struct.get("title"):
        parts.append(str(struct["title"]))
    blocks: list[tuple[str, list[str]]] = []
    verses = struct.get("verses")
    if isinstance(verses, list) and verses:
        blocks.extend((f"verse {index}", list(lines)) for index, lines in enumerate(verses, 1))
    else:
        blocks.extend(
            (key.replace("verse", "verse "), list(struct[key]))
            for key in _verse_keys(struct)
        )
    chorus = struct.get("chorus") or []
    # Припев ставится после первого куплета (так строится и шаблон, и LLM-текст).
    for index, (label, lines) in enumerate(blocks):
        if not lines:
            continue
        parts.append(f"[{label}]")
        parts.extend(lines)
        if index == 0 and chorus:
            parts.append("[hook]")
            parts.extend(chorus)
    if chorus and not blocks:
        parts.append("[hook]")
        parts.extend(chorus)
    return "\n".join(parts)


def _fallback_lyrics(theme: str, genre: str, n_verses: int = 2) -> dict[str, Any]:
    """v22: выбираем жанровый шаблон, подмешиваем тему. Не выдаём за LLM.

    `n_verses` уважается: сколько куплетов выбрал пользователь, столько блоков
    и будет. Шаблон содержит две строфы по 4 строки — 8 уникальных строк на
    4 куплета (16 строк), поэтому строки переиспользуются; важно лишь, что
    ни один куплет не повторяет другой целиком и не является сдвигом на одну
    строку (прежде 3-й куплет на три четверти совпадал с 1-м).
    """
    g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
    tpl = LYRICS_TEMPLATES.get(g, LYRICS_TEMPLATES["drift_phonk"])
    # `0` — это осознанный выбор «один куплет», а не «не задано»: значение по
    # умолчанию подставляется только при None/пустом.
    count = max(1, min(4, 2 if n_verses in (None, "") else int(n_verses)))
    base_verses = [list(tpl["verse1"]), list(tpl["verse2"])]
    out: dict[str, Any] = {
        "title": tpl["title"].format(genre=genre),
        "chorus": list(tpl["chorus"]),
        "language": "ru+en",
    }
    for index in range(count):
        round_index = index // len(base_verses)
        if round_index == 0:
            block = list(base_verses[index % len(base_verses)])
        else:
            # Строки из восьми уникальных: дословного повтора не избежать, но
            # перемежение двух строф даёт новую последовательность и оставляет
            # максимум половину общих строк с первым куплетом.
            block = [
                base_verses[line % len(base_verses)][(index + line) % len(base_verses[0])]
                for line in range(len(base_verses[0]))
            ]
        out[f"verse{index + 1}"] = block
    out["verses"] = [out[f"verse{index + 1}"] for index in range(count)]
    # Подмешиваем тему в первую строку куплета, если тема нестандартная
    if theme and theme not in ("лето, тачки, движ", "ночь", "движ"):
        topic = theme.split(",")[0].strip()
        if topic and len(topic) <= 40:
            first = f"{topic.capitalize()} — вот наша тема"
            out["verse1"][0] = first
            out["verses"][0][0] = first
    return out


def _stage_lyrics(
    theme: str, genre: str, n_verses: int = 2,
    style_vector: dict[str, Any] | None = None, bilingual: bool = True,
    creative_context: str = "",
) -> dict[str, Any]:
    """Всегда возвращает И text, И структуру lyrics — независимо от провайдера.

    `n_verses` из мастера доезжает до промпта: раньше выбор пользователя
    (сколько куплетов) терялся по дороге, и стадия всегда писала «16–24 строки».

    Порядок провайдеров прежний и явный: локальные веса → LLM-роутер →
    шаблон. Каждый отказ остаётся в `fallback_attempts`, шаблон помечается
    `fallback_used: True`.
    """
    fallback_attempts: list[dict[str, str]] = []
    auto_model: str | None = None
    try:
        from app.ai.registry import registry

        auto_model = _discover_auto_model(registry)
    except Exception as exc:  # noqa: BLE001 - реестр недоступен, идём дальше
        fallback_attempts.append(
            {
                "engine": "lyrics_llm",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )

    result, attempts = _try_local_lyrics_model(
        theme,
        genre,
        n_verses,
        style_vector,
        bilingual,
        creative_context,
        router_only=bool(os.environ.get("ZSMM_OLLAMA_MODEL", "").strip()) or bool(auto_model),
    )
    fallback_attempts.extend(attempts)
    if result is not None:
        return result

    result, attempts = _try_llm_router(
        theme,
        genre,
        n_verses,
        style_vector,
        bilingual,
        creative_context,
        auto_model,
        router_cls=LLMRouter,
    )
    fallback_attempts.extend(attempts)
    if result is not None:
        result["fallback_attempts"] = fallback_attempts
        return result

    fb = _fallback_lyrics(theme, genre, n_verses)
    fallback: dict[str, Any] = {
        "ok": True,
        "text": _struct_to_text(fb),
        "lyrics": fb,
        "fallback_used": True,
        "provider": "local_template",
        "reason": "no LLM available; template used",
    }
    if fallback_attempts:
        fallback["fallback_attempts"] = fallback_attempts
    return fallback


def _run_lyrics_stage(recipe: dict[str, Any]) -> tuple[StageResult, dict[str, Any], str]:
    """Текст: свои строки пользователя приоритетнее любой генерации."""
    started = time.monotonic()
    user_lines = recipe["user_lyrics_lines"]
    manual = str(recipe.get("reference_lyrics") or "")
    if not manual.strip():
        manual = ""
    asr_report: dict[str, Any] = {"requested": False, "status": "NOT_REQUESTED"}
    transcript = ""
    if recipe.get("transcribe_references"):
        if user_lines or recipe.get("dry_run"):
            asr_report = {"requested": True, "status": "SKIPPED",
                          "reason": "user lyrics take priority" if user_lines else "dry run"}
        else:
            from app.core.reference_asr import transcribe_references

            transcript, asr_report = transcribe_references(recipe.get("refs") or [])
    prefix = manual + "\n" if manual.strip() and transcript else manual
    combined = prefix + transcript
    included = max(0, min(len(combined), MAX_REFERENCE_CHARS) - min(len(prefix), MAX_REFERENCE_CHARS))
    asr_report["provided_to_generator"] = False
    asr_report["context_characters_used"] = included
    asr_report["context_truncated"] = included < len(transcript)
    source = "mixed" if manual.strip() and included else "audio_asr" if included else None
    context_report, creative_context = build_lyric_context(
        combined, recipe.get("trend_notes", ""), reference_source=source
    )
    context_report["reference_asr"] = asr_report
    context_report["provided_to_generator"] = False
    if user_lines:
        own_text = "\n".join(user_lines)
        struct = _text_to_struct(own_text, recipe["genre"])
        return (
            StageResult(
                name="_stage_lyrics",
                status=StageStatus.OK,
                duration_sec=time.monotonic() - started,
                output={
                    "ok": True,
                    "text": own_text,
                    "lyrics": struct,
                    "provider": "user_lyrics",
                    "reason": "user-provided lyrics from wizard",
                    "creative_context": context_report,
                },
            ),
            struct,
            own_text,
        )
    stage = _timed(
        "_stage_lyrics",
        lambda: _stage_lyrics(
            recipe["theme"], recipe["genre"], recipe.get("n_verses", 2),
            style_vector=recipe.get("style_vector"), bilingual=recipe.get("bilingual", True),
            creative_context=creative_context,
        ),
    )
    stage.duration_sec = time.monotonic() - started
    out = _output(stage)
    stage.output = out
    context_report["provided_to_generator"] = bool(
        creative_context and stage.ok and not out.get("fallback_used") and out.get("provider")
    )
    asr_report["provided_to_generator"] = bool(included and context_report["provided_to_generator"])
    if asr_report["status"] in ("BLOCKED", "NO_USABLE_TEXT", "PARTIAL") or asr_report["context_truncated"]:
        if stage.status == StageStatus.OK:
            stage.status = StageStatus.FALLBACK
        out["fallback_used"] = True
        stage.reason = stage.reason or "reference ASR unavailable, incomplete or truncated"
    out["creative_context"] = context_report
    struct = out.get("lyrics") or {}
    text = out.get("text") or _struct_to_text(struct)
    return stage, struct, text
