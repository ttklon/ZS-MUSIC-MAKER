"""
ZS Music Maker — smoke_v23
Проверяет пакет правок v23:
  1) voice_convert: import без побочных эффектов (нет output/voice_vault/models)
  2) real_e2e_v14: sys.path содержит ROOT (прямой запуск не падает)
  3) mastering: numpy-DSP НЕ помечен fallback + K-взвешенная громкость
  4) texture scaffold: реально пишет WAV (не пустой path)
  5) version.json = 23.0.0
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS = []


def _rep(name: str, ok: bool, note: str = ""):
    RESULTS.append((name, ok, note))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:44s} {note}")


def t_voice_convert_lazy():
    code = (
        "import os,sys;sys.path.insert(0,'.');"
        "import modules.voice_convert as vc;"
        "bad=[w for w in ('output','voice_vault','models') if os.path.exists(w)];"
        "print('CREATED:',bad)"
    )
    tmp = tempfile.mkdtemp()
    try:
        for d in ("modules", "app"):
            shutil.copytree(
                ROOT / d, Path(tmp) / d, ignore=shutil.ignore_patterns("__pycache__")
            )
        si = ROOT / "safe_import.py"
        if si.exists():
            shutil.copy(si, tmp)
        r = subprocess.run(
            [sys.executable, "-c", code], cwd=tmp, capture_output=True, text=True
        )
        ok = "CREATED: []" in r.stdout
        _rep("v23.voice_convert_no_side_effect", ok, r.stdout.strip()[-60:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_e2e_syspath():
    # read file, ensure sys.path.insert with ROOT present before app import
    src = (ROOT / "tools" / "real_e2e_v14.py").read_text(encoding="utf-8")
    has_path = "sys.path.insert(0, str(ROOT))" in src
    # also ensure the import of app happens AFTER the path insert
    i_path = src.find("sys.path.insert(0, str(ROOT))")
    i_app = src.find("from app.core.orchestrator import")
    ok = has_path and (i_app == -1 or i_path < i_app)
    _rep("v23.real_e2e_sys_path", ok, "ROOT inserted before app import")


def t_mastering_numpy():
    import math

    import numpy as np

    from modules.mastering import _k_weighted_loudness_approx

    sr = 44100
    t = np.arange(sr * 4) / sr
    y = np.stack([0.5 * np.sin(2 * np.pi * 1000 * t)] * 2, axis=1).astype("float32")
    approx = _k_weighted_loudness_approx(y, sr)
    rms_old = 20 * math.log10(float(np.sqrt(np.mean(y**2))) + 1e-9) - 3.0
    # K-weighted should be LOUDER (closer to true ~-9 LUFS) than naive RMS-3
    ok = approx > rms_old
    _rep(
        "v23.mastering_k_weighted_louder", ok, f"K={approx:.2f} vs RMS-3={rms_old:.2f}"
    )


def t_mastering_not_fallback():
    import inspect

    from modules import mastering

    src = inspect.getsource(mastering._try_numpy_dsp)
    # the numpy path returns fallback_used=False (it is a real DSP path)
    ok = "fallback_used=False" in src
    _rep("v23.mastering_numpy_honest_label", ok, "numpy_dsp not marked as fallback")


def t_texture_scaffold():
    from app.core import orchestrator as orch

    with tempfile.TemporaryDirectory() as td:
        r = orch._texture_scaffold("test atmosphere", Path(td))
        ok = (
            bool(r.get("ok"))
            and r.get("path")
            and Path(r["path"]).exists()
            and Path(r["path"]).stat().st_size > 1000
            and r.get("synthetic")
        )
        _rep(
            "v23.texture_scaffold_real_wav",
            ok,
            f"path={bool(r.get('path'))} engine={r.get('engine')}",
        )


def t_version():
    try:
        v = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
        ok = v.get("version") == "23.0.0"
        _rep("v23.version_v23", ok, v.get("version", "?"))
    except Exception as e:
        _rep("v23.version_v23", False, str(e))


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v23 — smoke_v23")
    print("=" * 64)
    t_voice_convert_lazy()
    t_e2e_syspath()
    t_mastering_numpy()
    t_mastering_not_fallback()
    t_texture_scaffold()
    t_version()
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    nfail = sum(1 for _, ok, _ in RESULTS if not ok)
    print("-" * 64)
    print(f"RESULT: {npass} PASS / {nfail} FAIL / {len(RESULTS)} total")
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
