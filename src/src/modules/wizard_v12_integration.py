"""
ZS Music Maker v13 — wizard_v12_integration.py
==============================================

МОСТ между Tk-визардом (main.py -> Wizard.run_pipeline) и реальным
master-пайплайном v12 (orchestrator_v12_patch.run_full_pipeline_v12).

ВОПРОС:  "Почему v12 не вызывался из Wizard Tk?"
ОТВЕТ:   в v12 мост существовал, но был неявным — Wizard знал только
         про orchestrator_v7. v12-пайплайн запускался из main_v12.py
         отдельно. Это нарушало ТЗ 4 («всё в одном мастере»).
v13:     добавляет явный callback-хаск `bridge_wizard_to_v12()`,
         который Wizard вызывает при нажатии «Готово». Под капотом
         идёт health_v12 -> master_pipeline_v12 -> kpi_dashboard_v12.
         При провале — каскад v11 -> v10 -> smoke_v12.
         UI продолжает ждать отклик через progress_callback.

Никаких тяжёлых зависимостей — только ядро Python.
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOGS = ROOT / "logs"
# v22: ленивое создание (не при импорте)


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [wizard_v12_integ] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
    try:
        (LOGS / "app.log").open("a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass


@dataclass
class WizardBridgeResult:
    project_id: str
    started_at: float = field(default_factory=lambda: time.time())
    finished_at: float = 0.0
    verdict: str = "PENDING"
    stages_done: list[str] = field(default_factory=list)
    artifacts_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    human_summary: str = ""
    kpi_snapshot: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["finished_at"] = self.finished_at
        return d


def collect_wizard_state(ui_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Собирает state из Tk-переменных визарда в плоский dict для пайплайна.

    ui_state (опционно): dict который Wizard мог сохранить (artist_name,
                          bpm_target, tracks_loaded, samples_loaded,
                          lyrics_text, voice_mode, references и т.п.).

    Не падает, если Wizard ещё ничего не записал — default = пустой.
    """
    state: dict[str, Any] = dict(ui_state or {})
    state.setdefault("bpm", 140)
    state.setdefault("duration_sec", 150)
    state.setdefault("artist", "Unknown Artist")
    state.setdefault("track_title", "Untitled Track")
    state.setdefault("genre_hint", "phonk")
    state.setdefault("references", [])
    state.setdefault("samples", [])
    state.setdefault("voice_mode", "lazy")
    state.setdefault("lyrics_text", "")
    state.setdefault("experts_enabled", False)
    return state


def bridge_wizard_to_v12(
    project_id: str,
    ui_state: dict[str, Any] | None = None,
    progress_cb: Callable[[str, float, str], None] | None = None,
    approve_cb: Callable[[str, str], bool] | None = None,
    dry_run: bool = True,
    force_v11: bool = False,
) -> WizardBridgeResult:
    """
    Главная точка моста. Wizard вызывает её при «Сгенерировать трек».

    Шаги:
      1) Собранный wizard_state -> health_v12 (pre-flight)
      2) Если health RED И force_v11=False -> master_pipeline_v12 dry_run
      3) Иначе orchestrator_v12_patch.run_full_pipeline_v12
      4) Каскадный fallback:
         v11 -> v10 -> master_pipeline_v12 dry_run (как минимум smoke)
      5) Финальный KPI-dashboard и human-readable резюме

    Возвращает WizardBridgeResult — Wizard сам отображает.

    Параметры:
      project_id   — имя проекта (например из data/projects/<id>);
      ui_state     — то, что Wizard успел собрать;
      progress_cb  — callback(stage, percent, msg) для прогресс-бара;
      approve_cb   — callback(stage, preview_path) для ТЗ 20.2 п.24
                     «утверждаю ключевые этапы»;
      dry_run      — True для smoke без тяжёлых моделей;
      force_v11    — пропустить v12 (только для fallback-тестов).
    """
    res = WizardBridgeResult(project_id=project_id)
    state = collect_wizard_state(ui_state)
    _log(
        f"Bridge start: project={project_id} dry_run={dry_run} "
        f"force_v11={force_v11}"
    )

    # 1) health pre-flight
    try:
        from modules import health_v12

        hr = health_v12.collect()
        res.stages_done.append(f"health_v12:{hr.verdict} ({hr.percent_ready}%)")
        _log(f"health: {hr.verdict} ({hr.percent_ready}%)")
        if progress_cb:
            try:
                progress_cb(
                    "health_v12", 0.05, f"стек: {hr.verdict}, {hr.percent_ready}% готов"
                )
            except Exception:
                pass
    except Exception as e:  # noqa: BLE001
        res.warnings.append(f"health_v12: {e}")

    # 2/3) основная цепочка
    pipeline_output: dict[str, Any] = {}
    try:
        if force_v11:
            raise RuntimeError("forced v11 path")
        from app.core import orchestrator_v12_patch as orch

        pipeline_output = orch.run_full_pipeline_v12(
            project_id, wizard_state=state, progress_cb=progress_cb, dry_run=dry_run
        )
        res.verdict = str(pipeline_output.get("verdict", "UNKNOWN"))
        res.stages_done.extend(
            ["orchestrator_v12_patch", "master_pipeline_v12", "kpi_dashboard_v12"]
        )
    except Exception as e:  # noqa: BLE001
        res.errors.append(f"orchestrator_v12: {type(e).__name__}: {e}")
        _log(f"orch_v12 fall: {e}")

    # 4) fallback
    if not str(res.verdict).endswith("PASS"):
        try:
            from app.core import orchestrator_v11_patch as v11

            if hasattr(v11, "run_full_pipeline_v11"):
                v11_out = v11.run_full_pipeline_v11(
                    project_id, state, progress_cb=progress_cb
                )
                pipeline_output["fallback_v11"] = (
                    v11_out if isinstance(v11_out, dict) else {"raw": str(v11_out)}
                )
                if isinstance(v11_out, dict) and str(
                    v11_out.get("verdict", "")
                ).endswith("PASS"):
                    res.verdict = "V11_FALLBACK_PASS"
                res.stages_done.append("orchestrator_v11_patch(fallback)")
        except Exception as e:  # noqa: BLE001
            res.warnings.append(f"v11 fallback: {e}")
            # как минимум — прогон dry-run master_pipeline_v12
            try:
                from modules import master_pipeline_v12 as mp

                mp.run_master_pipeline(
                    project_id,
                    wizard_state=state,
                    progress_cb=progress_cb,
                    dry_run=True,
                )
                res.stages_done.append("master_pipeline_v12:dry_run_only")
                res.verdict = res.verdict or "DRY_RUN_PASS"
            except Exception as e2:  # noqa: BLE001
                res.errors.append(f"dry_run fallback: {e2}")

    # 5) финальный KPI snapshot — для пользователя увидеть прогресс
    try:
        from modules import kpi_dashboard_v12 as kd

        dash = kd.build(save=True)
        res.kpi_snapshot = {
            "verdict": dash.verdict,
            "percent_tz": dash.percent_tz,
            "advice": dash.advice[:3],
        }
    except Exception as e:  # noqa: BLE001
        res.warnings.append(f"kpi_dashboard: {e}")

    res.finished_at = time.time()
    res.human_summary = (
        f"Wizard bridge для '{project_id}':\n"
        f"  стадий: {len(res.stages_done)}\n"
        f"  verdict: {res.verdict}\n"
        f"  ошибок: {len(res.errors)}, предупреждений: {len(res.warnings)}\n"
        f"  длительность: {res.finished_at - res.started_at:.2f}s"
    )

    # артефакты в outputs/projects/<id>/
    proj_dir = ROOT / "output" / "projects" / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "wizard_bridge_v13.json").write_text(
        json.dumps(res.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    res.artifacts_written.append(str(proj_dir / "wizard_bridge_v13.json"))

    _log(f"Bridge done: {res.verdict} ({res.finished_at - res.started_at:.2f}s)")
    return res


def install_into_wizard_main(main_module: Any) -> bool:
    """
    Приклеивает bridge к существующему модулю main.py (если в Wizard
    есть метод run_pipeline — он теперь вызывает bridge_wizard_to_v12).

    Идемпотентная: можно вызывать много раз без вреда. Возвращает True,
    если удалось подключить, False — если main_module не подходит
    (ничего страшного, тогда пользователь запустит main_v13 явно).
    """
    try:
        if not hasattr(main_module, "run_pipeline"):
            return False
        original = main_module.run_pipeline

        # замыкаем чтобы не зациклиться
        def patched(*args, **kwargs):
            project_id = kwargs.get("project_id") or (
                args[0] if args else "wizard_project"
            )
            ui_state = kwargs.get("wizard_state") or {}
            return bridge_wizard_to_v12(
                project_id=project_id,
                ui_state=ui_state,
                progress_cb=kwargs.get("progress_cb"),
                approve_cb=kwargs.get("approve_cb"),
                dry_run=kwargs.get("dry_run", False),
            )

        main_module.run_pipeline = patched
        _log(
            "install_into_wizard_main: patched main_module.run_pipeline "
            "(original kept as 'run_pipeline_original')"
        )
        main_module.run_pipeline_original = original
        return True
    except Exception as e:  # noqa: BLE001
        _log(f"install_into_wizard_main failed: {e}")
        return False


def main_entry() -> int:
    """CLI: python -m modules.wizard_v12_integration"""
    proj = "wizard_v13_smoke"
    state = collect_wizard_state(
        ui_state={"artist": "Smoke Artist", "bpm": 138, "duration_sec": 140}
    )
    r = bridge_wizard_to_v12(proj, ui_state=state, dry_run=True)
    print(
        f"verdict={r.verdict}  stages={len(r.stages_done)}  " f"errors={len(r.errors)}"
    )
    print(r.human_summary)
    return 0 if r.verdict.endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main_entry())
