# -*- coding: utf-8 -*-
"""modules/mastering/stands.py — все стенды: параллельно, но бит-в-бит.

Стенды независимы, поэтому считаются процессами (до `min(cpu, 4)`).
`ZSMM_MASTER_WORKERS=1` принудительно включает последовательный счёт, а если
пул недоступен (например, внутри чужого процесса) — честный фолбэк.
"""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from modules.mastering.chain import master_one
from modules.mastering.targets import ALL_STANDS, STAND_TARGET_LUFS

_LOG = logging.getLogger(__name__)

# Оригинал `master_one`. Если его подменили (тесты, эксперименты), стенды
# считаются в этом же процессе: чужая функция живёт только здесь, в дочерний
# процесс она не попадёт.
_MASTER_ONE_IMPL = master_one


def _current_master_one():
    """Актуальная реализация `master_one`.

    Пакет `modules.mastering` реэкспортирует функцию, и тесты/эксперименты
    подменяют именно его (`mastering.master_one = ...`). Читаем атрибут
    пакета во время вызова, иначе подмена молча игнорировалась бы.
    """
    import sys

    package = sys.modules.get(__package__ or "modules.mastering")
    overridden = getattr(package, "master_one", None) if package is not None else None
    return overridden or master_one


def _master_stand_job(job: tuple[str, str, str]) -> tuple[str, dict[str, Any]]:
    """Один стенд в отдельном процессе (аргументы должны быть picklable)."""
    mix_wav, out_wav, stand = job
    return stand, _current_master_one()(mix_wav, out_wav, stand=stand)


def _stand_workers(count: int) -> int:
    """Сколько стендов считать параллельно.

    Стенды независимы, поэтому 8 версий считаются одновременно, а не
    последовательно — на 8-ядерной машине время мастеринга падает почти
    линейно. Потолок 4: каждый процесс держит в памяти весь трек
    (120 с стерео ≈ 42 МБ float64 на буфер), и больше четырёх воркеров
    начинают мешать друг другу сильнее, чем помогать. `ZSMM_MASTER_WORKERS=1`
    принудительно включает последовательный режим.
    """
    try:
        forced = int(os.environ.get("ZSMM_MASTER_WORKERS", "0") or 0)
    except ValueError:
        forced = 0
    if forced > 0:
        return max(1, min(forced, count))
    return max(1, min(count, os.cpu_count() or 1, 4))


def _run_stands(
    mix_wav: str,
    out: Path,
    chosen: list[str],
) -> list[tuple[str, dict[str, Any]]]:
    """Посчитать стенды; при любой проблеме с процессами — честный фолбэк."""
    jobs = [(mix_wav, str(out / f"master_{stand}.wav"), stand) for stand in chosen]
    workers = 1 if _current_master_one() is not _MASTER_ONE_IMPL else _stand_workers(len(jobs))
    if workers > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor

            with ProcessPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(_master_stand_job, jobs))
        except Exception as error:  # noqa: BLE001 - пул может быть запрещён сборкой
            _LOG.warning("parallel mastering unavailable (%s); falling back to serial", error)
    return [_master_stand_job(job) for job in jobs]


def master_all_stands(
    mix_wav: str,
    out_dir: str,
    stands: list[str] | None = None,
) -> dict[str, Any]:
    """Мастеринг под все запрошенные стенды + сводный отчёт по гейтам."""
    chosen = stands or ALL_STANDS
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    masters: dict[str, str] = {}
    reports: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for stand, result in _run_stands(mix_wav, out, list(chosen)):
        if result.get("ok"):
            masters[stand] = str(result["path"])
            reports[stand] = result
        else:
            errors[stand] = str(result.get("reason", "unknown"))

    failed_gates = {
        stand: [name for name, ok in data["gates"].items() if not ok]
        for stand, data in reports.items()
        if not data["gates_passed"]
    }
    summary = {
        "total": len(chosen),
        "done": len(masters),
        "fallback": 0,
        "errors": errors,
        "gates_passed": all(data["gates_passed"] for data in reports.values()) if reports else False,
        "failed_gates": failed_gates,
    }
    payload: dict[str, Any] = {
        "ok": bool(masters),
        "masters": masters,
        "reports": {stand: data["report"] for stand, data in reports.items()},
        "summary": summary,
    }
    report_path = out / "mastering_report.json"
    report_path.write_text(
        json.dumps(
            {
                "standards": {s: STAND_TARGET_LUFS[s] for s in chosen if s in STAND_TARGET_LUFS},
                "reports": payload["reports"],
                "gates": {stand: data["gates"] for stand, data in reports.items()},
                "failed_gates": failed_gates,
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    payload["report_path"] = str(report_path)
    return payload
