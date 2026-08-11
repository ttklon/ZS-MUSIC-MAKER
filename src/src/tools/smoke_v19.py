"""
ZS Music Maker v19 — tools/smoke_v19.py

Регресс-тесты для P0/P1 фиксов v19:
  1) hit_score_real           — hit_scorer.score_track(...) реально вызывается
  2) stems_uses_split_stems   — стадия стемов пытается позвать split_stems
  3) voice_synth_scaffold     — при отсутствии TTS честный rap_scaffold_numpy
  4) rvc_refuses_scaffold     — RVC отказывается работать поверх скэффолда
  5) sidechain_kick_bp        — sidechain пропускает kick через 30-200 Hz BP
  6) texture_honest_skip      — texture skipped honestly, path пуст
"""

from __future__ import annotations

import sys
import traceback
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
        _record(
            name,
            False,
            "",
            f"{type(e).__name__}: {e}\n" + traceback.format_exc(limit=3),
        )


def t_hit_score_real():
    from app.core import orchestrator

    r = orchestrator.run_full_pipeline(
        "smoke_v19_hit",
        {"references": [], "theme": "test", "genre": "phonk"},
        dry_run=True,
    )
    hs = [s for s in r["stages"] if s["name"] == "_stage_hit_score"]
    if not hs:
        return False, "no hit_score stage"
    st = hs[0]
    if not st.get("ok"):
        return False, f"stage not ok: {st.get('reason')}"
    out = st.get("output") or {}
    if not isinstance(out.get("metrics"), dict):
        return False, "no metrics dict in output"
    if out.get("hit_score") in (None, 60.0):
        return False, f"suspicious hit_score={out.get('hit_score')}"
    if "score_track" not in str(out.get("engine", "")):
        return False, f"wrong engine={out.get('engine')}"
    return True, f"hit={out['hit_score']} verdict={out.get('verdict')}"


def t_stems_uses_split_stems():
    src = (ROOT / "app" / "core" / "orchestrator.py").read_text(encoding="utf-8")
    if "split_stems" not in src:
        return False, "no split_stems reference in _stage_stems"
    from modules import stem_splitter

    if not callable(getattr(stem_splitter, "split_stems", None)):
        return False, "stem_splitter.split_stems missing"
    from app.core import orchestrator

    r = orchestrator._stage_stems(str(ROOT / "main.py"), ROOT / "output")
    if r.get("ok"):
        return True, "demucs available, stems ok"
    if not r.get("blocked") and "not installed" not in (r.get("reason") or ""):
        return False, f"stems failure not blocked: {r}"
    return True, f"honest blocked: {r.get('reason', '')[:50]}"


def t_voice_synth_scaffold():
    from app.core import orchestrator

    r = orchestrator._stage_voice_synth(
        "тест раз два три четыре пять", ROOT / "output" / "audit_v19_smoke"
    )
    if not r.get("ok"):
        return False, f"voice_synth failed even scaffold: {r.get('reason')}"
    if not r.get("synthetic"):
        if r.get("engine") in ("pyttsx3", "voice_synth.synth"):
            return True, f"real TTS available: {r.get('engine')}"
        return False, f"no synthetic flag: {r}"
    if not r.get("blocked"):
        return False, "synthetic must be blocked=True"
    if r.get("engine") != "rap_scaffold_numpy":
        return False, f"wrong engine {r.get('engine')}"
    return True, "rap_scaffold_numpy honest"


def t_rvc_refuses_scaffold():
    from app.core import orchestrator

    r = orchestrator._stage_rvc(
        "nonexistent.wav", ROOT / "output", upstream_synthetic=True
    )
    if r.get("ok"):
        return False, "RVC accepted scaffold — P0.05 violation"
    if not r.get("blocked"):
        return False, f"RVC didn't block scaffold: {r}"
    if (
        "P0.05" not in (r.get("reason") or "")
        and "synthetic" not in (r.get("reason") or "").lower()
    ):
        return False, f"unclear reason: {r.get('reason')}"
    return True, "RVC honestly blocked scaffold"


def t_sidechain_kick_bp():
    src = (ROOT / "modules" / "sidechain.py").read_text(encoding="utf-8")
    if "_bandpass_numpy(kick" not in src:
        return False, "kick bandpass not applied before envelope"
    if "30.0" not in src or "200.0" not in src:
        return False, "kick bandpass 30-200 Hz limits missing"
    return True, "kick HP/BP 30-200 Hz enforced"


def t_texture_honest_skip():
    from app.core import orchestrator

    r = orchestrator._stage_texture("test prompt", ROOT / "output")
    if not r.get("ok"):
        return False, f"texture not ok: {r.get('reason')}"
    if r.get("path"):
        return True, "real texture generated"
    if not r.get("blocked"):
        return False, f"no path and no blocked flag: {r}"
    if not r.get("fallback_used"):
        return False, "blocked but no fallback_used flag"
    return True, "honest blocked (no fake audio)"


def main():
    tests = [
        ("v19.hit_score_real", t_hit_score_real),
        ("v19.stems_uses_split_stems", t_stems_uses_split_stems),
        ("v19.voice_synth_scaffold", t_voice_synth_scaffold),
        ("v19.rvc_refuses_scaffold", t_rvc_refuses_scaffold),
        ("v19.sidechain_kick_bp", t_sidechain_kick_bp),
        ("v19.texture_honest_skip", t_texture_honest_skip),
    ]

    print("=" * 64)
    print("ZS Music Maker v19 — smoke_v19")
    print("=" * 64)
    for name, fn in tests:
        _run(name, fn)

    for r in RESULTS:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"[{status}] {r['name']:36s} {r['detail']}")
        if r["err"]:
            print(f"       err: {r['err'].splitlines()[0]}")

    n_pass = sum(1 for r in RESULTS if r["ok"])
    n_fail = sum(1 for r in RESULTS if not r["ok"])
    print("-" * 64)
    print(f"RESULT: {n_pass} PASS / {n_fail} FAIL / {len(RESULTS)} total")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
