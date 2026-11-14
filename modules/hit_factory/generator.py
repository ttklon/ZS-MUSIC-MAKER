# -*- coding: utf-8 -*-
"""
modules.hit_factory.generator — сердце фабрики: HitFactory.

Вызывает run_full_pipeline (бесплатный DSP), меряет hit_score, эволюционирует.
Изолирует Numba кэш на каждый прогон (обходит краш параллельных либрос).
"""
from __future__ import annotations

import json
import logging
import random
import time
import uuid
from pathlib import Path
from typing import Any

from app.core.numba_cache import isolated_numba_cache

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


from modules.hit_factory.config import HIT_THRESHOLDS
from modules.hit_factory.evolver import mutate, select_best, should_evolve
from modules.hit_factory.humanizer import ensure_human
from modules.hit_factory.themes import (
    build_random_recipe_overrides,
    pick_aggression,
    pick_bpm,
    pick_genre,
    pick_theme,
    trend_context,
)


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
        max_attempts: int = 3,
        duration_sec: int | None = None,
        human_preset: str = "standard",
        verbose: bool = True,
    ):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.min_score = float(min_score)
        self.evolve = bool(evolve)
        self.max_attempts = max(1, int(max_attempts))
        self.duration_sec = duration_sec
        self.human_preset = human_preset
        self.verbose = verbose

    # --------------------------------------------------------------- helpers
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
        """Собирает wizard_state для run_full_pipeline."""
        g = genre or pick_genre(rng)
        t = theme or pick_theme(rng)
        # Phase 2: обогащаем тему сленгом 2026 для вирусности (если тема авто)
        if not theme:
            try:
                from modules.hit_factory.themes import enrich_theme_with_slang
                t = enrich_theme_with_slang(t, rng)
            except Exception:
                pass
        bpm = pick_bpm(g, rng, bpm_override)
        agr = aggression if aggression is not None else pick_aggression(rng, g)
        s = int(seed if seed is not None else rng.randint(1, 1_000_000))
        dur = int(duration_sec or self.duration_sec or 120)

        # Phase 2: тренд-контекст для lyrics (hype_words в заметки)
        try:
            tc = trend_context(t)
            hype_str = ", ".join((tc.get("hype_words") or [])[:6])
        except Exception:
            hype_str = ""
        state: dict[str, Any] = {
            "genre": g,
            "theme": t,
            "preset": None,
            "bpm_override": bpm,
            "aggression": agr,
            "seed": s,
            "duration_sec": dur,
            "n_verses": 2,
            "voice_mode": "pro",  # TTS free, scaffold fallback
            "use_rvc": False,
            "use_vocal_fx": True,  # Phase 3: форсим человечность — всегда FX
            "export_stems": False,  # быстрее для фабрики; включаем если нужно
            "bilingual": True,
            "quality_mode": "quality",
            "stands": ["streaming", "tiktok", "club"],
            "references": [],
            "trend_notes": hype_str,
            "artist": "ZS Producer",
        }
        return state

    def _run_pipeline_once(
        self,
        project_id: str,
        wizard_state: dict[str, Any],
        rng: random.Random,
    ) -> dict[str, Any]:
        """Один прогон пайплайна + скор."""
        if run_full_pipeline is None:
            raise RuntimeError(f"HitFactory unavailable: {_IMPORT_ERROR}")

        out_root = self.output_root / project_id

        # колбэк прогресса для логов
        def on_stage(name: str, status: str, idx: int, total: int) -> None:
            self._log(f"  [{idx}/{total}] {name}: {status}")

        # Изолируем Numba кэш на первый прогон; после импорта numba — просто прямой вызов
        # (иначе RuntimeError: cannot isolate after Numba imported, см. app/core/numba_cache.py)
        try:
            # пробуем изолировать, если ещё не импортирован numba
            import sys
            if "numba" in sys.modules:
                raise RuntimeError("numba already imported — skip isolation")
            with isolated_numba_cache():
                report = run_full_pipeline(
                    project_id=project_id,
                    wizard_state=wizard_state,
                    dry_run=False,
                    out_root=out_root,
                    on_stage=on_stage if self.verbose else None,
                )
        except RuntimeError as e:
            # fallback: уже изолировано или нечего изолировать — прямой прогон
            if "cannot isolate" in str(e) or "already imported" in str(e):
                report = run_full_pipeline(
                    project_id=project_id,
                    wizard_state=wizard_state,
                    dry_run=False,
                    out_root=out_root,
                    on_stage=on_stage if self.verbose else None,
                )
            else:
                raise

        # hit_score
        master = report.get("master_path")
        hit = None
        if master and Path(master).exists():
            try:
                hit = score_track(master) if score_track else None
            except Exception as exc:  # noqa: BLE001
                hit = {"hit_score": 0.0, "verdict": "flop_risk", "error": f"{type(exc).__name__}: {exc}"}
            # доп. human polish (нероншно) — опциональный, не ломает скор
            # делаем копию с human суффиксом и логируем, но master_path оставляем оригинал
            try:
                hres = ensure_human(master, preset=self.human_preset, seed=wizard_state.get("seed"))
                report["humanizer"] = hres
            except Exception as exc:  # noqa: BLE001
                report["humanizer"] = {"ok": False, "reason": str(exc)}
            # TikTok нарезки (15s/30s/hook_loop) — бесплатно, не требует ffmpeg
            try:
                from modules.tiktok_edit import make_all_cuts
                tiktok_dir = Path(out_root) / "tiktok"
                tiktok_res = make_all_cuts(master, str(tiktok_dir), hit_report=hit)
                report["tiktok_cuts"] = tiktok_res
            except Exception as exc:  # noqa: BLE001
                report["tiktok_cuts"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            # Обложка (PIL, оффлайн) — всегда бесплатно
            try:
                from modules.cover_art_gen import generate as gen_cover
                lyrics_title = (hit or {}).get("meta", {}).get("file", "")
                # достаём заголовок из report если есть
                title = report.get("recipe", {}).get("theme") or wizard_state.get("theme") or "ZS Hit"
                # обрезаем до 30 символов для красоты
                short_title = str(title)[:32]
                artist = str(wizard_state.get("artist") or "ZS Producer")
                # стиль по жанру
                style_map = {"drift_phonk": "neon", "phonk": "neon", "trap": "glitch", "jersey_club": "gradient", "rage": "glitch", "hyperpop": "chrome", "house": "minimal"}
                style = style_map.get(wizard_state.get("genre"), "gradient")
                cover_path = str(Path(out_root) / "cover.png")
                cover_res = gen_cover(short_title, artist, cover_path, style=style, seed=wizard_state.get("seed"))
                report["cover"] = cover_res
            except Exception as exc:  # noqa: BLE001
                report["cover"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            # Вертикальное видео (если ffmpeg есть) — tiktok_15s + cover → 9:16 mp4
            try:
                from modules.tiktok_edit import make_vertical_video
                tiktok_15 = Path(out_root) / "tiktok" / "tiktok_15s.wav"
                cover_png = Path(out_root) / "cover.png"
                if tiktok_15.exists() and cover_png.exists():
                    vid_out = str(Path(out_root) / "tiktok" / "tiktok_15s.mp4")
                    vres = make_vertical_video(str(tiktok_15), vid_out, str(cover_png))
                    report["tiktok_video"] = vres
                else:
                    report["tiktok_video"] = {"ok": False, "reason": "tiktok or cover missing"}
            except Exception as exc:
                report["tiktok_video"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            # Перезаписываем report.json с tiktok и cover и video (иначе на диске старые данные)
            try:
                import json
                (Path(out_root) / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            except Exception:
                pass
        else:
            hit = {"hit_score": 0.0, "verdict": "flop_risk", "error": "no master produced"}

        # сохраняем hit_report.json рядом с report.json
        try:
            hr_path = Path(out_root) / "hit_report.json"
            hr_path.write_text(json.dumps(hit or {}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

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

    # --------------------------------------------------------------- public
    def make_one(
        self,
        genre: str | None = None,
        theme: str | None = None,
        seed: int | None = None,
        bpm_override: int | None = None,
        aggression: float | None = None,
        duration_sec: int | None = None,
        evolve: bool | None = None,
    ) -> dict[str, Any]:
        """
        Сгенерить один хит с эволюцией.
        Возвращает лучший attempt dict.
        """
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
        # если genre/theme не заданы — берём рандом из state
        base_state["genre"] = genre or base_state["genre"]
        # theme уже внутри state, не перетираем если None
        if theme:
            base_state["theme"] = theme
        if seed is not None:
            base_state["seed"] = int(seed)
        if bpm_override is not None:
            base_state["bpm_override"] = int(bpm_override)
        if aggression is not None:
            base_state["aggression"] = float(aggression)
        if duration_sec is not None:
            base_state["duration_sec"] = int(duration_sec)

        attempts: list[dict[str, Any]] = []
        cur_state = dict(base_state)

        attempts_limit = self.max_attempts if do_evolve else 1

        for attempt_idx in range(attempts_limit):
            pid = self._new_project_id(cur_state["genre"]) if attempt_idx > 0 else self._new_project_id(cur_state["genre"])
            # для первой попытки используем красивый id с жанром
            if attempt_idx == 0:
                # переиспользуем первый id но с жанром
                pass
            self._log(f"\n[HIT FACTORY] Попытка {attempt_idx+1}/{attempts_limit}  genre={cur_state['genre']}  BPM={cur_state['bpm_override']}  seed={cur_state['seed']}  theme='{cur_state['theme'][:60]}'")
            ctx = self._run_pipeline_once(pid, cur_state, rng)
            # обогащаем ctx для evolver
            ctx["attempt"] = attempt_idx + 1
            ctx["wizard_state"] = dict(cur_state)
            attempts.append(ctx)

            hit_score = float(ctx.get("hit_score") or 0.0)
            verdict = str(ctx.get("verdict") or "")
            self._log(f"[HIT FACTORY] -> {pid}  hit_score={hit_score:.1f}  verdict={verdict}  master={ctx.get('master_path')}")

            # решаем эволюционировать ли
            if not do_evolve or attempt_idx + 1 >= attempts_limit:
                break
            if not should_evolve(hit_score, verdict, self.min_score):
                self._log(f"[HIT FACTORY] Порог {self.min_score} пробит ({hit_score:.1f} ≥ {self.min_score}) — стоп эволюция.")
                break
            # мутируем
            cur_state = mutate(cur_state, ctx.get("hit"), rng)
            self._log(f"[HIT FACTORY] Эволюция → next BPM={cur_state['bpm_override']} seed={cur_state['seed']} aggression={cur_state['aggression']}")

        best = select_best(attempts)
        # сохраняем summary в папку лучшего
        if best:
            try:
                summary_path = Path(best["out_root"]) / "factory_summary.json"
                summary_path.write_text(
                    json.dumps(
                        {
                            "best_project_id": best["project_id"],
                            "best_hit_score": best["hit_score"],
                            "best_verdict": best["verdict"],
                            "attempts": [
                                {
                                    "project_id": a["project_id"],
                                    "hit_score": a["hit_score"],
                                    "verdict": a["verdict"],
                                    "master_path": a["master_path"],
                                    "wizard_state": a["wizard_state"],
                                }
                                for a in attempts
                            ],
                            "min_score": self.min_score,
                            "evolve": do_evolve,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except Exception:
                pass
        # также общий индекс батча + KPI
        try:
            from modules.hit_factory.kpi import build_kpi
            build_kpi(str(self.output_root), save=True)
        except Exception:
            pass
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
        """
        Батч-генерация count хитов.
        Если genre/theme заданы — фиксируем; иначе каждый трек — рандомный жанр/тема.
        Последовательно (чтобы не падал Numba кэш). Для параллели — нужен isolated.
        """
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
            cur_genre = genre  # если фиксирован — один жанр
            cur_theme = theme
            cur_seed = None
            if seed is not None:
                cur_seed = int(seed) + i
            # если не фиксирован — рандом каждый шаг
            if genre is None:
                cur_genre = None  # make_one сам выберет
            if theme is None:
                cur_theme = None

            self._log(f"\n--- Трек {i+1}/{count} ---")
            try:
                hit = self.make_one(
                    genre=cur_genre,
                    theme=cur_theme,
                    seed=cur_seed,
                    duration_sec=duration_sec,
                    evolve=evolve,
                )
                hit["batch_index"] = i + 1
                hit["batch_id"] = batch_id
                results.append(hit)
            except Exception as exc:  # noqa: BLE001
                _LOG.exception("batch item %s failed", i + 1)
                results.append({"batch_index": i + 1, "error": f"{type(exc).__name__}: {exc}", "hit_score": 0.0, "verdict": "error"})
            # промежуточный сейв батча
            try:
                batch_meta_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            except Exception:
                pass

        # итоговый отчёт
        total = len(results)
        avg_score = sum(float(r.get("hit_score") or 0) for r in results) / max(1, total)
        best = max(results, key=lambda r: float(r.get("hit_score") or 0)) if results else None
        self._log(f"\n[HIT FACTORY] === BATCH DONE {batch_id} ===")
        self._log(f"  Треков: {total}  Средний hit_score: {avg_score:.1f}")
        if best:
            self._log(f"  Лучший: {best.get('project_id')}  score={best.get('hit_score'):.1f}  verdict={best.get('verdict')}")
            self._log(f"  Папка: {best.get('out_root')}  master: {best.get('master_path')}")
        self._log(f"  Индекс: {batch_meta_path}")
        # KPI агрегат (Phase 4)
        try:
            from modules.hit_factory.kpi import build_kpi
            build_kpi(str(self.output_root), save=True)
        except Exception:
            pass

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


# CLI entry for `python -m modules.hit_factory`
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
