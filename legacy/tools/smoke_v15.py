# -*- coding: utf-8 -*-
"""
ZS Music Maker v15/v16 — tools/smoke_v15.py

Smoke-тест модулей, добавленных в v15 (TZ 30, P1):
  - modules/release_pack_full.py  (P1.44 полный релиз-пакет)
  - modules/llm_clients_v15.py    (P1.45 LLMRouter: OpenRouter→Grok→Gemini→Ollama→template)
  - tools/ab_compare.py           (P1.46 A/B сравнение user vs reference)
  - agents/github_scout.py        (P2.47 GitHub scout)

Файл был заявлен в CHANGELOG_v15_APPEND.md как доказательство, но в архиве
v15 отсутствовал (потерянное доказательство). Восстановлен в v16.

Принцип честности (TZ 1.9): каждая проверка реально вызывает код,
реальный выход проверяется по файлам/полям, fallback помечается явно.
Запуск:  python3 tools/smoke_v15.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS: list = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def _make_test_wav(path: Path, seconds: float = 2.0, sr: int = 44100, freq: float = 440.0) -> bool:
    """Синтезирует реальный тестовый WAV (синус + гармоники), не тишину."""
    try:
        import numpy as np
        import soundfile as sf
        t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
        sig = (0.5 * np.sin(2 * np.pi * freq * t)
               + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
               + 0.1 * np.sin(2 * np.pi * freq * 3 * t))
        # лёгкая огибающая, чтобы сигнал был «музыкальным», а не ровным тоном
        env = 0.5 + 0.5 * np.sin(2 * np.pi * 2.0 * t)
        stereo = np.stack([sig * env, sig * env * 0.9], axis=-1).astype("float32")
        sf.write(str(path), stereo, sr, subtype="PCM_16")
        return path.exists() and path.stat().st_size > 1000
    except Exception as e:
        print(f"  (wav synth failed: {e})")
        return False


def main() -> int:
    t0 = time.time()
    print("=== ZS Music Maker smoke_v15 ===")

    # ---------- 1. Импорты v15-модулей ----------
    try:
        from modules import release_pack_full
        helpers = [h for h in ("build_pack", "_fake_stems", "_make_cover",
                               "_lyrics_to_lrc", "_lyrics_to_srt",
                               "_instrumental_and_acapella", "_make_clip",
                               "_distrokid_xml", "_spotify_description")
                   if hasattr(release_pack_full, h)]
        check("import release_pack_full", hasattr(release_pack_full, "build_pack"),
              f"helpers present: {len(helpers)}/9")
    except Exception as e:
        check("import release_pack_full", False, str(e))
        release_pack_full = None

    try:
        from modules.llm_clients_v15 import LLMRouter
        check("import llm_clients_v15.LLMRouter", True)
    except Exception as e:
        check("import llm_clients_v15.LLMRouter", False, str(e))
        LLMRouter = None

    try:
        from tools import ab_compare
        check("import tools/ab_compare", True)
    except Exception as e:
        check("import tools/ab_compare", False, str(e))
        ab_compare = None

    try:
        from agents import github_scout
        check("import agents/github_scout", True)
    except Exception as e:
        check("import agents/github_scout", False, str(e))
        github_scout = None

    tmp = Path(tempfile.mkdtemp(prefix="zsmm_smoke_v15_"))
    print(f"workdir: {tmp}")

    # ---------- 2. Реальный прогон release_pack_full.build_pack ----------
    if release_pack_full is not None:
        master = tmp / "master.wav"
        wav_ok = _make_test_wav(master)
        check("synth test master wav", wav_ok,
              f"{master.stat().st_size} bytes" if master.exists() else "no file")
        if wav_ok:
            try:
                rep = release_pack_full.build_pack(
                    str(master), str(tmp / "pack"),
                    meta={"title": "Smoke V15", "artist": "ZS", "genre": "phonk"},
                    lyrics_text="куплет: smoke-тест релиз-пакета v15",
                    stages=[{"stage": "master", "ok": True}],
                    hit_metrics={"hit_score": 61.0},
                )
                n = rep.get("n_files", 0)
                # ТЗ 23: ~38 файлов в полном пакете; в песочнице часть категорий
                # может честно уйти в fallback (нет ffmpeg/клип-генератора) — считаем
                # реальные файлы и проверяем, что отчёт честно их помечает.
                real_files = [f for f in rep.get("files", []) if Path(f).exists()]
                check("release_pack_full.build_pack runs", rep.get("ok", False),
                      f"n_files={n}, on_disk={len(real_files)}, "
                      f"fallback_used={rep.get('fallback_used')}")
                check("release_pack_full produces >=10 real files", len(real_files) >= 10,
                      f"{len(real_files)} files on disk")
                # ключевые артефакты по ТЗ 23
                must = ["full_master_streaming.wav"]
                missing = [m for m in must if not (tmp / "pack" / m).exists()]
                check("release_pack contains streaming master", not missing,
                      f"missing: {missing}" if missing else "ok")
                if rep.get("fallback_used"):
                    print(f"  FALLBACK_USED: {rep.get('fallback_used')}")
            except Exception as e:
                check("release_pack_full.build_pack runs", False, repr(e))

    # ---------- 3. LLMRouter: без ключей обязан честно уйти в local_template ----------
    if LLMRouter is not None:
        try:
            router = LLMRouter(keys={}, timeout=3)
            r = router.complete("напиши короткий куплет про ночной город",
                                theme="ночной город", genre="phonk", language="ru")
            prov = r.get("provider", "?")
            chain = r.get("provider_chain", [])
            # В песочнице нет API-ключей и Ollama — честный результат: local_template
            honest = prov == "local_template" and r.get("fallback_used") is True
            check("LLMRouter honest fallback to local_template", honest,
                  f"provider={prov}, chain={'→'.join(chain)}, "
                  f"fallback_used={r.get('fallback_used')}")
            check("LLMRouter returns non-empty text", bool((r.get("text") or "").strip()),
                  f"{len((r.get('text') or '').split())} words")
        except Exception as e:
            check("LLMRouter honest fallback to local_template", False, repr(e))

    # ---------- 4. ab_compare на двух синтетических WAV ----------
    if ab_compare is not None:
        try:
            import inspect
            fns = [n for n, _ in inspect.getmembers(ab_compare, inspect.isfunction)
                   if not n.startswith("_")]
            check("ab_compare exposes functions", len(fns) > 0, ",".join(fns[:6]))
            wa, wb = tmp / "a.wav", tmp / "b.wav"
            if _make_test_wav(wa, freq=440.0) and _make_test_wav(wb, freq=330.0):
                ran = False
                for cand in ("compare", "run", "main", "ab"):
                    fn = getattr(ab_compare, cand, None)
                    if callable(fn):
                        try:
                            out = fn(str(wa), str(wb), str(tmp / "ab"))
                            ran = True
                            check("ab_compare real run", True,
                                  f"{cand}() -> {str(out)[:120]}")
                            break
                        except TypeError:
                            try:
                                out = fn(str(wa), str(wb))
                                ran = True
                                check("ab_compare real run", True, f"{cand}() ok")
                                break
                            except Exception:
                                continue
                if not ran:
                    check("ab_compare real run", False,
                          "no callable entry accepted (a,b[,out]) — NOT_TESTED")
        except Exception as e:
            check("ab_compare real run", False, repr(e))

    # ---------- 5. github_scout в офлайн-режиме (без сети не должен падать) ----------
    if github_scout is not None:
        try:
            rep = github_scout.scan(offline_fallback=True)
            check("github_scout.scan offline-safe", isinstance(rep, dict) and "topics" in rep,
                  f"offline_fallback={rep.get('offline_fallback')}, "
                  f"errors={len(rep.get('errors', []))}, new={len(rep.get('new_repos', []))}")
        except Exception as e:
            check("github_scout.scan offline-safe", False, repr(e))

    # ---------- итог ----------
    n_ok = sum(1 for r in RESULTS if r["ok"])
    n_all = len(RESULTS)
    report = {
        "smoke": "v15", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "passed": n_ok, "failed": n_all - n_ok, "total": n_all,
        "elapsed_sec": round(time.time() - t0, 2),
        "results": RESULTS, "workdir": str(tmp),
    }
    out_json = ROOT / "output" / "audit_v15" / "smoke_v15_report.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== {n_ok}/{n_all} PASS, {n_all - n_ok} FAIL ===")
    print(f"report: {out_json}")
    return 0 if n_ok == n_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
