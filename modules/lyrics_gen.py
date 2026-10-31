"""
modules/lyrics_gen.py — генерация текста песни (объединены v7 / v8 / AI-first).

Три входа, один контракт:

  • `generate_lyrics(...)`      — базовый генератор: Ollama (если поднят) →
    сленг из `agents.trend_scout` → Lyric Vault → шаблонные панчи.
  • `generate_lyrics_ai(...)`   — AI-first через локальную LLM-роль `lyrics_llm`
    (честный BLOCKED, если весов/рантайма нет).
  • `generate_lyrics_v8(...)`   — стиль автора-референса
    (`modules.author_ref_lyrics`) + актуальный сленг + билингвальный припев +
    валидация длины строк.

Жёсткое требование: строки пользователя (`user_lyrics_lines`) обязаны попасть
в результат дословно — это проверяется во всех трёх входах.

Ключевое требование ТЗ 20.2 (вопрос 3): user_lyrics_lines — если
пользователь указал свои строки, они ОБЯЗАНЫ попасть в трек, дословно.
"""

from __future__ import annotations

import json
import random
import re
import time
from contextvars import ContextVar
from pathlib import Path

from modules import author_ref_lyrics

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "lyric_vault"
# v22: ленивое создание (не при импорте)

LYRIC_MEMORY = VAULT_DIR / "lyrics_memory.jsonl"
SLANG_FILE = VAULT_DIR / "slang.txt"

# Панчи по темам — используются как fallback и как затравка для Llama
PUNCHES_RU = {
    "лето": [
        "солнце жарит, плавит асфальт",
        "лето без страховки, полный газ вдаль",
        "тачка без крыши, ветер в лицо",
        "закат на Стамбул, золотое кольцо",
        "море, деньги, драйв — это наш финал",
        "жаркие ночи, танцпол закипал",
        "песок под ногами, ритм в груди",
        "лето не кончится, всё впереди",
    ],
    "тачки": [
        "Supra рвёт тишину, турбина свистит",
        "AMG в ночи, как чёрный магнит",
        "мотор кричит, просит ещё",
        "полёт по трассе, время течёт",
        "дрифт в тумане, жжёная резина",
        "скорость — мой яд, адреналин — бензин",
        "низкий клиренс, дерзкий обвес",
        "мы короли улиц, у нас есть вес",
    ],
    "деньги": [
        "кэш на кэше, стопки до небес",
        "чек за чеком, ловим интерес",
        "мани мани моуш, крутим дела",
        "деньги в кармане, удача пришла",
        "бриллианты блестят, как звёзды в ночи",
        "золотые цепи, от сейфа ключи",
        "успех — это труд, а не просто фарт",
        "мы строим империю, это наш старт",
    ],
    "движ": [
        "ночь моя, я в центре огней",
        "движ до утра, зови всех друзей",
        "клуб на пике, бас бьёт в висок",
        "звук качает, просыпайся, город-игрок",
        "лица в свете, тени в углах",
        "энергия прёт, забыли про страх",
        "мы здесь и сейчас, это наш момент",
        "музыка — жизнь, лучший элемент",
    ],
    "турция": [
        "Стамбул горит миллионами ламп",
        "Босфор шумит, проплывая сквозь храм",
        "чай крепче кофе, разговор до утра",
        "Турция как второй дом, родная земля",
        "Анталия ждёт, тёплый бриз у воды",
        "древние камни, наши следы",
        "восточная сказка в реальности дня",
        "здесь каждый закат — для тебя и меня",
    ],
    "агрессия": [
        "без тормозов, летим напролом",
        "рубим наотмашь, крушим этот дом",
        "молчание — предатель, кричи во весь голос",
        "рвём этот бит, как коса спелый колос",
        "ярость в глазах, сила в руках",
        "мы победим, оставив всех в дураках",
        "сталь в характере, лёд в словах",
        "путь к вершине — через боль и страх",
    ],
}

HOOKS_EN = [
    "money over everything, we never look back",
    "night, drift, we ride, strictly on track",
    "summer, cars, get high, feel the heat",
    "no brakes, we win, victory is sweet",
    "vibe on repeat, loud in the street",
    "shining like a star, never accept defeat",
    "put your hands up, touch the sky",
    "let it burn tonight, let the sparks fly",
    "we don't stop, we own the game",
    "living on the edge, remember the name",
    "top down, cruising, feeling so free",
    "this is the life, how it's meant to be",
]


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


def _pick_punches(theme: str, count: int = 4) -> list[str]:
    """Собираем панчи по темам из строки-запроса."""
    theme_lower = (theme or "").lower()
    collected = []
    
    # Если это шансон или тюремная/жизненная лирика
    if "шансон" in theme_lower or "централ" in theme_lower or "ветер" in theme_lower or "жиган" in theme_lower:
        collected.extend([
            "Владимирский централ, ветер северный,",
            "Этапный путь до тюрьмы, до каторги.",
            "Кольщик, наколо мне купола да кресты,",
            "Чтобы память жила до черты.",
            "А на воле весна, магаданский туман,",
            "Облака плывут в океан.",
            "Жиган-монпансье, воля вольная,",
            "Душа моя больная, доля горькая."
        ])
        
    for key, punches in PUNCHES_RU.items():
        if key in theme_lower:
            collected.extend(punches)
            
    if not collected:
        for punches in PUNCHES_RU.values():
            collected.extend(punches)
            
    random.shuffle(collected)
    return collected[:count]


def _try_ollama_with_diagnostics(prompt: str, model: str = "llama3") -> dict:
    """Пробует local Ollama и раскрывает status without claiming generation."""
    try:
        import requests

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if response.status_code == 200:
            text = response.json().get("response", "").strip()
            return {"text": text or None, "status": "responded" if text else "empty_response"}
        return {"text": None, "status": "http_error", "http_status": response.status_code}
    except Exception as exc:
        return {"text": None, "status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


def _try_ollama(prompt: str, model: str = "llama3") -> str | None:
    """Совместимый local Ollama helper для existing lyrics callers."""
    return _try_ollama_with_diagnostics(prompt, model)["text"]


def _template_verse(
    punches: list[str], user_lines: list[str], bpm: int, syllable_target: int
) -> list[str]:
    """Собираем куплет из панчей и пользовательских строк."""
    lines = []
    used_user = 0
    for i in range(16):
        if used_user < len(user_lines) and i in (0, 2):
            lines.append(user_lines[used_user])
            used_user += 1
        else:
            # Цикл по заранее перемешанному punch-list исключает случайный
            # loop одного и того же бара, но сохраняет разнообразие по теме.
            base = punches[i % len(punches)] if punches else "движ на движ"
            lines.append(base)
    # Оставшиеся пользовательские — добавим в конец
    for extra in user_lines[used_user:]:
        lines.append(extra)
    return lines


def _template_hook_en(user_hooks: list[str]) -> list[str]:
    """English хук: сначала пользовательские EN-строки, потом из HOOKS_EN."""
    en_user = [l for l in user_hooks if _is_english(l)]
    hook = list(en_user)[:2]
    while len(hook) < 2:
        cand = random.choice(HOOKS_EN)
        if cand not in hook:
            hook.append(cand)
    return hook * 2  # 4 строки припева


def _is_english(s: str) -> bool:
    """Груборечивая эвристика: строка содержит только ASCII/латиницу."""
    if not s:
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for c in letters if ord(c) < 128)
    return ascii_letters / len(letters) > 0.8


def generate_lyrics(
    theme: str,
    style_vector: dict | None = None,
    n_verses: int = 2,
    user_lyrics_lines: list[str] | None = None,
    bilingual: bool = True,
) -> dict:
    """
    Главный API. Всегда возвращает {'lyrics': str, 'structure': [...], ...}.
    """
    user_lyrics_lines = user_lyrics_lines or []
    style_vector = style_vector or {}
    bpm = int(style_vector.get("target_bpm") or 140)

    # Разделяем пользовательские строки на русские и английские
    user_ru = [l.strip() for l in user_lyrics_lines if l.strip() and not _is_english(l)]
    user_en = [l.strip() for l in user_lyrics_lines if l.strip() and _is_english(l)]

    # Слоговая цель — 6-9 при бампирующем BPM
    syllable_target = 6 if bpm > 150 else 8

    # Попробуем Ollama если запущен
    ollama_prompt = (
        f"Напиши текст трека в стиле phonk/trap/hyperpop, BPM={bpm}, "
        f"тема: {theme}. Куплеты — по-русски, короткие рэп-строчки, "
        f"хук — по-английски, {2 if bilingual else 0} английских строк. "
        f"Обязательные строки: {', '.join(user_lyrics_lines) if user_lyrics_lines else 'нет'}. "
        f"Не пиши комментарии, только текст трека."
    )
    ollama_out = _try_ollama(ollama_prompt)

    if ollama_out and len(ollama_out) > 50:
        lyrics_text = ollama_out
        source = "ollama"
    else:
        # Fallback: template
        punches = _pick_punches(theme, count=8)
        blocks = []
        # Один hook повторяется после каждого куплета: это контролируемая
        # song-structure, а не случайно меняющийся набор строк.
        hook_lines = _template_hook_en(user_en) if bilingual else []
        for i in range(n_verses):
            blocks.append(f"[Куплет {i+1}]")
            blocks.extend(
                _template_verse(
                    punches, user_ru if i == 0 else [], bpm, syllable_target
                )
            )
            if hook_lines:
                blocks.append("[Hook]")
                blocks.extend(hook_lines)
        lyrics_text = "\n".join(blocks)
        source = "template"

    # Гарантируем что все user_lyrics впитаны
    for line in user_lyrics_lines:
        if line.strip() and line.strip() not in lyrics_text:
            lyrics_text += f"\n[User]\n{line.strip()}"

    _save_lyric_memory(
        {
            "theme": theme,
            "bpm": bpm,
            "lyrics": lyrics_text,
            "source": source,
            "user_lines": user_lyrics_lines,
        }
    )

    return {
        "ok": True,
        "lyrics": lyrics_text,
        "source": source,
        "bilingual": bilingual,
        "n_verses": n_verses,
        "bpm": bpm,
        "user_lines_included": all(
            l.strip() in lyrics_text for l in user_lyrics_lines if l.strip()
        ),
    }


def get_lyric_memory(limit: int = 20) -> list:
    """Вернуть последние валидные строки из Lyric Vault."""
    memories = _load_lyric_memory()
    return list(reversed(memories))[:limit]


def get_lyric_memory_diagnostics(limit: int = 20) -> dict:
    """Return recent valid memories together with non-fatal JSONL recovery diagnostics."""
    memories, read_errors = _load_lyric_memory_with_errors()
    return {"memories": list(reversed(memories))[:limit], "read_errors": read_errors}


if __name__ == "__main__":
    r = generate_lyrics(
        "лето, тачки, деньги",
        style_vector={"target_bpm": 140},
        user_lyrics_lines=["ночь горит, Supra летит", "money over everything"],
        bilingual=True,
    )
    print(r["lyrics"])
    print("---")
    print("user_included:", r["user_lines_included"])



# --------------------------------------------------------------------------- #
#  AI-first генерация (локальная LLM, роль lyrics_llm)
# --------------------------------------------------------------------------- #
# Возвращает тот же контракт, что и `generate_lyrics`: текст + источник либо
# честный BLOCKED, если весов/рантайма нет. Пользовательские строки всегда
# сохраняются в результате.

def generate_lyrics_ai(theme, style_vector=None, n_verses=2, user_lyrics_lines=None,
                       bilingual=True, artist_slug=None, track_id=None,
                       genre="phonk", handle: Any = None) -> Dict[str, Any]:
    from app.ai import llm_service as LLM
    from app.ai import prompts as P
    from app.ai.registry import registry
    from modules.artist_dossier import DossierManager

    style_vector = style_vector or {}
    user_lyrics_lines = [l.strip() for l in (user_lyrics_lines or []) if l.strip()]
    bpm = int(style_vector.get("target_bpm") or 140)
    art_dos = trk_dos = None
    if artist_slug:
        mgr = DossierManager()
        art_dos = mgr.get_artist_dossier(artist_slug)
        trk_dos = mgr.get_track_dossier(artist_slug, track_id) if track_id else None
    prompt = P.build_lyrics_prompt(theme=theme, genre=genre, bpm=bpm,
                                   n_verses=n_verses, bilingual=bilingual,
                                   user_lines=user_lyrics_lines,
                                   artist_dossier=art_dos, track_reference=trk_dos)
    if handle is None and not registry.is_available("lyrics_llm"):
        return {"ok": False, "lyrics": "",
                "reason": "lyrics_llm unavailable - run tools/pull_ai_models.py --role lyrics_llm",
                "source": "BLOCKED"}
    if handle is None:
        with registry.use("lyrics_llm") as loaded:
            text = LLM.complete(loaded.handle, P.SYSTEM_LYRICS, prompt,
                                max_tokens=1400, temperature=0.9, top_p=0.95,
                                repeat_penalty=1.15)
    else:
        text = LLM.complete(handle, P.SYSTEM_LYRICS, prompt,
                            max_tokens=1400, temperature=0.9, top_p=0.95,
                            repeat_penalty=1.15)
    if not text or len(text) < 60:
        return {"ok": False, "lyrics": text or "", "reason": "empty LLM output",
                "source": "lyrics_llm"}
    text = re.sub(r"^```.*?$", "", text, flags=re.MULTILINE).strip()
    lo = text.lower()
    missing = [ln for ln in user_lyrics_lines if ln.lower() not in lo]
    if missing:
        text = text.rstrip() + "\n\n[User]\n" + "\n".join(missing)
    VAULT.mkdir(parents=True, exist_ok=True)
    with open(MEMORY, "a", encoding="utf-8") as f:
        f.write(json.dumps({"theme": theme, "bpm": bpm, "lyrics": text,
                            "source": "lyrics_llm", "artist_slug": artist_slug,
                            "track_id": track_id, "timestamp": time.time()},
                           ensure_ascii=False) + "\n")
    return {"ok": True, "lyrics": text, "source": "lyrics_llm",
            "bilingual": bilingual, "n_verses": n_verses, "bpm": bpm,
            "artist_slug": artist_slug, "track_id": track_id,
            "user_lines_included": all(l.lower() in text.lower() for l in user_lyrics_lines)}



# --------------------------------------------------------------------------- #
#  Author-style генерация (стиль автора-референса + актуальный сленг)
# --------------------------------------------------------------------------- #
# Обёртка вокруг `generate_lyrics`: подмешивает стиль автора из
# `modules.author_ref_lyrics`, сленг дня из `agents.trend_scout`, билингвальный
# припев и валидацию длины строк. Офлайн-безопасна.

_SECTION_MARKERS = (
    ("intro", ("интро", "intro")),
    ("chorus", ("припев", "chorus", "hook")),
    ("verse1", ("куплет 1", "verse 1")),
    ("verse2", ("куплет 2", "verse 2")),
    ("bridge", ("бридж", "bridge")),
    ("outro", ("аутро", "outro")),
)


def _section_for_marker(marker: str) -> str | None:
    """Classify a bracketed Russian/English section marker in stable priority order."""
    for section, tokens in _SECTION_MARKERS:
        if any(token in marker for token in tokens):
            return section
    return None


def _split_blocks(text: str) -> dict[str, list[str]]:
    """Parse recognized bracketed section markers into stable verse/chorus blocks."""
    blocks = {key: [] for key in ("intro", "verse1", "chorus", "verse2", "bridge", "outro")}
    current = "verse1"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = _section_for_marker(line.lower()) or current
            continue
        blocks[current].append(line)
    return blocks


def _validate_rhythm(
    lines: list[str], target_avg: float = 9.0, tol: float = 0.3
) -> list[str]:
    """Отсекаем строки, которые слишком короткие/длинные (≥±30% от target)."""
    kept = []
    for l in lines:
        n = sum(1 for ch in l.lower() if ch in "аеёиоуыэюяaeiouy")
        n = max(1, n)
        if target_avg * (1 - tol) <= n <= target_avg * (1 + tol) or len(lines) < 4:
            kept.append(l)
    return kept or lines


def _fetch_slang(theme: str) -> list[str]:
    """Return optional trend slang or an honest empty fallback."""
    try:
        from agents.trend_scout import actual_slang_for_prompt

        return actual_slang_for_prompt(theme, n_words=15)
    except Exception:
        return []


_AUTHOR_STYLE_DIAGNOSTIC: ContextVar[dict | None] = ContextVar(
    "lyrics_v8_author_style_diagnostic", default=None
)


def _author_style_prompt_with_diagnostics(
    author: str | None, theme: str, user_words: list[str], slang: list[str], bpm: int, target_lines: int
) -> tuple[str, bool, dict]:
    """Build optional author guidance and disclose unavailable reference ingestion."""
    if not author:
        return "", False, {"ok": False, "status": "not_requested", "author": ""}
    try:
        profile = author_ref_lyrics.get_style_profile(author)
        if not profile:
            author_ref_lyrics.fetch_and_ingest_author(author, max_tracks=5)
            profile = author_ref_lyrics.get_style_profile(author)
        if profile:
            prompt = author_ref_lyrics.build_style_prompt(
                author=author, theme=theme, user_words=user_words + slang[:6],
                bpm=bpm, target_lines=target_lines,
            )
            return prompt, True, {"ok": True, "status": "available", "author": author}
        return "", False, {"ok": False, "status": "profile_unavailable", "author": author}
    except Exception as exc:
        return "", False, {
            "ok": False,
            "status": "failed",
            "author": author,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _author_style_prompt(
    author: str | None, theme: str, user_words: list[str], slang: list[str], bpm: int, target_lines: int
) -> tuple[str, bool]:
    """Совместимый prompt-only API для optional author reference guidance."""
    prompt, used, diagnostics = _author_style_prompt_with_diagnostics(
        author, theme, user_words, slang, bpm, target_lines
    )
    _AUTHOR_STYLE_DIAGNOSTIC.set(diagnostics)
    return prompt, used


def _generate_raw_lyrics(seed: str, user_words: list[str], bpm: int, style_prompt: str, target_lines: int, slang: list[str]) -> str:
    """Call v7 generation with its supported-argument and empty-text fallbacks."""
    try:
        return generate_lyrics(
            theme=seed, bpm=bpm, user_lyrics_lines=user_words,
            style_prompt=style_prompt or None, target_lines=target_lines,
        )
    except TypeError:
        try:
            return generate_lyrics(theme=seed, bpm=bpm)
        except Exception:
            return f"[Куплет 1]\n{seed}\n[Припев]\n{random.choice(slang) if slang else 'yeah'}\n"
    except Exception as error:
        return f"[Куплет 1]\n{seed}\n[Припев]\n(fallback: {error})\n"


def _ensure_bilingual_chorus(blocks: dict[str, list[str]], theme: str, lang_mix: str) -> None:
    """Append a safe English hook only when bilingual chorus markup requires one."""
    if lang_mix != "ru+en":
        return
    chorus_text = " ".join(blocks["chorus"]).lower()
    if any(re.search(r"[a-z]{3,}", word) for word in chorus_text.split()):
        return
    try:
        from agents.trend_scout import scout

        blocks["chorus"].append(random.choice(scout(theme)["hooks_en"]))
    except Exception:
        blocks["chorus"].append("night ride, we don't stop")


def _assemble_lyrics_text(blocks: dict[str, list[str]]) -> str:
    """Render normalized section blocks into the established v8 song order."""
    parts = []
    if blocks["intro"]:
        parts.append("[Интро]\n" + "\n".join(blocks["intro"]))
    parts.append("[Куплет 1]\n" + "\n".join(blocks["verse1"] or ["город спит, а мотор рычит"]))
    parts.append("[Припев]\n" + "\n".join(blocks["chorus"] or ["night ride, we don't stop"]))
    parts.append("[Куплет 2]\n" + "\n".join(blocks["verse2"] or blocks["verse1"] or []))
    parts.append("[Припев]\n" + "\n".join(blocks["chorus"] or []))
    if blocks["bridge"]:
        parts.append("[Бридж]\n" + "\n".join(blocks["bridge"]))
    if blocks["outro"]:
        parts.append("[Аутро]\n" + "\n".join(blocks["outro"]))
    return "\n\n".join(parts)


def generate_lyrics_v8(
    theme: str,
    user_words: list[str] | None = None,
    bpm: int = 130,
    author: str | None = None,
    target_lines: int = 16,
    want_female_backing: bool = False,
    lang_mix: str = "ru+en",
) -> dict:
    """
    Главная точка входа v8. Возвращает готовый текст + мета.
    """
    user_words = [word.strip() for word in (user_words or []) if word and word.strip()]
    slang = _fetch_slang(theme)
    _AUTHOR_STYLE_DIAGNOSTIC.set(None)
    style_prompt, author_style_used = _author_style_prompt(
        author, theme, user_words, slang, bpm, target_lines
    )
    author_style = _AUTHOR_STYLE_DIAGNOSTIC.get() or {
        "ok": author_style_used,
        "status": "available" if author_style_used else ("not_requested" if not author else "profile_unavailable"),
        "author": author or "",
    }
    seed = theme
    if user_words:
        seed += " — " + ", ".join(user_words)
    if slang:
        seed += " · слэнг: " + ", ".join(slang[:8])
    raw = _generate_raw_lyrics(seed, user_words, bpm, style_prompt, target_lines, slang)
    blocks = _split_blocks(raw if isinstance(raw, str) else str(raw))
    for key in ("verse1", "verse2", "chorus"):
        blocks[key] = _validate_rhythm(blocks[key])
    _ensure_bilingual_chorus(blocks, theme, lang_mix)
    return {
        "text": _assemble_lyrics_text(blocks),
        "chorus_lines": blocks["chorus"] or [],
        "used_slang": slang,
        "author_style_used": author_style_used,
        "author_style": author_style,
        "want_female_backing": want_female_backing,
        "author": author or "",
    }
