# -*- coding: utf-8 -*-
"""ZS Music Maker - app/core/orchestrator_ai.py (v38 GOD MODE 4.0 AI)"""
from __future__ import annotations
import json, shutil
from pathlib import Path
from app.core.logger import app_logger
from app.ai.sequential_runner import SequentialAIRunner, AIStage
from app.ai import prompts as P
from app.ai import llm_service as LLM
from app.ai.quality import (
    validate_audio_artifact,
    validate_cover_artifact,
    validate_master_artifact,
    validate_metadata_json,
    validate_rvc_artifact,
    validate_song_lyrics,
    validate_stereo_texture,
    validate_vocal_artifact,
)
from modules.artist_dossier import DossierManager


def _slug(name: str) -> str:
    import re
    s = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", (name or "").strip()).strip("_")
    return s.lower() or "unknown"


def render_stereo_texture(handle, prompt: str, duration_sec: int, out_path: str) -> dict:
    """Рендерить отдельную стерео-текстуру через совместимый MusicGen handle."""
    try:
        import soundfile as sf

        handle.set_generation_params(
            duration=duration_sec, top_k=250, temperature=1.0, cfg_coef=3.0
        )
        generated = handle.generate([prompt], progress=False)[0].detach().cpu().numpy()
        if generated.ndim == 1:
            generated = generated[:, None]
        elif generated.ndim == 2:
            generated = generated.T
        else:
            return {"ok": False, "reason": "unexpected MusicGen stereo tensor shape"}
        if generated.shape[1] == 1:
            generated = generated.repeat(2, axis=1)
        sf.write(out_path, generated.astype("float32"), int(getattr(handle, "sample_rate", 32000)),
                 subtype="PCM_16")
        return {"ok": True, "texture_path": out_path}
    except Exception as exc:
        return {"ok": False, "reason": f"music_stereo generation failed: {exc}"}


def extend_beat_with_stereo_sections(
    base_path: str,
    intro_path: str,
    outro_path: str,
    out_path: str,
    fade_sec: float = 1.0,
) -> dict:
    """Stitch generated stereo intro/outro around a beat using equal-power fades."""
    try:
        import numpy as np
        import soundfile as sf

        def stereo(data):
            array = np.asarray(data, dtype="float32")
            if array.ndim == 1:
                return np.column_stack((array, array))
            if array.ndim != 2:
                raise ValueError("audio must be mono or stereo")
            if array.shape[1] == 1:
                return np.repeat(array, 2, axis=1)
            return array[:, :2]

        def resample(data, from_sr: int, to_sr: int):
            if from_sr == to_sr:
                return data
            from scipy.signal import resample_poly
            from math import gcd
            divisor = gcd(from_sr, to_sr)
            return resample_poly(data, to_sr // divisor, from_sr // divisor, axis=0).astype("float32")

        def crossfade(left, right, samples: int):
            overlap = min(samples, len(left), len(right))
            if overlap <= 0:
                return np.vstack((left, right))
            phase = np.linspace(0.0, np.pi / 2.0, overlap, endpoint=False, dtype="float32")
            mixed = left[-overlap:] * np.cos(phase)[:, None] + right[:overlap] * np.sin(phase)[:, None]
            return np.vstack((left[:-overlap], mixed, right[overlap:]))

        base, sample_rate = sf.read(base_path, always_2d=False)
        intro, intro_rate = sf.read(intro_path, always_2d=False)
        outro, outro_rate = sf.read(outro_path, always_2d=False)
        base = stereo(base)
        intro = resample(stereo(intro), int(intro_rate), int(sample_rate))
        outro = resample(stereo(outro), int(outro_rate), int(sample_rate))
        fade_samples = max(1, int(float(fade_sec) * sample_rate))
        stitched = crossfade(crossfade(intro, base, fade_samples), outro, fade_samples)
        peak = float(np.max(np.abs(stitched))) if len(stitched) else 0.0
        if peak > 0.98:
            stitched *= 0.98 / peak
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(target, stitched, int(sample_rate), subtype="PCM_16")
        return {
            "ok": True,
            "beat_path": str(target),
            "sample_rate": int(sample_rate),
            "channels": 2,
            "duration_sec": len(stitched) / sample_rate,
            "fade_sec": float(fade_sec),
        }
    except Exception as exc:
        return {"ok": False, "reason": f"stereo beat extension failed: {exc}"}


def render_xtts_vocal(handle, text: str, out_path: str, speaker_wav: str | None = None) -> dict:
    """Синтезировать вокал через совместимый XTTS handle и подтвердить файл-результат."""
    try:
        kwargs = {"text": text, "file_path": out_path, "language": "ru"}
        if speaker_wav and Path(speaker_wav).exists():
            kwargs["speaker_wav"] = speaker_wav
        handle.tts_to_file(**kwargs)
        target = Path(out_path)
        if not target.exists() or target.stat().st_size <= 100:
            return {"ok": False, "reason": "XTTS did not produce an audio file"}
        quality = validate_vocal_artifact(target, text)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "xtts_v2",
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"XTTS synthesis failed: {exc}"}


def render_voice_synth_fallback(text: str, out_path: str, synth_fn=None) -> dict:
    """Запустить существующую честную TTS-цепочку и привести результат к vocal-артефакту проекта."""
    try:
        if synth_fn is None:
            from modules.voice_synth import synth as synth_fn
        source_path = synth_fn(text, engine="auto", out_name=Path(out_path).name)
        source = Path(source_path) if source_path else None
        if source is None or not source.exists():
            return {"ok": False, "reason": "no fallback TTS engine produced audio"}
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        quality = validate_vocal_artifact(target, text)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "voice_synth_fallback",
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"fallback TTS failed: {exc}"}


def render_rvc_vocal(handle, input_wav: str, out_path: str, voice_name: str, pitch_shift: int = 0) -> dict:
    """Выполнить RVC через публичный ``rvc_manager.infer`` и сохранить проектный артефакт."""
    try:
        safe_voice_name = Path(voice_name).name
        if not safe_voice_name:
            return {"ok": False, "reason": "RVC voice name is missing"}
        produced = handle.infer(
            input_wav=input_wav,
            voice_name=safe_voice_name,
            pitch_shift=int(pitch_shift),
            out_name=Path(out_path).name,
        )
        source = Path(produced) if produced else None
        if source is None or not source.exists() or source.stat().st_size <= 100:
            return {"ok": False, "reason": "RVC did not produce an audio file"}
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        quality = validate_rvc_artifact(input_wav, target)
        return {
            "ok": bool(quality["ok"]),
            "vocal_path": str(target),
            "engine": "rvc",
            "voice_name": safe_voice_name,
            "pitch_shift": int(pitch_shift),
            "quality": quality,
            "reason": quality["reason"],
        }
    except Exception as exc:
        return {"ok": False, "reason": f"RVC inference failed: {exc}"}


def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
    ws = dict(wizard_state or {})
    try:
        from config.settings import get_settings
        cfg = get_settings()
        app_logger.info(f"[orchestrator_ai] config_path={cfg.config_path} vram_gb={cfg.vram_gb}")
    except Exception:  # noqa: BLE001
        cfg = None
    ws.setdefault("genre", "drift_phonk")
    ws.setdefault("theme", "движ, ночь, город")
    ws.setdefault("bpm", 140)
    ws.setdefault("key", "A minor")
    ws.setdefault("mood", "dark, hypnotic, energetic")
    ws.setdefault("n_verses", 2)
    ws.setdefault("bilingual", True)
    ws.setdefault("duration_sec", 120)
    if not out_root:
        out_root = Path(__file__).resolve().parents[2] / "output" / project_id
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "masters").mkdir(exist_ok=True)
    artist_slug = _slug(ws["artist_slug"]) if ws.get("artist_slug") else None
    ref_track_id = ws.get("track_id")

    def stage_hw(_, ctx):
        try:
            from app.core.hw_autodetect import get_hardware_profile
            return get_hardware_profile()
        except Exception as e:
            return {"error": str(e)}

    def stage_dossier_load(_, ctx):
        if not artist_slug:
            return {"skipped": "no artist_slug"}
        mgr = DossierManager()
        return {"artist_dossier": mgr.get_artist_dossier(artist_slug),
                "track_dossier": mgr.get_track_dossier(artist_slug, ref_track_id) if ref_track_id else None}

    def stage_lyrics(handle, ctx):
        if dry_run:
            return {"ok": True, "lyrics": "[dry-run]", "source": "dry"}
        requested_lines = ws.get("user_lyrics_lines") or []
        text, source = "", "lyrics_llm"
        quality = {"ok": False, "reason": "lyrics_llm unavailable", "metrics": {}}
        if handle is not None:
            try:
                from modules.lyrics_gen_ai import generate_lyrics_ai

                ai_result = generate_lyrics_ai(
                    theme=ws["theme"],
                    style_vector={"target_bpm": ws["bpm"]},
                    n_verses=ws["n_verses"],
                    user_lyrics_lines=requested_lines,
                    bilingual=ws["bilingual"],
                    artist_slug=artist_slug,
                    track_id=ref_track_id,
                    genre=ws["genre"],
                    handle=handle,
                )
                text = str(ai_result.get("lyrics") or "")
                source = str(ai_result.get("source") or "lyrics_llm")
                quality = validate_song_lyrics(text, user_lines=requested_lines)
            except Exception as exc:  # noqa: BLE001
                app_logger.error("[orchestrator_ai] stage=lyrics event=ai_failed reason=%s", exc)
                quality = {"ok": False, "reason": f"lyrics_ai failed: {exc}", "metrics": {}}
        if not quality["ok"]:
            try:
                from modules import lyrics_gen

                fallback = lyrics_gen.generate_lyrics(
                    theme=ws["theme"],
                    style_vector={"target_bpm": ws["bpm"]},
                    n_verses=ws["n_verses"],
                    user_lyrics_lines=requested_lines,
                    bilingual=ws["bilingual"],
                )
                text = str(fallback.get("lyrics") or "")
                source = "punch_lib_fallback"
                quality = validate_song_lyrics(text, user_lines=requested_lines)
            except Exception as exc:  # noqa: BLE001
                app_logger.error("[orchestrator_ai] stage=lyrics event=fallback_failed reason=%s", exc)
        (out_root / "lyrics.txt").write_text(text or "", encoding="utf-8")
        return {"ok": bool(quality["ok"]), "lyrics": text, "source": source,
                "path": str(out_root / "lyrics.txt"), "quality": quality,
                "reason": quality["reason"]}

    def _metadata_fallback() -> dict[str, object]:
        """Create genre-aware metadata that satisfies the release quality contract."""
        genre = str(ws.get("genre") or "music").strip() or "music"
        theme = " ".join(str(ws.get("theme") or "").split()).strip()
        mood = " ".join(str(ws.get("mood") or "").split()).strip() or "выразительное"
        title = theme[:80] or f"{genre.title()} Pulse"
        if len(title) < 3:
            title = f"{genre.title()} Pulse"
        return {
            "title": title,
            "spotify_desc": (
                f"Независимый {genre}-релиз «{title}» с настроением {mood}. "
                "Трек создан для внимательного прослушивания и ночной дороги."
            )[:400],
            "youtube_desc": (
                f"«{title}» — новый {genre}-трек о теме «{theme or title}» и настроении {mood}. "
                "Слушайте релиз, сохраняйте и делитесь с теми, кому близен этот звук."
            )[:400],
            "tags_tiktok": [genre, "newmusic", "independent"],
            "tags_instagram": ["music", "release", "underground"],
        }

    def stage_metadata(handle, ctx):
        lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
        fallback = _metadata_fallback()
        source = "metadata_fallback"
        if dry_run:
            js, source = fallback, "dry"
        elif handle is not None:
            js = LLM.complete_json(handle, P.SYSTEM_METADATA,
                P.build_metadata_prompt(ws["theme"], ws["genre"], lyrics),
                max_tokens=1200, temperature=0.6) or {}
            source = "metadata_llm"
        else:
            js = fallback
        quality = validate_metadata_json(js)
        if not quality["ok"]:
            js, source = fallback, "metadata_fallback"
            quality = validate_metadata_json(js)
        js = dict(js)
        js.update({"ok": bool(quality["ok"]), "source": source, "quality": quality,
                   "reason": quality["reason"]})
        (out_root / "metadata.json").write_text(
            json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")
        return js

    def stage_music(handle, ctx):
        if dry_run:
            return {"ok": True, "beat_path": "[dry]"}
        out_path = str(out_root / "beat.wav")
        if handle is None:
            try:
                from modules.cyber_synth import CyberSynth

                result = CyberSynth().synthesize_track(
                    bpm=ws["bpm"], duration_sec=ws["duration_sec"], out_path=out_path
                )
                result = dict(result) if isinstance(result, dict) else {}
                result["engine"] = "cyber_synth_fallback"
                result["beat_path"] = out_path
            except Exception as exc:
                return {"ok": False, "reason": f"no music engine: {exc}"}
        else:
            art = (ctx["sink"].get("dossier_load") or {}).get("artist_dossier")
            track = (ctx["sink"].get("dossier_load") or {}).get("track_dossier")
            instruments = track.get("reusable_elements", [])[:5] if isinstance(track, dict) else []
            reference_features = {
                "instruments": instruments,
                "atmosphere": (art or {}).get("flow", ""),
            } if art else None
            prompt = P.build_music_prompt(
                ws["genre"], ws["bpm"], ws["key"], ws["mood"],
                reference_artist=ws.get("reference_artist") or ws.get("artist_slug"),
                reference_track_features=reference_features,
            )
            from modules.beat_gen_ai import render_beat_ai

            result = render_beat_ai(
                prompt=prompt,
                bpm=ws["bpm"],
                duration_sec=ws["duration_sec"],
                out_path=out_path,
                reference_wav=ws.get("reference_wav"),
                handle=handle,
            )
            result["prompt"] = prompt
        quality = validate_audio_artifact(
            out_path, min_duration_sec=max(1.0, min(5.0, ws["duration_sec"] * 0.5))
        )
        result["quality"] = quality
        result["reason"] = quality["reason"]
        result["ok"] = bool(result.get("ok", True)) and bool(quality["ok"])
        return result

    def stage_music_stereo(handle, ctx):
        """Extend the base beat with MusicGen stereo intro/outro through crossfades."""
        if dry_run:
            return {"skipped": "dry-run", "fallback": "base beat is preserved"}
        base_beat = (ctx["sink"].get("music") or {}).get("beat_path")
        if not base_beat or not Path(base_beat).exists():
            return {"skipped": "no base beat", "fallback": "base beat is unavailable"}
        if handle is None:
            return {
                "skipped": "music_stereo unavailable",
                "reason": "audiocraft model is not installed or not loadable",
                "fallback": "base beat is preserved without a synthetic extension",
            }
        prompt = P.build_music_prompt(ws["genre"], ws["bpm"], ws["key"], ws["mood"])
        duration = max(2, min(int(ws.get("texture_duration_sec", 8)), 20))
        intro_path = str(out_root / "texture_intro_stereo.wav")
        outro_path = str(out_root / "texture_outro_stereo.wav")
        intro = render_stereo_texture(
            handle, prompt + ", wide stereo intro, gentle fade-in, no lead vocal", duration, intro_path
        )
        outro = render_stereo_texture(
            handle, prompt + ", wide stereo outro, resolving fade-out, no lead vocal", duration, outro_path
        )
        for section in (intro, outro):
            path = section.get("texture_path")
            if not section.get("ok") or not path:
                return {
                    "skipped": "music_stereo generation failed",
                    "reason": section.get("reason", "texture did not render"),
                    "fallback": "base beat is preserved without a synthetic extension",
                }
            quality = validate_stereo_texture(path, min_duration_sec=max(1.0, duration * 0.5))
            if not quality["ok"]:
                return {
                    "skipped": "music_stereo quality rejected",
                    "reason": quality["reason"],
                    "fallback": "base beat is preserved without a synthetic extension",
                }
        result = extend_beat_with_stereo_sections(
            str(base_beat),
            str(intro["texture_path"]),
            str(outro["texture_path"]),
            str(out_root / "beat_stereo_extended.wav"),
            fade_sec=float(ws.get("texture_crossfade_sec", 1.0)),
        )
        if not result.get("ok"):
            result.update({"skipped": "stereo extension failed", "fallback": "base beat is preserved"})
            return result
        quality = validate_audio_artifact(result["beat_path"], min_duration_sec=1.0)
        result.update({
            "ok": bool(quality["ok"]),
            "quality": quality,
            "reason": quality["reason"],
            "engine": "musicgen-stereo-medium",
            "intro_path": intro["texture_path"],
            "outro_path": outro["texture_path"],
            "extension_sec": duration * 2,
        })
        return result

    def stage_vocal(handle, ctx):
        if dry_run:
            return {"skipped": "dry-run"}
        lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
        if not lyrics.strip():
            return {"skipped": "no lyrics"}
        import re
        clean = re.sub(r"^\[.*?\]\s*$", "", lyrics, flags=re.MULTILINE).strip()
        clean = re.sub(r"\n{3,}", "\n\n", clean)[:3500]
        out_path = str(out_root / "vocal_xtts.wav")
        speaker_wav = ws.get("speaker_wav")
        if not speaker_wav:
            try:
                from modules.voice_vault_v9 import select_speaker_wav
                speaker_wav = select_speaker_wav(ws.get("vocal_style"))
            except Exception:
                speaker_wav = None
        if handle is not None:
            from modules.voice_synth_ai import synth_vocal_ai

            primary = synth_vocal_ai(
                clean,
                out_path,
                speaker_wav=speaker_wav,
                language="ru",
                tts_handle=handle,
            )
            if primary.get("ok"):
                return primary
        else:
            primary = {"ok": False, "reason": "XTTS model unavailable"}
        fallback = render_voice_synth_fallback(clean, out_path)
        fallback["xtts_attempt"] = primary.get("reason")
        return fallback

    def stage_rvc(handle, ctx):
        if dry_run:
            return {"skipped": "dry-run"}
        if handle is None:
            return {"skipped": "RVC unavailable", "reason": "no installed RVC model/runtime"}
        vocal = (ctx["sink"].get("vocal_synth") or {}).get("vocal_path")
        if not vocal or not Path(vocal).exists():
            return {"skipped": "no vocal"}
        voice_name = ws.get("rvc_voice_name") or Path(str(ws.get("rvc_model") or "")).stem
        if not voice_name:
            return {"skipped": "no rvc_voice_name"}
        out_path = str(out_root / "vocal_rvc.wav")
        return render_rvc_vocal(
            handle,
            vocal,
            out_path,
            voice_name=voice_name,
            pitch_shift=int(ws.get("rvc_pitch_shift", 0)),
        )

    def stage_mix(_, ctx):
        beat = ((ctx["sink"].get("music_stereo") or {}).get("beat_path")
                or (ctx["sink"].get("music") or {}).get("beat_path"))
        vocal = ((ctx["sink"].get("rvc") or {}).get("vocal_path")
                 or (ctx["sink"].get("vocal_synth") or {}).get("vocal_path"))
        texture = (ctx["sink"].get("music_stereo") or {}).get("texture_path")
        mix_path = str(out_root / "mix.wav")
        if not beat or not Path(beat).exists():
            return {"skipped": "no beat"}
        try:
            import numpy as np, soundfile as sf
            b, sr_b = sf.read(beat)
            if b.ndim == 1:
                b = np.stack([b, b], axis=-1)
            texture_mixed = False
            if texture and Path(texture).exists():
                t, sr_t = sf.read(texture)
                if sr_t != sr_b:
                    import librosa
                    t = librosa.resample(t.T if t.ndim > 1 else t, orig_sr=sr_t, target_sr=sr_b)
                    t = t.T if t.ndim > 1 else t
                if t.ndim == 1:
                    t = np.stack([t, t], axis=-1)
                n_texture = min(len(b), len(t))
                beat_rms = float(np.sqrt(np.mean(b[:n_texture] ** 2)) + 1e-9)
                texture_rms = float(np.sqrt(np.mean(t[:n_texture] ** 2)) + 1e-9)
                texture_gain = (beat_rms * (10.0 ** (-18.0 / 20.0))) / texture_rms
                b[:n_texture] = b[:n_texture] + t[:n_texture] * min(texture_gain, 1.0)
                texture_mixed = True
            if not vocal or not Path(vocal).exists():
                peak = float(np.max(np.abs(b)) + 1e-9)
                if peak > 0.99:
                    b = b * (0.98 / peak)
                sf.write(mix_path, b, sr_b)
                return {"ok": True, "mix_path": mix_path, "vocal": False, "texture_mixed": texture_mixed}
            v, sr_v = sf.read(vocal)
            if sr_v != sr_b:
                import librosa
                v = librosa.resample(v.T if v.ndim > 1 else v, orig_sr=sr_v, target_sr=sr_b)
                v = v.T if v.ndim > 1 else v
            if v.ndim == 1:
                v = np.stack([v, v], axis=-1)
            n = min(len(b), len(v))
            mix = b[:n] * 0.9 + v[:n] * 0.75
            peak = float(np.max(np.abs(mix)) + 1e-9)
            if peak > 0.99:
                mix = mix * (0.98 / peak)
            sf.write(mix_path, mix, sr_b)
            return {"ok": True, "mix_path": mix_path, "vocal": True, "texture_mixed": texture_mixed}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def stage_master(handle, ctx):
        mix = (ctx["sink"].get("mix") or {}).get("mix_path")
        if not mix:
            return {"skipped": "no mix"}
        out_master = str(out_root / "masters" / "master_ai.wav")
        from modules.mastering_ai import master_ai
        result = master_ai(
            mix,
            out_master,
            reference_wav=ws.get("reference_master_wav"),
            target_lufs=-14.0,
            handle=handle,
        )
        if result.get("ok") and result.get("path"):
            quality = validate_master_artifact(
                mix, result["path"], max_true_peak_dbtp=-1.0
            )
            result["quality"] = quality
            result["ok"] = bool(quality["ok"])
            result["reason"] = quality["reason"]
        return result

    def stage_cover(handle, ctx):
        meta = ctx["sink"].get("metadata") or {}
        title = meta.get("title") or ws.get("theme", "Untitled")
        artist = ws.get("artist_display") or ws.get("artist_slug") or "ZS"
        from modules.cover_art_ai import render_cover_ai
        result = render_cover_ai(
            title=title,
            artist=artist,
            genre=ws["genre"],
            mood=ws["mood"],
            out_path=str(out_root / "cover.png"),
            handle=handle,
        )
        if result.get("ok") and result.get("path"):
            quality = validate_cover_artifact(
                result["path"], min_size=1024, min_bytes=100_000
            )
            result["ok"] = bool(quality["ok"])
            result["quality"] = quality
            result["reason"] = quality["reason"]
        return result

    def stage_tag(bundle, ctx):
        if bundle is None:
            return {"skipped": "no clap"}
        master = ((ctx["sink"].get("master") or {}).get("path")
                  or str(out_root / "masters" / "master_ai.wav"))
        if not Path(master).exists():
            return {"skipped": "no master"}
        try:
            import torch, librosa, numpy as np
            model, proc = bundle
            y, sr = librosa.load(master, sr=48000, mono=True, duration=30)
            cand = ["phonk", "trap", "drill", "pop", "rock", "shanson",
                    "aggressive", "melancholic", "party", "romantic"]
            inputs = proc(text=cand, audios=y, sampling_rate=48000,
                          return_tensors="pt", padding=True)
            if any(p.is_cuda for p in model.parameters()):
                inputs = {k: (v.cuda() if hasattr(v, "cuda") else v)
                          for k, v in inputs.items()}
            with torch.no_grad():
                logits = model(**inputs).logits_per_audio[0].cpu().numpy()
            tags = [cand[i] for i in np.argsort(-logits)[:5]]
            return {"ok": True, "tags": tags, "goal": ws["genre"],
                    "match_genre": ws["genre"] in tags}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    runner = SequentialAIRunner()
    runner.add(AIStage("hw_check",     None,               stage_hw))
    runner.add(AIStage("dossier_load", None,               stage_dossier_load))
    runner.add(AIStage("lyrics",       "lyrics_llm",       stage_lyrics,   optional=True))
    runner.add(AIStage("metadata",     "metadata_llm",     stage_metadata, optional=True))
    runner.add(AIStage("music",        "music_generation", stage_music,    optional=True))
    runner.add(AIStage("music_stereo", "music_stereo",     stage_music_stereo, optional=True))
    runner.add(AIStage("vocal_synth",  "tts_vocal",        stage_vocal,    optional=True))
    runner.add(AIStage("rvc",          "vocal_rvc",        stage_rvc,      optional=True))
    runner.add(AIStage("mix",          None,               stage_mix))
    runner.add(AIStage(
        "master",
        "mastering_ai" if ws.get("reference_master_wav") else None,
        stage_master,
        optional=True,
    ))
    runner.add(AIStage("cover",        "cover_art",        stage_cover,    optional=True))
    runner.add(AIStage("tag",          "audio_tagger",     stage_tag,      optional=True))
    report = runner.run({"project_id": project_id, "wizard_state": ws})
    result = {"project_id": project_id, "god_mode": "4.0-AI", "wizard_state": ws,
              "report": report.to_dict(),
              "config": cfg.dump() if cfg is not None else None,
              "artefacts": {"lyrics": str(out_root / "lyrics.txt"),
                            "metadata": str(out_root / "metadata.json"),
                            "beat": str(out_root / "beat.wav"),
                            "texture_stereo": str(out_root / "texture_stereo.wav"),
                            "vocal": str(out_root / "vocal_xtts.wav"),
                            "mix": str(out_root / "mix.wav"),
                            "master": str(out_root / "masters" / "master_ai.wav"),
                            "cover": str(out_root / "cover.png")}}
    (out_root / "project_meta.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    from app.ai.registry import MODEL_REGISTRY
    manifest = {
        "schema_version": 1,
        "project_id": project_id,
        "generator": "ZS Music Maker AI pipeline",
        "wizard_state": ws,
        "stages": result["report"].get("stages", []),
        "model_roles": {
            key: {"engine": spec["engine"], "file": spec.get("file", ""),
                  "hf_repo": spec.get("hf_repo", "")}
            for key, spec in MODEL_REGISTRY.items()
        },
        "artefacts": result["artefacts"],
    }
    manifest_path = out_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    result["manifest_path"] = str(manifest_path)
    app_logger.info(f"[orchestrator_ai] finished project={project_id}")
    return result
