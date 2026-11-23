# -*- coding: utf-8 -*-
"""
modules.agent_guide.runner — 4 ответа → готовый трек, без ручных галочек.

Порядок ровно тот, что обещает интерфейс:

  1. `trend_scout`    — тема и вайб, если пользователь их не задал;
  2. `sample_hunter`  — подбор бесплатных сэмплов под жанр (CC0/PD, fail closed);
  3. досье артиста    — почему популярен и что делает;
  4. текст            — `LLMRouter` → Ollama qwen, честный `BLOCKED` без заглушки;
  5. голос            — своя запись → RVC (клон), либо честный `BLOCKED`;
  6. `HitFactory`     — один прогон пайплайна: бит (MusicGen / процедурный),
                        микс, мастеринг, humanizer, релизный пакет.

`sequential_runner` держит одну тяжёлую модель в памяти: прогон идёт
ступенями, а не «всё сразу».
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable

from modules.agent_guide.questions import answer_summary, parse_answers

_LOG = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]

# Жанр по умолчанию, если ни референсы, ни тренды ничего не подсказали.
DEFAULT_GENRE = "drift_phonk"


def _online_allowed() -> bool:
    try:
        from app.core.net_policy import network_allowed

        return bool(network_allowed())
    except Exception as exc:  # noqa: BLE001 — политика сети опциональна
        _LOG.debug("net policy unavailable: %s", exc)
        return False


def _trend(theme: str) -> dict[str, Any]:
    """`trend_scout` под тему. Сеть — только если разрешена политикой."""
    try:
        from agents.trend_scout import scout

        data = scout(theme=theme or "лето тачки движ", offline_only=not _online_allowed())
        return {
            "ok": True,
            "hype_words": list(data.get("hype_words") or [])[:12],
            "punchlines": list(data.get("punchlines") or [])[:6],
            "themes": list(data.get("themes") or [])[:6],
            "offline": bool(data.get("offline", True)),
            "reason": data.get("reason", ""),
        }
    except Exception as exc:  # noqa: BLE001 — без трендов хит всё равно соберётся
        _LOG.debug("trend_scout failed: %s", exc)
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


def _genre_from_trend(trend: dict[str, Any]) -> str:
    """Жанр выбирается сам: сначала по вайб-словам, потом по умолчанию."""
    known = ("phonk", "trap", "drift", "house", "techno", "hyperpop", "pluggnb", "jersey")
    for word in trend.get("hype_words") or []:
        lowered = str(word).lower()
        for name in known:
            if name in lowered:
                return name
    return DEFAULT_GENRE


def _samples(genre: str) -> dict[str, Any]:
    """`sample_hunter`: бесплатные сэмплы под жанр. Лицензия проверяется внутри."""
    try:
        from agents.sample_hunter import hunt

        data = hunt(query=genre, max_results=3, allow_online=_online_allowed())
        found = data.get("results") if isinstance(data, dict) else None
        return {
            "ok": bool(found),
            "count": len(found or []),
            "offline": bool((data or {}).get("offline", True)) if isinstance(data, dict) else True,
            "reason": "" if found else "в локальном банке нет подходящих сэмплов",
        }
    except Exception as exc:  # noqa: BLE001 — сэмплы не блокируют генерацию
        _LOG.debug("sample_hunter failed: %s", exc)
        return {"ok": False, "count": 0, "reason": f"{type(exc).__name__}: {exc}"}


def _dossier(artist: str) -> dict[str, Any]:
    """Досье артиста: локальная база, иначе LLM-разбор без выдуманных фактов."""
    if not artist:
        return {"ok": False, "reason": "артист не указан"}
    try:
        from modules.hit_factory.breakthrough import build_artist_dossier

        return build_artist_dossier(artist, use_llm=True)
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("dossier failed: %s", exc)
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


def _references(paths: list[str]) -> dict[str, Any]:
    """Референсы → style_vector. Ссылки качает `breakthrough`, файлы читает `reference_ingest`."""
    if not paths:
        return {"ok": False, "reason": "референсы не заданы — жанр берётся из трендов"}
    try:
        from modules.hit_factory.breakthrough import analyze_references

        return analyze_references(paths)
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("references failed: %s", exc)
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


def _reference_genre(style: dict[str, Any]) -> str | None:
    consensus = (style or {}).get("consensus") or {}
    hint = str(consensus.get("genre_hint") or "").strip()
    if not hint:
        return None
    return hint.split("/")[0].split()[0].strip().lower() or None


def build_plan(answers: dict[str, Any], trend: dict[str, Any] | None = None,
               style: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ответы + тренды + референсы → `wizard_state` для пайплайна.

    Это единственное место, где решается жанр, темп и тема. Пайплайн ниже
    ничего не «догадывает»: он получает готовое состояние.
    """
    trend = trend or {}
    style = style or {}
    style_vector = style.get("style_vector") or style.get("consensus") or {}
    genre = _reference_genre(style) or _genre_from_trend(trend) or DEFAULT_GENRE
    theme = answers.get("mood") or ""
    if not theme:
        themes = trend.get("themes") or trend.get("hype_words") or []
        theme = str(themes[0]) if themes else "ночной город, движение, свой вайб"
    voice = answers.get("voice") or {}
    bpm = style_vector.get("bpm") or style_vector.get("target_bpm")
    return {
        "genre": genre,
        "theme": theme,
        "artist": answers.get("artist") or "ZS Producer",
        "references": list(answers.get("refs") or []),
        "bpm_override": int(bpm) if isinstance(bpm, (int, float)) and bpm else None,
        "duration_sec": 90,
        "voice_mode": "pro" if voice.get("mode") == "file" and voice.get("path") else "off",
        "use_texture": False,
        "use_rvc": voice.get("mode") == "file",
        "own_vocal_wav": voice.get("path") or "",
        "bilingual": True,
        "n_verses": 2,
        "trend_notes": ", ".join((trend.get("hype_words") or [])[:6]),
        "style_vector": style_vector,
    }


def _lyrics(plan: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
    """Текст: только локальный LLM. Нет модели — `BLOCKED` с причиной, не шаблон."""
    try:
        from modules.llm.router import LLMRouter

        router = LLMRouter()
        prompt = (
            f"Тема: {plan['theme']}. Жанр: {plan['genre']}. Артист-ориентир: {plan['artist']}. "
            f"Актуальные слова: {plan.get('trend_notes') or '—'}. "
            "Напиши текст: два куплета на русском и припев с двумя английскими строками. "
            "Только текст трека, без пояснений."
        )
        result = router.complete(prompt=prompt, theme=plan["theme"], genre=plan["genre"])
        text = str(result.get("text") or "").strip()
        ok = bool(text) and not result.get("fallback_used", False)
        return {
            "ok": ok,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "source": "ollama" if ok else "BLOCKED",
            "text": text,
            "reason": "" if ok else _blocked_reason(result),
        }
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("lyrics failed: %s", exc)
        return {"ok": False, "source": "BLOCKED", "text": "",
                "reason": f"LLM недоступен: {type(exc).__name__}: {exc}"}


def _blocked_reason(result: dict[str, Any]) -> str:
    errors = result.get("error") or {}
    ollama = errors.get("ollama") if isinstance(errors, dict) else None
    if ollama:
        return f"Ollama не дал текст ({ollama}) — запусти `ollama serve` и `ollama pull qwen3:4b`"
    return "локальная LLM не ответила — текст не подменяется шаблоном"


def _voice(plan: dict[str, Any], work_dir: Path) -> dict[str, Any]:
    """Голос: запись пользователя → RVC-клон. Нет записи — честный BLOCKED."""
    path = str(plan.get("own_vocal_wav") or "").strip()
    if not path:
        return {"ok": False, "source": "none",
                "reason": "голос не записан — трек соберётся без вокала (это не выдача TTS за голос)"}
    try:
        from modules.hit_factory.breakthrough import prepare_voice

        result = prepare_voice(path, use_rvc=True)
        if result.get("ok") and result.get("source") == "rvc":
            plan["use_rvc"] = False  # already converted; do not run RVC twice
            plan["own_vocal_wav"] = result.get("path") or path
        return result
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("voice failed: %s", exc)
        return {"ok": False, "source": "BLOCKED", "reason": f"{type(exc).__name__}: {exc}"}


def _run_pipeline(plan: dict[str, Any], output_root: str,
                  progress: Callable[[str], None] | None,
                  adaptive_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Единственный прогон `HitFactory`: бит, микс, мастер, релиз — всё внутри."""
    from modules.hit_factory.generator import HitFactory

    factory = HitFactory(
        output_root=output_root, min_score=68.0, evolve=True,
        duration_sec=int(plan.get("duration_sec") or 90), verbose=False,
        adaptive_config=adaptive_config,
    )
    if progress:
        progress("HitFactory: бит → микс → мастер → релиз")
    hit = factory.make_one(
        recipe=plan, evolve=False,
    )
    return hit if isinstance(hit, dict) else {}


def _hardware_preflight(recipe: dict[str, Any], output_root: str):
    """Shared Python preflight; the renderer never computes hardware budgets."""
    from app.ai.agent_preflight import preflight_agent_hardware

    return preflight_agent_hardware(recipe, output_root)


def _agent_stages(answers: dict[str, Any], preflight: dict[str, Any],
                  adaptive_config: dict[str, Any], output_root: str, started: float,
                  say: Callable[[str], None]) -> dict[str, Any]:
    """Run non-preflight agent stages after the safe route has been established."""
    trend = _trend(answers.get("mood") or "")
    style = _references(answers.get("refs") or [])
    plan = build_plan(answers, trend, style)
    say(f"Жанр выбран сам: {plan['genre']} · тема «{plan['theme']}»")
    dossier = _dossier(answers.get("artist") or "")
    samples = _samples(plan["genre"])
    lyrics = _lyrics(plan, dossier)
    if lyrics.get("ok"):
        lyrics_text = str(lyrics["text"])
        plan["reference_lyrics"] = lyrics_text
        plan["user_lyrics_lines"] = lyrics_text.splitlines()
        plan["theme"] = plan["theme"] or lyrics_text.splitlines()[0][:60]
    voice = _voice(plan, Path(output_root))
    hit = _run_pipeline(plan, output_root, say, adaptive_config)
    report = _build_agent_report(answers, plan, preflight, started, trend, style,
                                 dossier, samples, lyrics, voice, hit, output_root)
    say(f"Прогон завершён за {report['elapsed_sec']} с: {report['master_path'] or report['agent_failed']}; статус {report['result']['status']}")
    return report


def _build_agent_report(answers, plan, preflight, started, trend, style,
                        dossier, samples, lyrics, voice, hit, output_root) -> dict[str, Any]:
    """Assess stage outputs and preserve the unverified preflight record."""
    from app.pipeline.result import assess_result

    blocked = _blocked_stages(lyrics, voice, samples, style, trend)
    report = {
        "master_reported": bool(hit.get("master_path")), "answers": answers, "plan": plan,
        "trend": trend, "style": style, "dossier": dossier, "samples": samples,
        "lyrics": lyrics, "voice": voice, "hit": hit,
        "master_path": hit.get("master_path"), "hit_score": hit.get("hit_score"),
        "verdict": hit.get("verdict"), "blocked": blocked,
        "hardware_preflight": preflight,
        "elapsed_sec": round(time.time() - started, 1),
        "output_root": str(Path(hit.get("out_root") or output_root)),
        "agent_failed": "" if hit.get("master_path") else "пайплайн не отдал мастер — смотри hit.error",
    }
    report["result"] = assess_result(report, requested_kind="generated_singing")
    report["ok"] = report["result"]["succeeded"]
    report["artifact_available"] = report["result"]["artifact"]["valid"]
    if not report["master_reported"]:
        _LOG.warning("conversation hit failed: %s", report["agent_failed"])
    return report


def run_conversation_hit(payload: dict[str, Any] | None = None,
                         output_root: str = "output/hits",
                         progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Полный прогон агентика: recipe → hardware preflight → Python stages → typed result."""
    started = time.time()
    answers = parse_answers(payload)
    say = progress or (lambda _message: None)
    say(f"Агентик понял: {answer_summary(answers)}")

    # Нормализуем все четыре пользовательских ответа до проверки оборудования.
    # Сеть, анализ референсов, LLM, RVC и HitFactory запускаются только после неё.
    request_recipe = build_plan(answers)
    error = None
    try:
        result = _hardware_preflight(request_recipe, output_root)
    except Exception as exc:  # noqa: BLE001 — preflight failure must stop heavy work
        result, error = None, exc
    from modules.agent_guide.preflight_report import preflight_refusal_report, validate_preflight_result

    preflight, adaptive_config, may_attempt = validate_preflight_result(result, error)
    if not may_attempt:
        return preflight_refusal_report(answers, request_recipe, preflight, output_root, started, say)

    return _agent_stages(answers, preflight, adaptive_config, output_root, started, say)


def _blocked_stages(lyrics: dict[str, Any], voice: dict[str, Any], samples: dict[str, Any],
                    style: dict[str, Any], trend: dict[str, Any]) -> list[dict[str, str]]:
    """Какие ступени честно не сработали. Пустой список — значит всё прошло."""
    stages: list[dict[str, str]] = []
    if not lyrics.get("ok"):
        stages.append({"stage": "lyrics", "reason": str(lyrics.get("reason") or "BLOCKED")})
    if not voice.get("ok"):
        stages.append({"stage": "voice", "reason": str(voice.get("reason") or "BLOCKED")})
    if not samples.get("ok"):
        stages.append({"stage": "samples", "reason": str(samples.get("reason") or "не найдены")})
    if not style.get("ok"):
        stages.append({"stage": "references", "reason": str(style.get("reason") or "не заданы")})
    if not trend.get("ok"):
        stages.append({"stage": "trends", "reason": str(trend.get("reason") or "недоступны")})
    return stages
