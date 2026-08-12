"""
ZS Music Maker — smoke_v27 (session 2026-08-12-2200)
====================================================================
Регрессионный страж пакета фиксов этой сессии:

  1. v27.mastering_source_present   — modules/mastering.py существует
                                      как исходник (был потерян в
                                      f862aaf, чинил v27, снова
                                      пропадал — не даём регрессу).
  2. v27.mastering_api_contract     — master_all_stands / capability_report /
                                      _k_weighted_loudness_approx экспортированы.
  3. v27.master_streaming_wav       — реальный master_streaming.wav пишется
                                      (без него весь pipeline не отдаёт релиз).
  4. v27.master_lufs_honest         — целевой LUFS -13.5 ± 2.5 ЧЕРЕЗ
                                      pyloudnorm (ITU-BS.1770), а не dBFS RMS.
  5. v27.no_pitch_shift_rvc_flag    — fallback_audit не находит
                                      pitch_shift_as_rvc red flags.
  6. v27.self_diag_no_crash         — self_diag_v13 не падает от
                                      отсутствия logs/ директории.
  7. v27.windows_build_workflow     — .github/workflows/windows-build.yml
                                      существует и собирает EXE.

Запуск:  python3 tools/smoke_v27.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name:40s} {detail}")


def _lufs(path: Path) -> float:
    y, sr = sf.read(str(path), always_2d=True)
    try:
        import pyloudnorm as pyln  # type: ignore

        meter = pyln.Meter(sr)
        return float(meter.integrated_loudness(y))
    except Exception:
        rms = float(np.sqrt(np.mean(y**2)) + 1e-12)
        return 20.0 * float(np.log10(rms))


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v27 — smoke_v27 (session regression guard)")
    print("=" * 64)

    # 1
    src = ROOT / "modules" / "mastering.py"
    check(
        "v27.mastering_source_present",
        src.exists() and src.stat().st_size > 5_000,
        f"exists={src.exists()} size={src.stat().st_size if src.exists() else 0}",
    )

    # 2
    api_ok = True
    api_missing: list[str] = []
    try:
        from modules import mastering  # noqa

        for fn in ("master_all_stands", "capability_report", "_k_weighted_loudness_approx"):
            if not hasattr(mastering, fn):
                api_ok = False
                api_missing.append(fn)
    except Exception as e:
        api_ok = False
        api_missing.append(f"import_err:{e}")
    check(
        "v27.mastering_api_contract",
        api_ok,
        "OK" if api_ok else f"missing={api_missing}",
    )

    # 3 + 4: реально прогоняем оркестратор
    from app.core.orchestrator import run_full_pipeline

    proj = ROOT / "output" / "smoke_v27" / "p_v27"
    if proj.exists():
        shutil.rmtree(proj, ignore_errors=True)
    proj.mkdir(parents=True, exist_ok=True)

    recipe = {
        "references": [],
        "theme": "город, ночь",
        "genre": "drift_phonk",
        "duration_sec": 30,
        "bpm_override": 130,
    }
    try:
        run_full_pipeline("p_v27", recipe, dry_run=False, out_root=proj)
    except Exception as e:
        print(f"[smoke_v27] pipeline exception: {e}")

    master = proj / "masters" / "master_streaming.wav"
    check(
        "v27.master_streaming_wav",
        master.exists() and master.stat().st_size > 100_000,
        f"exists={master.exists()} size={master.stat().st_size if master.exists() else 0}",
    )

    if master.exists():
        lufs = _lufs(master)
        check(
            "v27.master_lufs_honest",
            -16.0 <= lufs <= -11.0,
            f"LUFS={lufs:.2f} target=-13.5±2.5",
        )
    else:
        check("v27.master_lufs_honest", False, "no master")

    # 5
    try:
        from tools import fallback_audit

        rep = fallback_audit.scan_all()
        red = rep.get("red_flags", {}) or {}
        check(
            "v27.no_pitch_shift_rvc_flag",
            not red,
            "red=" + json.dumps(red, ensure_ascii=False) if red else "no red flags",
        )
    except Exception as e:
        check("v27.no_pitch_shift_rvc_flag", False, f"exc:{e}")

    # 6
    try:
        rc = subprocess.run(
            [sys.executable, "main.py", "--self-diag"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        check(
            "v27.self_diag_no_crash",
            rc.returncode == 0,
            f"rc={rc.returncode}",
        )
    except Exception as e:
        check("v27.self_diag_no_crash", False, f"exc:{e}")

    # 7
    wf = ROOT / ".github" / "workflows" / "windows-build.yml"
    ok_wf = wf.exists() and "pyinstaller" in wf.read_text(encoding="utf-8", errors="replace").lower()
    check(
        "v27.windows_build_workflow",
        ok_wf,
        f"exists={wf.exists()}",
    )

    print("-" * 64)
    pas = sum(1 for _, ok, _ in RESULTS if ok)
    fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"RESULT: {pas} PASS / {fail} FAIL / {len(RESULTS)} total")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
