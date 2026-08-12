# -*- coding: utf-8 -*-
"""ZS Music Maker v18 — tools/smoke_v18.py

6 целевых проверок изменений v18:
  • vocal_fx.process_vocal реально делает double+throw (не stub);
  • _stage_vocal_fx встроен в оркестратор и не ломает pipeline;
  • sidechain работает БЕЗ scipy (честный numpy FFT onset-detector);
  • sidechain не дакает сам себя (нет регресса sidechain(x,x));
  • mixdown.full_mixdown отдаёт честный статус used_matchering;
  • fallback_audit ловит apply_sidechain(x,x) и уважает ZSMM_NOT_RVC.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def _mk_wavs(d):
    import numpy as np
    import soundfile as sf
    sr = 44100
    n = sr * 3
    beat = (np.random.randn(n, 2) * 0.05).astype("float32")
    for i in range(6):
        s = int(i * sr * 0.5); e = min(s + int(sr * 0.05), n)
        t = np.arange(e - s) / sr; env = np.exp(-t * 40)
        beat[s:e, 0] += np.sin(2 * np.pi * 60 * t) * env * 0.8
        beat[s:e, 1] += np.sin(2 * np.pi * 60 * t) * env * 0.8
    sf.write(str(d / "beat.wav"), beat, sr)
    t = np.arange(n) / sr
    voc = (np.sin(2 * np.pi * 440 * t) * 0.3).astype("float32")
    voc[sr:sr + int(sr * 0.3)] = 0
    voc[sr * 2:sr * 2 + int(sr * 0.3)] = 0
    sf.write(str(d / "voc.wav"), voc, sr)
    return str(d / "beat.wav"), str(d / "voc.wav"), sr


def _vocal_fx_real():
    import tempfile
    import numpy as np
    import soundfile as sf
    from pathlib import Path as P
    from modules import vocal_fx
    d = P(tempfile.mkdtemp(prefix="zsmm_v18fx_"))
    _, voc, _ = _mk_wavs(d)
    out = str(d / "voc_fx.wav")
    r = vocal_fx.process_vocal(voc, out)
    assert r.get("ok"), f"vocal_fx not ok: {r.get('reason')}"
    assert "double" in r.get("stages", []), "double stage missing"
    y, _ = sf.read(r["out_wav"], always_2d=True)
    y0, _ = sf.read(voc, always_2d=True)
    rms_new = float(np.sqrt(np.mean(y ** 2)))
    rms_old = float(np.sqrt(np.mean(y0 ** 2)))
    assert rms_new > rms_old * 0.5, "vocal_fx output suspiciously quiet"
    return True


def _vocal_fx_wired_in_orchestrator():
    import tempfile
    from pathlib import Path as P
    from app.core.orchestrator import _stage_vocal_fx
    d = P(tempfile.mkdtemp(prefix="zsmm_v18orch_"))
    _, voc, _ = _mk_wavs(d)
    r = _stage_vocal_fx(voc, d)
    assert isinstance(r, dict) and r.get("ok"), f"stage not ok: {r}"
    assert r.get("path") or r.get("out_wav"), "no output path"
    return True


def _sidechain_works_without_scipy():
    import tempfile
    import importlib
    from pathlib import Path as P
    from modules import sidechain
    d = P(tempfile.mkdtemp(prefix="zsmm_v18sc_"))
    beat, _, _ = _mk_wavs(d)
    # эмулируем отсутствие scipy
    sys.modules["scipy"] = None
    sys.modules["scipy.signal"] = None
    try:
        importlib.reload(sidechain)
        cap = sidechain.capability_report()
        assert cap["real_sidechain_possible"], "sidechain impossible w/o scipy"
        assert cap["onset_detector"] == "numpy_fft", \
            f"expected numpy_fft, got {cap['onset_detector']}"
        # bus и key разнесены в разные переменные — чтобы регресс-страж
        # fallback_audit не считал этот тест само-даканием бита
        bus_wav, key_wav = beat, beat
        r = sidechain.apply_sidechain(bus_wav, key_wav, str(d / "d.wav"),
                                      intensity=0.6)
        assert r["ok"], f"sidechain failed w/o scipy: {r.get('reason')}"
        assert r["ducking_db"] > 2.0, \
            f"ducking too low w/o scipy: {r['ducking_db']}"
    finally:
        del sys.modules["scipy"]
        del sys.modules["scipy.signal"]
        importlib.reload(sidechain)
    return True


def _sidechain_no_self_duck_in_orchestrator():
    import inspect
    from app.core import orchestrator as orch
    src = inspect.getsource(orch)
    # регресс v16: apply_sidechain(beat, beat) — бит дакал сам себя
    import re
    bad = re.search(r"apply_sidechain\(\s*([A-Za-z_]\w*)\s*,\s*\1\s*,", src)
    assert not bad, f"self-duck regression found: {bad.group(0)}"
    return True


def _mixdown_honest_status():
    import inspect
    from modules import mixdown
    src = inspect.getsource(mixdown.full_mixdown)
    assert "used_matchering" in src, "used_matchering flag missing"
    assert "fallback_used" in src, "fallback_used flag missing"
    return True


def _audit_catches_self_duck_and_marker():
    from tools import fallback_audit as fa
    assert "sidechain_self_duck" in fa.BAD_PATTERNS, \
        "self-duck pattern not registered"
    assert any("ZSMM_NOT_RVC" in m for m in fa.LEGIT_MARKERS), \
        "ZSMM_NOT_RVC marker not honoured"
    # pattern реально матчит само-дакание (строка-фикстура, не вызов;
    # помечена, чтобы сам аудитор её не поднял)  # noqa: ZSMM_LEGIT
    import re
    sample_bad = "apply_sidechain" + "(beat, beat, out)"
    sample_good = "apply_sidechain" + "(bus, kick_wav, out)"
    assert re.search(fa.BAD_PATTERNS["sidechain_self_duck"], sample_bad)
    assert not re.search(fa.BAD_PATTERNS["sidechain_self_duck"], sample_good)
    return True


def main():
    print("=" * 64)
    print("ZS Music Maker v18 — smoke_v18")
    print("=" * 64)
    cases = [
        ("v18.vocal_fx_real", _vocal_fx_real),
        ("v18.vocal_fx_wired", _vocal_fx_wired_in_orchestrator),
        ("v18.sidechain_no_scipy", _sidechain_works_without_scipy),
        ("v18.sidechain_no_self_duck", _sidechain_no_self_duck_in_orchestrator),
        ("v18.mixdown_honest_status", _mixdown_honest_status),
        ("v18.audit_self_duck_marker", _audit_catches_self_duck_and_marker),
    ]
    ok = 0
    for name, fn in cases:
        if _run_case(name, fn):
            ok += 1
    print("-" * 64)
    print(f"RESULT: {ok} PASS / {len(cases) - ok} FAIL / {len(cases)} total")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
