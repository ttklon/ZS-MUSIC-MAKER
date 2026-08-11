"""
ZS Music Maker v12 «Hit Locked Pro» — orchestrator_v12_patch.py
================================================================

Тонкая обёртка поверх v11: подсовывает мастер-пайплайн v12 в качестве
основной точки входа и, при провале, откатывается на v11-каскад.

Соединяет:
  1. modules.health_v12         — pre-flight
  2. modules.master_pipeline_v12 — единый связный сценарий (ТЗ раздел 4)
  3. modules.kpi_dashboard_v12  — итоговый отчёт для пользователя
  4. app.core.orchestrator_v11_patch.run_full_pipeline_v11 — fallback

Никакого «магического» ML — только оркестрация.
"""

from __future__ import annotations

import sys
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", "replace"))


def run_full_pipeline_v12(
    project_id: str,
    wizard_state: dict[str, Any] | None = None,
    expert_config: dict[str, Any] | None = None,
    progress_cb: Callable[[str, float, str], None] | None = None,
    dry_run: bool = True,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """
    Главная точка входа v12.

    Возвращает dict со сводкой, чтобы UI мог его показать как есть.
    """
    t0 = time.time()
    wizard_state = wizard_state or {}
    result: dict[str, Any] = {
        "project_id": project_id,
        "started_at": t0,
        "verdict": "PENDING",
        "master_v12": None,
        "kpi_v12": None,
        "fallback_v11": None,
        "errors": [],
        "warnings": [],
    }

    # ---- 1. health-check ----
    try:
        from modules import health_v12

        hr = health_v12.collect()
        result["health"] = {
            "verdict": hr.verdict,
            "percent_ready": hr.percent_ready,
            "advice_head": hr.advice[:5],
        }
        _safe_print(f"[orch_v12] health: {hr.verdict} ({hr.percent_ready}%)")
    except Exception as e:  # noqa: BLE001
        result["warnings"].append(f"health_v12 failed: {e}")

    # ---- 2. master pipeline v12 ----
    master_ok = False
    try:
        from modules import master_pipeline_v12 as mp

        mr = mp.run_master_pipeline(
            project_id,
            wizard_state=wizard_state,
            progress_cb=progress_cb,
            dry_run=dry_run,
        )
        result["master_v12"] = mr.as_dict()
        result["verdict"] = mr.verdict
        master_ok = mr.verdict.endswith("PASS")
    except Exception as e:  # noqa: BLE001
        result["errors"].append(f"master_pipeline_v12: " f"{type(e).__name__}: {e}")
        traceback.print_exc()

    # ---- 3. если master упал → пробуем v11 ----
    if not master_ok:
        try:
            from app.core import orchestrator_v11_patch as v11

            if hasattr(v11, "run_full_pipeline_v11"):
                v11_out = v11.run_full_pipeline_v11(
                    project_id,
                    wizard_state,
                    expert_config=expert_config,
                    progress_cb=progress_cb,
                    project_root=project_root or ROOT,
                )
                result["fallback_v11"] = v11_out
                if isinstance(v11_out, dict) and str(
                    v11_out.get("verdict", "")
                ).endswith("PASS"):
                    result["verdict"] = "V11_FALLBACK_PASS"
                    master_ok = True
        except Exception as e:  # noqa: BLE001
            result["errors"].append(
                f"orchestrator_v11 fallback: " f"{type(e).__name__}: {e}"
            )

    # ---- 4. KPI dashboard ----
    try:
        from modules import kpi_dashboard_v12 as kd

        dash = kd.build(save=True)
        result["kpi_v12"] = {
            "verdict": dash.verdict,
            "percent_tz": dash.percent_tz,
            "advice_head": dash.advice[:5],
        }
    except Exception as e:  # noqa: BLE001
        result["warnings"].append(f"kpi_dashboard_v12 failed: {e}")

    result["duration_sec"] = time.time() - t0
    return result


def register() -> str:
    """Позволяет main_v12 узнать, что патч встал."""
    return "orchestrator_v12_patch:ready"


if __name__ == "__main__":
    out = run_full_pipeline_v12("demo_v12_orch", wizard_state={}, dry_run=True)
    _safe_print(f"verdict={out['verdict']}  ready={out.get('duration_sec')}")
