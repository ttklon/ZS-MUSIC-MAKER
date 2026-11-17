# -*- coding: utf-8 -*-
"""
modules.hit_factory.generator — сердце фабрики: HitFactory.

Вызывает run_full_pipeline (бесплатный DSP), меряет hit_score, эволюционирует.
Изолирует Numba кэш на каждый прогон (обходит краш параллельных либрос).
Рефактор 41.1.2: тяжёлые методы вынесены в _state/_runner для лимита 400 строк.
"""
from __future__ import annotations

import json
import logging
import random
import time
import uuid
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

try:
    from app.core.orchestrator import run_full_pipeline
    from modules.hit_scorer import score_track
except Exception as exc:  # noqa: BLE001
    run_full_pipeline = None
    score_track = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from modules.hit_factory.evolver import mutate, select_best, should_evolve
from modules.hit_factory.readiness import attempt_readiness

try:
    from modules.hit_factory.adaptive import get_adaptive_config, log_adaptive
except Exception:
    get_adaptive_config = lambda overrides=None: {"level": 0, "level_name": "ultra_light (DSP only)", "duration_sec": 30, "max_attempts": 2, "human_preset": "light", "use_acestep": False, "use_musicgen": False, "use_silero": False, "ram_gb": 0, "gpu": {}}
    log_adaptive = lambda: {}


def _maybe_auto_genre(genre: str | None, theme: str | None) -> str | None:
    """full_agents автономно: trend_scout везде, сам понимает без вопросов."""
    try:
        from app.core.bootstrap import wire_full_agents
        wire_full_agents()
        if not genre:
            try:
                from agents.trend_scout import scout
                _trend = scout(theme=theme or "лето", offline_only=False)
                _hype = _trend.get("hype_words") or []
                for w in _hype:
                    if w.lower() in ("phonk","trap","drift","house","techno","hyperpop"):
                        return w.lower()
            except Exception as _e:
                _LOG.debug(f"[hit_factory] trend auto genre skip: {_e}")
    except Exception as _e:
        _LOG.debug(f"[hit_factory] wire agents skip: {_e}")
    return genre


def _apply_overrides(state: dict[str, Any], **kwargs: Any) -> None:
    """Перенести референсы и причину их отказа в `wizard_state`.

    Базовые поля (жанр/тема/seed/bpm/aggression/длительность) выставляет
    `_build_wizard_state`; здесь только то, чего он не знает. Отдельная
    функция, потому что `make_one` упирался в бюджет длины.
    """
    refs = kwargs.get("references")
    if refs:
        state["references"] = [str(item) for item in refs if str(item).strip()]
    warns = kwargs.get("reference_warnings")
    if warns:
        state["reference_warnings"] = [str(w) for w in warns]


def _save_factory_summary(best, attempts, min_score, do_evolve) -> None:
    """Persist musical ratings separately from render readiness."""
    if best:
        try:
            summary_path = Path(best["out_root"]) / "factory_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "best_project_id": best["project_id"],
                        "best_hit_score": best["hit_score"],
                        "best_verdict": best["verdict"],
                        "readiness": best["readiness"],
                        "attempts": [
                            {
                                "project_id": a["project_id"],
                                "hit_score": a["hit_score"],
                                "verdict": a["verdict"],
                                "readiness": a["readiness"],
                                "master_path": a["master_path"],
                                "wizard_state": a["wizard_state"],
                            }
                            for a in attempts
                        ],
                        "min_score": min_score,
                        "evolve": do_evolve,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as _exc:
            print(f"[hit_factory] ignored: {_exc}")


class HitFactory:

    """
    Автономная фабрика хитов.

    Пример:
        factory = HitFactory(output_root="output/hits", min_score=68, evolve=True, max_attempts=3)
        hit = factory.make_one(genre="trap", theme="ночь, деньги, движ", seed=42)
        batch = factory.make_batch(count=5)
    """

    def __init__(
        self,
        output_root: str | Path = "output/hits",
        min_score: float = 68.0,
        evolve: bool = True,
        max_attempts: int | None = None,
        duration_sec: int | None = None,
        human_preset: str | None = None,
        verbose: bool = True,
        adaptive: bool = True,
    ):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.adaptive_cfg = get_adaptive_config() if adaptive else {}
        if adaptive and self.adaptive_cfg:
            log_adaptive()
        self.min_score = float(min_score)
        self.evolve = bool(evolve)
        if max_attempts is None:
            max_attempts = self.adaptive_cfg.get("max_attempts", 3) if adaptive else 3
        self.max_attempts = max(1, int(max_attempts))
        if duration_sec is None:
            duration_sec = self.adaptive_cfg.get("duration_sec", 60) if adaptive else 60
        self.duration_sec = int(duration_sec)
        if human_preset is None:
            human_preset = self.adaptive_cfg.get("human_preset", "standard") if adaptive else "standard"
        self.human_preset = str(human_preset)
        self.verbose = verbose
        self.adaptive = bool(adaptive)
        if adaptive:
            self._log(f"[ADAPTIVE] HitFactory level={self.adaptive_cfg.get('level')} {self.adaptive_cfg.get('level_name')} duration={self.duration_sec} attempts={self.max_attempts} human={self.human_preset}")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)
        _LOG.info(msg)

    def _new_project_id(self, genre: str) -> str:
        short = genre[:6]
        return f"hit_{short}_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def _build_wizard_state(
        self,
        genre: str,
        theme: str,
        bpm_override: int | None,
        aggression: float | None,
        seed: int | None,
        duration_sec: int | None,
        rng: random.Random,
    ) -> dict[str, Any]:
        from modules.hit_factory._state import build_wizard_state

        return build_wizard_state(
            self.adaptive_cfg, self.duration_sec, genre, theme, bpm_override, aggression, seed, duration_sec, rng, self.adaptive
        )

    def _run_pipeline_once(
        self,
        project_id: str,
        wizard_state: dict[str, Any],
        rng: random.Random,
    ) -> dict[str, Any]:
        if run_full_pipeline is None:
            raise RuntimeError(f"HitFactory unavailable: {_IMPORT_ERROR}")
        from modules.hit_factory._runner import run_pipeline_once

        return run_pipeline_once(project_id, wizard_state, self.output_root, self.human_preset, self.verbose, self._log, rng)

    def make_one(
        self,
        genre: str | None = None,
        theme: str | None = None,
        seed: int | None = None,
        bpm_override: int | None = None,
        aggression: float | None = None,
        duration_sec: int | None = None,
        evolve: bool | None = None,
        references: list[str] | None = None,
        reference_warnings: list[str] | None = None,
    ) -> dict[str, Any]:
        """Сгенерить один хит с эволюцией. Возвращает лучший attempt dict.

        `references` и `reference_warnings` едут в `wizard_state` → рецепт →
        `_stage_analyze` (см. `_apply_overrides`): раньше путь «breakthrough»
        анализировал референсы и выбрасывал их, а отчёт показывал
        `n_refs: 0`/`source: genre_default` без единого предупреждения.
        """
        genre = _maybe_auto_genre(genre, theme)
        rng = random.Random(int(seed) if seed is not None else random.randint(1, 1_000_000))
        do_evolve = self.evolve if evolve is None else bool(evolve)
        base_state = self._build_wizard_state(
            genre=genre or "",
            theme=theme or "",
            bpm_override=bpm_override,
            aggression=aggression,
            seed=seed,
            duration_sec=duration_sec,
            rng=rng,
        )
        # `_build_wizard_state` знает только базовые поля; референсы и причина
        # их отказа добавляются здесь — через один вызов, без повторов.
        _apply_overrides(
            base_state, references=references, reference_warnings=reference_warnings
        )

        attempts: list[dict[str, Any]] = []
        cur_state = dict(base_state)
        attempts_limit = self.max_attempts if do_evolve else 1
        for attempt_idx in range(attempts_limit):
            pid = self._new_project_id(cur_state["genre"])
            self._log(f"\n[HIT FACTORY] Попытка {attempt_idx+1}/{attempts_limit}  genre={cur_state['genre']}  BPM={cur_state['bpm_override']}  seed={cur_state['seed']}  theme='{cur_state['theme'][:60]}'")
            ctx = self._run_pipeline_once(pid, cur_state, rng)
            ctx["readiness"] = attempt_readiness(ctx)
            ctx["attempt"] = attempt_idx + 1
            ctx["wizard_state"] = dict(cur_state)
            attempts.append(ctx)
            hit_score = float(ctx.get("hit_score") or 0.0)
            verdict = str(ctx.get("verdict") or "")
            self._log(f"[HIT FACTORY] -> {pid}  hit_score={hit_score:.1f}  verdict={verdict}  master={ctx.get('master_path')}")
            if not do_evolve or attempt_idx + 1 >= attempts_limit:
                break
            if ctx["readiness"]["ready"] and not should_evolve(hit_score, verdict, self.min_score):
                self._log(f"[HIT FACTORY] Порог {self.min_score} пробит ({hit_score:.1f} ≥ {self.min_score}) — стоп эволюция.")
                break
            cur_state = mutate(cur_state, ctx.get("hit"), rng)
            self._log(f"[HIT FACTORY] Эволюция → next BPM={cur_state['bpm_override']} seed={cur_state['seed']} aggression={cur_state['aggression']}")
        best = select_best(attempts)
        _save_factory_summary(best, attempts, self.min_score, do_evolve)
        try:
            from modules.hit_factory.kpi import build_kpi

            build_kpi(str(self.output_root), save=True)
        except Exception as _exc:
            print(f"[hit_factory] ignored: {_exc}")
        self._log(f"[HIT FACTORY] Лучший: {best['project_id']}  score={best['hit_score']:.1f}  verdict={best['verdict']}" if best else "[HIT FACTORY] нет попыток")
        return best or {}

    def make_batch(
        self,
        count: int = 5,
        genre: str | None = None,
        theme: str | None = None,
        evolve: bool | None = None,
        duration_sec: int | None = None,
        seed: int | None = None,
    ) -> list[dict[str, Any]]:
        """Батч-генерация count хитов. Последовательно, чтобы не падал Numba кэш."""
        if count < 1:
            count = 1
        if count > 100:
            count = 100
        rng = random.Random(int(seed) if seed is not None else random.randint(1, 999_999))
        results: list[dict[str, Any]] = []
        batch_id = f"batch_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        self._log(f"\n[HIT FACTORY] === BATCH {batch_id}  count={count}  evolve={self.evolve if evolve is None else evolve} ===")
        batch_meta_path = self.output_root / f"{batch_id}.json"
        for i in range(count):
            cur_genre = genre
            cur_theme = theme
            cur_seed = int(seed) + i if seed is not None else None
            if genre is None:
                cur_genre = None
            if theme is None:
                cur_theme = None
            self._log(f"\n--- Трек {i+1}/{count} ---")
            try:
                hit = self.make_one(genre=cur_genre, theme=cur_theme, seed=cur_seed, duration_sec=duration_sec, evolve=evolve)
                hit["batch_index"] = i + 1
                hit["batch_id"] = batch_id
                results.append(hit)
            except Exception as exc:  # noqa: BLE001
                _LOG.exception("batch item %s failed", i + 1)
                results.append({"batch_index": i + 1, "error": f"{type(exc).__name__}: {exc}", "hit_score": 0.0, "verdict": "error"})
            try:
                batch_meta_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            except Exception as _exc:
                print(f"[hit_factory] ignored: {_exc}")
        total = len(results)
        avg_score = sum(float(r.get("hit_score") or 0) for r in results) / max(1, total)
        best = max(results, key=lambda r: float(r.get("hit_score") or 0)) if results else None
        self._log(f"\n[HIT FACTORY] === BATCH DONE {batch_id} ===")
        self._log(f"  Треков: {total}  Средний hit_score: {avg_score:.1f}")
        if best:
            self._log(f"  Лучший: {best.get('project_id')}  score={best.get('hit_score'):.1f}  verdict={best.get('verdict')}")
            self._log(f"  Папка: {best.get('out_root')}  master: {best.get('master_path')}")
        self._log(f"  Индекс: {batch_meta_path}")
        try:
            from modules.hit_factory.kpi import build_kpi

            build_kpi(str(self.output_root), save=True)
        except Exception as _exc:
            print(f"[hit_factory] ignored: {_exc}")
        return results


def quick_hit(
    theme: str = "лето, тачки, движ",
    genre: str = "drift_phonk",
    seed: int = 42,
    min_score: float = 50.0,
) -> dict[str, Any]:
    """Однострочный хит для тестов/демо."""
    factory = HitFactory(min_score=min_score, evolve=False, verbose=False)
    return factory.make_one(genre=genre, theme=theme, seed=seed)


def _cli() -> int:
    import argparse

    p = argparse.ArgumentParser(description="ZS HIT FACTORY — автономная фабрика хитов (бесплатно)")
    p.add_argument("--count", type=int, default=1, help="сколько треков генерить")
    p.add_argument("--genre", type=str, default="", help="фиксированный жанр (пусто = рандом хитовый)")
    p.add_argument("--theme", type=str, default="", help="тема (пусто = авто из трендов 2026)")
    p.add_argument("--seed", type=int, default=None, help="базовый seed (детерминизм)")
    p.add_argument("--duration", type=int, default=None, help="длительность сек (65/90/120)")
    p.add_argument("--min-score", type=float, default=68.0, help="порог hit_score для эволюции")
    p.add_argument("--evolve", action="store_true", help="включает эволюцию (≤3 попытки на трек)")
    p.add_argument("--no-evolve", dest="evolve", action="store_false", help="выключает эволюцию")
    p.set_defaults(evolve=True)
    p.add_argument("--output", type=str, default="output/hits", help="куда складывать хиты")
    args = p.parse_args()

    factory = HitFactory(output_root=args.output, min_score=args.min_score, evolve=args.evolve, verbose=True)
    if args.count <= 1:
        hit = factory.make_one(genre=args.genre or None, theme=args.theme or None, seed=args.seed, duration_sec=args.duration)
        print(json.dumps(hit, ensure_ascii=False, indent=2, default=str))
    else:
        batch = factory.make_batch(count=args.count, genre=args.genre or None, theme=args.theme or None, seed=args.seed, duration_sec=args.duration)
        print(json.dumps(batch, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
