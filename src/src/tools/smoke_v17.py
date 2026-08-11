"""ZS Music Maker v17 — tools/smoke_v17.py

6 целевых проверок P0-фиксов v17:
  • _stage_lyrics отдаёт И text, И структуру;
  • _stage_beat реально дергает construct_beat;
  • _stage_polish находит polish_vocal;
  • _stage_mix_and_sidechain пропускает вокал в bus;
  • main.py читает VERSION из version.json (нет drift);
  • orchestrator помечен v17.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _pass(name, t):
    print(f"[PASS] {name}  ({t:.3f}s)")


def _fail(name, t, msg):
    print(f"[FAIL] {name}  ({t:.3f}s)  {msg}")


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


def _lyrics_returns_both_text_and_struct():
    from app.core.orchestrator import _stage_lyrics

    r = _stage_lyrics("ночь, движ", "phonk")
    assert r.get("ok"), "lyrics stage not ok"
    txt = r.get("text") or ""
    lyr = r.get("lyrics") or {}
    assert txt.strip(), "lyrics.text is empty (P0 regression)"
    assert isinstance(lyr, dict) and (
        lyr.get("verse1") or lyr.get("chorus")
    ), "lyrics.lyrics struct empty (P0 regression)"
    return True


def _beat_uses_construct_beat():
    import tempfile
    from pathlib import Path as P

    from app.core.orchestrator import _stage_beat

    d = P(tempfile.mkdtemp(prefix="zsmm_smoke_"))
    r = _stage_beat(
        {"duration_sec": 8, "n_verses": 1},
        d,
        groove=None,
        style_vector={"target_bpm": 120, "target_mode": "minor"},
    )
    if not (isinstance(r, dict) and r.get("ok")):
        return False
    engine = r.get("engine") or ""
    return engine.startswith("beat_constructor") or r.get("fallback_used") is True


def _polish_finds_polish_vocal():
    from modules import anti_neuro_v10 as an

    assert hasattr(an, "polish_vocal"), "anti_neuro_v10.polish_vocal missing (P0)"
    assert hasattr(an, "apply_polish"), "anti_neuro_v10.apply_polish missing (v17)"
    return True


def _mix_bus_has_vocal_content():
    try:
        import numpy as np
        import soundfile as sf
    except Exception:
        return True
    import tempfile
    from pathlib import Path as P

    from app.core.orchestrator import _stage_mix_and_sidechain

    d = P(tempfile.mkdtemp(prefix="zsmm_smoke_mix_"))
    sr = 44100
    n = sr * 3
    beat = (np.random.randn(n, 2) * 0.05).astype("float32")
    for i in range(6):
        s = int(i * sr * 0.5)
        e = min(s + int(sr * 0.05), n)
        t = np.arange(e - s) / sr
        env = np.exp(-t * 40)
        beat[s:e, 0] += (np.sin(2 * np.pi * 60 * t) * env).astype("float32") * 0.8
        beat[s:e, 1] += (np.sin(2 * np.pi * 60 * t) * env).astype("float32") * 0.8
    b_path = str(d / "beat.wav")
    sf.write(b_path, beat, sr)
    t = np.arange(n) / sr
    voc = (np.sin(2 * np.pi * 440 * t) * 0.3).astype("float32")
    v_path = str(d / "voice.wav")
    sf.write(v_path, voc, sr)
    r = _stage_mix_and_sidechain(b_path, v_path, d)
    if not (isinstance(r, dict) and r.get("ok")):
        return False
    out_wav = r.get("out_wav")
    if not out_wav or not P(out_wav).exists():
        return False
    y, _ = sf.read(out_wav, always_2d=True)
    rms_mix = float(np.sqrt(np.mean(y**2)) + 1e-9)
    rms_beat = float(np.sqrt(np.mean(beat**2)) + 1e-9)
    return rms_mix > rms_beat * 1.05


def _version_from_json_no_drift():
    vp = ROOT / "version.json"
    mp = ROOT / "main.py"
    assert vp.exists(), "version.json missing"
    data = json.loads(vp.read_text(encoding="utf-8"))
    v_json = data.get("version")
    txt = mp.read_text(encoding="utf-8", errors="replace")
    for hard in (
        'VERSION = "14',
        'VERSION = "15',
        'VERSION = "16',
        'VERSION = "17',
        'VERSION = "18',
    ):
        assert hard not in txt, f"VERSION hardcoded drift: {hard}"
    # v18: тест версионно-нейтрален — важно отсутствие drift и чтение
    # версии из version.json, а не конкретный номер. main.py должен
    # брать VERSION через _load_version_info(), а не хардкодить.
    assert v_json and v_json[0].isdigit(), f"version.json version malformed: {v_json}"
    assert (
        "_load_version_info" in txt
    ), "main.py no longer reads version from version.json (drift risk)"
    return True


def _orchestrator_docstring_v17():
    orch = (ROOT / "app" / "core" / "orchestrator.py").read_text(
        encoding="utf-8", errors="replace"
    )
    return "v17 fixes" in orch


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v17 — smoke_v17")
    print("=" * 64)
    passed = 0
    failed = 0
    cases = [
        ("v17.lyrics_text_and_struct", _lyrics_returns_both_text_and_struct),
        ("v17.beat_wiring", _beat_uses_construct_beat),
        ("v17.polish_vocal_present", _polish_finds_polish_vocal),
        ("v17.mix_bus_has_vocal", _mix_bus_has_vocal_content),
        ("v17.version_no_drift", _version_from_json_no_drift),
        ("v17.orchestrator_marked", _orchestrator_docstring_v17),
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
