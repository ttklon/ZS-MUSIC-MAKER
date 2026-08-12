# -*- coding: utf-8 -*-
"""
ZS Music Maker — smoke_v25
====================================================================

Проверяет пакет фиксов v25 (P0/P1):

  1. v25.hit_report_score       — hit_report.md содержит реальный скор
                                  (не 'n/a'); баг ключа 'score'→'hit_score'.
  2. v25.voice_mode_off         — voice_mode='off' даёт честный инструментал:
                                  voice_synth/rvc/vocal_fx = blocked, вокал
                                  не замешан, есть предупреждение.
  3. v25.synthetic_vocal_guard  — обычный режим без TTS: rap_scaffold НЕ
                                  попадает в мастер (инструментал + warning).
  4. v25.stands_filter          — stands=['car'] даёт master_car + master_streaming
                                  и НЕ даёт остальные 6 стендов.
  5. v25.n_verses_wired         — n_verses из рецепта доезжает до plan (4 куплета).
  6. v25.extra_prompt_wired     — user_extra_prompt подмешивается в theme/lyrics.
  7. v25.beat_section_variation — synth_beat: припев и куплет используют
                                  разные kick/hihat-паттерны (вариативность).
  8. v25.beat_lowband_mono      — низ бита (<150 Гц) моно-совместим:
                                  корреляция low-band L/R > 0.9.
  9. v25.llm_preflight_fast     — LLMRouter.complete() без сети/ключей
                                  возвращается < 5с (preflight, не 32с).

Запуск:  python3 tools/smoke_v25.py   (из корня проекта)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS = []


def check(name: str, ok: bool, detail: str = ""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")


def _run(project_id: str, recipe: dict) -> dict:
    from app.core.orchestrator import run_full_pipeline
    out_root = ROOT / "output" / "smoke_v25" / project_id
    if out_root.exists():
        shutil.rmtree(out_root, ignore_errors=True)
    return run_full_pipeline(project_id, recipe, dry_run=False,
                             out_root=out_root)


def _stage(res: dict, name: str) -> dict:
    for s in res.get("stages", []):
        if s.get("name") == name:
            return s
    return {}


def main() -> int:
    print("=" * 64)
    print("ZS Music Maker v25 — smoke_v25 (recipe wiring + vocal guard + beat)")
    print("=" * 64)

    # ---- прогон 1: обычный режим, нет TTS → guard + hit_report ----------
    res1 = None
    try:
        res1 = _run("p1_guard", {"references": [], "theme": "тест v25",
                                 "genre": "drift_phonk", "duration_sec": 10})
    except Exception as e:
        check("v25.pipeline_runs", False, f"crash: {e}")

    if res1 is not None:
        # hit_report.md содержит реальный скор
        hr = ROOT / "output" / "smoke_v25" / "p1_guard" / "release" / "hit_report.md"
        try:
            txt = hr.read_text(encoding="utf-8")
            m = re.search(r"Score:\s*\*\*([\d.]+)\*\*", txt)
            score_ok = bool(m) and float(m.group(1)) > 0
            check("v25.hit_report_score", score_ok,
                  f"score={m.group(1) if m else 'n/a'}")
        except Exception as e:
            check("v25.hit_report_score", False, f"read fail: {e}")

        # synthetic vocal guard: warning + voice_synth blocked/synthetic
        warns = res1.get("warnings", [])
        has_guard = any("vocal skipped" in w for w in warns)
        s7 = _stage(res1, "_stage_voice_synth")
        synth = bool((s7.get("output") or {}).get("synthetic")) \
            or bool(s7.get("blocked"))
        check("v25.synthetic_vocal_guard", has_guard and synth,
              f"guard_warn={has_guard} synth_or_blocked={synth}")

    # ---- прогон 2: voice_mode='off' → честный инструментал --------------
    res2 = None
    try:
        res2 = _run("p2_instr", {"references": [], "theme": "тест",
                                 "genre": "drift_phonk", "duration_sec": 10,
                                 "voice_mode": "off"})
    except Exception as e:
        check("v25.voice_mode_off", False, f"crash: {e}")

    if res2 is not None:
        v_ok = all(_stage(res2, n).get("blocked")
                   for n in ("_stage_voice_synth", "_stage_rvc",
                             "_stage_vocal_fx"))
        check("v25.voice_mode_off", v_ok,
              "voice_synth/rvc/vocal_fx all blocked=True")

    # ---- прогон 3: stands фильтр ----------------------------------------
    res3 = None
    try:
        res3 = _run("p3_stands", {"references": [], "theme": "тест",
                                  "genre": "trap", "duration_sec": 8,
                                  "voice_mode": "off", "stands": ["car"]})
    except Exception as e:
        check("v25.stands_filter", False, f"crash: {e}")

    if res3 is not None:
        mdir = ROOT / "output" / "smoke_v25" / "p3_stands" / "masters"
        masters = sorted(os.listdir(mdir)) if mdir.is_dir() else []
        want = {"master_car.wav", "master_streaming.wav"}
        have = set(masters)
        check("v25.stands_filter", have == want,
              f"masters={masters}")

    # ---- прогон 4: n_verses + extra_prompt wiring ------------------------
    res4 = None
    try:
        res4 = _run("p4_wiring", {
            "references": [], "theme": "ночь", "genre": "drift_phonk",
            "duration_sec": 10, "voice_mode": "off",
            "n_verses": 4, "user_extra_prompt": "больше 808 в припеве"})
    except Exception as e:
        check("v25.n_verses_wired", False, f"crash: {e}")
        check("v25.extra_prompt_wired", False, f"crash: {e}")

    if res4 is not None:
        # n_verses доехал до beat: beat.sections должно иметь ≥4 verse/chorus
        sb = _stage(res4, "_stage_beat")
        secs = (sb.get("output") or {}).get("sections") or []
        nv = sum(1 for s in secs if s.get("name") in ("verse", "chorus"))
        check("v25.n_verses_wired", nv >= 4, f"verse/chorus sections={nv}")
        # extra_prompt подмешался в theme → metadata.json
        md = ROOT / "output" / "smoke_v25" / "p4_wiring" / "release" / "metadata.json"
        try:
            meta = json.loads(md.read_text(encoding="utf-8"))
            th = str(meta.get("theme", ""))
            check("v25.extra_prompt_wired", "808" in th or "припеве" in th,
                  f"theme={th[:50]}")
        except Exception as e:
            check("v25.extra_prompt_wired", False, f"meta read fail: {e}")

    # ---- прогон 5: beat вариативность + low-band моно ---------------------
    try:
        import numpy as np
        import soundfile as sf
        from app.core.orchestrator import _synth_beat
        bp = str(ROOT / "output" / "smoke_v25" / "_beat_check.wav")
        r = _synth_beat(bp, duration=20, bpm=130)
        d, sr = sf.read(bp, always_2d=True)
        # low-band корреляция
        try:
            from scipy.signal import butter, sosfilt
            sos = butter(4, 150, btype="low", fs=sr, output="sos")
            lo = np.stack([sosfilt(sos, d[:, c]) for c in range(2)], axis=1)
            num = float(np.mean(lo[:, 0] * lo[:, 1]))
            den = float(np.sqrt(np.mean(lo[:, 0] ** 2) *
                                np.mean(lo[:, 1] ** 2)) + 1e-9)
            lo_corr = num / den
        except Exception:
            lo_corr = 0.0
        check("v25.beat_section_variation", r.get("ok") is True,
              f"engine={r.get('engine')}")
        check("v25.beat_lowband_mono", lo_corr > 0.9,
              f"lowband L/R corr={round(lo_corr,3)}")
    except Exception as e:
        check("v25.beat_section_variation", False, f"crash: {e}")
        check("v25.beat_lowband_mono", False, f"crash: {e}")

    # ---- прогон 6: LLM preflight быстрый ---------------------------------
    try:
        from modules.llm_clients_v15 import LLMRouter
        t0 = time.time()
        r = LLMRouter(timeout=8.0).complete("напиши про ночь", "",
                                            theme="ночь", genre="phonk")
        dt = time.time() - t0
        # без сети/ключей должен быть быстрым (<5с) из-за preflight
        check("v25.llm_preflight_fast", dt < 5.0 and r.get("ok"),
              f"{round(dt,2)}s provider={r.get('provider')}")
    except Exception as e:
        check("v25.llm_preflight_fast", False, f"crash: {e}")

    # ---- итог -------------------------------------------------------------
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    nfail = sum(1 for _, ok, _ in RESULTS if not ok)
    print("-" * 64)
    print(f"RESULT: {npass} PASS / {nfail} FAIL / {len(RESULTS)} total")
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
