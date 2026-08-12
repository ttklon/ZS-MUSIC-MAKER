# -*- coding: utf-8 -*-
"""ZS Music Maker v14 — tools/smoke_v14.py"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# FIX v16 (P0): при запуске «python3 tools/smoke_v14.py» в sys.path попадает
# каталог tools/, а не корень проекта — все __import__("modules.*") ложно
# падали (21/28 FAIL без PYTHONPATH). Гарантируем доступность корня.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _pass(name, t): print(f"[PASS] {name}  ({t:.3f}s)")
def _fail(name, t, msg): print(f"[FAIL] {name}  ({t:.3f}s)  {msg}")


def _run_case(name, fn):
    t0 = time.time()
    try:
        r = fn()
        if r is False:
            _fail(name, time.time() - t0, "returned False")
            return False
        _pass(name, time.time() - t0)
        return True
    except Exception as e:
        _fail(name, time.time() - t0, f"{type(e).__name__}: {e}")
        return False


def _import(mod_name):
    def _f():
        __import__(mod_name)
        return True
    return _f


def _capability(mod_name):
    def _f():
        m = __import__(mod_name, fromlist=["capability_report"])
        return bool(m.capability_report())
    return _f


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v14 — smoke_v14")
    print("=" * 64)
    passed = 0; failed = 0
    cases = [
        ("import.mastering",       _import("modules.mastering")),
        ("import.sidechain",       _import("modules.sidechain")),
        ("import.voice_recording", _import("modules.voice_recording")),
        ("import.voice_onboarding",_import("modules.voice_onboarding")),
        ("import.updater",         _import("updater.updater")),
        ("import.readiness",       _import("tools.readiness")),
        ("import.fallback_audit",  _import("tools.fallback_audit")),
        ("import.orchestrator",    _import("app.core.orchestrator")),
        ("capability.mastering",       _capability("modules.mastering")),
        ("capability.sidechain",       _capability("modules.sidechain")),
        ("capability.voice_recording", _capability("modules.voice_recording")),
        ("legacy.mains_isolated",  lambda: (ROOT / "legacy" / "mains").exists()),
        ("legacy.patches_isolated",lambda: (ROOT / "legacy" / "patches").exists()),
        ("main.py.unified", lambda: len(list(ROOT.glob("main_v*.py"))) == 0),
        ("TZ.txt.present",     lambda: (ROOT / "TZ.txt").exists()),
        ("PROMPT.txt.present", lambda: (ROOT / "PROMPT.txt").exists()),
        ("genre_presets.50", lambda: len(list((ROOT / "data" / "genre_presets").glob("*.json"))) >= 50),
        ("updater.info",  lambda: __import__("updater.updater", fromlist=["program_dir"]).program_dir() is not None),
        ("readiness.compute", lambda: __import__("tools.readiness", fromlist=["compute"]).compute()[0] >= 0),
        ("fallback_audit.scan", lambda: __import__("tools.fallback_audit", fromlist=["scan_all"]).scan_all()["files_scanned"] > 0),
        ("modules.analyzer",   _import("modules.analyzer")),
        ("modules.groove",     _import("modules.groove_extractor")),
        ("modules.beat_ctor",  _import("modules.beat_constructor")),
        ("modules.hit_scorer", _import("modules.hit_scorer")),
        ("modules.anti_neuro", _import("modules.anti_neuro_v10")),
        ("modules.recording_v13", _import("modules.recording_v13")),
        ("modules.rvc_manager",_import("modules.rvc_manager")),
        ("rvc.no_pitch_fallback_in_infer", lambda: "raise RuntimeError" in (ROOT / "modules" / "rvc_manager.py").read_text(encoding="utf-8", errors="replace")),
    ]
    for name, fn in cases:
        r = _run_case(name, fn)
        if r:
            passed += 1
        else:
            failed += 1
    total = passed + failed
    print("-" * 64)
    print(f"RESULT: {passed} PASS / {failed} FAIL / {total} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
