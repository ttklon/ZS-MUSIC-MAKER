"""
ZS Music Maker — smoke_v26
====================================================================
Проверяет пакет фиксов v26 (P0/P1) — качество финального аудио:

  1. v26.beat_stereo             — beat_constructor пишет СТЕРЕО (было моно
                                   → весь мастер corr=1.0). Проверяем
                                   shape=(N,2) и corr ∈ [0.3, 0.98].
  2. v26.master_stereo_preserved — master_streaming.wav сохраняет стерео.
  3. v26.master_loudness_target  — master в target -13.5 dBFS ±1.5.
  4. v26.beat_drop_fade          — есть fade ≥100мс перед первым hook
                                   (реальный drop, не плаво).
  5. v26.hit_score_improved      — итоговый hit_score ≥55 (был 50.28 на v25).
  6. v26.hook_repeat_fallback    — hook_repeatability даёт raw ≥ 1 на
                                   коротком ритмичном сигнале.
Запуск:  python3 tools/smoke_v26.py
"""

from __future__ import annotations

import shutil
import sys
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

    out_root = ROOT / "output" / "smoke_v26" / project_id
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
    rms = float(np.sqrt(np.mean(y**2)))
    return 20.0 * np.log10(max(rms, 1e-12))


def main():
    print("=" * 64)
    print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
    print("=" * 64)

    res = _run(
        "p_v26",
        {
            "references": [],
            "theme": "лето, тачки",
            "genre": "drift_phonk",
            "duration_sec": 35,
            "bpm_override": 130,
        },
    )
    root_out = ROOT / "output" / "smoke_v26" / "p_v26"
    beat = root_out / "beat.wav"
    master = root_out / "masters" / "master_streaming.wav"

    # 1
    if beat.exists():
        y, sr = sf.read(str(beat), always_2d=True)
        stereo = y.shape[1] >= 2
        c = _corr(str(beat)) if stereo else 1.0
        check(
            "v26.beat_stereo",
            stereo and 0.3 <= c <= 0.98,
            f"shape={y.shape} corr={c:.3f}",
        )
    else:
        check("v26.beat_stereo", False, "beat.wav missing")

    # 2
    if master.exists():
        c = _corr(str(master))
        check("v26.master_stereo_preserved", 0.3 <= c <= 0.98, f"corr={c:.3f}")
    else:
        check("v26.master_stereo_preserved", False, "master missing")

    # 3
    if master.exists():
        db = _dbfs(str(master))
        check(
            "v26.master_loudness_target",
            -15.0 <= db <= -12.0,
            f"dBFS={db:.2f} target=-13.5±1.5",
        )
    else:
        check("v26.master_loudness_target", False, "master missing")

    # 4
    if beat.exists():
        y, sr = sf.read(str(beat), always_2d=False)
        if y.ndim > 1:
            y = y.mean(axis=1)
        win = int(sr * 0.020)
        hop = int(sr * 0.010)
        rms = np.array(
            [
                float(np.sqrt(np.mean(y[i : i + win] ** 2)) + 1e-12)
                for i in range(0, len(y) - win, hop)
            ]
        )
        med = float(np.median(rms))
        low = rms < (med * 0.15)
        max_run = cur = 0
        for v in low:
            if v:
                cur += 1
                max_run = max(max_run, cur)
            else:
                cur = 0
        check(
            "v26.beat_drop_fade",
            max_run >= 10,
            f"max_low_run={max_run} hops (need>=10, ~100ms)",
        )
    else:
        check("v26.beat_drop_fade", False, "beat.wav missing")

    # 5
    hit = None
    for s in res.get("stages", []):
        if s.get("name") == "_stage_hit_score":
            hit = s.get("output") or {}
            break
    if hit:
        sc = float(hit.get("hit_score", 0.0) or 0.0)
        check(
            "v26.hit_score_improved",
            sc >= 55.0,
            f"score={sc:.2f} (need>=55, prev v25=50.28)",
        )
    else:
        check("v26.hit_score_improved", False, "no hit_score stage")

    # 6
    try:
        from modules import hit_scorer as hs

        sr = 22050
        t = np.arange(sr * 5) / sr
        env = np.zeros_like(t)
        for i in range(5):
            st = int(i * sr * 1.0)
            en = min(st + int(sr * 0.4), len(env))
            env[st:en] = np.linspace(1.0, 0.0, en - st)
        y = env * np.sin(2 * np.pi * 220 * t) * 0.5
        score, raw = hs._hook_repeatability(y.astype(np.float32), sr)
        check(
            "v26.hook_repeat_fallback",
            raw >= 1,
            f"raw={raw} score={score:.1f} (need raw>=1)",
        )
    except Exception as e:
        check("v26.hook_repeat_fallback", False, f"crash: {e}")

    print("-" * 64)
    p = sum(1 for _, o, _ in RESULTS if o)
    f = len(RESULTS) - p
    print(f"RESULT: {p} PASS / {f} FAIL / {len(RESULTS)} total")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
