# -*- coding: utf-8 -*-
"""
ZS Music Maker — smoke_v27
====================================================================
Проверяет пакет v27 (P0/P1) — качество аранжировки и честность скоринга.

  1. v27.no_regress_v26           — регрессия v26 (стерео, громкость).
  2. v27.structure_aware_score    — hit_scorer получает разметку секций
                                    и помечает метрики [structure-aware].
  3. v27.hook_energy_real         — hook_energy на 90 c треке ≥ 60.
  4. v27.structure_clarity_real   — structure_clarity ≥ 80.
  5. v27.hit_score_long_track     — итоговый hit_score на 90 c ≥ 65.
  6. v27.instant_intro            — первые 2 сек не тише медианы ×0.6.
Запуск:  python3 tools/smoke_v27.py
"""
from __future__ import annotations
import shutil, sys
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")


def _run(project_id, recipe):
    from app.core.orchestrator import run_full_pipeline
    out_root = ROOT / "output" / "smoke_v27" / project_id
    if out_root.exists():
        shutil.rmtree(out_root, ignore_errors=True)
    return run_full_pipeline(project_id, recipe, dry_run=False, out_root=out_root)


def _corr(p):
    y, _ = sf.read(p, always_2d=True)
    if y.shape[1] < 2:
        return 1.0
    return float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])


def _dbfs(p):
    y, _ = sf.read(p, always_2d=True)
    rms = float(np.sqrt(np.mean(y ** 2)))
    return 20.0 * np.log10(max(rms, 1e-9))


def main():
    print("=" * 64)
    print("ZS Music Maker v27 — smoke_v27 (structure-aware scoring)")
    print("=" * 64)

    _run("p_v27_short", {
        "references": [], "genre": "drift_phonk", "theme": "лето, тачки",
        "duration_sec": 12, "bpm_override": 130, "voice_mode": "off",
        "n_verses": 2, "aggression": 0.85,
    })
    out_short = ROOT / "output" / "smoke_v27" / "p_v27_short"
    master = out_short / "masters" / "master_streaming.wav"
    check("v27.no_regress_v26",
          master.exists() and 0.3 < _corr(master) < 0.98
          and abs(_dbfs(master) - (-13.5)) < 1.5,
          f"corr={_corr(master):.3f} dBFS={_dbfs(master):.2f}")

    r_long = _run("p_v27_long", {
        "references": [], "genre": "drift_phonk", "theme": "лето, тачки",
        "duration_sec": 90, "bpm_override": 130, "voice_mode": "off",
        "n_verses": 2, "aggression": 0.85,
    })
    out_long = ROOT / "output" / "smoke_v27" / "p_v27_long"
    hs = {}
    for s in r_long.get("stages", []):
        if s.get("name") == "_stage_hit_score":
            hs = s.get("output") or {}
    metrics = hs.get("metrics") or {}

    hints = " | ".join(str((metrics.get(k) or {}).get("hint", ""))
                       for k in ("hook_energy", "structure_clarity"))
    check("v27.structure_aware_score", "structure-aware" in hints,
          "hint contains [structure-aware]")

    he = (metrics.get("hook_energy") or {}).get("score", 0.0)
    check("v27.hook_energy_real", he >= 60.0, f"hook_energy={he}")

    sc = (metrics.get("structure_clarity") or {}).get("score", 0.0)
    check("v27.structure_clarity_real", sc >= 80.0, f"structure_clarity={sc}")

    total = hs.get("hit_score", 0.0)
    check("v27.hit_score_long_track", total >= 65.0, f"hit_score={total}")

    y, sr = sf.read(str(out_long / "masters" / "master_streaming.wav"),
                    always_2d=True)
    y = y.mean(axis=1)
    head = float(np.sqrt(np.mean(y[:int(sr * 2)] ** 2)))
    med = float(np.sqrt(np.mean(y ** 2)))
    check("v27.instant_intro", head > med * 0.6,
          f"head_rms={head:.4f} median_rms={med:.4f}")

    print("-" * 64)
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"RESULT: {npass} PASS / {len(RESULTS) - npass} FAIL / "
          f"{len(RESULTS)} total")
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
