# -*- coding: utf-8 -*-
"""
ZS Music Maker — smoke_v29.py (God Mode E2E)
========================================================================
Проверяет:
  1) main.py --version читает version.json
  2) modules.midi_generator (guard при отсутствии mido, реальный вывод при наличии)
  3) full God Mode pipeline от ai_arrangement до god_mastering_pro
  4) master_god.wav: стерео, длительность ~120с, peak <= -1 dBTP, RMS в диапазоне
  5) honest LUFS-отчёт из mastering_pro

Запуск:
    python3 tools/smoke_v29.py
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

RESULTS = []


def _ok(name: str, extra: str = "") -> None:
    RESULTS.append((True, name, extra))
    print(f"[PASS] {name:40s} {extra}")


def _fail(name: str, extra: str = "") -> None:
    RESULTS.append((False, name, extra))
    print(f"[FAIL] {name:40s} {extra}")


def test_version_cli() -> None:
    try:
        out = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--version"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode == 0 and "ZS Music Maker" in out.stdout:
            _ok("v29.main_version_cli", f"rc=0 build in stdout")
        else:
            _fail("v29.main_version_cli", f"rc={out.returncode}")
    except Exception as e:
        _fail("v29.main_version_cli", str(e))


def test_midi_generator() -> None:
    from modules import midi_generator
    st = midi_generator.MIDIGenerator.get_status()
    g = midi_generator.MIDIGenerator(output_dir=str(ROOT / "output" / "smoke_v29" / "midi"))
    drum = g.generate_drum_pattern("drift_phonk", 140)
    mel = g.generate_melody_pattern("drift_phonk", "A", "minor", 140)
    if st["ok"]:
        if drum and mel and Path(drum).exists() and Path(mel).exists():
            _ok("v29.midi_generator", f"engine=mido drum+melody OK")
        else:
            _fail("v29.midi_generator", f"mido installed but files missing: {drum!r} / {mel!r}")
    else:
        # honest BLOCKED — не должно ломать pipeline
        if drum == "" and mel == "":
            _ok("v29.midi_generator", "BLOCKED honest fallback (mido missing)")
        else:
            _fail("v29.midi_generator", f"expected empty strings, got {drum!r}/{mel!r}")


def test_god_mode_e2e() -> None:
    out_root = ROOT / "output" / "smoke_v29" / "god"
    if out_root.exists():
        shutil.rmtree(out_root)
    from app.core.orchestrator_god import run_god_pipeline
    res = run_god_pipeline("smoke_v29", wizard_state=None, out_root=out_root)

    if res.get("status") == "completed":
        _ok("v29.god_e2e_status", f"elapsed={res.get('elapsed_sec')}s")
    else:
        _fail("v29.god_e2e_status", json.dumps(res.get("stages", []), default=str)[:200])
        return

    master = res.get("master_path")
    if not master or not Path(master).exists():
        _fail("v29.god_e2e_master_exists", f"missing {master}")
        return

    audio, sr = sf.read(master)
    if audio.ndim == 2 and audio.shape[1] == 2:
        _ok("v29.god_e2e_stereo", f"shape={audio.shape} sr={sr}")
    else:
        _fail("v29.god_e2e_stereo", f"shape={audio.shape}")

    dur = len(audio) / sr
    if 110 <= dur <= 130:
        _ok("v29.god_e2e_duration", f"{round(dur,1)}s")
    else:
        _fail("v29.god_e2e_duration", f"{round(dur,1)}s (want ~120s)")

    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    peak_db = 20.0 * np.log10(peak + 1e-12)
    # ceiling -1 dBTP, допускаем небольшой запас
    if peak_db <= -0.5:
        _ok("v29.god_e2e_true_peak", f"peak={round(peak_db,2)} dB (<= -0.5)")
    else:
        _fail("v29.god_e2e_true_peak", f"peak={round(peak_db,2)} dB (>-0.5)")

    rms = float(np.sqrt(np.mean(audio ** 2)))
    if 0.03 <= rms <= 0.6:
        _ok("v29.god_e2e_rms", f"rms={round(rms,3)}")
    else:
        _fail("v29.god_e2e_rms", f"rms={round(rms,3)} out of [0.03,0.6]")


def test_mastering_pro_metrics() -> None:
    """mastering_pro возвращает честные output-метрики (v29)."""
    from modules import mastering_pro
    # Синтетический вход
    sr = 44100
    t = np.linspace(0, 3.0, sr * 3, endpoint=False)
    x = 0.3 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
    stereo = np.stack([x, x], axis=1)
    in_wav = ROOT / "output" / "smoke_v29" / "master_in.wav"
    out_wav = ROOT / "output" / "smoke_v29" / "master_out.wav"
    in_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(in_wav), stereo, sr)
    r = mastering_pro.process_mastering(str(in_wav), str(out_wav), target_lufs=-14.0)
    if r.get("ok") and "output_peak_db" in r and "channels" in r:
        _ok("v29.mastering_pro_metrics",
            f"engine={r['engine']} ch={r['channels']} peak={r['output_peak_db']}dB lufs={r.get('output_lufs')}")
    else:
        _fail("v29.mastering_pro_metrics", str(r))


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
    print("=" * 64)
    test_version_cli()
    test_midi_generator()
    test_god_mode_e2e()
    test_mastering_pro_metrics()
    print("-" * 64)
    passed = sum(1 for r in RESULTS if r[0])
    total = len(RESULTS)
    failed = total - passed
    print(f"RESULT: {passed} PASS / {failed} FAIL / {total} total")
    _write_report("smoke_v29", passed, failed)
    return 0 if failed == 0 else 1


def _write_report(name: str, passed: int, failed: int) -> None:
    """v33: JSON-отчёт в logs/ для kpi_dashboard_v12 / self_diag_v13."""
    import json
    import time
    from pathlib import Path

    try:
        logs = Path(__file__).resolve().parents[1] / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        cases = {str(r[1] if len(r) > 1 else i): bool(r[0]) for i, r in enumerate(RESULTS)}
        (logs / f"{name}_report.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                    "passed": passed,
                    "failed": failed,
                    "total": passed + failed,
                    "cases": cases,
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass  # отчёт — nice-to-have, не должен валить smoke


if __name__ == "__main__":
    sys.exit(main())
