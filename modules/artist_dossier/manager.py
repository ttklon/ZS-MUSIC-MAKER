# -*- coding: utf-8 -*-
"""
modules/artist_dossier/manager.py — `DossierManager`: жизненный цикл досье.

Пайплайн на трек: demucs → whisper (ASR) → librosa/DSP → CLAP → analysis_llm.
Результат всегда пишется на диск (трек и артист — отдельные JSON), а недоступная
модель честно помечается в статусе, а не подменяется шаблоном.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ai import llm_service as LLM
from app.ai import prompts as P
from app.ai.quality import (
    validate_analysis_json,
    validate_audio_tags,
    validate_dsp_features,
    validate_stem_artifact,
)
from app.ai.registry import registry
from app.ai.sequential_runner import AIStage, SequentialAIRunner
from modules.artist_dossier.features import (
    extract_dsp_features,
    rank_clap_tags,
    resolve_vocal_source_index,
    transcribe_reference_audio,
)
from modules.artist_dossier.models import ArtistEntry, TrackEntry
from modules.artist_dossier.schema import (
    DOSSIER_ROOT,
    _slug,
    _track_id,
    normalize_artist_dossier,
    validate_artist_dossier,
)
from modules.artist_dossier.storage import (
    load_artist,
    load_track,
    save_artist,
    save_track,
)

class DossierManager:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else DOSSIER_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def add_artist(self, artist: str,
                   tracks: Optional[List[Dict[str, Any]]] = None) -> ArtistEntry:
        slug = _slug(artist)
        adir = self.root / slug
        for sub in ("tracks", "audio", "vocals", "lyrics"):
            (adir / sub).mkdir(parents=True, exist_ok=True)
        entry = self._load_artist(slug) or ArtistEntry(
            artist=artist, slug=slug, added_at=time.time(), updated_at=time.time())
        self._save_artist(entry)  # скелет, чтобы add_track увидел артиста
        for t in tracks or []:
            self.add_track(artist, t.get("title", "untitled"),
                           audio_path=t.get("audio_path"),
                           external_url=t.get("external_url"),
                           lyrics=t.get("lyrics"))
        entry = self._load_artist(slug) or entry
        entry.updated_at = time.time()
        self._save_artist(entry)
        return entry

    def add_track(self, artist: str, title: str,
                  audio_path: Optional[str] = None,
                  external_url: Optional[str] = None,
                  lyrics: Optional[str] = None) -> TrackEntry:
        slug = _slug(artist)
        tid = _track_id(title, external_url or "")
        entry = TrackEntry(track_id=tid, title=title, artist=artist,
                           audio_path=audio_path, external_url=external_url,
                           lyrics=lyrics, added_at=time.time())
        if audio_path:
            source = Path(audio_path)
            if not source.exists():
                entry.audio_copy = {
                    "ok": False,
                    "source": str(source),
                    "status": "source_missing",
                }
            else:
                dst = self.root / slug / "audio" / f"{tid}{source.suffix.lower()}"
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dst)
                    entry.audio_path = str(dst)
                    entry.audio_copy = {"ok": True, "source": str(source), "path": str(dst)}
                except Exception as exc:
                    entry.audio_copy = {
                        "ok": False,
                        "source": str(source),
                        "path": str(dst),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
        if lyrics:
            (self.root / slug / "lyrics" / f"{tid}.txt").write_text(lyrics, encoding="utf-8")
        self._save_track(slug, entry)
        a = self._load_artist(slug) or ArtistEntry(
            artist=artist, slug=slug, added_at=time.time(), updated_at=time.time())
        if tid not in a.tracks:
            a.tracks.append(tid)
        a.updated_at = time.time()
        self._save_artist(a)
        return entry

    def build_full_dossier(self, artist: str, refresh: bool = False,
                           progress_cb=None) -> Dict[str, Any]:
        slug = _slug(artist)
        a = self._load_artist(slug)
        if not a:
            raise ValueError(f"Artist {artist} not registered")
        for tid in a.tracks:
            tr = self._load_track(slug, tid)
            if not tr:
                continue
            if not refresh and tr.status == "analyzed":
                if progress_cb:
                    progress_cb(tid, "cached")
                continue
            try:
                self._analyze_single_track(slug, tr, progress_cb=progress_cb)
            except Exception as e:
                tr.status = "failed"
                tr.dossier = {"error": str(e)}
                self._save_track(slug, tr)
        a.dossier = self._aggregate_artist_dossier(slug, a)
        a.updated_at = time.time()
        self._save_artist(a)
        return a.dossier

    def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
        if progress_cb:
            progress_cb(tr.track_id, "start")
        runner = SequentialAIRunner()

        def _demucs_stage(model, ctx):
            if model is None:
                return {"skipped": "stem_splitter unavailable"}
            if not tr.audio_path or not Path(tr.audio_path).exists():
                return {"skipped": "no audio"}
            try:
                import torchaudio, soundfile as sf
                from demucs.apply import apply_model
                wav, sr = torchaudio.load(tr.audio_path)
                if wav.dim() == 1:
                    wav = wav.unsqueeze(0)
                if wav.shape[0] == 1:
                    wav = wav.repeat(2, 1)
                wav = wav.unsqueeze(0)
                dev = str(next(model.parameters()).device)
                if dev.startswith("cuda"):
                    wav = wav.cuda()
                vocal_index = resolve_vocal_source_index(model)
                sources = apply_model(model, wav, device=dev, split=True, overlap=0.25)
                vocals = sources[0, vocal_index].cpu().numpy().T
                out = self.root / slug / "vocals" / f"{tr.track_id}_vocals.wav"
                out.parent.mkdir(parents=True, exist_ok=True)
                sf.write(str(out), vocals, int(sr))
                quality = validate_stem_artifact(tr.audio_path, out)
                return {
                    "ok": bool(quality["ok"]),
                    "vocals_path": str(out),
                    "source_index": vocal_index,
                    "quality": quality,
                    "reason": quality["reason"],
                }
            except Exception as e:
                return {"ok": False, "error": str(e)}
        runner.add(AIStage("demucs", "stem_splitter", _demucs_stage, optional=True))

        def _asr_stage(model, ctx):
            if tr.lyrics:
                return {"lyrics": tr.lyrics, "source": "user"}
            if model is None:
                return {"skipped": "asr unavailable"}
            vocals = (ctx.get("sink", {}).get("demucs") or {}).get("vocals_path")
            src = vocals or tr.audio_path
            if not src or not Path(src).exists():
                return {"skipped": "no audio for ASR"}
            return transcribe_reference_audio(
                model,
                str(src),
                str(self.root / slug / "lyrics" / f"{tr.track_id}.txt"),
            )
        runner.add(AIStage("asr", "asr", _asr_stage, optional=True))

        def _features_stage(handle, ctx):
            if not tr.audio_path or not Path(tr.audio_path).exists():
                return {"skipped": "no audio for DSP"}
            if handle is None:
                return {
                    "skipped": "essentia/librosa unavailable",
                    "fallback": "reference audio retained without DSP metadata",
                }
            features = extract_dsp_features(tr.audio_path, engine=str(handle))
            if not features.get("ok"):
                return features
            quality = validate_dsp_features(features)
            if not quality["ok"]:
                return {
                    "ok": False,
                    "reason": quality["reason"],
                    "quality": quality,
                    "fallback": "reference audio retained without unreliable DSP metadata",
                }
            features["quality"] = quality
            features["reason"] = None
            return features
        runner.add(AIStage("features", "essentia", _features_stage, optional=True))

        def _tag_stage(bundle, ctx):
            if bundle is None:
                return {"skipped": "audio_tagger unavailable"}
            if not tr.audio_path or not Path(tr.audio_path).exists():
                return {"skipped": "no audio"}
            try:
                model, proc = bundle
                import torch, librosa, numpy as np
                y, sr = librosa.load(tr.audio_path, sr=48000, mono=True, duration=30)
                cand = ["phonk", "trap", "drill", "hip-hop", "pop", "rock", "shanson",
                        "aggressive", "melancholic", "dark", "party", "romantic",
                        "808 bass", "acoustic guitar", "piano", "female vocal",
                        "male vocal", "rap", "singing"]
                inputs = proc(text=cand, audios=y, sampling_rate=48000,
                              return_tensors="pt", padding=True)
                if any(p.is_cuda for p in model.parameters()):
                    inputs = {k: (v.cuda() if hasattr(v, "cuda") else v)
                              for k, v in inputs.items()}
                with torch.no_grad():
                    logits = model(**inputs).logits_per_audio[0].cpu().numpy()
                tags = rank_clap_tags(cand, logits)
                quality = validate_audio_tags(tags, cand)
                return {
                    "ok": bool(quality["ok"]),
                    "tags": tags if quality["ok"] else [],
                    "source": "clap",
                    "quality": quality,
                    "reason": quality["reason"],
                }
            except Exception as e:
                return {"ok": False, "error": str(e)}
        runner.add(AIStage("tags", "audio_tagger", _tag_stage, optional=True))

        def _llm_stage(handle, ctx):
            lyrics = (tr.lyrics or (ctx.get("sink", {}).get("asr") or {}).get("lyrics") or "")
            if not lyrics.strip():
                return {"skipped": "no lyrics"}
            if handle is None:
                return {"skipped": "analysis_llm unavailable"}
            feats = (ctx.get("sink", {}).get("features") or {}).copy()
            feats["tags"] = (ctx.get("sink", {}).get("tags") or {}).get("tags", [])
            js = LLM.complete_json(handle, P.SYSTEM_TRACK_ANALYSIS,
                                   P.build_track_dossier_prompt(tr.title, lyrics, feats),
                                   max_tokens=3000, temperature=0.35)
            quality = validate_analysis_json(js, track_level=True)
            if not quality["ok"]:
                return {"error": quality["reason"], "quality": quality}
            js["quality"] = quality
            return js
        runner.add(AIStage(
            "llm_breakdown", "analysis_llm", _llm_stage, optional=True, fallback_fn=False
        ))

        report = runner.run({"track_id": tr.track_id, "artist": tr.artist})
        sink = runner.sink()
        tr.features.update(sink.get("features") or {})
        demucs = sink.get("demucs") or {}
        if demucs.get("vocals_path"):
            tr.features["stems"] = {"vocals": demucs["vocals_path"]}
            tr.features["stem_source_index"] = demucs.get("source_index")
        if (sink.get("tags") or {}).get("tags"):
            tr.features["tags"] = sink["tags"]["tags"]
        asr = sink.get("asr") or {}
        if asr.get("transcript_path"):
            tr.features["transcript_path"] = asr["transcript_path"]
        if asr.get("lyrics") and not tr.lyrics:
            tr.lyrics = asr["lyrics"]
        br = sink.get("llm_breakdown")
        if isinstance(br, dict) and "error" not in br and "skipped" not in br:
            tr.dossier = br
            tr.status = "analyzed"
        else:
            tr.status = "partial"
            tr.dossier = {"partial": True, "report": report.to_dict()}
        self._save_track(slug, tr)
        if progress_cb:
            progress_cb(tr.track_id, "done")

    def _aggregate_artist_dossier(self, slug: str, a: ArtistEntry) -> Dict[str, Any]:
        chunks = []
        for tid in a.tracks:
            tr = self._load_track(slug, tid)
            if tr and tr.lyrics and tr.lyrics.strip():
                chunks.append(f"=== {tr.title} ===\n{tr.lyrics}\n")
        if not chunks:
            return {"note": "no lyrics collected - cannot build dossier"}
        blob = "\n".join(chunks)
        if not registry.is_available("analysis_llm"):
            return {"note": "analysis_llm unavailable - dossier deferred",
                    "tracks_count": len(a.tracks), "lyrics_bytes": len(blob)}
        with registry.use("analysis_llm") as m:
            js = LLM.complete_json(m.handle, P.SYSTEM_ANALYSIS,
                                   P.build_dossier_prompt(a.artist, blob),
                                   max_tokens=2500, temperature=0.4)
        quality = validate_analysis_json(js)
        if not quality["ok"]:
            return {
                "note": "analysis_llm output rejected: " + str(quality["reason"]),
                "tracks_count": len(a.tracks),
                "quality": quality,
            }
        js = normalize_artist_dossier(js)
        js["quality"] = quality
        js["tracks_count"] = len(a.tracks)
        js["updated_at"] = time.time()
        schema_quality = validate_artist_dossier(js)
        if not schema_quality["ok"]:
            return {
                "note": "artist dossier schema rejected: " + str(schema_quality["reason"]),
                "tracks_count": len(a.tracks),
                "quality": schema_quality,
            }
        return js

    def get_artist_dossier(self, artist: str) -> Optional[Dict[str, Any]]:
        a = self._load_artist(_slug(artist))
        return a.dossier if a else None

    def get_track_dossier(self, artist: str, track_id: str) -> Optional[Dict[str, Any]]:
        tr = self._load_track(_slug(artist), track_id)
        return tr.dossier if tr else None

    def list_artists(self) -> List[Dict[str, Any]]:
        out = []
        for adir in sorted(self.root.iterdir()):
            if not adir.is_dir():
                continue
            a = self._load_artist(adir.name)
            if a:
                out.append({"artist": a.artist, "slug": a.slug, "tracks": len(a.tracks),
                            "has_dossier": bool(a.dossier), "updated_at": a.updated_at})
        return out

    def list_tracks(self, artist: str) -> List[Dict[str, Any]]:
        slug = _slug(artist)
        a = self._load_artist(slug)
        if not a:
            return []
        out = []
        for tid in a.tracks:
            tr = self._load_track(slug, tid)
            if tr:
                out.append({"track_id": tr.track_id, "title": tr.title,
                            "status": tr.status, "has_lyrics": bool(tr.lyrics),
                            "has_audio": bool(tr.audio_path and Path(tr.audio_path).exists()),
                            "features": {k: tr.features.get(k) for k in ("bpm", "key", "tags")}})
        return out

    def _save_artist(self, a: ArtistEntry) -> None:
        save_artist(self.root, a)

    def _load_artist(self, slug: str) -> Optional[ArtistEntry]:
        return load_artist(self.root, slug)

    def _save_track(self, slug: str, tr: TrackEntry) -> None:
        save_track(self.root, slug, tr)

    def _load_track(self, slug: str, tid: str) -> Optional[TrackEntry]:
        return load_track(self.root, slug, tid)
