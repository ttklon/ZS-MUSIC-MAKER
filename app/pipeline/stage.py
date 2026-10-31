# -*- coding: utf-8 -*-
"""
app/pipeline/stage.py — модель результата стадии и сводка пайплайна.

Проектные правила:

  • статус стадии всегда один из четырёх (`StageStatus`), без «почти ок»;
  • `FALLBACK` и `BLOCKED` не маскируются под `OK` — причина/движок
    обязаны быть видны в отчёте;
  • `summarize()` — единственное место, где считается `verdict` и `percent`,
    чтобы разные пайплайны не считали успех по-разному.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class StageStatus(str, Enum):
    """Честный статус стадии."""

    OK = "OK"
    FALLBACK = "FALLBACK"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class StageResult:
    """Результат одной стадии пайплайна.

    `ok` сохранён как legacy-проекция (`status != FAILED`) для отчётов,
    которые ещё считают «сколько стадий не сломалось». Источник истины —
    `status`: `FALLBACK` и `BLOCKED` не считаются полноценным успехом.
    """

    name: str
    status: StageStatus
    output: Any = None
    duration_sec: float = 0.0
    reason: str | None = None
    attempts: list[str] = field(default_factory=list)

    # --- производные флаги (единая семантика для всех отчётов) ------------
    @property
    def ok(self) -> bool:
        """Стадия не сломалась (BLOCKED тоже «не сломалась»)."""
        return self.status is not StageStatus.FAILED

    @property
    def succeeded(self) -> bool:
        """Стадия дала полноценный результат (OK или честный FALLBACK)."""
        return self.status in (StageStatus.OK, StageStatus.FALLBACK)

    @property
    def error(self) -> str | None:
        """Legacy-алиас `reason` — старые пайплайны читают поле `.error`."""
        return self.reason

    @property
    def fallback_used(self) -> bool:
        return self.status is StageStatus.FALLBACK

    @property
    def blocked(self) -> bool:
        return self.status is StageStatus.BLOCKED

    @property
    def synthetic(self) -> bool:
        out = self.output if isinstance(self.output, dict) else {}
        return bool(out.get("synthetic") or out.get("dry_run") or out.get("placeholder"))

    @property
    def is_simulation(self) -> bool:
        """Симуляция = synthetic, но не честный BLOCKED."""
        return self.synthetic and self.status is not StageStatus.BLOCKED

    def to_dict(self) -> dict[str, Any]:
        """JSON-совместимое представление (с legacy-ключами отчётов)."""
        return {
            "name": self.name,
            "status": self.status.value,
            "ok": self.ok,
            "succeeded": self.succeeded,
            "fallback_used": self.fallback_used,
            "blocked": self.blocked,
            "synthetic": self.synthetic,
            "duration_sec": self.duration_sec,
            "output": self.output,
            "reason": self.reason,
            "attempts": list(self.attempts),
        }


def classify(
    output: Any,
    *,
    failed: bool = False,
    reason: str | None = None,
    attempts: Iterable[str] | None = None,
    duration_sec: float = 0.0,
    name: str = "",
) -> StageResult:
    """Построить `StageResult` из «сырого» результата стадии.

    Приоритет статусов: FAILED → BLOCKED → FALLBACK → OK. Порядок важен:
    честный BLOCKED (нет тяжёлой зависимости) не должен считаться сбоем,
    а synthetic-заглушка без blocked — это FALLBACK, а не успех.
    """
    data = output if isinstance(output, dict) else {}
    flag_ok = output is not None if not isinstance(output, dict) else bool(data.get("ok", True))

    if failed or not flag_ok:
        status = StageStatus.FAILED
    elif data.get("blocked"):
        status = StageStatus.BLOCKED
    elif data.get("fallback_used") or data.get("synthetic") or data.get("dry_run") or data.get("placeholder"):
        status = StageStatus.FALLBACK
    else:
        status = StageStatus.OK

    return StageResult(
        name=name,
        status=status,
        output=output,
        duration_sec=round(float(duration_sec), 3),
        reason=reason or data.get("reason"),
        attempts=list(attempts or ()),
    )


def summarize(stages: Iterable[dict[str, Any] | StageResult], *, dry_run: bool = False) -> dict[str, Any]:
    """Итоговый вердикт и честный процент по списку стадий.

    * `PASS` — все стадии OK и ни одного упрощения;
    * `PASS_WITH_FALLBACK` — всё отработало, но часть стадий с fallback;
    * `PASS_BLOCKED` — часть тяжёлых стадий честно BLOCKED, остальное ок;
    * `BLOCKED_SIMULATION` — в непустом прогоне появилась синтетическая заглушка;
    * `PARTIAL` — есть провалы.

    `percent`: полный зачёт за OK/FALLBACK, половинный за BLOCKED, ноль за
    FAILED. При симуляции процент ограничен 60, чтобы «зелёный» отчёт нельзя
    было получить на заглушках.
    """
    rows = [s.to_dict() if isinstance(s, StageResult) else dict(s) for s in stages]
    warnings: list[str] = []

    def _status(row: dict[str, Any]) -> str:
        return str(row.get("status") or ("OK" if row.get("ok") else "FAILED"))

    all_ok = all(row.get("ok") for row in rows)
    any_blocked = any(_status(row) == "BLOCKED" for row in rows)
    any_fallback = any(_status(row) == "FALLBACK" for row in rows)
    any_sim = any(
        _status(row) != "BLOCKED"
        and bool((row.get("output") or {}).get("synthetic") or (row.get("output") or {}).get("dry_run")
                 or (row.get("output") or {}).get("placeholder"))
        for row in rows
        if isinstance(row.get("output"), dict)
    ) or any(row.get("synthetic") and _status(row) != "BLOCKED" for row in rows)
    non_blocked_ok = all(row.get("ok") or _status(row) == "BLOCKED" for row in rows)

    if dry_run:
        verdict = "PASS" if all_ok else "PARTIAL"
    elif any_sim:
        verdict = "BLOCKED_SIMULATION"
        warnings.append("Non-dry pipeline detected explicit synthetic/dry_run placeholder output.")
    elif not non_blocked_ok:
        verdict = "PARTIAL"
    elif any_blocked:
        verdict = "PASS_BLOCKED"
        warnings.append(
            "Some heavy stages BLOCKED (missing deps): see status=BLOCKED. "
            f"Stages: {', '.join(row.get('name', '?') for row in rows if _status(row) == 'BLOCKED')}."
        )
        if any_fallback:
            warnings.append("Some stages used fallback (see status=FALLBACK).")
    elif any_fallback:
        verdict = "PASS_WITH_FALLBACK"
        warnings.append(
            "Some stages used fallback. Output might be simplified "
            "(e.g. template lyrics or basic mastering)."
        )
    else:
        verdict = "PASS"

    score = 0.0
    for row in rows:
        status = _status(row)
        if status == "BLOCKED":
            score += 0.5
        elif status in ("OK", "FALLBACK") or row.get("ok"):
            score += 1.0
    percent = int(round(100.0 * score / len(rows))) if rows else 0
    if any_sim and not dry_run:
        percent = min(percent, 60)

    return {
        "verdict": verdict,
        "percent": percent,
        "warnings": warnings,
        "blocked_stages": [row.get("name") for row in rows if _status(row) == "BLOCKED"],
        "fallback_stages": [row.get("name") for row in rows if _status(row) == "FALLBACK"],
        "failed_stages": [row.get("name") for row in rows if _status(row) == "FAILED"],
    }
