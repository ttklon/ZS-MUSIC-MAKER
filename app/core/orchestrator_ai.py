# -*- coding: utf-8 -*-
"""ZS Music Maker - app/core/orchestrator_ai.py (v38 GOD MODE 4.0 AI)"""
from __future__ import annotations
import json, math
from pathlib import Path
from app.core.logger import app_logger
from app.ai.sequential_runner import SequentialAIRunner, AIStage
from app.ai import prompts as P
from app.ai import llm_service as LLM
from modules.artist_dossier import DossierManager


def _slug(name: str) -> str:
    import re
    s = re.sub(r"[^A-Za-z0-9а-яА-ЯёЁ_-]+", "_", (name or "").strip()).strip("_")
    return s.lower() or "unknown"


def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
    ws = dict(wizard_state or {})
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
        art = (ctx["sink"].get("dossier_load") or {}).get("artist_dossier")
        trk = (ctx["sink"].get("dossier_load") or {}).get("track_dossier")
        text, source = "", "lyrics_llm"
        if handle is not None:
            prompt = P.build_lyrics_prompt(theme=ws["theme"], genre=ws["genre"], bpm=ws["bpm"],
                n_verses=ws["n_verses"], bilingual=ws["bilingual"],
                user_lines=ws.get("user_lyrics_lines"),
                artist_dossier=art, track_reference=trk)
            text = LLM.complete(handle, P.SYSTEM_LYRICS, prompt, max_tokens=1400,
                                temperature=0.9, repeat_penalty=1.15)
        if not text or len(text) < 60:
            try:
                from modules import lyrics_gen
                r = lyrics_gen.generate_lyrics(theme=ws["theme"],
                    style_vector={"target_bpm": ws["bpm"]}, n_verses=ws["n_verses"],
                    user_lyrics_lines=ws.get("user_lyrics_lines") or [],
                    bilingual=ws["bilingual"])
                text = r.get("lyrics", "")
                source = "punch_lib_fallback"
            except Exception as _lg_e:  # noqa: BLE001
                # v39.4 (ШАГ 005): молчаливый except заменён на честный лог
                app_logger.error(
                    f"[orchestrator_ai] stage=lyrics event=fallback_failed "
                    f"reason={type(_lg_e).__name__}: {_lg_e}")
        (out_root / "lyrics.txt").write_text(text or "", encoding="utf-8")
        return {"ok": bool(text), "lyrics": text, "source": source,
                "path": str(out_root / "lyrics.txt")}

    def stage_metadata(handle, ctx):
        if dry_run or handle is None:
            return {"ok": True, "title": ws.get("theme", "Untitled")[:30],
                    "source": "dry" if dry_run else "no_llm"}
        lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
        js = LLM.complete_json(handle, P.SYSTEM_METADATA,
            P.build_metadata_prompt(ws["theme"], ws["genre"], lyrics),
            max_tokens=1200, temperature=0.6) or {}
        (out_root / "metadata.json").write_text(
            json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")
        return js

    def stage_music(handle, ctx):
        if dry_run:
            return {"ok": True, "beat_path": "[dry]"}
        if handle is None:
            try:
                from modules.cyber_synth import CyberSynth
                out_p = str(out_root / "beat.wav")
                res = CyberSynth().synthesize_track(bpm=ws["bpm"],
                    duration_sec=ws["duration_sec"], out_path=out_p)
                res["engine"] = "cyber_synth_fallback"; res["beat_path"] = out_p
                return res
            except Exception as e:
                return {"ok": False, "reason": f"no music engine: {e}"}
        art = (ctx["sink"].get("dossier_load") or {}).get("artist_dossier")
        trk = (ctx["sink"].get("dossier_load") or {}).get("track_dossier")
        instruments = trk.get("reusable_elements", [])[:5] if isinstance(trk, dict) else []
        ref_feats = {"instruments": instruments,
                     "atmosphere": (art or {}).get("flow", "")} if art else None
        prompt = P.build_music_prompt(ws["genre"], ws["bpm"], ws["key"], ws["mood"],
            reference_artist=ws.get("reference_artist") or ws.get("artist_slug"),
            reference_track_features=ref_feats)
        import numpy as np, soundfile as sf, torch
        out_path = str(out_root / "beat.wav")
        model = handle
        try:
            model.set_generation_params(duration=20, top_k=250, temperature=1.0, cfg_coef=3.0)
        except Exception:
            pass
        n_chunks = max(1, math.ceil(ws["duration_sec"] / 20))
        sr = getattr(model, "sample_rate", 32000)
        chunks = [model.generate([prompt], progress=False)[0].cpu().numpy()]
        for i in range(1, n_chunks):
            try:
                prev_t = torch.from_numpy(chunks[-1]).unsqueeze(0)
                if any(p.is_cuda for p in model.lm.parameters()):
                    prev_t = prev_t.cuda()
                cont = model.generate_continuation(prev_t, sr, [prompt], progress=False)[0]
                chunks.append(cont.cpu().numpy())
            except Exception:
                chunks.append(model.generate([prompt], progress=False)[0].cpu().numpy())
        full = np.concatenate(chunks, axis=-1)
        total = int(ws["duration_sec"] * sr)
        if full.shape[-1] > total:
            full = full[..., :total]
        if full.ndim == 1:
            full = np.stack([full, full], axis=-1)
        else:
            full = full.T
            if full.shape[1] == 1:
                full = np.concatenate([full, full], axis=1)
        peak = float(np.max(np.abs(full)) + 1e-9)
        if peak > 0.99:
            full = full * (0.98 / peak)
        sf.write(out_path, full.astype("float32"), int(sr), subtype="PCM_16")
        return {"ok": True, "beat_path": out_path, "engine": "musicgen-large",
                "sample_rate": int(sr), "prompt": prompt, "chunks": n_chunks}

    def stage_vocal(handle, ctx):
        if dry_run or handle is None:
            return {"skipped": "dry-run" if dry_run else "no tts model"}
        lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
        if not lyrics.strip():
            return {"skipped": "no lyrics"}
        import re
        clean = re.sub(r"^\[.*?\]\s*$", "", lyrics, flags=re.MULTILINE).strip()
        clean = re.sub(r"\n{3,}", "\n\n", clean)[:3500]
        out_path = str(out_root / "vocal_xtts.wav")
        speaker_wav = ws.get("speaker_wav")
        try:
            kwargs = dict(text=clean, file_path=out_path, language="ru")
            if speaker_wav and Path(speaker_wav).exists():
                kwargs["speaker_wav"] = speaker_wav
            handle.tts_to_file(**kwargs)
            return {"ok": True, "vocal_path": out_path, "engine": "xtts_v2"}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def stage_rvc(handle, ctx):
        if dry_run or handle is None:
            return {"skipped": "dry-run" if dry_run else "no rvc"}
        vocal = (ctx["sink"].get("vocal_synth") or {}).get("vocal_path")
        if not vocal or not Path(vocal).exists():
            return {"skipped": "no vocal"}
        rvc_model = ws.get("rvc_model")
        if not rvc_model:
            return {"skipped": "no rvc_model"}
        out_path = vocal.replace(".wav", "_rvc.wav")
        try:
            ok = False
            try:
                ok = handle.convert(input_path=vocal, output_path=out_path,
                                    model_path=rvc_model)
            except Exception:
                ok = False
            if ok and Path(out_path).exists():
                return {"ok": True, "vocal_path": out_path, "engine": "rvc",
                        "model": rvc_model}
        except Exception as e:
            return {"ok": False, "reason": str(e)}
        return {"skipped": "rvc convert failed"}

    def stage_mix(_, ctx):
        beat = (ctx["sink"].get("music") or {}).get("beat_path")
        vocal = ((ctx["sink"].get("rvc") or {}).get("vocal_path")
                 or (ctx["sink"].get("vocal_synth") or {}).get("vocal_path"))
        mix_path = str(out_root / "mix.wav")
        if not beat or not Path(beat).exists():
            return {"skipped": "no beat"}
        try:
            import numpy as np, soundfile as sf
            b, sr_b = sf.read(beat)
            if b.ndim == 1:
                b = np.stack([b, b], axis=-1)
            if not vocal or not Path(vocal).exists():
                sf.write(mix_path, b, sr_b)
                return {"ok": True, "mix_path": mix_path, "vocal": False}
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
            return {"ok": True, "mix_path": mix_path, "vocal": True}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def stage_master(_, ctx):
        mix = (ctx["sink"].get("mix") or {}).get("mix_path")
        if not mix:
            return {"skipped": "no mix"}
        out_master = str(out_root / "masters" / "master_ai.wav")
        from modules.mastering_ai import master_ai
        return master_ai(mix, out_master, reference_wav=ws.get("reference_master_wav"),
                         target_lufs=-9.0)

    def stage_cover(_, ctx):
        meta = ctx["sink"].get("metadata") or {}
        title = meta.get("title") or ws.get("theme", "Untitled")
        artist = ws.get("artist_display") or ws.get("artist_slug") or "ZS"
        from modules.cover_art_ai import render_cover_ai
        return render_cover_ai(title=title, artist=artist, genre=ws["genre"],
                               mood=ws["mood"], out_path=str(out_root / "cover.png"))

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
    runner.add(AIStage("vocal_synth",  "tts_vocal",        stage_vocal,    optional=True))
    runner.add(AIStage("rvc",          "vocal_rvc",        stage_rvc,      optional=True))
    runner.add(AIStage("mix",          None,               stage_mix))
    runner.add(AIStage("master",       None,               stage_master))
    runner.add(AIStage("cover",        "cover_art",        stage_cover,    optional=True))
    runner.add(AIStage("tag",          "audio_tagger",     stage_tag,      optional=True))
    report = runner.run({"project_id": project_id, "wizard_state": ws})
    result = {"project_id": project_id, "god_mode": "4.0-AI", "wizard_state": ws,
              "report": report.to_dict(),
              "artefacts": {"lyrics": str(out_root / "lyrics.txt"),
                            "metadata": str(out_root / "metadata.json"),
                            "beat": str(out_root / "beat.wav"),
                            "vocal": str(out_root / "vocal_xtts.wav"),
                            "mix": str(out_root / "mix.wav"),
                            "master": str(out_root / "masters" / "master_ai.wav"),
                            "cover": str(out_root / "cover.png")}}
    (out_root / "project_meta.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    app_logger.info(f"[orchestrator_ai] finished project={project_id}")
    return result
