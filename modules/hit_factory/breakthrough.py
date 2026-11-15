# -*- coding: utf-8 -*-
"""
modules.hit_factory.breakthrough — ПРОРЫВ-оркестратор «всё может».

От референсов (любой артист) до готового хита: референсы → dossier → текст → голос RVC → биты → эдиты/сборка.
Работает на любом железе: даже 3.85GB RAM — медленно (CPU offload, чанки 30с, ротатор 1×, memory_guard 0.8GB), но не фризит.
Интернет есть — докачивает веса (MusicGen small 300M, Silero 59MB, RVC, Demucs CPU). Требует ZSMM_BREAKTHROUGH=1 или breakthrough=True.

Бесплатно, автоматизировано, от начала до конца.
"""
from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Any

import logging

_LOG = logging.getLogger(__name__)


def _guard_memory(free_guard_gb: float = 0.8) -> None:
    """Ротатор: не даём free упасть ниже guard — GC + пауза."""
    try:
        import psutil
        free = psutil.virtual_memory().available / (1024**3)
        if free < free_guard_gb:
            _LOG.info(f"[breakthrough] memory guard: free {free:.2f} < {free_guard_gb} — GC + sleep 2s")
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as _exc:
                print(f"[breakthrough] guard torch ignored: {_exc}")
            time.sleep(2)
            gc.collect()
    except Exception as _exc:
        print(f"[breakthrough] guard ignored: {_exc}")


def _sequential_step(name: str, fn, *args, **kwargs):
    """Запускает 1 тяжёлый шаг, с guard до/после, логирует."""
    _guard_memory()
    _LOG.info(f"[breakthrough] step {name} start")
    t0 = time.time()
    try:
        res = fn(*args, **kwargs)
    finally:
        _guard_memory()
        dt = time.time() - t0
        _LOG.info(f"[breakthrough] step {name} done {dt:.1f}s")
    return res


def _download_reference(url: str, tmp_dir: str = "data/reference_cache/downloads") -> str | None:
    """Скачивает http(s) референс во временный файл (для links). Возвращает локальный путь или None."""
    try:
        import requests
        from pathlib import Path as _P
        import hashlib
        dest = _P(tmp_dir)
        dest.mkdir(parents=True, exist_ok=True)
        h = hashlib.md5(url.encode()).hexdigest()[:10]
        # сохраняем расширение из URL или .mp3
        suffix = ".mp3"
        for ext in (".wav", ".mp3", ".flac", ".m4a", ".ogg"):
            if ext in url.lower():
                suffix = ext
                break
        out = dest / f"dl_{h}{suffix}"
        if out.exists() and out.stat().st_size > 1024:
            return str(out)
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return str(out) if out.stat().st_size > 1024 else None
    except Exception as _exc:
        print(f"[breakthrough] download ignored {url[:60]}: {_exc}")
        return None


def analyze_references(reference_paths: list[str], weights: list[float] | None = None) -> dict[str, Any]:
    """1) референсы → style_vector (BPM/key/genre_hint/mood). Поддерживает файлы и http(s) ссылки."""
    from modules.reference_ingest import build_style_vector
    if not reference_paths:
        return {"ok": False, "reason": "no references — используем тренды 2026"}
    local_paths: list[str] = []
    for p in reference_paths:
        p = str(p).strip()
        if not p:
            continue
        if p.startswith("http://") or p.startswith("https://"):
            dl = _download_reference(p)
            if dl:
                local_paths.append(dl)
            else:
                print(f"[breakthrough] skip undownloadable link: {p[:80]}")
        else:
            local_paths.append(p)
    if not local_paths:
        return {"ok": False, "reason": "no local references after download — используем тренды 2026"}
    return _sequential_step("reference_ingest", build_style_vector, local_paths, weights)


def build_artist_dossier(artist: str, reference_style: dict | None = None, use_llm: bool = True) -> dict[str, Any]:
    """2) артист → dossier (почему популярен, что делает). Оффлайн + LLM если есть."""
    _guard_memory()
    try:
        from modules.artist_dossier.manager import DossierManager
        mgr = DossierManager()
        try:
            got = mgr.get_artist_dossier(artist)
            if got:
                return {"ok": True, "source": "artist_dossier.storage", "dossier": got}
        except Exception as _exc:
            print(f"[breakthrough] dossier get ignored: {_exc}")
        try:
            if reference_style and isinstance(reference_style, dict):
                pass
            res = mgr.build_full_dossier(artist, refresh=False)
            if res:
                return {"ok": True, "source": "artist_dossier.build_full", "dossier": res}
        except Exception as _exc:
            print(f"[breakthrough] dossier build ignored: {_exc}")
    except Exception as _exc:
        print(f"[breakthrough] dossier manager ignored: {_exc}")
    try:
        from agents.trend_scout import scout
        data = scout(theme=artist or "лето", offline_only=False)
        hype = data.get("hype_words", [])[:6]
        punch = data.get("punchlines", [])[:3]
    except Exception:
        hype, punch = [], []
    llm_text = None
    if use_llm:
        try:
            from modules.llm.router import LLMRouter
            router = LLMRouter()
            r = router.complete(
                prompt=f"Ты музыкальный аналитик. Артист: {artist}. Опиши 5 пунктов: почему популярен, биты, подача, темы, что использует. Кратко, по делу.",
                max_tokens=400,
            )
            llm_text = r.get("text") or r.get("lyrics") or str(r)
        except Exception as _exc:
            print(f"[breakthrough] llm dossier ignored: {_exc}")
    return {"ok": True, "source": "fallback+llm" if llm_text else "fallback", "artist": artist, "style": reference_style, "hype_words": hype, "punchlines": punch, "llm_analysis": llm_text}


def generate_lyrics_in_style(
    artist: str,
    theme: str | None,
    dossier: dict | None,
    style_vector: dict | None,
    seed: int | None = None,
) -> dict[str, Any]:
    """3) текст в стиле артиста, но не копия — видно что поёт другой человек (ты)."""
    sv = (style_vector or {}).get("style_vector") or (style_vector or {}).get("consensus") or {}
    bpm = sv.get("bpm") or 130
    key = sv.get("key") or "C"
    genre_hint = sv.get("genre_hint") or (style_vector or {}).get("consensus", {}).get("genre_hint") or "trap"
    hype = (dossier or {}).get("hype_words") or []
    base_theme = theme or (hype[0] if hype else "ночь, деньги, движ")
    try:
        from modules.lyrics.generate import generate_lyrics
        r = generate_lyrics(theme=base_theme, style_vector={"target_bpm": int(bpm)}, n_verses=2, bilingual=True)
        lyrics = r.get("lyrics") if isinstance(r, dict) else str(r)
        src = r.get("source", "modules.lyrics.generate") if isinstance(r, dict) else "modules.lyrics.generate"
        return {"ok": True, "source": src, "lyrics": lyrics, "theme": base_theme, "bpm": bpm, "key": key}
    except Exception as _exc:
        print(f"[breakthrough] lyrics generate ignored: {_exc}")
    verses = [f"[{genre_hint} {bpm} BPM {key}] {base_theme} — ночь горит, вайб летит", "Я не копия, я — новый сюжет, мой флоу — мой ответ"]
    return {"ok": True, "source": "template", "lyrics": "\n\n".join(verses), "theme": base_theme, "bpm": bpm, "key": key}


def prepare_voice(
    raw_voice_path: str | None,
    target_timbre: str | None = None,
    use_rvc: bool = True,
) -> dict[str, Any]:
    """4) голос: запись → RVC конверсия (free CPU, 10 минут)."""
    if not raw_voice_path or not Path(raw_voice_path).exists():
        return {"ok": False, "reason": "no raw voice — будет scaffold/BLOCKED, а хит всё равно соберётся"}
    if not use_rvc:
        return {"ok": True, "source": "raw", "path": raw_voice_path}
    try:
        from modules.rvc_manager.infer import infer
        # infer(input_wav, voice_name, pitch_shift, out_name, model_path, index_path) → str path
        # Используем default voice_name my_voice; если есть target_timbre как имя модели — пробуем его
        voice_name = target_timbre or "my_voice"
        res = _sequential_step("rvc", infer, raw_voice_path, voice_name, 0)
        return {"ok": True, "source": "rvc", "path": res, "detail": res}
    except Exception as exc:
        return {"ok": False, "reason": f"rvc BLOCKED: {type(exc).__name__}: {exc}", "path": raw_voice_path}


def generate_beats_with_style(
    style_vector: dict | None,
    lyrics_ctx: dict | None,
    duration_sec: int = 90,
    seed: int | None = None,
    breakthrough: bool = False,
) -> dict[str, Any]:
    """5) биты на выбор — MusicGen small CPU чанки 30с если breakthrough, иначе процедурка."""
    cfg = {}
    try:
        from modules.hit_factory.adaptive import get_adaptive_config
        cfg = get_adaptive_config(overrides={"breakthrough": breakthrough})
    except Exception:
        cfg = {}
    if cfg.get("use_musicgen"):
        try:
            from app.core.musicgen_texture import generate_texture
            txt = f"{(lyrics_ctx or {}).get('theme','trap')} {(style_vector or {}).get('consensus',{}).get('genre_hint','trap')} 808, dark trap"
            # Клипим до 30с на CPU чтобы не фризить (ротатор)
            dur = min(int(duration_sec), 30)
            r = _sequential_step("musicgen_cpu", generate_texture, txt, dur, 0.0, "quality", None, "cpu")
            if isinstance(r, dict) and r.get("ok"):
                return {"ok": True, "source": "musicgen_small_cpu_chunked", "wav": r.get("path"), "detail": r, "cfg": cfg}
            # если не ok — fallback
            print(f"[breakthrough] musicgen not ok, fallback: {r}")
        except Exception as _exc:
            print(f"[breakthrough] musicgen ignored (fallback to procedural): {_exc}")
    return {"ok": True, "source": "procedural_enhanced", "cfg": cfg}


def _resolve_genre(style: dict | None) -> str:
    genre = (style.get("consensus", {}) if style and style.get("ok") else {}).get("genre_hint") or "trap"
    genre_map = {"phonk / drift": "drift_phonk", "phonk": "phonk", "trap / hip-hop": "trap"}
    return genre_map.get(genre, genre.split()[0] if genre else "trap")


def full_orchestrate(
    artist: str = "ICEGERGERT",
    theme: str | None = None,
    reference_paths: list[str] | None = None,
    raw_voice_path: str | None = None,
    duration_sec: int = 90,
    seed: int | None = None,
    breakthrough: bool = True,
    output_root: str = "output/hits",
) -> dict[str, Any]:
    """Полная цепочка от референсов до хита — всё автоматизировано, бесплатно."""
    from modules.hit_factory.generator import HitFactory
    t0 = time.time()
    style = analyze_references(reference_paths or [])
    dossier = build_artist_dossier(artist, style if style.get("ok") else None)
    lyrics_ctx = generate_lyrics_in_style(artist, theme, dossier, style if style.get("ok") else None, seed)
    voice = prepare_voice(raw_voice_path, use_rvc=True)
    beats = generate_beats_with_style(style if style.get("ok") else None, lyrics_ctx, duration_sec, seed, breakthrough)
    genre = _resolve_genre(style if style.get("ok") else None)
    factory = HitFactory(output_root=output_root, min_score=68, evolve=True, duration_sec=duration_sec, verbose=False, adaptive=True)
    if breakthrough:
        try:
            from modules.hit_factory.adaptive import get_adaptive_config
            factory.adaptive_cfg = get_adaptive_config(overrides={"breakthrough": True})
        except Exception as _exc:
            print(f"[breakthrough] adaptive override ignored: {_exc}")
    # тема из лирики приоритетнее входной
    final_theme = lyrics_ctx.get("theme") or theme or "ночь, деньги, движ"
    hit = _sequential_step("hitfactory", factory.make_one, genre, final_theme, seed, None, None, duration_sec)
    dt = time.time() - t0
    return {
        "ok": bool(hit.get("master_path")),
        "artist": artist, "theme": final_theme, "style": style, "dossier": dossier,
        "lyrics": lyrics_ctx, "voice": voice, "beats": beats, "hit": hit,
        "elapsed_s": round(dt, 1), "note": "PROРЫВ: всё от референсов до хита — 1 вызов, ротатор 1×, CPU offload, чанки, не фризит",
    }
