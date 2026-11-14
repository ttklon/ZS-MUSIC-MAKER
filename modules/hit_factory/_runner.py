# -*- coding: utf-8 -*-
"""modules.hit_factory._runner — исполнение пайплайна + постобработка (вынесено из generator)."""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

from app.core.numba_cache import isolated_numba_cache

_LOG = logging.getLogger(__name__)


def _enhance_master(master: str | Path, wizard_state: dict[str, Any]) -> None:
    """Лёгкая сатурация + расширение для ultra_light без нейросетей."""
    try:
        lvl = int(wizard_state.get("adaptive_level", 0))
        if lvl != 0:
            return
        from modules.hit_factory.adaptive import get_adaptive_config as _gac

        _cfg = _gac()
        if _cfg.get("use_acestep") or _cfg.get("use_musicgen"):
            return
        try:
            import numpy as np
            import soundfile as sf

            data, sr = sf.read(str(master))
            if data.ndim == 1:
                data = np.stack([data, data], axis=1)
            if data.shape[0] > sr * 0.02:
                drive = 0.02
                data = np.tanh(data * (1 + drive)) / np.tanh(1 + drive)
                delay = int(sr * 0.012)
                if delay > 0 and data.shape[0] > delay:
                    data[delay:, 1] = 0.7 * data[delay:, 1] + 0.3 * data[:-delay, 1]
            try:
                from scipy.signal import butter, lfilter

                b, a = butter(2, 80 / (sr / 2), btype="low")
                low = lfilter(b, a, data, axis=0)
                data = data * 0.85 + low * 0.15 * 1.2
            except Exception as _exc:
                print(f"[adaptive] ignored: {_exc}")
            peak = float(np.max(np.abs(data)) + 1e-9)
            if peak > 0.99:
                data = data / peak * 0.95
            sf.write(str(master), data, sr)
            _LOG.info(f"[adaptive] enhanced DSP applied to {master} (lvl 0, ultra_light)")
        except Exception as _e:
            _LOG.debug(f"adaptive enhance failed: {_e}")
    except Exception as _exc:
        print(f"[adaptive] ignored: {_exc}")


def _postprocess(
    report: dict[str, Any],
    hit: dict[str, Any] | None,
    master: str | None,
    out_root: Path,
    wizard_state: dict[str, Any],
    human_preset: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Humanizer + tiktok + cover + video — мутирует report, возвращает (report, hit)."""
    if master and Path(master).exists():
        # humanizer
        try:
            from modules.hit_factory.humanizer import ensure_human

            hres = ensure_human(master, preset=human_preset, seed=wizard_state.get("seed"))
            report["humanizer"] = hres
        except Exception as exc:  # noqa: BLE001
            report["humanizer"] = {"ok": False, "reason": str(exc)}

        # tiktok cuts
        try:
            from modules.tiktok_edit import make_all_cuts

            tiktok_dir = out_root / "tiktok"
            tiktok_res = make_all_cuts(master, str(tiktok_dir), hit_report=hit)
            report["tiktok_cuts"] = tiktok_res
        except Exception as exc:  # noqa: BLE001
            report["tiktok_cuts"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        # cover
        try:
            from modules.cover_art_gen import generate as gen_cover

            title = report.get("recipe", {}).get("theme") or wizard_state.get("theme") or "ZS Hit"
            short_title = str(title)[:32]
            artist = str(wizard_state.get("artist") or "ZS Producer")
            style_map = {
                "drift_phonk": "neon",
                "phonk": "neon",
                "trap": "glitch",
                "jersey_club": "gradient",
                "rage": "glitch",
                "hyperpop": "chrome",
                "house": "minimal",
            }
            style = style_map.get(wizard_state.get("genre"), "gradient")
            cover_path = str(out_root / "cover.png")
            cover_res = gen_cover(short_title, artist, cover_path, style=style, seed=wizard_state.get("seed"))
            report["cover"] = cover_res
        except Exception as exc:  # noqa: BLE001
            report["cover"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        # vertical video
        try:
            from modules.tiktok_edit import make_vertical_video

            tiktok_15 = out_root / "tiktok" / "tiktok_15s.wav"
            cover_png = out_root / "cover.png"
            if tiktok_15.exists() and cover_png.exists():
                vid_out = str(out_root / "tiktok" / "tiktok_15s.mp4")
                vres = make_vertical_video(str(tiktok_15), vid_out, str(cover_png))
                report["tiktok_video"] = vres
            else:
                report["tiktok_video"] = {"ok": False, "reason": "tiktok or cover missing"}
        except Exception as exc:
            report["tiktok_video"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        # persist updated report
        try:
            (out_root / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        except Exception as _exc:
            print(f"[hit_factory] ignored: {_exc}")
    return report, hit


def run_pipeline_once(
    project_id: str,
    wizard_state: dict[str, Any],
    output_root: Path,
    human_preset: str,
    verbose: bool,
    log_fn,
    rng: random.Random,  # kept for signature parity, not used directly
) -> dict[str, Any]:
    """Один прогон пайплайна + скор + постобработка."""
    try:
        from app.core.orchestrator import run_full_pipeline
        from modules.hit_scorer import score_track
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"HitFactory unavailable: {exc}") from exc

    try:
        from app.core.orchestrator import run_full_pipeline as _rfp  # noqa: F401
        from modules.hit_scorer import score_track as _st  # noqa: F401
    except Exception as _exc:
        print(f"[hit_factory] ignored: {_exc}")

    # late imports to keep parity with original
    from app.core.orchestrator import run_full_pipeline as rfp  # type: ignore
    from modules.hit_scorer import score_track as st  # type: ignore
    from modules.hit_factory.themes import trend_context

    out_root = output_root / project_id

    def on_stage(name: str, status: str, idx: int, total: int) -> None:
        log_fn(f"  [{idx}/{total}] {name}: {status}")

    try:
        import sys

        if "numba" in sys.modules:
            raise RuntimeError("numba already imported — skip isolation")
        with isolated_numba_cache():
            report = rfp(
                project_id=project_id,
                wizard_state=wizard_state,
                dry_run=False,
                out_root=out_root,
                on_stage=on_stage if verbose else None,
            )
    except RuntimeError as e:
        if "cannot isolate" in str(e) or "already imported" in str(e):
            report = rfp(
                project_id=project_id,
                wizard_state=wizard_state,
                dry_run=False,
                out_root=out_root,
                on_stage=on_stage if verbose else None,
            )
        else:
            raise

    master = report.get("master_path")
    if master and Path(master).exists() and wizard_state.get("enhanced_dsp"):
        _enhance_master(master, wizard_state)

    hit = None
    if master and Path(master).exists():
        try:
            hit = st(master) if st else None  # type: ignore
        except Exception as exc:  # noqa: BLE001
            hit = {"hit_score": 0.0, "verdict": "flop_risk", "error": f"{type(exc).__name__}: {exc}"}
        report, hit = _postprocess(report, hit, master, out_root, wizard_state, human_preset)
    else:
        hit = {"hit_score": 0.0, "verdict": "flop_risk", "error": "no master produced"}

    try:
        hr_path = out_root / "hit_report.json"
        hr_path.write_text(json.dumps(hit or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as _exc:
        print(f"[hit_factory] ignored: {_exc}")

    return {
        "project_id": project_id,
        "out_root": str(out_root),
        "report": report,
        "hit": hit or {},
        "hit_score": float((hit or {}).get("hit_score") or 0.0),
        "verdict": (hit or {}).get("verdict") or report.get("verdict"),
        "master_path": master,
        "wizard_state": wizard_state,
        "trend_ctx": trend_context(wizard_state.get("theme", "")),
    }
