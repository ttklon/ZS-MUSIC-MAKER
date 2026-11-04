# -*- coding: utf-8 -*-
"""
app/core/orchestrator_async.py — асинхронная обёртка над общим пайплайном.

Раньше это был третий по счёту пайплайн: он сам собирал бит
(`beat_constructor` + `phonk_engine.create_cowbell_melody`), сам чистил вокал
и сам мастерил в −12 LUFS — то есть `--async` звучал иначе, чем обычный
прогон, и не получал ни рецепта, ни гейтов качества. Теперь «async» — это
способ запуска, а не отдельная музыка: все стадии те же, что у
`run_full_pipeline`.

Стадии уже идут в порядке зависимостей (бит → вокал → микс → мастеринг),
поэтому параллелить их нельзя без потери корректности; выигрыш здесь —
не блокировать event loop: пайплайн исполняется в рабочем потоке, а прогресс
отдаётся через колбэк `on_stage`.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass
class AsyncStage:
    """Плоское представление стадии — прежний формат отчёта `--async`."""

    name: str
    ok: bool = False
    duration_sec: float = 0.0
    output: Any = None
    reason: str | None = None
    status: str = "BLOCKED"


async def run_stage_async(name: str, fn: Callable[[], Any]) -> AsyncStage:
    """Выполнить один шаг в потоке, не блокируя event loop."""
    started = time.time()
    try:
        output = await asyncio.to_thread(fn)
        return AsyncStage(name=name, ok=True, output=output, status="OK",
                          duration_sec=round(time.time() - started, 3))
    except Exception as error:  # noqa: BLE001 - статус важнее трейсбека
        return AsyncStage(name=name, ok=False, status="FAILED",
                          reason=f"{type(error).__name__}: {error}",
                          duration_sec=round(time.time() - started, 3))


class AsyncOrchestrator:
    """Async-вход в общий пайплайн (совместимый API `run_pipeline`)."""

    def __init__(self, project_id: str, out_root: Path):
        self.project_id = project_id
        self.out_root = Path(out_root)
        self.out_root.mkdir(parents=True, exist_ok=True)
        self.stages: list[AsyncStage] = []

    async def run_pipeline(self, wizard_state: dict[str, Any]) -> dict[str, Any]:
        # импорт внутри метода: без раннего связывания (тесты и повторные
        # запуски в одном процессе должны видеть актуальный пайплайн)
        from app.core.orchestrator import run_full_pipeline

        started = time.time()
        progress: list[tuple[str, str]] = []

        def collect(name: str, status: str, index: int, total: int) -> None:
            progress.append((name, status))

        state: dict[str, Any] = dict(wizard_state or {})
        state.setdefault("genre", "drift_phonk")

        stage = await run_stage_async(
            "pipeline",
            lambda: run_full_pipeline(
                self.project_id, state, dry_run=False,
                out_root=self.out_root, on_stage=collect,
            ),
        )
        # Прогресс уже собран колбэком — превращаем его в список стадий отчёта.
        if stage.ok and isinstance(stage.output, dict):
            self.stages = [
                AsyncStage(name=name, status=status, ok=status != "FAILED")
                for name, status in progress
            ]
        else:
            self.stages = [stage]

        report = stage.output if isinstance(stage.output, dict) else {}
        verdict = report.get("verdict")
        result = {
            "project_id": self.project_id,
            "status": "completed"
            if verdict in {"PASS", "PASS_WITH_FALLBACK", "PASS_BLOCKED", "BLOCKED_SIMULATION"}
            else "partial",
            "verdict": verdict,
            "error": stage.reason,
            "duration_sec": round(time.time() - started, 2),
            "master_path": report.get("master_path"),
            "stages": [asdict(item) for item in self.stages],
        }
        (self.out_root / "async_meta.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        return result


async def main_async() -> None:  # pragma: no cover - ручной запуск
    orch = AsyncOrchestrator("async_test", Path("./output/async_test"))
    result = await orch.run_pipeline({"genre": "drift_phonk", "bpm_override": 140})
    print(f"Async pipeline done in {result['duration_sec']}s, verdict={result['verdict']}")


if __name__ == "__main__":  # pragma: no cover
    from app.core.numba_cache import isolated_numba_cache

    with isolated_numba_cache():
        asyncio.run(main_async())
