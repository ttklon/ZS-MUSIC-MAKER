# BARE_PRINT — print() вместо logger

**Severity:** 🟢 LOW
**Всего:** 311
**Как чинить:** `print(x)` → `logger.info(x)`.

## Все вхождения

### `agents/sample_hunter.py` — 3 шт.
- **строка 86** — print() вместо logger
  ```
         84 |             )
         85 |     except Exception as e:
  >>>    86 |         print(f"[sample_hunter.wikimedia] {e}")
         87 |     return results
         88 | 
  ```
- **строка 200** — print() вместо logger
  ```
        198 |         return None
        199 |     except Exception as e:
  >>>   200 |         print(f"[sample_hunter.download] {e}")
        201 |         return None
        202 | 
  ```
- **строка 205** — print() вместо logger
  ```
        203 | 
        204 | if __name__ == "__main__":
  >>>   205 |     print(json.dumps(hunt("phonk 808", max_results=3), ensure_ascii=False, indent=2))
  ```

### `agents/sample_hunter_v9.py` — 4 шт.
- **строка 297** — print() вместо logger
  ```
        295 |             it["license_blocked"] = True
        296 |             it["license_reason"] = f"blocked by license gate: {lic}"
  >>>   297 |             print(f"[sample_hunter_v9] BLOCKED non-free sample: "
        298 |                   f"{it.get('name','?')[:60]} ({lic})")
        299 |     return out
  ```
- **строка 364** — print() вместо logger
  ```
        362 |     sv = {"bpm": 132, "genre_hint": "phonk / drift"}
        363 |     q = plan_queries(sv)
  >>>   364 |     print("PLAN:", q)
        365 |     local = list_local()
        366 |     print(f"LOCAL: {len(local)} files")
  ```
- **строка 366** — print() вместо logger
  ```
        364 |     print("PLAN:", q)
        365 |     local = list_local()
  >>>   366 |     print(f"LOCAL: {len(local)} files")
        367 |     print(f"HAS_REQ: {HAS_REQ}")
  ```
- **строка 367** — print() вместо logger
  ```
        365 |     local = list_local()
        366 |     print(f"LOCAL: {len(local)} files")
  >>>   367 |     print(f"HAS_REQ: {HAS_REQ}")
  ```

### `agents/training_texts.py` — 1 шт.
- **строка 140** — print() вместо logger
  ```
        138 | 
        139 | if __name__ == "__main__":
  >>>   140 |     print(json.dumps(get_next_text(), ensure_ascii=False, indent=2))
  ```

### `agents/trend_scout.py` — 1 шт.
- **строка 156** — print() вместо logger
  ```
        154 | 
        155 | if __name__ == "__main__":
  >>>   156 |     print(json.dumps(scout_trends("phonk drift"), ensure_ascii=False, indent=2))
  ```

### `agents/trend_scout_v3.py` — 1 шт.
- **строка 247** — print() вместо logger
  ```
        245 | 
        246 |     theme = sys.argv[1] if len(sys.argv) > 1 else "лето тачки"
  >>>   247 |     print(json.dumps(scout(theme, offline_only=True), ensure_ascii=False, indent=2))
  ```

### `app/core/font_utils.py` — 2 шт.
- **строка 35** — print() вместо logger
  ```
         33 |         ]
         34 |     except OSError as e:  # noqa: BLE001 — сообщаем причину и работаем без конфига
  >>>    35 |         print(f"[font_utils] cannot read {cfg}: {e}", file=sys.stderr)
         36 |         return []
         37 | 
  ```
- **строка 107** — print() вместо logger
  ```
        105 |             continue  # штатное отсутствие
        106 |         except Exception as e:  # noqa: BLE001
  >>>   107 |             print(f"[font_utils] TTF load error {cand}: {e}", file=sys.stderr)
        108 |             continue
        109 |     return ImageFont.load_default()
  ```

### `app/core/hw_autodetect.py` — 3 шт.
- **строка 210** — print() вместо logger
  ```
        208 | if __name__ == "__main__":
        209 |     p = detect(force=True)
  >>>   210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
        211 |     print()
        212 |     print(human_summary(p))
  ```
- **строка 211** — print() вместо logger
  ```
        209 |     p = detect(force=True)
        210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
  >>>   211 |     print()
        212 |     print(human_summary(p))
  ```
- **строка 212** — print() вместо logger
  ```
        210 |     print(json.dumps(p, ensure_ascii=False, indent=2))
        211 |     print()
  >>>   212 |     print(human_summary(p))
  ```

### `app/core/musicgen_texture.py` — 4 шт.
- **строка 60** — print() вместо logger
  ```
         58 |         return model
         59 |     except Exception as e:
  >>>    60 |         print(f"[musicgen_texture] audiocraft недоступен: {e}")
         61 |         return None
         62 | 
  ```
- **строка 165** — print() вместо logger
  ```
        163 |         # v35: честный лог причины один раз на вызов (не молчаливо)
        164 |         avail = detect_availability()
  >>>   165 |         print(f"[musicgen_texture] BLOCKED: {avail['reason']} | {avail['install_hint']}")
        166 |     if model is not None:
        167 |         try:
  ```
- **строка 187** — print() вместо logger
  ```
        185 |             }
        186 |         except Exception as e:
  >>>   187 |             print(f"[musicgen_texture] generation failed: {e}")
        188 | 
        189 |     # 3) Honest failure: pink noise is not MusicGen and must not be presented as it.
  ```
- **строка 261** — print() вместо logger
  ```
        259 | if __name__ == "__main__":
        260 |     r = generate_texture("dark phonk atmosphere", duration_sec=10, vram_gb=4.0)
  >>>   261 |     print(r)
  ```

### `app/core/orchestrator_async.py` — 1 шт.
- **строка 115** — print() вместо logger
  ```
        113 |     orch = AsyncOrchestrator("async_test", Path("./output/async_test"))
        114 |     res = await orch.run_pipeline({"genre": "phonk", "bpm_override": 140})
  >>>   115 |     print(f"Async Pipeline Done in {res['duration_sec']}s")
        116 | 
        117 | if __name__ == "__main__":
  ```

### `app/core/orchestrator_god.py` — 3 шт.
- **строка 128** — print() вместо logger
  ```
        126 |                 return out_name
        127 |         except Exception as e:
  >>>   128 |             print(f"[orchestrator_god] Engine fallback due to: {e}")
        129 | 
        130 |         # Fallback to beat_constructor if needed
  ```
- **строка 180** — print() вместо logger
  ```
        178 |                 ctx.shared_data["vocal_status"] = "BLOCKED"
        179 |                 ctx.shared_data["vocal_reason"] = "no_vocal_engine (silero/xtts/bark/pyttsx3/gtts недоступны)"
  >>>   180 |                 print("[orchestrator_god] vocal synth BLOCKED: no TTS engine available — pipeline продолжает без вокала")
        181 |             except Exception as e:
        182 |                 print(f"[orchestrator_god] Auto-vocal synthesis error: {e}")
  ```
- **строка 182** — print() вместо logger
  ```
        180 |                 print("[orchestrator_god] vocal synth BLOCKED: no TTS engine available — pipeline продолжает без вокала")
        181 |             except Exception as e:
  >>>   182 |                 print(f"[orchestrator_god] Auto-vocal synthesis error: {e}")
        183 |                 ctx.shared_data["vocal_status"] = "FAILED"
        184 |                 ctx.shared_data["vocal_reason"] = str(e)
  ```

### `app/core/orchestrator_v10_patch.py` — 1 шт.
- **строка 226** — print() вместо logger
  ```
        224 |     d = Dummy()
        225 |     r = apply_v10_patch(d)
  >>>   226 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `app/core/orchestrator_v11_patch.py` — 2 шт.
- **строка 23** — print() вместо logger
  ```
         21 | def _safe_print(msg):
         22 |     try:
  >>>    23 |         print(msg)
         24 |     except UnicodeEncodeError:
         25 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```
- **строка 401** — print() вместо logger
  ```
        399 | 
        400 | if __name__ == "__main__":
  >>>   401 |     print("orchestrator_v11_patch self-test:", "OK" if _self_test() else "FAIL")
  ```

### `app/core/orchestrator_v12_patch.py` — 1 шт.
- **строка 33** — print() вместо logger
  ```
         31 | def _safe_print(msg: str) -> None:
         32 |     try:
  >>>    33 |         print(msg)
         34 |     except UnicodeEncodeError:
         35 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", "replace"))
  ```

### `app/core/security_utils.py` — 1 шт.
- **строка 38** — print() вместо logger
  ```
         36 |         return True
         37 |     except Exception as e:
  >>>    38 |         print(f"Download failed: {e}")
         39 |         return False
         40 | 
  ```

### `app/gui/theme_v12.py` — 1 шт.
- **строка 258** — print() вместо logger
  ```
        256 | if __name__ == "__main__":
        257 |     s = qss()
  >>>   258 |     print(
        259 |         f"theme_v12 QSS length = {len(s)} chars, "
        260 |         f"tokens = {len(TOKENS)}, fonts = {len(FONTS)}"
  ```

### `app/hw_probe.py` — 1 шт.
- **строка 61** — print() вместо logger
  ```
         59 | 
         60 | def main():
  >>>    61 |     print(json.dumps(asdict(probe()), ensure_ascii=False, indent=2))
         62 | 
         63 | 
  ```

### `app/plugins/base.py` — 2 шт.
- **строка 52** — print() вместо logger
  ```
         50 |                     except Exception as _log_err:  # noqa: BLE001 — fallback на stderr, не падаем
         51 |                         import sys as _sys
  >>>    52 |                         print(
         53 |                             f"[plugins/base] logger unavailable ({_log_err}); "
         54 |                             f"sanitizing NaN/Inf in {type(plugin).__name__}",
  ```
- **строка 86** — print() вместо logger
  ```
         84 |                 except Exception as e:  # noqa: BLE001
         85 |                     # v39.4 (ШАГ 005): честный лог причины падения плагина
  >>>    86 |                     print(f"[plugins/base] failed to load {module_name}: "
         87 |                           f"{type(e).__name__}: {e}")
         88 |         return self.discovered
  ```

### `app/runtime_orchestrator.py` — 1 шт.
- **строка 44** — print() вместо logger
  ```
         42 |                 self.log.info(msg)
         43 |             else:
  >>>    44 |                 print(msg)
         45 |         except Exception:
         46 |             pass
  ```

### `config/settings.py` — 1 шт.
- **строка 41** — print() вместо logger
  ```
         39 |             out[k] = v.strip().strip('"').strip("'")
         40 |     except OSError as e:  # noqa: BLE001
  >>>    41 |         print(f"[settings] cannot read {path}: {e}")
         42 |     return out
         43 | 
  ```

### `install.py` — 19 шт.
- **строка 20** — print() вместо logger
  ```
         18 |     риск injection + поломка на путях с пробелами. cmd может быть строкой
         19 |     (разбивается shlex) или списком аргументов."""
  >>>    20 |     print(f"Executing: {cmd}")
         21 |     try:
         22 |         args = shlex.split(cmd) if isinstance(cmd, str) else cmd
  ```
- **строка 26** — print() вместо logger
  ```
         24 |         return True
         25 |     except subprocess.CalledProcessError as e:
  >>>    26 |         print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
         27 |         if critical:
         28 |             print("[CRITICAL] Critical dependency installation failed. Aborting.")
  ```
- **строка 28** — print() вместо logger
  ```
         26 |         print(f"[ERROR] Command failed with exit code {e.returncode}: {e}")
         27 |         if critical:
  >>>    28 |             print("[CRITICAL] Critical dependency installation failed. Aborting.")
         29 |             sys.exit(1)
         30 |         return False
  ```
- **строка 32** — print() вместо logger
  ```
         30 |         return False
         31 |     except Exception as e:
  >>>    32 |         print(f"[ERROR] Unexpected error executing command: {e}")
         33 |         if critical:
         34 |             sys.exit(1)
  ```
- **строка 38** — print() вместо logger
  ```
         36 | 
         37 | def setup():
  >>>    38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
         39 |     os_name = platform.system()
         40 |     print(f"Detected OS: {os_name}")
  ```
- **строка 40** — print() вместо logger
  ```
         38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
         39 |     os_name = platform.system()
  >>>    40 |     print(f"Detected OS: {os_name}")
         41 | 
         42 |     # 1. Системные зависимости (на Linux)
  ```
- **строка 48** — print() вместо logger
  ```
         46 |     # 2. Основные Python зависимости
         47 |     req_file = "requirements.txt"
  >>>    48 |     print("Installing core Python dependencies...")
         49 |     success = run_cmd([sys.executable, "-m", "pip", "install", "-r", req_file], critical=True)
         50 |     if not success:
  ```
- **строка 51** — print() вместо logger
  ```
         49 |     success = run_cmd([sys.executable, "-m", "pip", "install", "-r", req_file], critical=True)
         50 |     if not success:
  >>>    51 |         print("[CRITICAL] Failed to install core requirements.")
         52 |         sys.exit(1)
         53 | 
  ```
- **строка 55** — print() вместо logger
  ```
         53 | 
         54 |     # 3. Опциональные тяжелые зависимости (Torch / Audio ML)
  >>>    55 |     print("Checking/Installing optional heavy neural dependencies (torch, torchaudio)...")
         56 |     run_cmd([sys.executable, "-m", "pip", "install", "torch", "torchaudio",
         57 |              "--index-url", "https://download.pytorch.org/whl/cpu"], critical=False)
  ```
- **строка 60** — print() вместо logger
  ```
         58 | 
         59 |     # 4. Проверка GPU / Hardware
  >>>    60 |     print("Checking for hardware acceleration...")
         61 |     try:
         62 |         import torch
  ```
- **строка 64** — print() вместо logger
  ```
         62 |         import torch
         63 |         if torch.cuda.is_available():
  >>>    64 |             print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
         65 |         else:
         66 |             print("CUDA not found, using CPU / Optimized Fallback.")
  ```
- **строка 66** — print() вместо logger
  ```
         64 |             print(f"CUDA Detected: {torch.cuda.get_device_name(0)}")
         65 |         else:
  >>>    66 |             print("CUDA not found, using CPU / Optimized Fallback.")
         67 |     except Exception:
         68 |         print("Torch CUDA check skipped (Torch not present).")
  ```
- **строка 68** — print() вместо logger
  ```
         66 |             print("CUDA not found, using CPU / Optimized Fallback.")
         67 |     except Exception:
  >>>    68 |         print("Torch CUDA check skipped (Torch not present).")
         69 | 
         70 |     # 5. Инициализация менеджера моделей
  ```
- **строка 71** — print() вместо logger
  ```
         69 | 
         70 |     # 5. Инициализация менеджера моделей
  >>>    71 |     print("Initializing Model Manager...")
         72 |     try:
         73 |         sys.path.insert(0, os.path.abspath("."))
  ```
- **строка 76** — print() вместо logger
  ```
         74 |         from app.core.model_manager import models
         75 |         models.ensure_model("whisper_tiny")
  >>>    76 |         print("Base models verified successfully.")
         77 |     except Exception as e:
         78 |         print(f"[WARNING] Model initialization notice: {e}")
  ```
- **строка 78** — print() вместо logger
  ```
         76 |         print("Base models verified successfully.")
         77 |     except Exception as e:
  >>>    78 |         print(f"[WARNING] Model initialization notice: {e}")
         79 | 
         80 |     # 6. Создание необходимых директорий
  ```
- **строка 92** — print() вместо logger
  ```
         90 |         os.makedirs(d, exist_ok=True)
         91 | 
  >>>    92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
         93 |     print("To start CLI God Mode, run: python main.py --god")
         94 |     print("To start Desktop GUI, run: python main.py --desktop")
  ```
- **строка 93** — print() вместо logger
  ```
         91 | 
         92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
  >>>    93 |     print("To start CLI God Mode, run: python main.py --god")
         94 |     print("To start Desktop GUI, run: python main.py --desktop")
         95 | 
  ```
- **строка 94** — print() вместо logger
  ```
         92 |     print("\n=== INSTALLATION & VERIFICATION COMPLETE ===")
         93 |     print("To start CLI God Mode, run: python main.py --god")
  >>>    94 |     print("To start Desktop GUI, run: python main.py --desktop")
         95 | 
         96 | if __name__ == "__main__":
  ```

### `main.py` — 10 шт.
- **строка 122** — print() вместо logger
  ```
        120 | def _safe_print(msg: str) -> None:
        121 |     try:
  >>>   122 |         print(msg)
        123 |     except UnicodeEncodeError:
        124 |         try:
  ```
- **строка 462** — print() вместо logger
  ```
        460 |         from modules.genre_engine import StyleRegistry
        461 |         reg = StyleRegistry()
  >>>   462 |         print("\nAvailable Genres:")
        463 |         for g in sorted(reg.list_genres()):
        464 |             print(f"  - {g}")
  ```
- **строка 464** — print() вместо logger
  ```
        462 |         print("\nAvailable Genres:")
        463 |         for g in sorted(reg.list_genres()):
  >>>   464 |             print(f"  - {g}")
        465 |         return 0
        466 | 
  ```
- **строка 500** — print() вместо logger
  ```
        498 |     if args.ai_status:
        499 |         from app.ai.registry import registry, MODEL_REGISTRY
  >>>   500 |         print("[AI] Hardware budget:", registry.hw)
        501 |         for k, v in MODEL_REGISTRY.items():
        502 |             avail = "OK" if registry.is_available(k) else "--"
  ```
- **строка 503** — print() вместо logger
  ```
        501 |         for k, v in MODEL_REGISTRY.items():
        502 |             avail = "OK" if registry.is_available(k) else "--"
  >>>   503 |             print(f"  {avail} {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
        504 |         return 0
        505 | 
  ```
- **строка 526** — print() вместо logger
  ```
        524 |         tracks += LyricVaultCollector(str(ROOT / "lyric_vault")).collect(args.dossier_artist)
        525 |         mgr.add_artist(args.dossier_artist, tracks=tracks)
  >>>   526 |         print(f"[dossier] artist={args.dossier_artist} tracks_added={len(tracks)}")
        527 |         return 0
        528 | 
  ```
- **строка 534** — print() вместо logger
  ```
        532 |         d = mgr.build_full_dossier(args.dossier_artist,
        533 |                                    progress_cb=lambda tid, st: print(f"  [{tid}] {st}"))
  >>>   534 |         print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
        535 |         return 0
        536 | 
  ```
- **строка 542** — print() вместо logger
  ```
        540 |               "artist_slug": args.dossier_artist or None}
        541 |         out = run_ai_pipeline("ai_cli", ws, dry_run=False)
  >>>   542 |         print(json.dumps({"stages": out["report"]["stages"],
        543 |                           "artefacts": out["artefacts"]}, ensure_ascii=False, indent=2))
        544 |         return 0
  ```
- **строка 558** — print() вместо logger
  ```
        556 |             result = asyncio.run(orch.run_pipeline({"genre": args.genre}))
        557 |         except Exception as e:
  >>>   558 |             print(f"[async-mode] PIPELINE FAILED: {e}")
        559 |             return 1
        560 |         # Оркестратор может вернуть dict со статусом или None —
  ```
- **строка 565** — print() вместо logger
  ```
        563 |             status = str(result.get("status", "")).lower()
        564 |             if status in ("failed", "error"):
  >>>   565 |                 print(f"[async-mode] pipeline status={status}")
        566 |                 return 1
        567 |         return 0
  ```

### `modules/ai_arranger.py` — 1 шт.
- **строка 52** — print() вместо logger
  ```
         50 | if __name__ == "__main__":
         51 |     arranger = AIArranger()
  >>>    52 |     print(arranger.get_structure(["electronic", "techno"]))
  ```

### `modules/ai_detector_pro.py` — 1 шт.
- **строка 190** — print() вместо logger
  ```
        188 |     import json
        189 | 
  >>>   190 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `modules/analyzer.py` — 2 шт.
- **строка 254** — print() вместо logger
  ```
        252 |     files = sys.argv[1:]
        253 |     if not files:
  >>>   254 |         print("Usage: python analyzer.py <ref1.mp3> [ref2.mp3 ...]")
        255 |     else:
        256 |         result = analyze_multi(files) if len(files) > 1 else analyze_single(files[0])
  ```
- **строка 257** — print() вместо logger
  ```
        255 |     else:
        256 |         result = analyze_multi(files) if len(files) > 1 else analyze_single(files[0])
  >>>   257 |         print(json.dumps(result, ensure_ascii=False, indent=2))
  ```

### `modules/anti_ai_polish.py` — 2 шт.
- **строка 308** — print() вместо logger
  ```
        306 | 
        307 |     if len(sys.argv) < 3:
  >>>   308 |         print("usage: python anti_ai_polish.py <in.wav> <out.wav> [preset]")
        309 |         sys.exit(1)
        310 |     r = polish_track(
  ```
- **строка 317** — print() вместо logger
  ```
        315 |     import json
        316 | 
  >>>   317 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `modules/anti_neuro_v10.py` — 1 шт.
- **строка 401** — print() вместо logger
  ```
        399 | 
        400 | if __name__ == "__main__":
  >>>   401 |     print(json.dumps(capability_report(), ensure_ascii=False, indent=2))
  ```

### `modules/arrangement_engine.py` — 1 шт.
- **строка 325** — print() вместо logger
  ```
        323 |     }
        324 |     p = build_arrangement(sv, total_seconds=180, seed=42, variant=1)
  >>>   325 |     print(json.dumps(p, ensure_ascii=False, indent=2)[:3000])
  ```

### `modules/author_ref_lyrics.py` — 3 шт.
- **строка 363** — print() вместо logger
  ```
        361 | 
        362 |     if len(sys.argv) > 1 and sys.argv[1] == "scan":
  >>>   363 |         print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
        364 |     elif len(sys.argv) > 2 and sys.argv[1] == "profile":
        365 |         print(
  ```
- **строка 365** — print() вместо logger
  ```
        363 |         print(json.dumps(scan_library(), ensure_ascii=False, indent=2))
        364 |     elif len(sys.argv) > 2 and sys.argv[1] == "profile":
  >>>   365 |         print(
        366 |             json.dumps(build_style_profile(sys.argv[2]), ensure_ascii=False, indent=2)
        367 |         )
  ```
- **строка 369** — print() вместо logger
  ```
        367 |         )
        368 |     else:
  >>>   369 |         print(json.dumps(list_authors(), ensure_ascii=False, indent=2))
  ```

### `modules/beat_constructor.py` — 3 шт.
- **строка 111** — print() вместо logger
  ```
        109 |             return samples
        110 |         except Exception as e:
  >>>   111 |             print(f"[beat_constructor] load fail {path}: {e}")
        112 |             return np.zeros(self.sr, dtype=np.float32)
        113 | 
  ```
- **строка 585** — print() вместо logger
  ```
        583 |                 stereo = stereo / _pk * 0.95
        584 |         except Exception as exc:
  >>>   585 |             print(f"[beat_constructor] stereo width fallback: {exc}")
        586 | 
        587 |         os.makedirs(OUTPUT_DIR, exist_ok=True)
  ```
- **строка 658** — print() вместо logger
  ```
        656 |     sv = {"target_bpm": 130, "target_mode": "minor"}
        657 |     result = construct_beat(groove, [], sv, duration_sec=90)
  >>>   658 |     print(json.dumps(result, ensure_ascii=False, indent=2))
  ```

### `modules/beat_gen.py` — 1 шт.
- **строка 153** — print() вместо logger
  ```
        151 |         "vibe_tags": ["phonk/drift", "bass-heavy", "dark", "aggressive"],
        152 |     }
  >>>   153 |     print(build_prompt(demo_style, user_extra="summer, cars, istanbul"))
  ```

### `modules/cover_art_gen.py` — 2 шт.
- **строка 246** — print() вместо logger
  ```
        244 |             "Turkish Nights", "ZS", "output/covers/test_cover.png", style="neon"
        245 |         )
  >>>   246 |         print(r)
        247 |     else:
        248 |         print("PIL missing")
  ```
- **строка 248** — print() вместо logger
  ```
        246 |         print(r)
        247 |     else:
  >>>   248 |         print("PIL missing")
  ```

### `modules/distribution_export_v11.py` — 2 шт.
- **строка 22** — print() вместо logger
  ```
         20 | def _safe_print(msg):
         21 |     try:
  >>>    22 |         print(msg)
         23 |     except UnicodeEncodeError:
         24 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```
- **строка 474** — print() вместо logger
  ```
        472 | 
        473 | if __name__ == "__main__":
  >>>   474 |     print("distribution_export_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### `modules/essentia_analyzer.py` — 2 шт.
- **строка 169** — print() вместо logger
  ```
        167 | 
        168 |     if len(sys.argv) < 2:
  >>>   169 |         print(json.dumps({"engine_available": ESSENTIA_OK}, ensure_ascii=False))
        170 |     else:
        171 |         rep = analyze_advanced(sys.argv[1])
  ```
- **строка 172** — print() вместо logger
  ```
        170 |     else:
        171 |         rep = analyze_advanced(sys.argv[1])
  >>>   172 |         print(json.dumps(rep, ensure_ascii=False, indent=2))
  ```

### `modules/expert_mode_v11.py` — 2 шт.
- **строка 19** — print() вместо logger
  ```
         17 | def _safe_print(msg):
         18 |     try:
  >>>    19 |         print(msg)
         20 |     except UnicodeEncodeError:
         21 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```
- **строка 324** — print() вместо logger
  ```
        322 | 
        323 | if __name__ == "__main__":
  >>>   324 |     print("expert_mode_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### `modules/female_backing.py` — 6 шт.
- **строка 50** — print() вместо logger
  ```
         48 |         return True
         49 |     except Exception as e:
  >>>    50 |         print(f"[female_backing] silero failed: {e}")
         51 |         return False
         52 | 
  ```
- **строка 63** — print() вместо logger
  ```
         61 |         return True
         62 |     except Exception as e:
  >>>    63 |         print(f"[female_backing] bark failed: {e}")
         64 |         return False
         65 | 
  ```
- **строка 84** — print() вместо logger
  ```
         82 |         return out_wav.exists() and out_wav.stat().st_size > 500
         83 |     except Exception as e:
  >>>    84 |         print(f"[female_backing] pyttsx failed: {e}")
         85 |         return False
         86 | 
  ```
- **строка 151** — print() вместо logger
  ```
        149 |         return out
        150 |     except Exception as e:
  >>>   151 |         print(f"[female_backing] sweeten failed: {e}")
        152 |         return wav_path
        153 | 
  ```
- **строка 186** — print() вместо logger
  ```
        184 |         return sweeten_backing(out_wav)
        185 |     except Exception as e:
  >>>   186 |         print(f"[female_backing] make_chorus_backing failed: {e}")
        187 |         return out_wav
        188 | 
  ```
- **строка 224** — print() вместо logger
  ```
        222 |         return out
        223 |     except Exception as e:
  >>>   224 |         print(f"[female_backing] mix failed: {e}")
        225 |         return main_vocal_wav
  ```

### `modules/freesound_client.py` — 1 шт.
- **строка 200** — print() вместо logger
  ```
        198 |     q = sys.argv[1] if len(sys.argv) > 1 else "trap 808 kick"
        199 |     res = search(q, bpm_min=120, bpm_max=160, duration_max=5.0)
  >>>   200 |     print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])
  ```

### `modules/genre_engine.py` — 3 шт.
- **строка 124** — print() вместо logger
  ```
        122 |     reg = StyleRegistry()
        123 |     factory = GenreFactory(reg)
  >>>   124 |     print(f"Available genres: {len(reg.list_genres())}")
        125 |     # Тест на конкретный жанр из 100+
        126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
  ```
- **строка 126** — print() вместо logger
  ```
        124 |     print(f"Available genres: {len(reg.list_genres())}")
        125 |     # Тест на конкретный жанр из 100+
  >>>   126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
        127 |     print(f"Generated Techno state: {factory.create_wizard_state('techno')}")
  ```
- **строка 127** — print() вместо logger
  ```
        125 |     # Тест на конкретный жанр из 100+
        126 |     print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
  >>>   127 |     print(f"Generated Techno state: {factory.create_wizard_state('techno')}")
  ```

### `modules/global_audit_fixer.py` — 1 шт.
- **строка 35** — print() вместо logger
  ```
         33 | 
         34 | if __name__ == "__main__":
  >>>    35 |     print(json.dumps(audit_system_integrity(), indent=2))
  ```

### `modules/groove_extractor.py` — 2 шт.
- **строка 232** — print() вместо logger
  ```
        230 | 
        231 |     if len(sys.argv) < 2:
  >>>   232 |         print("Usage: python groove_extractor.py <track.mp3>")
        233 |     else:
        234 |         print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
  ```
- **строка 234** — print() вместо logger
  ```
        232 |         print("Usage: python groove_extractor.py <track.mp3>")
        233 |     else:
  >>>   234 |         print(json.dumps(extract_groove(sys.argv[1]), ensure_ascii=False, indent=2))
  ```

### `modules/health_v12.py` — 21 шт.
- **строка 334** — print() вместо logger
  ```
        332 |     argv = argv or sys.argv[1:]
        333 |     rep = collect()
  >>>   334 |     print("=" * 72)
        335 |     print("ZS Music Maker v12 — Health Check")
        336 |     print(f"Generated: {rep.generated_at_human}")
  ```
- **строка 335** — print() вместо logger
  ```
        333 |     rep = collect()
        334 |     print("=" * 72)
  >>>   335 |     print("ZS Music Maker v12 — Health Check")
        336 |     print(f"Generated: {rep.generated_at_human}")
        337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
  ```
- **строка 336** — print() вместо logger
  ```
        334 |     print("=" * 72)
        335 |     print("ZS Music Maker v12 — Health Check")
  >>>   336 |     print(f"Generated: {rep.generated_at_human}")
        337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
        338 |     print(
  ```
- **строка 337** — print() вместо logger
  ```
        335 |     print("ZS Music Maker v12 — Health Check")
        336 |     print(f"Generated: {rep.generated_at_human}")
  >>>   337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
        338 |     print(
        339 |         f"HW mode  : {rep.hw_profile.get('mode', '?')}   "
  ```
- **строка 338** — print() вместо logger
  ```
        336 |     print(f"Generated: {rep.generated_at_human}")
        337 |     print(f"Platform : {rep.platform}   Python: {rep.python}")
  >>>   338 |     print(
        339 |         f"HW mode  : {rep.hw_profile.get('mode', '?')}   "
        340 |         f"GPU: {rep.hw_profile.get('gpu', '?')}"
  ```
- **строка 342** — print() вместо logger
  ```
        340 |         f"GPU: {rep.hw_profile.get('gpu', '?')}"
        341 |     )
  >>>   342 |     print("-" * 72)
        343 |     print("EXTERNAL DEPENDENCIES:")
        344 |     for e in rep.externals:
  ```
- **строка 343** — print() вместо logger
  ```
        341 |     )
        342 |     print("-" * 72)
  >>>   343 |     print("EXTERNAL DEPENDENCIES:")
        344 |     for e in rep.externals:
        345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
  ```
- **строка 345** — print() вместо logger
  ```
        343 |     print("EXTERNAL DEPENDENCIES:")
        344 |     for e in rep.externals:
  >>>   345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
        346 |     print("-" * 72)
        347 |     print("INTERNAL MODULES:")
  ```
- **строка 346** — print() вместо logger
  ```
        344 |     for e in rep.externals:
        345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
  >>>   346 |     print("-" * 72)
        347 |     print("INTERNAL MODULES:")
        348 |     for e in rep.internals:
  ```
- **строка 347** — print() вместо logger
  ```
        345 |         print(_fmt_row(e["name"], e["ok"], e.get("version"), e["requirement"]))
        346 |     print("-" * 72)
  >>>   347 |     print("INTERNAL MODULES:")
        348 |     for e in rep.internals:
        349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
  ```
- **строка 349** — print() вместо logger
  ```
        347 |     print("INTERNAL MODULES:")
        348 |     for e in rep.internals:
  >>>   349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
        350 |     print("-" * 72)
        351 |     print(
  ```
- **строка 350** — print() вместо logger
  ```
        348 |     for e in rep.internals:
        349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
  >>>   350 |     print("-" * 72)
        351 |     print(
        352 |         f"VERDICT: {rep.verdict}  |  READY: {rep.percent_ready}%  |  "
  ```
- **строка 351** — print() вместо logger
  ```
        349 |         print(_fmt_row(e["name"], e["ok"], None, e["requirement"]))
        350 |     print("-" * 72)
  >>>   351 |     print(
        352 |         f"VERDICT: {rep.verdict}  |  READY: {rep.percent_ready}%  |  "
        353 |         f"core_ok={rep.core_ok} quality_ok={rep.quality_ok}  "
  ```
- **строка 366** — print() вместо logger
  ```
        364 |                        if e.get("requirement") == "core_alt" and not e["ok"]]
        365 |         if core_missing:
  >>>   366 |             print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
        367 |         elif gui_missing:
        368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
  ```
- **строка 368** — print() вместо logger
  ```
        366 |             print(f"  ! RED причина: отсутствует ЯДРО: {', '.join(core_missing)}")
        367 |         elif gui_missing:
  >>>   368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
        369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
        370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
  ```
- **строка 369** — print() вместо logger
  ```
        367 |         elif gui_missing:
        368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
  >>>   369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
        370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
        371 |             print("    `pip install PySide6` или `pip install gradio`.")
  ```
- **строка 370** — print() вместо logger
  ```
        368 |             print(f"  ! RED причина: нет GUI-бэкенда ({', '.join(gui_missing)}).")
        369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
  >>>   370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
        371 |             print("    `pip install PySide6` или `pip install gradio`.")
        372 |     if rep.advice:
  ```
- **строка 371** — print() вместо logger
  ```
        369 |             print("    Аудио-ядро (beat/mix/mastering) при этом может быть полностью")
        370 |             print("    рабочим — проверь `python tools/smoke_v29.py`. Установи GUI:")
  >>>   371 |             print("    `pip install PySide6` или `pip install gradio`.")
        372 |     if rep.advice:
        373 |         print("ADVICE:")
  ```
- **строка 373** — print() вместо logger
  ```
        371 |             print("    `pip install PySide6` или `pip install gradio`.")
        372 |     if rep.advice:
  >>>   373 |         print("ADVICE:")
        374 |         for a in rep.advice[:20]:
        375 |             print(f"  - {a}")
  ```
- **строка 375** — print() вместо logger
  ```
        373 |         print("ADVICE:")
        374 |         for a in rep.advice[:20]:
  >>>   375 |             print(f"  - {a}")
        376 |     print("=" * 72)
        377 |     return 0 if rep.core_ok else 2
  ```
- **строка 376** — print() вместо logger
  ```
        374 |         for a in rep.advice[:20]:
        375 |             print(f"  - {a}")
  >>>   376 |     print("=" * 72)
        377 |     return 0 if rep.core_ok else 2
        378 | 
  ```

### `modules/hit_kpi_monitor_v11.py` — 2 шт.
- **строка 24** — print() вместо logger
  ```
         22 | def _safe_print(msg):
         23 |     try:
  >>>    24 |         print(msg)
         25 |     except UnicodeEncodeError:
         26 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```
- **строка 349** — print() вместо logger
  ```
        347 | 
        348 | if __name__ == "__main__":
  >>>   349 |     print("hit_kpi_monitor_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### `modules/hit_scorer.py` — 2 шт.
- **строка 585** — print() вместо logger
  ```
        583 | 
        584 |     if len(sys.argv) < 2:
  >>>   585 |         print("usage: python hit_scorer.py <master.wav> [out.json]")
        586 |         sys.exit(1)
        587 |     r = score_track(sys.argv[1], out_json=sys.argv[2] if len(sys.argv) > 2 else None)
  ```
- **строка 588** — print() вместо logger
  ```
        586 |         sys.exit(1)
        587 |     r = score_track(sys.argv[1], out_json=sys.argv[2] if len(sys.argv) > 2 else None)
  >>>   588 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `modules/hw_directml.py` — 1 шт.
- **строка 145** — print() вместо logger
  ```
        143 | if __name__ == "__main__":
        144 |     p = save_profile()
  >>>   145 |     print(json.dumps(p, ensure_ascii=False, indent=2))
  ```

### `modules/karaoke_engine.py` — 1 шт.
- **строка 191** — print() вместо logger
  ```
        189 | if __name__ == "__main__":
        190 |     wm = make_wordmap_from_lyrics("Тачки летят по трассе\nЛето жарит нас", bpm=140)
  >>>   191 |     print(json.dumps(wm, ensure_ascii=False, indent=2))
  ```

### `modules/kpi_dashboard_v12.py` — 1 шт.
- **строка 406** — print() вместо logger
  ```
        404 | def main() -> int:
        405 |     dash = build()
  >>>   406 |     print(render_text(dash))
        407 |     return 0 if dash.verdict == "GREEN" else (1 if dash.verdict == "YELLOW" else 2)
        408 | 
  ```

### `modules/llm_clients_v15.py` — 1 шт.
- **строка 563** — print() вместо logger
  ```
        561 |         a.prompt, a.system, theme=a.theme, genre=a.genre, language=a.language
        562 |     )
  >>>   563 |     print(
        564 |         json.dumps(
        565 |             {
  ```

### `modules/lyric_vault_v10.py` — 1 шт.
- **строка 252** — print() вместо logger
  ```
        250 | if __name__ == "__main__":
        251 |     r = rebuild_index()
  >>>   252 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `modules/lyrics_gen.py` — 3 шт.
- **строка 308** — print() вместо logger
  ```
        306 |         bilingual=True,
        307 |     )
  >>>   308 |     print(r["lyrics"])
        309 |     print("---")
        310 |     print("user_included:", r["user_lines_included"])
  ```
- **строка 309** — print() вместо logger
  ```
        307 |     )
        308 |     print(r["lyrics"])
  >>>   309 |     print("---")
        310 |     print("user_included:", r["user_lines_included"])
  ```
- **строка 310** — print() вместо logger
  ```
        308 |     print(r["lyrics"])
        309 |     print("---")
  >>>   310 |     print("user_included:", r["user_lines_included"])
  ```

### `modules/master_pipeline_v12.py` — 2 шт.
- **строка 61** — print() вместо logger
  ```
         59 |     line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [master_v12] {msg}"
         60 |     try:
  >>>    61 |         print(line)
         62 |     except UnicodeEncodeError:
         63 |         sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
  ```
- **строка 714** — print() вместо logger
  ```
        712 |     }
        713 |     r = run_master_pipeline(project_id, wizard_state=state, dry_run=True)
  >>>   714 |     print("\n" + r.human_summary)
        715 |     return 0 if r.verdict.endswith("PASS") else 1
        716 | 
  ```

### `modules/mastering.py` — 2 шт.
- **строка 208** — print() вместо logger
  ```
        206 | 
        207 |     if len(sys.argv) > 2:
  >>>   208 |         print(master_all_stands(sys.argv[1], sys.argv[2]))
        209 |     else:
        210 |         print("usage: python -m modules.mastering <mix.wav> <out_dir>")
  ```
- **строка 210** — print() вместо logger
  ```
        208 |         print(master_all_stands(sys.argv[1], sys.argv[2]))
        209 |     else:
  >>>   210 |         print("usage: python -m modules.mastering <mix.wav> <out_dir>")
  ```

### `modules/mastering_pro.py` — 3 шт.
- **строка 88** — print() вместо logger
  ```
         86 |             input_wav = temp_mix
         87 |         except Exception as e:
  >>>    88 |             print(f"[mastering_pro] Mix failed: {e}")
         89 | 
         90 |     mastered = None
  ```
- **строка 112** — print() вместо logger
  ```
        110 |             engine = "pedalboard_pro_safe"
        111 |         except Exception as e:
  >>>   112 |             print(f"[mastering_pro] Pedalboard execution error: {e}, falling back to numpy/soundfile")
        113 |             HAS_PEDALBOARD = False
        114 | 
  ```
- **строка 137** — print() вместо logger
  ```
        135 |             mastered = mastered.T  # back to (channels, frames)
        136 |         except Exception as e:
  >>>   137 |             print(f"[mastering_pro] pyloudnorm error: {e}, using RMS fallback")
        138 |             HAS_PYLOUDNORM = False
        139 | 
  ```

### `modules/mastering_v9.py` — 2 шт.
- **строка 267** — print() вместо logger
  ```
        265 | 
        266 |     if len(sys.argv) < 3:
  >>>   267 |         print("usage: python mastering_v9.py <in.wav> <out_dir>")
        268 |         sys.exit(1)
        269 |     r = render_all_stands(sys.argv[1], sys.argv[2])
  ```
- **строка 270** — print() вместо logger
  ```
        268 |         sys.exit(1)
        269 |     r = render_all_stands(sys.argv[1], sys.argv[2])
  >>>   270 |     print(
        271 |         json.dumps(
        272 |             {
  ```

### `modules/matchering_master.py` — 1 шт.
- **строка 133** — print() вместо logger
  ```
        131 | 
        132 | if __name__ == "__main__":
  >>>   133 |     print("Matchering available:", MG_OK)
  ```

### `modules/midi_generator.py` — 5 шт.
- **строка 138** — print() вместо logger
  ```
        136 |             return out_path
        137 |         except Exception as e:
  >>>   138 |             print(f"[midi_generator] drum error: {e}")
        139 |             return ""
        140 | 
  ```
- **строка 196** — print() вместо logger
  ```
        194 |             return out_path
        195 |         except Exception as e:
  >>>   196 |             print(f"[midi_generator] melody error: {e}")
        197 |             return ""
        198 | 
  ```
- **строка 202** — print() вместо logger
  ```
        200 | if __name__ == "__main__":
        201 |     gen = MIDIGenerator()
  >>>   202 |     print("Status:", gen.get_status())
        203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
        204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
  ```
- **строка 203** — print() вместо logger
  ```
        201 |     gen = MIDIGenerator()
        202 |     print("Status:", gen.get_status())
  >>>   203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
        204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
  ```
- **строка 204** — print() вместо logger
  ```
        202 |     print("Status:", gen.get_status())
        203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
  >>>   204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
  ```

### `modules/mixdown.py` — 3 шт.
- **строка 119** — print() вместо logger
  ```
        117 |     except ImportError:
        118 |         shutil.copy(mix_path, out)
  >>>   119 |         print("[matchering] MISSING — fallback: copy")
        120 |     except Exception as e:
        121 |         shutil.copy(mix_path, out)
  ```
- **строка 122** — print() вместо logger
  ```
        120 |     except Exception as e:
        121 |         shutil.copy(mix_path, out)
  >>>   122 |         print(f"[matchering error] {e} — fallback: copy")
        123 | 
        124 |     # Дополнительно: mp3 320
  ```
- **строка 177** — print() вместо logger
  ```
        175 | 
        176 | if __name__ == "__main__":
  >>>   177 |     print("mixdown module ready v2")
  ```

### `modules/musical_intelligence.py` — 1 шт.
- **строка 90** — print() вместо logger
  ```
         88 | if __name__ == "__main__":
         89 |     intel = MusicalIntelligence()
  >>>    90 |     print(intel.suggest_chords("A", "minor"))
  ```

### `modules/onboarding_tour.py` — 4 шт.
- **строка 204** — print() вместо logger
  ```
        202 |     """
        203 |     for i, step in enumerate(TOUR_STEPS):
  >>>   204 |         print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
        205 |         print(step["text"])
        206 |         if step.get("anchor"):
  ```
- **строка 205** — print() вместо logger
  ```
        203 |     for i, step in enumerate(TOUR_STEPS):
        204 |         print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
  >>>   205 |         print(step["text"])
        206 |         if step.get("anchor"):
        207 |             print(f"  → элемент интерфейса: {step['anchor']}")
  ```
- **строка 207** — print() вместо logger
  ```
        205 |         print(step["text"])
        206 |         if step.get("anchor"):
  >>>   207 |             print(f"  → элемент интерфейса: {step['anchor']}")
        208 |     mark_done()
        209 |     print("\nТур завершён.")
  ```
- **строка 209** — print() вместо logger
  ```
        207 |             print(f"  → элемент интерфейса: {step['anchor']}")
        208 |     mark_done()
  >>>   209 |     print("\nТур завершён.")
        210 | 
        211 | 
  ```

### `modules/phoneme_coverage.py` — 1 шт.
- **строка 137** — print() вместо logger
  ```
        135 | if __name__ == "__main__":
        136 |     r = compute_coverage()
  >>>   137 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `modules/presets.py` — 1 шт.
- **строка 170** — print() вместо logger
  ```
        168 | 
        169 | if __name__ == "__main__":
  >>>   170 |     print(json.dumps(list_presets(), ensure_ascii=False, indent=2))
  ```

### `modules/provenance.py` — 1 шт.
- **строка 142** — print() вместо logger
  ```
        140 | 
        141 | if __name__ == "__main__":
  >>>   142 |     print(json.dumps(check_commercial_safe(), ensure_ascii=False, indent=2))
  ```

### `modules/reference_ingest.py` — 2 шт.
- **строка 315** — print() вместо logger
  ```
        313 | 
        314 |     if len(sys.argv) < 2:
  >>>   315 |         print("usage: python reference_ingest.py <ref1> [ref2 ...]")
        316 |         sys.exit(1)
        317 |     r = build_style_vector(sys.argv[1:])
  ```
- **строка 318** — print() вместо logger
  ```
        316 |         sys.exit(1)
        317 |     r = build_style_vector(sys.argv[1:])
  >>>   318 |     print(json.dumps(r, ensure_ascii=False, indent=2))
  ```

### `modules/release_export.py` — 3 шт.
- **строка 58** — print() вместо logger
  ```
         56 |         return True
         57 |     except Exception as e:
  >>>    58 |         print(f"[release_export._copy_or_convert] {e}")
         59 |         try:
         60 |             shutil.copy(src, dst)
  ```
- **строка 95** — print() вместо logger
  ```
         93 |         return True
         94 |     except Exception as e:
  >>>    95 |         print(f"[release_export._write_id3] {e}")
         96 |         return False
         97 | 
  ```
- **строка 267** — print() вместо logger
  ```
        265 | 
        266 | if __name__ == "__main__":
  >>>   267 |     print("release_export v7 ready")
  ```

### `modules/release_pack_full.py` — 3 шт.
- **строка 916** — print() вместо logger
  ```
        914 | 
        915 |     if sf is None:
  >>>   916 |         print("soundfile not available")
        917 |         raise SystemExit(1)
        918 |     tmp = Path(tempfile.mkdtemp())
  ```
- **строка 945** — print() вместо logger
  ```
        943 |         hit_metrics={"score": 72, "verdict": "solid"},
        944 |     )
  >>>   945 |     print(
        946 |         json.dumps(
        947 |             {k: v for k, v in result.items() if k != "files"},
  ```
- **строка 952** — print() вместо logger
  ```
        950 |         )
        951 |     )
  >>>   952 |     print("Files:", len(result["files"]))
  ```

### `modules/release_pack_v9.py` — 2 шт.
- **строка 164** — print() вместо logger
  ```
        162 | 
        163 |     if len(sys.argv) < 2:
  >>>   164 |         print("usage: python release_pack_v9.py <release_dir>")
        165 |         sys.exit(1)
        166 |     r = build_release_v9(
  ```
- **строка 180** — print() вместо logger
  ```
        178 |         master_wav="/tmp/none.wav",
        179 |     )
  >>>   180 |     print(json.dumps(r, indent=2))
  ```

### `modules/render_queue.py` — 1 шт.
- **строка 197** — print() вместо logger
  ```
        195 | if __name__ == "__main__":
        196 |     q = RenderQueue()
  >>>   197 |     print(json.dumps(q.status_summary(), indent=2))
  ```

### `modules/rvc_manager.py` — 4 шт.
- **строка 136** — print() вместо logger
  ```
        134 |         if on_progress:
        135 |             on_progress(msg)
  >>>   136 |         print(f"[rvc_manager] {msg}")
        137 | 
        138 |     if fork_name == "rvc-python":
  ```
- **строка 448** — print() вместо logger
  ```
        446 |         )
        447 |     except Exception as e:
  >>>   448 |         print(f"[rvc_manager.infer] rvc-python failed: {e}")
        449 |         raise RuntimeError(
        450 |             f"RVC inference failed: {e}. No non-RVC fallback is permitted (TZ 33.5)."
  ```
- **строка 478** — print() вместо logger
  ```
        476 | if __name__ == "__main__":
        477 |     b = detect_backend()
  >>>   478 |     print(
        479 |         f"Backend: {b.kind} / fork={b.fork} / device={b.device_name} / vram={b.vram_gb} GB"
        480 |     )
  ```
- **строка 481** — print() вместо logger
  ```
        479 |         f"Backend: {b.kind} / fork={b.fork} / device={b.device_name} / vram={b.vram_gb} GB"
        480 |     )
  >>>   481 |     print(f"State: {json.dumps(_load_state(), ensure_ascii=False, indent=2)}")
  ```

### `modules/rvc_trainer_v9.py` — 1 шт.
- **строка 234** — print() вместо logger
  ```
        232 | 
        233 | if __name__ == "__main__":
  >>>   234 |     print(json.dumps(probe_backend(), ensure_ascii=False, indent=2))
  ```

### `modules/self_diag_v13.py` — 1 шт.
- **строка 302** — print() вместо logger
  ```
        300 | 
        301 |     report = render_report(layout, health, kpi, smoke, plan)
  >>>   302 |     print(report)
        303 | 
        304 |     out = {
  ```

### `modules/sidechain.py` — 1 шт.
- **строка 290** — print() вместо logger
  ```
        288 | 
        289 | if __name__ == "__main__":
  >>>   290 |     print(json.dumps(capability_report(), indent=2))
  ```

### `modules/stem_splitter.py` — 2 шт.
- **строка 73** — print() вместо logger
  ```
         71 | if __name__ == "__main__":
         72 |     if len(sys.argv) < 2:
  >>>    73 |         print("Usage: python stem_splitter.py <track.mp3>")
         74 |     else:
         75 |         print(split_stems(sys.argv[1]))
  ```
- **строка 75** — print() вместо logger
  ```
         73 |         print("Usage: python stem_splitter.py <track.mp3>")
         74 |     else:
  >>>    75 |         print(split_stems(sys.argv[1]))
  ```

### `modules/tiktok_edit_v9.py` — 2 шт.
- **строка 256** — print() вместо logger
  ```
        254 | 
        255 |     if len(sys.argv) < 3:
  >>>   256 |         print("usage: python tiktok_edit_v9.py <in.wav> <out_dir>")
        257 |         sys.exit(1)
        258 |     r = make_all_cuts(sys.argv[1], sys.argv[2])
  ```
- **строка 259** — print() вместо logger
  ```
        257 |         sys.exit(1)
        258 |     r = make_all_cuts(sys.argv[1], sys.argv[2])
  >>>   259 |     print(
        260 |         json.dumps(
        261 |             {
  ```

### `modules/user_profile.py` — 1 шт.
- **строка 157** — print() вместо logger
  ```
        155 | 
        156 | if __name__ == "__main__":
  >>>   157 |     print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
  ```

### `modules/video_edit_v11.py` — 2 шт.
- **строка 28** — print() вместо logger
  ```
         26 | def _safe_print(msg: str) -> None:
         27 |     try:
  >>>    28 |         print(msg)
         29 |     except UnicodeEncodeError:
         30 |         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
  ```
- **строка 464** — print() вместо logger
  ```
        462 | 
        463 | if __name__ == "__main__":
  >>>   464 |     print("video_edit_v11 self-test:", "OK" if _self_test() else "FAIL")
  ```

### `modules/vocal_fx.py` — 1 шт.
- **строка 370** — print() вместо logger
  ```
        368 | 
        369 | if __name__ == "__main__":
  >>>   370 |     print(json.dumps(capability_report(), indent=2))
  ```

### `modules/voice_convert.py` — 1 шт.
- **строка 204** — print() вместо logger
  ```
        202 | 
        203 | if __name__ == "__main__":
  >>>   204 |     print(json.dumps(vault_summary(), indent=2, ensure_ascii=False))
  ```

### `modules/voice_onboarding.py` — 12 шт.
- **строка 238** — print() вместо logger
  ```
        236 | 
        237 | def run_cli() -> int:
  >>>   238 |     print("=" * 64)
        239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
        240 |     print("=" * 64)
  ```
- **строка 239** — print() вместо logger
  ```
        237 | def run_cli() -> int:
        238 |     print("=" * 64)
  >>>   239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
        240 |     print("=" * 64)
        241 |     plan = build_plan()
  ```
- **строка 240** — print() вместо logger
  ```
        238 |     print("=" * 64)
        239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
  >>>   240 |     print("=" * 64)
        241 |     plan = build_plan()
        242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
  ```
- **строка 242** — print() вместо logger
  ```
        240 |     print("=" * 64)
        241 |     plan = build_plan()
  >>>   242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
        243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
  ```
- **строка 243** — print() вместо logger
  ```
        241 |     plan = build_plan()
        242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
  >>>   243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
        245 |     print(f"  — караоке: {PLAN['karaoke']}s")
  ```
- **строка 244** — print() вместо logger
  ```
        242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
        243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
  >>>   244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
        245 |     print(f"  — караоке: {PLAN['karaoke']}s")
        246 |     print()
  ```
- **строка 245** — print() вместо logger
  ```
        243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
  >>>   245 |     print(f"  — караоке: {PLAN['karaoke']}s")
        246 |     print()
        247 |     try:
  ```
- **строка 246** — print() вместо logger
  ```
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
        245 |     print(f"  — караоке: {PLAN['karaoke']}s")
  >>>   246 |     print()
        247 |     try:
        248 |         from modules import voice_recording as vr
  ```
- **строка 253** — print() вместо logger
  ```
        251 |     except Exception as e:
        252 |         cap = {"real_recording_possible": False, "error": str(e)}
  >>>   253 |     print("[capability]", json.dumps(cap, ensure_ascii=False))
        254 |     mic_ok = bool(cap.get("real_recording_possible"))
        255 |     if not mic_ok:
  ```
- **строка 256** — print() вместо logger
  ```
        254 |     mic_ok = bool(cap.get("real_recording_possible"))
        255 |     if not mic_ok:
  >>>   256 |         print("⚠️  Микрофон недоступен. Реальная запись НЕВОЗМОЖНА в этой среде.")
        257 |     m = _load_manifest()
        258 |     m["started_at"] = m.get("started_at") or int(time.time())
  ```
- **строка 262** — print() вместо logger
  ```
        260 |     m["recording_capable"] = mic_ok
        261 |     _save_manifest(m)
  >>>   262 |     print(f"✓ manifest saved: {MANIFEST}")
        263 |     # v34 FIX (P3.16): раньше run_cli() ВСЕГДА возвращал 0 — даже когда
        264 |     # микрофон недоступен и onboarding по факту «только план, без записи».
  ```
- **строка 268** — print() вместо logger
  ```
        266 |     # Теперь: 0 = полная capability, 1 = план сохранён, но запись невозможна.
        267 |     if not mic_ok:
  >>>   268 |         print("[voice_onboarding] exit=1 (plan-only: mic unavailable)")
        269 |         return 1
        270 |     return 0
  ```

### `modules/voice_recording.py` — 1 шт.
- **строка 395** — print() вместо logger
  ```
        393 | 
        394 | if __name__ == "__main__":
  >>>   395 |     print(json.dumps(capability_report(), indent=2))
  ```

### `modules/voice_synth.py` — 9 шт.
- **строка 40** — print() вместо logger
  ```
         38 |         return True
         39 |     except Exception as e:
  >>>    40 |         print(f"[voice_synth.silero] {e}")
         41 |         return False
         42 | 
  ```
- **строка 59** — print() вместо logger
  ```
         57 |         return True
         58 |     except Exception as e:
  >>>    59 |         print(f"[voice_synth.xtts] {e}")
         60 |         return False
         61 | 
  ```
- **строка 75** — print() вместо logger
  ```
         73 |         return True
         74 |     except Exception as e:
  >>>    75 |         print(f"[voice_synth.bark] {e}")
         76 |         return False
         77 | 
  ```
- **строка 90** — print() вместо logger
  ```
         88 |             return True
         89 |     except Exception as e:
  >>>    90 |         print(f"[voice_synth.pyttsx3] {e}")
         91 |     return False
         92 | 
  ```
- **строка 103** — print() вместо logger
  ```
        101 |         return os.path.exists(out_path) and os.path.getsize(out_path) > 100
        102 |     except Exception as e:
  >>>   103 |         print(f"[voice_synth.gtts] {e}")
        104 |         return False
        105 | 
  ```
- **строка 167** — print() вместо logger
  ```
        165 |             if engines[e]() and _produced():
        166 |                 return out_path
  >>>   167 |         print("[voice_synth] ALL engines failed/unavailable — honest empty return")
        168 |         return ""
        169 | 
  ```
- **строка 172** — print() вместо logger
  ```
        170 |     fn = engines.get(engine)
        171 |     if not fn:
  >>>   172 |         print(f"[voice_synth] unknown engine={engine}, fallback silero")
        173 |         fn = engines["silero"]
        174 | 
  ```
- **строка 185** — print() вместо logger
  ```
        183 |                 return out_path
        184 | 
  >>>   185 |     print("[voice_synth] no engine produced a file — honest empty return")
        186 |     return ""
        187 | 
  ```
- **строка 195** — print() вместо logger
  ```
        193 |         out_name="test_v7.wav",
        194 |     )
  >>>   195 |     print(f"WAV: {r}, exists: {os.path.exists(r)}")
  ```

### `modules/voice_vault_v9.py` — 1 шт.
- **строка 314** — print() вместо logger
  ```
        312 | # ============================================================ CLI
        313 | if __name__ == "__main__":
  >>>   314 |     print(json.dumps(clean_stats(), ensure_ascii=False, indent=2))
  ```

### `modules/wizard_v12_integration.py` — 3 шт.
- **строка 42** — print() вместо logger
  ```
         40 |     line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [wizard_v12_integ] {msg}"
         41 |     try:
  >>>    42 |         print(line)
         43 |     except UnicodeEncodeError:
         44 |         sys.stdout.buffer.write((line + "\n").encode("cp866", "replace"))
  ```
- **строка 281** — print() вместо logger
  ```
        279 |     )
        280 |     r = bridge_wizard_to_v12(proj, ui_state=state, dry_run=True)
  >>>   281 |     print(
        282 |         f"verdict={r.verdict}  stages={len(r.stages_done)}  " f"errors={len(r.errors)}"
        283 |     )
  ```
- **строка 284** — print() вместо logger
  ```
        282 |         f"verdict={r.verdict}  stages={len(r.stages_done)}  " f"errors={len(r.errors)}"
        283 |     )
  >>>   284 |     print(r.human_summary)
        285 |     return 0 if r.verdict.endswith("PASS") else 1
        286 | 
  ```

### `tests/test_genre_and_audit.py` — 3 шт.
- **строка 22** — print() вместо logger
  ```
         20 |     profile_unknown = get_genre_profile("unknown_cyber_jazz")
         21 |     assert profile_unknown["bpm"] == 120
  >>>    22 |     print("Genre expansion tests passed successfully.")
         23 | 
         24 | def test_audit_fixer():
  ```
- **строка 28** — print() вместо logger
  ```
         26 |     assert report["status"] == "PASSED_WITH_SELF_HEALING"
         27 |     assert report["critical_issues_resolved"] == 10
  >>>    28 |     print("Global audit fixer tests passed successfully.")
         29 | 
         30 | if __name__ == "__main__":
  ```
- **строка 33** — print() вместо logger
  ```
         31 |     test_genre_expansion()
         32 |     test_audit_fixer()
  >>>    33 |     print("ALL TESTS PASSED.")
  ```

### `tools/ab_compare.py` — 2 шт.
- **строка 30** — print() вместо logger
  ```
         28 |     import soundfile as sf
         29 | except Exception as e:
  >>>    30 |     print(f"[ab_compare] deps missing: {e}", file=sys.stderr)
         31 |     raise
         32 | 
  ```
- **строка 221** — print() вместо logger
  ```
        219 |     r = compare(a.user_wav, a.ref_wav, a.out)
        220 |     # Печатаем без spectrograms полных путей (короткая версия)
  >>>   221 |     print(
        222 |         json.dumps(
        223 |             {
  ```

### `tools/ast_dead_imports.py` — 4 шт.
- **строка 111** — print() вместо logger
  ```
        109 |     report = scan_all(dirs)
        110 |     if not report:
  >>>   111 |         print("AST dead-imports: CLEAN (0)")
        112 |         return 0
        113 |     print("AST dead-imports: FOUND")
  ```
- **строка 113** — print() вместо logger
  ```
        111 |         print("AST dead-imports: CLEAN (0)")
        112 |         return 0
  >>>   113 |     print("AST dead-imports: FOUND")
        114 |     total = 0
        115 |     for rel, items in sorted(report.items()):
  ```
- **строка 117** — print() вместо logger
  ```
        115 |     for rel, items in sorted(report.items()):
        116 |         for lineno, name in items:
  >>>   117 |             print(f"  {rel}:{lineno}  {name}")
        118 |             total += 1
        119 |     print(f"total: {total}")
  ```
- **строка 119** — print() вместо logger
  ```
        117 |             print(f"  {rel}:{lineno}  {name}")
        118 |             total += 1
  >>>   119 |     print(f"total: {total}")
        120 |     return 1
        121 | 
  ```

### `tools/audit_data_inventory.py` — 4 шт.
- **строка 120** — print() вместо logger
  ```
        118 | 
        119 |     if args.json:
  >>>   120 |         print(json.dumps(report, ensure_ascii=False, indent=2))
        121 |     else:
        122 |         print(
  ```
- **строка 122** — print() вместо logger
  ```
        120 |         print(json.dumps(report, ensure_ascii=False, indent=2))
        121 |     else:
  >>>   122 |         print(
        123 |             "data inventory: "
        124 |             f"files={len(report['files'])} managed={report['managed_count']} "
  ```
- **строка 128** — print() вместо logger
  ```
        126 |         )
        127 |         for entry in report["invalid"]:
  >>>   128 |             print(f"INVALID {entry['path']}: {entry['error']}")
        129 |         for path in report["unknown"]:
        130 |             print(f"UNKNOWN {path}")
  ```
- **строка 130** — print() вместо logger
  ```
        128 |             print(f"INVALID {entry['path']}: {entry['error']}")
        129 |         for path in report["unknown"]:
  >>>   130 |             print(f"UNKNOWN {path}")
        131 | 
        132 |     return 0 if not report["unknown"] and not report["invalid"] else 1
  ```

### `tools/deep_audit_v40.py` — 4 шт.
- **строка 273** — print() вместо logger
  ```
        271 |         for it in r["issues"]:
        272 |             stats[it["kind"]] += 1
  >>>   273 |     print("=== AUDIT STATS ===")
        274 |     for k, v in stats.most_common():
        275 |         print(f"  {k:32s}  {v}")
  ```
- **строка 275** — print() вместо logger
  ```
        273 |     print("=== AUDIT STATS ===")
        274 |     for k, v in stats.most_common():
  >>>   275 |         print(f"  {k:32s}  {v}")
        276 |     print(f"Total files: {len(reports)}")
        277 |     print(f"Total issues: {sum(stats.values())}")
  ```
- **строка 276** — print() вместо logger
  ```
        274 |     for k, v in stats.most_common():
        275 |         print(f"  {k:32s}  {v}")
  >>>   276 |     print(f"Total files: {len(reports)}")
        277 |     print(f"Total issues: {sum(stats.values())}")
        278 | 
  ```
- **строка 277** — print() вместо logger
  ```
        275 |         print(f"  {k:32s}  {v}")
        276 |     print(f"Total files: {len(reports)}")
  >>>   277 |     print(f"Total issues: {sum(stats.values())}")
        278 | 
        279 | 
  ```

### `tools/fallback_audit.py` — 1 шт.
- **строка 155** — print() вместо logger
  ```
        153 |     out = out_dir / "fallback_report.json"
        154 |     out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
  >>>   155 |     print(
        156 |         json.dumps(
        157 |             {
  ```

### `tools/genre_validator.py` — 5 шт.
- **строка 18** — print() вместо logger
  ```
         16 | 
         17 | def validate_all():
  >>>    18 |     print("=== Genre Integrity Audit (100+ Styles) ===")
         19 |     reg = StyleRegistry()
         20 |     factory = GenreFactory(reg)
  ```
- **строка 23** — print() вместо logger
  ```
         21 | 
         22 |     genres = reg.list_genres()
  >>>    23 |     print(f"Total genres found: {len(genres)}")
         24 | 
         25 |     errors = []
  ```
- **строка 43** — print() вместо logger
  ```
         41 | 
         42 |     if not errors:
  >>>    43 |         print("✅ All 119+ genres are VALID and BATTLE-READY.")
         44 |         return True
         45 |     else:
  ```
- **строка 46** — print() вместо logger
  ```
         44 |         return True
         45 |     else:
  >>>    46 |         print(f"❌ Found {len(errors)} issues:")
         47 |         for err in errors:
         48 |             print(f"  - {err}")
  ```
- **строка 48** — print() вместо logger
  ```
         46 |         print(f"❌ Found {len(errors)} issues:")
         47 |         for err in errors:
  >>>    48 |             print(f"  - {err}")
         49 |         return False
         50 | 
  ```

### `tools/lazy_dirs_patch.py` — 4 шт.
- **строка 157** — print() вместо logger
  ```
        155 |         p = MODS / fname
        156 |         if not p.exists():
  >>>   157 |             print(f"  [SKIP] {fname} not found")
        158 |             continue
        159 |         src = p.read_text(encoding="utf-8")
  ```
- **строка 166** — print() вместо logger
  ```
        164 |             p.write_text(src, encoding="utf-8")
        165 |             modified.append(fname)
  >>>   166 |             print(f"  [OK] {fname}")
        167 |         else:
        168 |             print(f"  [NOOP] {fname}")
  ```
- **строка 168** — print() вместо logger
  ```
        166 |             print(f"  [OK] {fname}")
        167 |         else:
  >>>   168 |             print(f"  [NOOP] {fname}")
        169 |     print(f"\nTotal modified: {len(modified)}")
        170 |     return 0
  ```
- **строка 169** — print() вместо logger
  ```
        167 |         else:
        168 |             print(f"  [NOOP] {fname}")
  >>>   169 |     print(f"\nTotal modified: {len(modified)}")
        170 |     return 0
        171 | 
  ```

### `tools/p0_truth_test.py` — 5 шт.
- **строка 30** — print() вместо logger
  ```
         28 |     try:
         29 |         rvc_manager.infer(str(src), voice_name="definitely_missing")
  >>>    30 |         print("RVC_FAIL: fallback still active")
         31 |     except RuntimeError as e:
         32 |         print("RVC_HONEST_FAIL_PASS:", e)
  ```
- **строка 32** — print() вместо logger
  ```
         30 |         print("RVC_FAIL: fallback still active")
         31 |     except RuntimeError as e:
  >>>    32 |         print("RVC_HONEST_FAIL_PASS:", e)
         33 |     out = Path(d) / "master.wav"
         34 |     r = matchering_master.master_to_stand(str(src), str(out), "streaming")
  ```
- **строка 35** — print() вместо logger
  ```
         33 |     out = Path(d) / "master.wav"
         34 |     r = matchering_master.master_to_stand(str(src), str(out), "streaming")
  >>>    35 |     print("MASTER_RESULT:", r)
         36 |     from app.core import musicgen_texture
         37 | 
  ```
- **строка 39** — print() вместо logger
  ```
         37 | 
         38 |     m = musicgen_texture.generate_texture("test", duration_sec=1, vram_gb=0.0)
  >>>    39 |     print("MUSICGEN_RESULT:", m)
         40 |     from modules import master_pipeline_v12
         41 | 
  ```
- **строка 43** — print() вместо logger
  ```
         41 | 
         42 |     x = master_pipeline_v12.run("api_test", {"references": []}, dry_run=True)
  >>>    43 |     print("PIPELINE_API:", x.get("verdict"), x.get("percent_ready"))
  ```

### `tools/pull_ai_models.py` — 16 шт.
- **строка 19** — print() вместо logger
  ```
         17 |     target = dest / spec["file"]
         18 |     if target.exists():
  >>>    19 |         print(f"[skip] {key}: already at {target}"); return True
         20 |     try:
         21 |         from huggingface_hub import hf_hub_download
  ```
- **строка 23** — print() вместо logger
  ```
         21 |         from huggingface_hub import hf_hub_download
         22 |     except Exception as e:
  >>>    23 |         print(f"[err] huggingface_hub: {e}"); return False
         24 |     try:
         25 |         print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
  ```
- **строка 25** — print() вместо logger
  ```
         23 |         print(f"[err] huggingface_hub: {e}"); return False
         24 |     try:
  >>>    25 |         print(f"[pull] {key} <- {spec['hf_repo']}/{spec['file']}")
         26 |         p = hf_hub_download(repo_id=spec["hf_repo"], filename=spec["file"],
         27 |                             local_dir=str(dest), local_dir_use_symlinks=False)
  ```
- **строка 28** — print() вместо logger
  ```
         26 |         p = hf_hub_download(repo_id=spec["hf_repo"], filename=spec["file"],
         27 |                             local_dir=str(dest), local_dir_use_symlinks=False)
  >>>    28 |         print(f"       -> {p}"); return True
         29 |     except Exception as e:
         30 |         print(f"[err] {key}: {e}"); return False
  ```
- **строка 30** — print() вместо logger
  ```
         28 |         print(f"       -> {p}"); return True
         29 |     except Exception as e:
  >>>    30 |         print(f"[err] {key}: {e}"); return False
         31 | 
         32 | 
  ```
- **строка 37** — print() вместо logger
  ```
         35 |     repo = spec.get("hf_repo")
         36 |     if not repo or repo == "user_supplied":
  >>>    37 |         print(f"[skip] {key}: user-supplied"); return True
         38 |     try:
         39 |         from huggingface_hub import snapshot_download
  ```
- **строка 40** — print() вместо logger
  ```
         38 |     try:
         39 |         from huggingface_hub import snapshot_download
  >>>    40 |         print(f"[pull] {key} <- {repo}")
         41 |         print(f"       -> {snapshot_download(repo_id=repo)}")
         42 |         return True
  ```
- **строка 41** — print() вместо logger
  ```
         39 |         from huggingface_hub import snapshot_download
         40 |         print(f"[pull] {key} <- {repo}")
  >>>    41 |         print(f"       -> {snapshot_download(repo_id=repo)}")
         42 |         return True
         43 |     except Exception as e:
  ```
- **строка 44** — print() вместо logger
  ```
         42 |         return True
         43 |     except Exception as e:
  >>>    44 |         print(f"[err] {key}: {e}"); return False
         45 | 
         46 | 
  ```
- **строка 50** — print() вместо logger
  ```
         48 |     try:
         49 |         from demucs.pretrained import get_model
  >>>    50 |         print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
         51 |     except Exception as e:
         52 |         print(f"[err] {key}: {e}"); return False
  ```
- **строка 52** — print() вместо logger
  ```
         50 |         print("[pull] demucs htdemucs ..."); get_model("htdemucs"); return True
         51 |     except Exception as e:
  >>>    52 |         print(f"[err] {key}: {e}"); return False
         53 | 
         54 | 
  ```
- **строка 66** — print() вместо logger
  ```
         64 |     if eng == "rvc":
         65 |         (ROOT / "models" / "rvc").mkdir(parents=True, exist_ok=True)
  >>>    66 |         print(f"[note] {key}: drop your .pth into models/rvc/"); return True
         67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
         68 |         print(f"[skip] {key}: pip-only"); return True
  ```
- **строка 68** — print() вместо logger
  ```
         66 |         print(f"[note] {key}: drop your .pth into models/rvc/"); return True
         67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
  >>>    68 |         print(f"[skip] {key}: pip-only"); return True
         69 |     print(f"[warn] unknown engine: {eng}"); return False
         70 | 
  ```
- **строка 69** — print() вместо logger
  ```
         67 |     if eng in ("matchering_plus", "essentia_or_librosa"):
         68 |         print(f"[skip] {key}: pip-only"); return True
  >>>    69 |     print(f"[warn] unknown engine: {eng}"); return False
         70 | 
         71 | 
  ```
- **строка 79** — print() вместо logger
  ```
         77 |     if args.list:
         78 |         for k, v in MODEL_REGISTRY.items():
  >>>    79 |             print(f"  {k:20s} {v['engine']:22s} VRAM~{v.get('vram_est_gb', 0)} GB - {v['role']}")
         80 |         return
         81 |     if args.model:
  ```
- **строка 87** — print() вместо logger
  ```
         85 |             pull(k)
         86 |         return
  >>>    87 |     print("See --list / --all / --model <name>.")
         88 | 
         89 | 
  ```

### `tools/readiness.py` — 1 шт.
- **строка 278** — print() вместо logger
  ```
        276 | def main() -> int:
        277 |     pct, blocks = compute()
  >>>   278 |     print(json.dumps({"percent": pct, "blocks": blocks}, ensure_ascii=False, indent=2))
        279 |     return 0
        280 | 
  ```

### `tools/real_e2e_v14.py` — 15 шт.
- **строка 83** — print() вместо logger
  ```
         81 | 
         82 | def main() -> int:
  >>>    83 |     print("=" * 64)
         84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
         85 |     print("=" * 64)
  ```
- **строка 84** — print() вместо logger
  ```
         82 | def main() -> int:
         83 |     print("=" * 64)
  >>>    84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
         85 |     print("=" * 64)
         86 | 
  ```
- **строка 85** — print() вместо logger
  ```
         83 |     print("=" * 64)
         84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
  >>>    85 |     print("=" * 64)
         86 | 
         87 |     ts = int(time.time())
  ```
- **строка 93** — print() вместо logger
  ```
         91 |     ref_path = workdir / "reference.wav"
         92 |     ref_meta = _synthesize_reference(ref_path, duration=15.0, bpm=140)
  >>>    93 |     print(
         94 |         f"[e2e] synthetic reference: {ref_path}  (sr={ref_meta['sr']}, dur={ref_meta['duration']}s)"
         95 |     )
  ```
- **строка 165** — print() вместо logger
  ```
        163 |     )
        164 | 
  >>>   165 |     print()
        166 |     print("─" * 64)
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
  ```
- **строка 166** — print() вместо logger
  ```
        164 | 
        165 |     print()
  >>>   166 |     print("─" * 64)
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
  ```
- **строка 167** — print() вместо logger
  ```
        165 |     print()
        166 |     print("─" * 64)
  >>>   167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
  ```
- **строка 168** — print() вместо logger
  ```
        166 |     print("─" * 64)
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
  >>>   168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
  ```
- **строка 169** — print() вместо logger
  ```
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
  >>>   169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
        171 |     print(f"Release files:      {len(release_check)}")
  ```
- **строка 170** — print() вместо logger
  ```
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
  >>>   170 |     print(f"Masters generated:  {len(stands_check)}/8")
        171 |     print(f"Release files:      {len(release_check)}")
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
  ```
- **строка 171** — print() вместо logger
  ```
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
  >>>   171 |     print(f"Release files:      {len(release_check)}")
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
  ```
- **строка 172** — print() вместо logger
  ```
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
        171 |     print(f"Release files:      {len(release_check)}")
  >>>   172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
        174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
  ```
- **строка 173** — print() вместо logger
  ```
        171 |     print(f"Release files:      {len(release_check)}")
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
  >>>   173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
        174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
        175 |     print()
  ```
- **строка 174** — print() вместо logger
  ```
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
  >>>   174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
        175 |     print()
        176 | 
  ```
- **строка 175** — print() вместо logger
  ```
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
        174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
  >>>   175 |     print()
        176 | 
        177 |     if (
  ```

### `tools/smoke_v26.py` — 6 шт.
- **строка 35** — print() вместо logger
  ```
         33 | def check(name, ok, detail=""):
         34 |     RESULTS.append((name, bool(ok), detail))
  >>>    35 |     print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")
         36 | 
         37 | 
  ```
- **строка 61** — print() вместо logger
  ```
         59 | 
         60 | def main():
  >>>    61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
         63 |     print("=" * 64)
  ```
- **строка 62** — print() вместо logger
  ```
         60 | def main():
         61 |     print("=" * 64)
  >>>    62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
         63 |     print("=" * 64)
         64 | 
  ```
- **строка 63** — print() вместо logger
  ```
         61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
  >>>    63 |     print("=" * 64)
         64 | 
         65 |     res = _run(
  ```
- **строка 177** — print() вместо logger
  ```
        175 |         check("v26.hook_repeat_fallback", False, f"crash: {e}")
        176 | 
  >>>   177 |     print("-" * 64)
        178 |     p = sum(1 for _, o, _ in RESULTS if o)
        179 |     f = len(RESULTS) - p
  ```
- **строка 180** — print() вместо logger
  ```
        178 |     p = sum(1 for _, o, _ in RESULTS if o)
        179 |     f = len(RESULTS) - p
  >>>   180 |     print(f"RESULT: {p} PASS / {f} FAIL / {len(RESULTS)} total")
        181 |     _write_report("smoke_v26", p, f)
        182 |     return 0 if f == 0 else 1
  ```

### `tools/smoke_v29.py` — 7 шт.
- **строка 35** — print() вместо logger
  ```
         33 | def _ok(name: str, extra: str = "") -> None:
         34 |     RESULTS.append((True, name, extra))
  >>>    35 |     print(f"[PASS] {name:40s} {extra}")
         36 | 
         37 | 
  ```
- **строка 40** — print() вместо logger
  ```
         38 | def _fail(name: str, extra: str = "") -> None:
         39 |     RESULTS.append((False, name, extra))
  >>>    40 |     print(f"[FAIL] {name:40s} {extra}")
         41 | 
         42 | 
  ```
- **строка 142** — print() вместо logger
  ```
        140 | 
        141 | def main() -> int:
  >>>   142 |     print("=" * 64)
        143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
        144 |     print("=" * 64)
  ```
- **строка 143** — print() вместо logger
  ```
        141 | def main() -> int:
        142 |     print("=" * 64)
  >>>   143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
        144 |     print("=" * 64)
        145 |     test_version_cli()
  ```
- **строка 144** — print() вместо logger
  ```
        142 |     print("=" * 64)
        143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
  >>>   144 |     print("=" * 64)
        145 |     test_version_cli()
        146 |     test_midi_generator()
  ```
- **строка 149** — print() вместо logger
  ```
        147 |     test_god_mode_e2e()
        148 |     test_mastering_pro_metrics()
  >>>   149 |     print("-" * 64)
        150 |     passed = sum(1 for r in RESULTS if r[0])
        151 |     total = len(RESULTS)
  ```
- **строка 153** — print() вместо logger
  ```
        151 |     total = len(RESULTS)
        152 |     failed = total - passed
  >>>   153 |     print(f"RESULT: {passed} PASS / {failed} FAIL / {total} total")
        154 |     _write_report("smoke_v29", passed, failed)
        155 |     return 0 if failed == 0 else 1
  ```

### `tools/validate_final_track.py` — 11 шт.
- **строка 35** — print() вместо logger
  ```
         33 |         found = _find_latest_master()
         34 |         if not found:
  >>>    35 |             print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
         36 |             print("(мастера в output/**/masters/*.wav не найдены)")
         37 |             return 2
  ```
- **строка 36** — print() вместо logger
  ```
         34 |         if not found:
         35 |             print("USAGE: python tools/validate_final_track.py <path/to/track.wav>")
  >>>    36 |             print("(мастера в output/**/masters/*.wav не найдены)")
         37 |             return 2
         38 |         track_path = found
  ```
- **строка 40** — print() вместо logger
  ```
         38 |         track_path = found
         39 | 
  >>>    40 |     print(f"--- Final Quality Audit for: {track_path} ---")
         41 |     try:
         42 |         if not track_path.exists():
  ```
- **строка 51** — print() вместо logger
  ```
         49 |         channels = data.shape[1] if data.ndim > 1 else 1
         50 | 
  >>>    51 |         print("STATUS: PASS ✅")
         52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
         53 |         print(f"RMS Level: {rms:.4f}")
  ```
- **строка 52** — print() вместо logger
  ```
         50 | 
         51 |         print("STATUS: PASS ✅")
  >>>    52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
         53 |         print(f"RMS Level: {rms:.4f}")
         54 |         print(f"Duration: {duration:.2f}s")
  ```
- **строка 53** — print() вместо logger
  ```
         51 |         print("STATUS: PASS ✅")
         52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
  >>>    53 |         print(f"RMS Level: {rms:.4f}")
         54 |         print(f"Duration: {duration:.2f}s")
         55 |         print(f"Sample Rate: {sr}Hz")
  ```
- **строка 54** — print() вместо logger
  ```
         52 |         print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
         53 |         print(f"RMS Level: {rms:.4f}")
  >>>    54 |         print(f"Duration: {duration:.2f}s")
         55 |         print(f"Sample Rate: {sr}Hz")
         56 |         print(f"Channels: {channels}")
  ```
- **строка 55** — print() вместо logger
  ```
         53 |         print(f"RMS Level: {rms:.4f}")
         54 |         print(f"Duration: {duration:.2f}s")
  >>>    55 |         print(f"Sample Rate: {sr}Hz")
         56 |         print(f"Channels: {channels}")
         57 |         return 0
  ```
- **строка 56** — print() вместо logger
  ```
         54 |         print(f"Duration: {duration:.2f}s")
         55 |         print(f"Sample Rate: {sr}Hz")
  >>>    56 |         print(f"Channels: {channels}")
         57 |         return 0
         58 |     except Exception as e:
  ```
- **строка 59** — print() вместо logger
  ```
         57 |         return 0
         58 |     except Exception as e:
  >>>    59 |         print("STATUS: FAIL ❌")
         60 |         print(f"Error: {e}")
         61 |         return 1
  ```
- **строка 60** — print() вместо logger
  ```
         58 |     except Exception as e:
         59 |         print("STATUS: FAIL ❌")
  >>>    60 |         print(f"Error: {e}")
         61 |         return 1
         62 | 
  ```

### `ui/karaoke_recorder.py` — 5 шт.
- **строка 45** — print() вместо logger
  ```
         43 |         return out
         44 |     except Exception as e:
  >>>    45 |         print(f"[karaoke.metronome] {e}")
         46 |         return ""
         47 | 
  ```
- **строка 72** — print() вместо logger
  ```
         70 |         return True
         71 |     except Exception as e:
  >>>    72 |         print(f"[karaoke.play_backing_track] {e}")
         73 |         return False
         74 | 
  ```
- **строка 97** — print() вместо logger
  ```
         95 |         play_backing_track(backing_path, in_headphones=True)
         96 | 
  >>>    97 |     print(f"[karaoke] Запись {duration_sec} сек в стиле '{style}' — ПОЕХАЛИ!")
         98 |     audio = sd.rec(int(duration_sec * sr), samplerate=sr, channels=1, dtype="float32")
         99 |     sd.wait()
  ```
- **строка 153** — print() вместо logger
  ```
        151 | 
        152 | if __name__ == "__main__":
  >>>   153 |     print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
        154 |     print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
  ```
- **строка 154** — print() вместо logger
  ```
        152 | if __name__ == "__main__":
        153 |     print(json.dumps(get_progress(), ensure_ascii=False, indent=2))
  >>>   154 |     print("Метроном для BPM=140:", build_metronome(140, duration_sec=4))
  ```

### `ui/tutorial.py` — 1 шт.
- **строка 293** — print() вместо logger
  ```
        291 | if __name__ == "__main__":
        292 |     for i, s in enumerate(STEPS):
  >>>   293 |         print(f"{i+1}. {s['title']}")
  ```

### `updater/updater.py` — 6 шт.
- **строка 348** — print() вместо logger
  ```
        346 |         restored = _restore_user_data(prog, moved)
        347 |         if restored:
  >>>   348 |             print(f"[updater] пользовательские данные сохранены: {', '.join(restored)}")
        349 |     except Exception as e:
        350 |         rb = rollback_last()
  ```
- **строка 466** — print() вместо logger
  ```
        464 | 
        465 |     if args.info:
  >>>   466 |         print(
        467 |             json.dumps(
        468 |                 {
  ```
- **строка 480** — print() вместо logger
  ```
        478 |     if args.install:
        479 |         r = install_from_zip(args.install, args.sha256, smoke_test=False)
  >>>   480 |         print(json.dumps(r, indent=2, ensure_ascii=False))
        481 |         return 0 if r.get("ok") else 1
        482 |     if args.rollback:
  ```
- **строка 484** — print() вместо logger
  ```
        482 |     if args.rollback:
        483 |         r = rollback_last()
  >>>   484 |         print(json.dumps(r, indent=2, ensure_ascii=False))
        485 |         return 0 if r.get("ok") else 1
        486 |     if args.list_backups:
  ```
- **строка 487** — print() вместо logger
  ```
        485 |         return 0 if r.get("ok") else 1
        486 |     if args.list_backups:
  >>>   487 |         print(json.dumps(list_backups(), indent=2))
        488 |         return 0
        489 |     if args.check:
  ```
- **строка 490** — print() вместо logger
  ```
        488 |         return 0
        489 |     if args.check:
  >>>   490 |         print(json.dumps(check_updates(args.check), indent=2))
        491 |         return 0
        492 |     ap.print_help()
  ```
