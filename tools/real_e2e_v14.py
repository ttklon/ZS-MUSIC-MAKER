"""
ZS Music Maker v14 — tools/real_e2e_v14.py

РЕАЛЬНЫЙ E2E-прогон:
  1) генерирует синтетический WAV-референс;
  2) вызывает run_full_pipeline(dry_run=False);
  3) сохраняет артефакты в output/audit_v14/e2e_v14_<ts>/;
  4) проверяет каждый выходной файл;
  5) собирает fallback_audit + readiness;
  6) финальный отчёт в JSON.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# v23 FIX: при прямом запуске «python3 tools/real_e2e_v14.py» каталог tools/
# попадает в sys.path вместо корня проекта — из-за этого `import app`
# падал с ModuleNotFoundError. Гарантируем ROOT в sys.path.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _synthesize_reference(
    out_wav: Path, duration: float = 15.0, sr: int = 44100, bpm: int = 140
) -> dict:
    import numpy as np
    import soundfile as sf

    n = int(sr * duration)
    t = np.arange(n) / sr
    y = np.zeros(n, dtype="float32")

    beat = 60.0 / bpm
    for i in range(int(duration / beat)):
        s = int(i * beat * sr)
        e = min(s + int(sr * 0.15), n)
        if i % 2 == 0:
            tt = np.arange(e - s) / sr
            freq = 55 * np.exp(-tt * 15)
            y[s:e] += np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-tt * 8) * 0.9
        else:
            tt = np.arange(e - s) / sr
            tone = np.sin(2 * np.pi * 220 * tt) * np.exp(-tt * 25)
            noise = np.random.randn(e - s).astype("float32") * np.exp(-tt * 10)
            y[s:e] += (tone * 0.4 + noise * 0.6) * 0.7
        y[s:e] += np.sin(2 * np.pi * 55 * t[s:e]) * 0.15

    for j in range(int(duration / (beat / 2))):
        s = int(j * beat / 2 * sr)
        e = min(s + int(sr * 0.05), n)
        tt = np.arange(e - s) / sr
        y[s:e] += np.random.randn(e - s).astype("float32") * np.exp(-tt * 60) * 0.35

    y = y / (np.max(np.abs(y)) + 1e-9) * 0.9
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_wav), y, sr)
    return {"path": str(out_wav), "sr": sr, "duration": duration, "bpm": bpm}


def _check_wav(path: str) -> dict:
    try:
        import soundfile as sf

        info = sf.info(path)
        return {
            "exists": True,
            "path": path,
            "sr": info.samplerate,
            "channels": info.channels,
            "duration_sec": round(info.frames / info.samplerate, 2),
            "size_bytes": Path(path).stat().st_size,
        }
    except Exception as e:
        return {"exists": False, "path": path, "error": str(e)}


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
    print("=" * 64)

    ts = int(time.time())
    workdir = ROOT / "output" / "audit_v14" / f"e2e_v14_{ts}"
    workdir.mkdir(parents=True, exist_ok=True)

    ref_path = workdir / "reference.wav"
    ref_meta = _synthesize_reference(ref_path, duration=15.0, bpm=140)
    print(
        f"[e2e] synthetic reference: {ref_path}  (sr={ref_meta['sr']}, dur={ref_meta['duration']}s)"
    )

    from app.core.orchestrator import run_full_pipeline

    result = run_full_pipeline(
        project_id=f"e2e_v14_{ts}",
        wizard_state={
            "references": [str(ref_path)],
            "theme": "лето, тачки, ночной драйв",
            "genre": "drift_phonk",
            "artist": "ZS Producer",
        },
        dry_run=False,
        out_root=workdir,
    )

    (workdir / "pipeline_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    artifacts = {}
    for cand in ("beat.wav", "voice_preview.wav", "mix_ducked.wav", "polished.wav"):
        p = workdir / cand
        if p.exists():
            artifacts[cand] = _check_wav(str(p))

    masters_dir = workdir / "masters"
    stands_check = {}
    if masters_dir.exists():
        for m in masters_dir.glob("master_*.wav"):
            stands_check[m.name] = _check_wav(str(m))

    release_dir = workdir / "release"
    release_check = {}
    if release_dir.exists():
        for f in release_dir.iterdir():
            if f.is_file():
                release_check[f.name] = {"size": f.stat().st_size, "path": str(f)}

    from tools import fallback_audit, readiness

    fb = fallback_audit.scan_all()
    pct, blocks = readiness.compute()

    summary = {
        "timestamp": ts,
        "workdir": str(workdir),
        "reference": ref_meta,
        "pipeline_verdict": result.get("verdict"),
        "pipeline_percent": result.get("percent"),
        "pipeline_stages": len(result.get("stages", [])),
        "stages_ok": sum(1 for s in result.get("stages", []) if s.get("ok")),
        "stages_fallback": sum(
            1 for s in result.get("stages", []) if s.get("fallback_used")
        ),
        "warnings": result.get("warnings", []),
        "artifacts_present": artifacts,
        "mastering_stands_present": stands_check,
        "release_pack_files": release_check,
        "fallback_audit_summary": fb.get("summary", {}),
        "fallback_red_flags_count": {
            k: len(v) for k, v in fb.get("red_flags", {}).items()
        },
        "readiness_percent": pct,
        "readiness_caps": blocks.get("caps_triggered", []),
    }
    (workdir / "e2e_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print()
    print("─" * 64)
    print(f"Verdict:            {summary['pipeline_verdict']}")
    print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
    print(f"Fallback stages:    {summary['stages_fallback']}")
    print(f"Masters generated:  {len(stands_check)}/8")
    print(f"Release files:      {len(release_check)}")
    print(f"Readiness (formula):{summary['readiness_percent']}%")
    print(f"Red flags:          {summary['fallback_red_flags_count']}")
    print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
    print()

    if (
        summary["pipeline_stages"]
        and summary["stages_ok"] / summary["pipeline_stages"] >= 0.6
    ):
        return 0
    return 1


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    raise SystemExit(main())
