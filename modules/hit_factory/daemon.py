# -*- coding: utf-8 -*-
"""
modules.hit_factory.daemon — автономный бесконечный генератор хитов.

Запускает HitFactory по расписанию, пишет KPI в output/hits/daemon.log

Использование:
    python -m modules.hit_factory.daemon --interval 6 --count 2
    # или из Python:
    from modules.hit_factory.daemon import run_daemon
    run_daemon(interval_hours=6, count_per_run=2, genre=None)

Останавливается Ctrl+C (ловит KeyboardInterrupt).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

def run_daemon(
    interval_hours: float = 6.0,
    count_per_run: int = 2,
    genre: str | None = None,
    theme: str | None = None,
    output_root: str = "output/hits",
    min_score: float = 68.0,
    evolve: bool = True,
) -> None:
    from modules.hit_factory.generator import HitFactory

    interval_sec = max(60.0, float(interval_hours) * 3600.0)
    factory = HitFactory(output_root=output_root, min_score=min_score, evolve=evolve, verbose=True)
    log_path = Path(output_root) / "daemon.log"

    run_idx = 0
    print(f"[DAEMON] HIT FACTORY daemon started: every {interval_hours}h, {count_per_run} hits/run, genre={genre or 'auto'}")
    print(f"[DAEMON] Log: {log_path}  — Ctrl+C to stop")
    # Phase 4: авто-обновление трендов раз в 24ч (trend_scout кэш 24ч)
    last_trend_update = 0.0
    while True:
        run_idx += 1
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        # тренды
        try:
            if time.time() - last_trend_update > 86400:
                from agents.trend_scout import scout
                # прогрев кэша трендов для текущего жанра/темы
                scout(theme or "лето, тачки, движ", offline_only=False)
                last_trend_update = time.time()
        except Exception:
            pass
        try:
            batch = factory.make_batch(count=count_per_run, genre=genre, theme=theme)
            scores = [float(b.get("hit_score") or 0) for b in batch]
            avg = sum(scores) / max(1, len(scores))
            best = max(batch, key=lambda b: float(b.get("hit_score") or 0)) if batch else {}
            msg = f"[{ts}] run#{run_idx} batch={len(batch)} avg={avg:.1f} best={best.get('hit_score',0):.1f} {best.get('verdict','')} {best.get('project_id','')}"
            print(msg)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(msg + "\n")
            # KPI агрегат после каждого батча
            try:
                from modules.hit_factory.kpi import build_kpi
                build_kpi(output_root, save=True)
            except Exception:
                pass
        except KeyboardInterrupt:
            print("\n[DAEMON] остановлен пользователем (Ctrl+C)")
            break
        except Exception as exc:  # noqa: BLE001
            msg = f"[{ts}] run#{run_idx} FAILED: {type(exc).__name__}: {exc}"
            print(msg)
            try:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        if interval_hours <= 0:
            break
        print(f"[DAEMON] sleep {interval_hours}h until next run ...")
        try:
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\n[DAEMON] остановлен во время сна")
            break


def _cli() -> int:
    p = argparse.ArgumentParser(description="HIT FACTORY daemon — бесконечный генератор хитов")
    p.add_argument("--interval", type=float, default=6.0, help="интервал часов между батчами (0=один раз)")
    p.add_argument("--count", type=int, default=2, help="хитов за один запуск")
    p.add_argument("--genre", type=str, default="", help="фиксированный жанр (пусто=рандом)")
    p.add_argument("--theme", type=str, default="", help="фиксированная тема")
    p.add_argument("--output", type=str, default="output/hits", help="куда писать")
    p.add_argument("--min-score", type=float, default=68.0, help="порог эволюции")
    p.add_argument("--no-evolve", action="store_true", help="выключить эволюцию")
    args = p.parse_args()
    run_daemon(
        interval_hours=args.interval,
        count_per_run=args.count,
        genre=args.genre or None,
        theme=args.theme or None,
        output_root=args.output,
        min_score=args.min_score,
        evolve=not args.no_evolve,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
