# -*- coding: utf-8 -*-
"""
app/core/stages/lyrics.py — Текст: структура куплет/припев, LLM/шаблоны, честный fallback.
"""

from __future__ import annotations

from typing import Any

try:  # локальный LLM-роутер опционален: без него работает шаблонный текст
    from modules.llm import LLMRouter
except Exception:  # noqa: BLE001
    LLMRouter = None


def _text_to_struct(text: str, genre: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    title = ""
    verse1: list[str] = []
    chorus: list[str] = []
    verse2: list[str] = []
    current = "verse1"
    for ln in lines:
        low = ln.lower()
        if low.startswith("[") and low.endswith("]"):
            if "hook" in low or "chorus" in low or "припев" in low:
                current = "chorus"
            elif "verse 2" in low or "куплет 2" in low or "verse2" in low:
                current = "verse2"
            elif "intro" in low:
                current = "intro"
            else:
                current = "verse1"
            continue
        if not title and len(ln) <= 60 and ln[0] not in "[(":
            title = ln
        if current == "verse1":
            verse1.append(ln)
        elif current == "chorus":
            chorus.append(ln)
        elif current == "verse2":
            verse2.append(ln)
    if not title:
        title = f"ZS Track ({genre})"
    return {
        "title": title,
        "verse1": verse1[:8] or [],
        "chorus": chorus[:6] or [],
        "verse2": verse2[:8] or [],
        "language": "ru+en",
    }


def _struct_to_text(struct: dict[str, Any]) -> str:
    parts: list[str] = []
    if struct.get("title"):
        parts.append(str(struct["title"]))
    if struct.get("verse1"):
        parts.append("[verse 1]")
        parts.extend(struct["verse1"])
    if struct.get("chorus"):
        parts.append("[hook]")
        parts.extend(struct["chorus"])
    if struct.get("verse2"):
        parts.append("[verse 2]")
        parts.extend(struct["verse2"])
    return "\n".join(parts)


_LYRICS_TEMPLATES = {
    "drift_phonk": {
        "title": "Ночь горит ({genre})",
        "verse1": [
            "Ночь горит, я в дороге",
            "Город спит, а мы на пороге",
            "Тачки, движ, лето внутри",
            "Мы не сдадимся, ты только смотри",
        ],
        "chorus": [
            "Money over everything",
            "Мы летим, ночь горит",
            "Turkish beat, sea and me",
            "Всё, что есть — это мы",
        ],
        "verse2": [
            "Дым в окно, асфальт поёт",
            "Ночь не спит, двигатель не ждёт",
            "Всё что было — было вчера",
            "Сегодня новая игра",
        ],
    },
    "trap": {
        "title": "Тёмный неон ({genre})",
        "verse1": [
            "Тёмный неон, город дымит",
            "Толку в словах нет, движ горит",
            "Пацаны рядом, басы в пол",
            "Ночь длинная, мы на взлёт",
        ],
        "chorus": [
            "Trap trap, на районе шум",
            "Басы как гром, мы на подъём",
            "Trap trap, не остановишь",
            "Тёмный неон в наших крови",
        ],
        "verse2": [
            "Дым из окон, свет фонарей",
            "Мы в этой ночи все сильней",
            "Кто не с нами — тот в стороне",
            "Наш звук гремит на всю стране",
        ],
    },
    "pop": {
        "title": "Лето внутри ({genre})",
        "verse1": [
            "Солнце в глазах, ветер в волосах",
            "Мы летим по трассе вдвоём",
            "Радио орёт, сердце бьётся",
            "Это лето будет вечным",
        ],
        "chorus": [
            "Лето внутри, свет внутри",
            "Мы горим, мы горим",
            "Пой со мной, лети со мной",
            "Эта ночь — только моя",
        ],
        "verse2": [
            "Город засыпает, мы не спим",
            "По крышам гуляем, по мостам",
            "Каждый миг как последний",
            "И никогда не будет скучным",
        ],
    },
    "lo_fi": {
        "title": "Дождь за окном ({genre})",
        "verse1": [
            "Дождь за окном, чай на столе",
            "Старый плейлист и тишина",
            "Мысли плывут по течению",
            "И время стало не спеша",
        ],
        "chorus": [
            "Lo-fi, lo-fi, медленный бит",
            "Пусть весь мир подождёт",
            "Lo-fi, lo-fi, душа дремлет",
            "В этом звуке я живу",
        ],
        "verse2": [
            "Книга открыта, страница белеет",
            "Винил крутится в полумраке",
            "Дождь рисует на стекле",
            "Картины из моей тоски",
        ],
    },
}


def _fallback_lyrics(theme: str, genre: str) -> dict[str, Any]:
    """v22: выбираем жанровый шаблон, подмешиваем тему. Не выдаём за LLM."""
    g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
    tpl = _LYRICS_TEMPLATES.get(g, _LYRICS_TEMPLATES["drift_phonk"])
    out = {
        "title": tpl["title"].format(genre=genre),
        "verse1": list(tpl["verse1"]),
        "chorus": list(tpl["chorus"]),
        "verse2": list(tpl["verse2"]),
        "language": "ru+en",
    }
    # Подмешиваем тему в первую строку куплета, если тема нестандартная
    if theme and theme not in ("лето, тачки, движ", "ночь", "движ"):
        topic = theme.split(",")[0].strip()
        if topic and len(topic) <= 40:
            out["verse1"][0] = f"{topic.capitalize()} — вот наша тема"
    return out


def _stage_lyrics(theme: str, genre: str) -> dict[str, Any]:
    """v17 FIX (P0): ВСЕГДА возвращаем И text, И lyrics-структуру."""
    fallback_attempts: list[dict[str, str]] = []
    if LLMRouter is not None:
        try:
            router = LLMRouter(timeout=8.0)
            prompt = (
                f"Напиши текст в жанре {genre} про {theme}, "
                f"16-24 строки, с verse и hook, на русском."
            )
            result = router.complete(prompt, "", theme=theme, genre=genre, language="ru")
            if isinstance(result, dict) and result.get("ok") and result.get("text", "").strip():
                lyrics_struct = _text_to_struct(result["text"], genre)
                return {
                    "ok": True,
                    "text": result["text"],
                    "lyrics": lyrics_struct,
                    "provider": result.get("provider"),
                    "fallback_used": result.get("fallback_used", False),
                    "provider_chain": result.get("provider_chain"),
                    "reason": (
                        result.get("provider") + "_ok"
                        if not result.get("fallback_used")
                        else "llm_all_failed_template_fallback"
                    ),
                }
            if isinstance(result, dict):
                fallback_attempts.append({
                    "engine": "LLMRouter",
                    "status": "empty_or_failed_response",
                    "error": str(result.get("reason") or result.get("error") or "no usable lyrics text"),
                })
            else:
                fallback_attempts.append({
                    "engine": "LLMRouter",
                    "status": "invalid_result",
                    "error": f"expected dict, got {type(result).__name__}",
                })
        except Exception as exc:
            fallback_attempts.append({
                "engine": "LLMRouter",
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
    fb = _fallback_lyrics(theme, genre)
    fallback = {
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
