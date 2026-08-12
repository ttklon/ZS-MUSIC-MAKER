# -*- coding: utf-8 -*-
"""ZS Music Maker v22 — smoke_v22."""
from __future__ import annotations
import sys, tempfile, traceback, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = []


def _record(name, ok, detail="", err=""):
    RESULTS.append({"name": name, "ok": ok, "detail": detail, "err": err})


def _run(name, fn):
    try:
        ok, detail = fn()
        _record(name, ok, detail)
    except Exception as e:
        _record(name, False, "",
                f"{type(e).__name__}: {e}\n" + traceback.format_exc(limit=3))


def t_analyze_no_refs_not_fallback():
    from app.core import orchestrator as o
    r = o._stage_analyze([], False, genre="drift_phonk")
    if r.get("fallback_used"):
        return False, "analyze with no refs still flagged as fallback_used"
    if not r.get("ok"):
        return False, "analyze with no refs not ok"
    analysis = r.get("analysis") or {}
    if analysis.get("bpm") != 130:
        return False, f"analyze default bpm wrong: {analysis.get('bpm')}"
    return True, f"analyze no-refs ok, bpm={analysis.get('bpm')}"


def t_groove_no_refs_not_fallback():
    from app.core import orchestrator as o
    r = o._stage_groove([], genre="drift_phonk")
    if r.get("fallback_used"):
        return False, "groove with no refs still flagged as fallback_used"
    if not r.get("ok"):
        return False, "groove with no refs not ok"
    g = r.get("groove") or {}
    if not g.get("kick_pattern"):
        return False, "groove default missing kick_pattern"
    return True, f"groove no-refs ok, swing={g.get('swing')}"


def t_synth_beat_structured():
    from app.core import orchestrator as o
    import soundfile as sf, numpy as np
    with tempfile.TemporaryDirectory() as td:
        out = str(Path(td) / "beat.wav")
        r = o._synth_beat(out, duration=30, bpm=130)
        if not r.get("ok"):
            return False, f"synth_beat failed: {r.get('reason')}"
        y, sr = sf.read(out)
        if y.shape[0] < sr * 25:
            return False, f"beat too short: {y.shape[0]/sr:.1f}s"
        if r.get("engine") != "synth_beat_v22":
            return False, f"engine={r.get('engine')}"
        sections = r.get("sections", [])
        if len(sections) < 4:
            return False, f"sections={len(sections)}"
        rms = float(np.sqrt(np.mean(y**2)))
        if rms < 0.01:
            return False, f"rms too low: {rms:.4f}"
        return True, f"beat 30s, sections={len(sections)}, rms={rms:.3f}"


def t_fallback_lyrics_genre_variety():
    from app.core import orchestrator as o
    r1 = o._fallback_lyrics("ночь", "drift_phonk")
    r2 = o._fallback_lyrics("любовь", "pop")
    r3 = o._fallback_lyrics("дождь", "lo_fi")
    if r1.get("title") == r2.get("title"):
        return False, "drift_phonk and pop titles identical"
    if r1.get("title") == r3.get("title"):
        return False, "drift_phonk and lo_fi titles identical"
    if "drift_phonk" not in r1.get("title"):
        return False, f"title missing genre: {r1.get('title')}"
    return True, f"3 genres, 3 titles: {r1['title']}, {r2['title']}, {r3['title']}"


def t_voice_scaffold_v22_formants():
    from app.core import orchestrator as o
    import soundfile as sf, numpy as np
    with tempfile.TemporaryDirectory() as td:
        out = str(Path(td) / "voice.wav")
        r = o._pyttsx3_speak("Привет мир как дела нормально всё", out)
        if not r.get("ok"):
            return False, f"scaffold failed: {r.get('reason')}"
        if r.get("engine") != "rap_scaffold_numpy_v22":
            return False, f"engine={r.get('engine')}"
        y, sr = sf.read(out)
        if len(y) < sr * 1.5:
            return False, f"too short: {len(y)/sr:.1f}s"
        return True, f"scaffold v22, dur={len(y)/sr:.1f}s, rms={float(np.sqrt(np.mean(y**2))):.3f}"


def t_modules_import_no_side_effects():
    import os
    # Убираем output/ если вдруг появился от прошлых запусков
    out_dir = ROOT / "output"
    had_before = out_dir.exists()
    if had_before:
        # не удаляем, просто фиксируем что он был
        pass
    mods = ["mixdown", "beat_gen", "humanization", "voice_synth",
            "release_export", "provenance", "track_templates",
            "render_queue", "lyrics_gen", "female_backing",
            "user_profile", "voice_recording", "voice_onboarding",
            "voice_vault_v9", "rvc_trainer_v9", "reference_ingest",
            "auto_qa", "self_diag_v13", "wizard_v12_integration",
            "master_pipeline_v12", "llm_clients_v15"]
    for m in mods:
        try:
            __import__(f"modules.{m}")
        except Exception as e:
            return False, f"module {m} import failed: {e}"
    # Проверяем что output/ не появился от чистого импорта
    # (если он был до — ок, если появился после — плохо)
    now_exists = out_dir.exists()
    if now_exists and not had_before:
        return False, "output/ created on import — side effect detected"
    return True, f"{len(mods)} modules imported, no import side effects"


def t_pipeline_verdict_not_blocked_sim():
    from app.core import orchestrator as o
    with tempfile.TemporaryDirectory() as td:
        r = o.run_full_pipeline(
            "smoke_v22", {"theme": "ночь", "genre": "drift_phonk"},
            dry_run=False, out_root=Path(td))
    v = r.get("verdict"); p = r.get("percent")
    if v == "BLOCKED_SIMULATION":
        return False, f"verdict={v} percent={p}"
    if v not in ("PASS", "PASS_WITH_FALLBACK", "PASS_BLOCKED"):
        return False, f"unexpected verdict={v}"
    if p < 80:
        return False, f"percent too low: {p}"
    return True, f"verdict={v} percent={p}"


def t_version_v22():
    v = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    ver = v.get("version", "")
    if not ver.startswith("22"):
        return False, f"version={ver} (expected 22.x)"
    return True, f"version={ver}"


TESTS = [
    ("v22.analyze_no_refs_not_fallback", t_analyze_no_refs_not_fallback),
    ("v22.groove_no_refs_not_fallback", t_groove_no_refs_not_fallback),
    ("v22.synth_beat_structured", t_synth_beat_structured),
    ("v22.fallback_lyrics_genre_variety", t_fallback_lyrics_genre_variety),
    ("v22.voice_scaffold_v22_formants", t_voice_scaffold_v22_formants),
    ("v22.modules_import_no_side_effects", t_modules_import_no_side_effects),
    ("v22.pipeline_verdict_not_blocked_sim", t_pipeline_verdict_not_blocked_sim),
    ("v22.version_v22", t_version_v22),
]


def main():
    print("=" * 64)
    print("ZS Music Maker v22 — smoke_v22")
    print("=" * 64)
    for name, fn in TESTS:
        _run(name, fn)
    n_ok = sum(1 for r in RESULTS if r["ok"])
    n_fail = sum(1 for r in RESULTS if not r["ok"])
    for r in RESULTS:
        status = "[PASS]" if r["ok"] else "[FAIL]"
        detail = r["detail"] or r["err"].splitlines()[-1] if r["err"] else ""
        print(f"{status} {r['name']:45s} {detail}")
    print("-" * 64)
    print(f"RESULT: {n_ok} PASS / {n_fail} FAIL / {len(RESULTS)} total")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
