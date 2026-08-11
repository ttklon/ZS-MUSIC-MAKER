"""
ZS Music Maker v11 — orchestrator_v11_patch.py

Master orchestrator для v11. Соединяет ВСЕ модули (v7 → v8 → v9 → v10 → v11)
в единый `run_full_pipeline_v11()`, реализующий ТЗ 20.5 KPI.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))


def _load_deps():
    deps = {}
    for name, path in [
        ("video_edit", "modules.video_edit_v11"),
        ("dist", "modules.distribution_export_v11"),
        ("kpi", "modules.hit_kpi_monitor_v11"),
        ("expert", "modules.expert_mode_v11"),
    ]:
        try:
            deps[name] = __import__(path, fromlist=["*"])
        except Exception as e:
            _safe_print(f"[orch_v11] {path} unavailable: {e}")
    for name, path in [
        ("v10_patch", "app.core.orchestrator_v10_patch"),
        ("v9_patch", "app.core.orchestrator_v9_patch"),
        ("hw", "app.core.hw_autodetect"),
    ]:
        try:
            deps[name] = __import__(path, fromlist=["*"])
        except Exception as e:
            _safe_print(f"[orch_v11] {path} unavailable: {e}")
    return deps


def run_full_pipeline_v11(
    project_id, wizard_state, expert_config=None, progress_cb=None, project_root=None
):
    """Единая точка входа полного пайплайна v11."""
    t0 = time.time()
    errors, warnings, stages_ran = [], [], []
    root = Path(project_root) if project_root else ROOT

    def prog(stage, pct, msg=""):
        _safe_print(f"[orch_v11][{pct*100:5.1f}%] {stage}: {msg}")
        if progress_cb:
            try:
                progress_cb(stage, pct, msg)
            except Exception:
                pass

    prog("init", 0.0, f"start project_id={project_id}")
    deps = _load_deps()

    # 1. HW mode
    hw_mode = "fallback_hw"
    hw_profile = {}
    try:
        if "hw" in deps:
            probe = None
            for m in ("detect_hardware", "detect"):
                if hasattr(deps["hw"], m):
                    probe = getattr(deps["hw"], m)()
                    break
            if isinstance(probe, dict):
                hw_profile = probe
                if (
                    probe.get("mode") in ("full", "full_hw", "cuda", "directml")
                    or probe.get("vram_gb", 0) >= 10
                ):
                    hw_mode = "full_hw"
    except Exception as e:
        warnings.append(f"hw detect failed: {e}")
    prog("hw", 0.03, f"mode={hw_mode}")

    # 2. KPI session
    kpi_session = None
    if "kpi" in deps:
        kpi_session = deps["kpi"].KpiSession(project_id=project_id, hw_mode=hw_mode)

    # 3. Expert config
    expert_flat = {"expert_mode_enabled": False}
    if expert_config and "expert" in deps:
        try:
            cfg = deps["expert"].ExpertConfig.from_dict(expert_config)
            v = deps["expert"].validate(cfg)
            if v["errors"]:
                warnings.extend([f"expert.{e}" for e in v["errors"]])
                cfg.enabled = False
            expert_flat = cfg.to_flat_dict()
            wizard_state = deps["expert"].merge_with_wizard_state(wizard_state, cfg)
        except Exception as e:
            warnings.append(f"expert_config bad: {e}")

    # 4. v10 pipeline (delegated)
    v10_out = {}
    release_dir = str(root / "output" / "releases" / project_id)
    os.makedirs(release_dir, exist_ok=True)
    st = kpi_session.start_stage("v10_pipeline") if kpi_session else None
    try:
        if "v10_patch" in deps and hasattr(deps["v10_patch"], "full_v10_pipeline"):
            prog("v10_pipeline", 0.15, "delegating to v10")
            try:
                v10_out = (
                    deps["v10_patch"].full_v10_pipeline(
                        project_id=project_id,
                        wizard_state=wizard_state,
                        release_dir=release_dir,
                    )
                    or {}
                )
            except TypeError:
                try:
                    v10_out = (
                        deps["v10_patch"].full_v10_pipeline(project_id, wizard_state)
                        or {}
                    )
                except Exception as e2:
                    warnings.append(f"v10 old sig failed: {e2}")
                    v10_out = _minimal_pipeline_fallback(
                        project_id, wizard_state, release_dir, prog
                    )
        else:
            v10_out = _minimal_pipeline_fallback(
                project_id, wizard_state, release_dir, prog
            )
        stages_ran.append("v10_pipeline")
        if st:
            kpi_session.end_stage(st, ok=True)
    except Exception as e:
        errors.append(f"v10_pipeline: {e}\n{traceback.format_exc()}")
        v10_out = _minimal_pipeline_fallback(
            project_id, wizard_state, release_dir, prog
        )
        if st:
            kpi_session.end_stage(st, ok=False, note=str(e))
    prog("v10_pipeline", 0.55, "done")

    # 5. Video edits
    video_edits = {}
    if "video_edit" in deps:
        st = kpi_session.start_stage("video_edits") if kpi_session else None
        try:
            master_wav = v10_out.get("master_wav") or os.path.join(
                release_dir, "master.wav"
            )
            cover_png = v10_out.get("cover_png") or os.path.join(
                release_dir, "cover.png"
            )
            lyrics_lrc = v10_out.get("lyrics_lrc") or os.path.join(
                release_dir, "lyrics.lrc"
            )
            bpm = float(wizard_state.get("bpm", 140.0))
            title = str(wizard_state.get("track_title", project_id))
            artist = str(wizard_state.get("artist_name", "ZS"))
            video_edits = deps["video_edit"].build_release_edits(
                master_wav=master_wav,
                cover_png=cover_png if os.path.exists(cover_png) else None,
                lyrics_lrc=lyrics_lrc if os.path.exists(lyrics_lrc) else None,
                bpm=bpm,
                title=title,
                artist=artist,
                out_dir=release_dir,
            )
            stages_ran.append("video_edits")
            if st:
                kpi_session.end_stage(st, ok=True)
        except Exception as e:
            errors.append(f"video_edits: {e}")
            if st:
                kpi_session.end_stage(st, ok=False, note=str(e))
    prog("video_edits", 0.75, f"{len(video_edits)} clips")

    # 6. Distribution packages
    distribution = {}
    if "dist" in deps:
        st = kpi_session.start_stage("distribution") if kpi_session else None
        try:
            meta = deps["dist"].TrackMetadata(
                title=str(wizard_state.get("track_title", project_id)),
                artist=str(wizard_state.get("artist_name", "ZS")),
                bpm=float(wizard_state.get("bpm", 140.0)),
                duration_sec=float(
                    v10_out.get("duration_sec", wizard_state.get("length_sec", 150.0))
                ),
                language=str(wizard_state.get("language", "ru")),
                tags=list(wizard_state.get("tags", ["car", "summer", "trap"])),
                lyrics_ru=str(v10_out.get("lyrics_ru", "")),
                lyrics_en_hook=str(v10_out.get("lyrics_en_hook", "")),
                genre=str(wizard_state.get("genre", "Hip-Hop/Rap")),
                subgenre=str(wizard_state.get("subgenre", "Phonk / Trap / Hyperpop")),
                key=str(wizard_state.get("key", "")),
                explicit=bool(wizard_state.get("explicit", False)),
            )
            files = deps["dist"].ReleaseFiles(
                master_wav=v10_out.get(
                    "master_wav", os.path.join(release_dir, "master.wav")
                ),
                mp3_320=v10_out.get("mp3_320", os.path.join(release_dir, "master.mp3")),
                flac=v10_out.get("flac", os.path.join(release_dir, "master.flac")),
                instrumental_wav=v10_out.get(
                    "instrumental", os.path.join(release_dir, "instrumental.wav")
                ),
                acapella_wav=v10_out.get(
                    "acapella", os.path.join(release_dir, "acapella.wav")
                ),
                stems_dir=v10_out.get("stems_dir", os.path.join(release_dir, "stems")),
                tiktok_mp4=os.path.join(release_dir, "tiktok_edit.mp4"),
                reels_mp4=os.path.join(release_dir, "reels_edit.mp4"),
                shorts_mp4=os.path.join(release_dir, "shorts_edit.mp4"),
                cover_png=v10_out.get(
                    "cover_png", os.path.join(release_dir, "cover.png")
                ),
                lyrics_txt=v10_out.get(
                    "lyrics_txt", os.path.join(release_dir, "lyrics.txt")
                ),
                lyrics_lrc=v10_out.get(
                    "lyrics_lrc", os.path.join(release_dir, "lyrics.lrc")
                ),
            )
            distribution = deps["dist"].build_all_distribution_packages(
                meta, files, out_dir=os.path.join(release_dir, "distribution")
            )
            stages_ran.append("distribution")
            if st:
                kpi_session.end_stage(st, ok=True)
        except Exception as e:
            errors.append(f"distribution: {e}")
            if st:
                kpi_session.end_stage(st, ok=False, note=str(e))
    prog("distribution", 0.9, f"{len(distribution)} platforms")

    # 7. KPI finalize
    kpi_report = None
    kpi_md = ""
    if kpi_session and "kpi" in deps:
        try:
            ai_report = (
                v10_out.get("ai_detector_report") or v10_out.get("auto_qa_report") or {}
            )
            kpi_session = deps["kpi"].finalize_session(
                kpi_session,
                release_dir=release_dir,
                ai_detector_report=ai_report,
                save_dir=str(root / "data"),
            )
            kpi_report = kpi_session.to_dict()
            kpi_md = deps["kpi"].render_kpi_report_md(kpi_session)
            with open(
                os.path.join(release_dir, "KPI_REPORT_v11.md"), "w", encoding="utf-8"
            ) as f:
                f.write(kpi_md)
            stages_ran.append("kpi")
        except Exception as e:
            errors.append(f"kpi_finalize: {e}")

    # 8. Master manifest
    manifest_path = os.path.join(release_dir, "manifest_v11.json")
    manifest = {
        "project_id": project_id,
        "generator": "ZS Music Maker v11",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wizard_state": wizard_state,
        "expert_flat": expert_flat,
        "hw_mode": hw_mode,
        "hw_profile": hw_profile,
        "v10_out_summary": {
            k: (v if isinstance(v, (str, int, float, bool)) else str(type(v).__name__))
            for k, v in (v10_out or {}).items()
        },
        "video_edits": video_edits,
        "distribution_dirs": {
            k: v.get("dir") for k, v in distribution.items() if isinstance(v, dict)
        },
        "kpi_verdict": kpi_report.get("verdict") if kpi_report else "N/A",
        "stages_ran": stages_ran,
        "errors": errors,
        "warnings": warnings,
        "total_seconds": time.time() - t0,
    }
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        errors.append(f"manifest_write: {e}")

    prog(
        "done",
        1.0,
        f"total={manifest['total_seconds']:.1f}s " f"verdict={manifest['kpi_verdict']}",
    )

    return {
        "ok": len(errors) == 0,
        "release_dir": release_dir,
        "manifest_path": manifest_path,
        "distribution": distribution,
        "video_edits": video_edits,
        "kpi": kpi_report,
        "kpi_md": kpi_md,
        "errors": errors,
        "warnings": warnings,
        "stages_ran": stages_ran,
        "total_seconds": time.time() - t0,
    }


def _minimal_pipeline_fallback(project_id, wizard_state, release_dir, prog):
    """Плейсхолдеры чтобы v11 не крашился если v10 недоступен."""
    prog("fallback", 0.2, "v10 unavailable; placeholders")
    os.makedirs(release_dir, exist_ok=True)
    import struct
    import wave

    p = os.path.join(release_dir, "master.wav")
    if not os.path.exists(p):
        try:
            with wave.open(p, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(struct.pack("<" + "h" * 44100, *([0] * 44100)))
        except Exception:
            pass
    lp = os.path.join(release_dir, "lyrics.txt")
    if not os.path.exists(lp):
        with open(lp, "w", encoding="utf-8") as f:
            f.write(str(wizard_state.get("lyrics_theme", "placeholder\n")))
    return {
        "master_wav": p,
        "mp3_320": p,
        "cover_png": "",
        "lyrics_txt": lp,
        "lyrics_lrc": "",
        "lyrics_ru": wizard_state.get("lyrics_theme", ""),
        "duration_sec": 1.0,
        "fallback": True,
    }


REGISTERED_MODULES_V11 = [
    "modules.video_edit_v11",
    "modules.distribution_export_v11",
    "modules.hit_kpi_monitor_v11",
    "modules.expert_mode_v11",
]


def register(app_ctx=None):
    ok = {}
    for m in REGISTERED_MODULES_V11:
        try:
            __import__(m)
            ok[m] = True
        except Exception as e:
            ok[m] = str(e)
    _safe_print(f"[orch_v11] registered: {ok}")
    return ok


def _self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        ws = {
            "track_title": "Selftest",
            "artist_name": "ZS",
            "bpm": 140.0,
            "length_sec": 90,
            "tags": ["test"],
        }
        res = run_full_pipeline_v11(
            project_id="selftest_v11",
            wizard_state=ws,
            expert_config=None,
            progress_cb=None,
            project_root=tmp,
        )
        return os.path.exists(res["release_dir"]) and os.path.exists(
            res["manifest_path"]
        )


if __name__ == "__main__":
    print("orchestrator_v11_patch self-test:", "OK" if _self_test() else "FAIL")
