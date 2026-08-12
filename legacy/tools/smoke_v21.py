# -*- coding: utf-8 -*-
"""ZS Music Maker v21 — smoke_v21."""
from __future__ import annotations
import os, sys, tempfile, traceback
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


def t_blocked_not_simulation():
    from app.core import orchestrator
    r1 = {"ok": True, "synthetic": True, "blocked": True, "engine": "rap_scaffold_numpy"}
    r2 = {"ok": True, "blocked": True, "reason": "no RVC model"}
    r3 = {"ok": True, "synthetic": True, "engine": "old_stub"}
    if orchestrator._is_simulation_result(r1):
        return False, "scaffold+blocked still classified as simulation"
    if orchestrator._is_simulation_result(r2):
        return False, "RVC blocked still classified as simulation"
    if not orchestrator._is_simulation_result(r3):
        return False, "real synthetic without blocked stopped being simulation"
    if not orchestrator._is_blocked_result(r1):
        return False, "_is_blocked_result missed scaffold+blocked"
    return True, "BLOCKED separated from simulation correctly"


def t_verdict_pass_with_fallback_no_heavy():
    from app.core import orchestrator
    with tempfile.TemporaryDirectory() as td:
        r = orchestrator.run_full_pipeline(
            "smoke_v21", {"theme": "ночь", "genre": "drift_phonk"},
            dry_run=False, out_root=Path(td))
    v = r.get("verdict"); p = r.get("percent")
    if v == "BLOCKED_SIMULATION":
        return False, f"honest baseline still hits BLOCKED_SIMULATION (percent={p})"
    if p < 75:
        return False, f"percent too low: {p} (expected >=75)"
    if v not in ("PASS", "PASS_WITH_FALLBACK", "PASS_BLOCKED"):
        return False, f"unexpected verdict={v} percent={p}"
    return True, f"verdict={v} percent={p}"


def t_rvc_stage_blocked_but_ok():
    from app.core import orchestrator
    with tempfile.TemporaryDirectory() as td:
        r = orchestrator._stage_rvc("dummy.wav", Path(td), upstream_synthetic=True)
    if not r.get("blocked"):
        return False, "RVC did not set blocked=True on synthetic upstream"
    if not r.get("ok"):
        return False, "RVC blocked should return ok=True (v21 honest BLOCKED)"
    return True, "RVC honest BLOCKED (ok=True + blocked=True)"


def t_stems_stage_blocked_when_no_demucs():
    from app.core import orchestrator
    try:
        import demucs  # noqa
        return True, "demucs installed — skipping"
    except Exception:
        pass
    with tempfile.TemporaryDirectory() as td:
        r = orchestrator._stage_stems("dummy.wav", Path(td))
    if not r.get("blocked"):
        return False, "Stems stage did not set blocked=True without demucs"
    if not r.get("ok"):
        return False, "Stems blocked should return ok=True"
    return True, "Stems honest BLOCKED"


def t_beat_constructor_no_import_side_effect():
    import importlib
    if "modules.beat_constructor" in sys.modules:
        del sys.modules["modules.beat_constructor"]
    tmp_missing = os.path.join(tempfile.gettempdir(),
                               "zsmm_bc_no_exist_" + os.urandom(4).hex())
    old = os.environ.get("ZSMM_BEAT_OUTPUT_DIR")
    os.environ["ZSMM_BEAT_OUTPUT_DIR"] = tmp_missing
    try:
        importlib.import_module("modules.beat_constructor")
        if os.path.isdir(tmp_missing):
            return False, "beat_constructor created OUTPUT_DIR on import"
    finally:
        if old is None:
            os.environ.pop("ZSMM_BEAT_OUTPUT_DIR", None)
        else:
            os.environ["ZSMM_BEAT_OUTPUT_DIR"] = old
        if os.path.isdir(tmp_missing):
            try:
                os.rmdir(tmp_missing)
            except Exception:
                pass
    return True, "no side effects on import"


def t_release_pack_placeholder_detectors():
    from modules import release_pack_full as rp
    if not rp._is_placeholder_isrc("XX-XXX-00-00000"):
        return False, "placeholder ISRC not detected"
    if rp._is_placeholder_isrc("US-A2P-25-00001"):
        return False, "real ISRC misclassified as placeholder"
    if not rp._is_placeholder_upc("0000000000000"):
        return False, "placeholder UPC not detected"
    if rp._is_placeholder_upc("602577123456"):
        return False, "real UPC misclassified as placeholder"
    return True, "placeholder detectors work correctly"


def t_version_bumped_to_21():
    import json
    data = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    v = str(data.get("version", ""))
    try:
        major = int(v.split(".")[0])
    except Exception:
        return False, f"bad version string: {v}"
    if major < 21:
        return False, f"version.json still on {v} (expected >=21)"
    return True, f"version={v} (>=21)"


def main():
    tests = [
        ("v21.blocked_not_simulation", t_blocked_not_simulation),
        ("v21.verdict_pass_with_fallback_no_heavy", t_verdict_pass_with_fallback_no_heavy),
        ("v21.rvc_stage_blocked_but_ok", t_rvc_stage_blocked_but_ok),
        ("v21.stems_stage_blocked_when_no_demucs", t_stems_stage_blocked_when_no_demucs),
        ("v21.beat_constructor_no_import_side_effect", t_beat_constructor_no_import_side_effect),
        ("v21.release_pack_placeholder_detectors", t_release_pack_placeholder_detectors),
        ("v21.version_bumped_to_21", t_version_bumped_to_21),
    ]
    print("=" * 64)
    print("ZS Music Maker v21 — smoke_v21")
    print("=" * 64)
    for name, fn in tests:
        _run(name, fn)
    for r in RESULTS:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"[{status}] {r['name']:48s} {r['detail']}")
        if r["err"]:
            print(f"       err: {r['err'].splitlines()[0]}")
    n_pass = sum(1 for r in RESULTS if r["ok"])
    n_fail = sum(1 for r in RESULTS if not r["ok"])
    print("-" * 64)
    print(f"RESULT: {n_pass} PASS / {n_fail} FAIL / {len(RESULTS)} total")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
