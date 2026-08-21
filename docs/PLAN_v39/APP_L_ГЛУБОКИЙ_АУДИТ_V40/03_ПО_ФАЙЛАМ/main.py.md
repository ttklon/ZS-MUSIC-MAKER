# АУДИТ ФАЙЛА: `main.py`

**LOC:** 585  |  **Размер:** 21781 байт  |  **Проблем:** 23  |  **Risk score:** 24

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 20 | `__future__.annotations` | from |
| 22 | `io` | import |
| 23 | `json` | import |
| 24 | `os` | import |
| 25 | `sys` | import |
| 26 | `traceback` | import |
| 27 | `argparse` | import |
| 28 | `pathlib.Path` | from |
| 140 | `modules.health_v12` | from |
| 156 | `PySide6.QtWidgets.QApplication` | from |
| 161 | `app.gui.theme_v12` | from |
| 162 | `app.gui.wizard.Wizard` | from |
| 163 | `app.hw_probe.probe` | from |
| 164 | `app.logger.setup_logger` | from |
| 165 | `app.runtime_orchestrator.RuntimeOrchestrator` | from |
| 193 | `gradio` | import |
| 198 | `app.core.orchestrator.build_gradio_ui` | from |
| 268 | `app.core.orchestrator.run_full_pipeline` | from |
| 282 | `modules.kpi_dashboard_v12` | from |
| 292 | `modules.self_diag_v13` | from |
| 302 | `tools.real_e2e_v14` | from |
| 312 | `modules.voice_onboarding` | from |
| 328 | `tools.readiness` | from |
| 342 | `config.settings.get_settings` | from |
| 353 | `app.core.orchestrator_god.run_god_pipeline` | from |
| 460 | `modules.genre_engine.StyleRegistry` | from |
| 499 | `app.ai.registry.registry` | from |
| 499 | `app.ai.registry.MODEL_REGISTRY` | from |
| 507 | `tools.pull_ai_models` | from |
| 517 | `modules.artist_dossier.DossierManager` | from |
| 518 | `modules.artist_dossier.collectors.LocalFolderCollector` | from |
| 518 | `modules.artist_dossier.collectors.LyricVaultCollector` | from |
| 530 | `modules.artist_dossier.DossierManager` | from |
| 538 | `app.core.orchestrator_ai.run_ai_pipeline` | from |
| 552 | `asyncio` | import |
| 553 | `app.core.orchestrator_async.AsyncOrchestrator` | from |
| 362 | `modules.genre_engine.StyleRegistry` | from |
| 509 | `app.ai.registry.MODEL_REGISTRY` | from |
| 365 | `difflib` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 34 | `_load_version_info` | 13 | 2 | ❌ |
| 68 | `_setup_console_encoding` | 49 | 7 | ✅ |
| 120 | `_safe_print` | 7 | 2 | ❌ |
| 130 | `_header` | 5 | 0 | ❌ |
| 138 | `_health_snapshot` | 13 | 1 | ❌ |
| 154 | `_try_launch_gui_pyside` | 34 | 5 | ❌ |
| 191 | `_try_launch_gui_gradio` | 17 | 2 | ❌ |
| 220 | `_register_patches` | 25 | 4 | ✅ |
| 248 | `_cli_smoke` | 15 | 3 | ✅ |
| 266 | `_cli_dry_run` | 11 | 1 | ❌ |
| 280 | `_cli_dashboard` | 7 | 2 | ❌ |
| 290 | `_cli_self_diag` | 7 | 2 | ❌ |
| 300 | `_cli_e2e` | 7 | 2 | ❌ |
| 310 | `_cli_onboarding` | 8 | 2 | ❌ |
| 321 | `_cli_health` | 2 | 0 | ❌ |
| 326 | `_cli_readiness` | 11 | 1 | ❌ |
| 340 | `_cli_version` | 8 | 1 | ❌ |
| 351 | `_cli_god` | 33 | 4 | ❌ |
| 387 | `_cli_console` | 27 | 10 | ❌ |
| 417 | `main` | 164 | 35 | ❌ |
| 51 | `__init__` | 4 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 50 | `ProjectContext` | ❌ |

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 10 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

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

### SILENT_EXCEPT_PASS — 7 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 45** — except: pass — тихое подавление ошибок

  ```
         43 |                 str(data.get("build", default_b)),
         44 |             )
  >>>    45 |     except Exception:
         46 |         pass
         47 |     return default_v, default_b
  ```

- **строка 116** — except: pass — тихое подавление ошибок

  ```
        114 |             except Exception:
        115 |                 pass
  >>>   116 |     except Exception:
        117 |         pass
        118 | 
  ```

- **строка 173** — except: pass — тихое подавление ошибок

  ```
        171 |     try:
        172 |         theme_v12.apply(app)
  >>>   173 |     except Exception:
        174 |         pass
        175 |     try:
  ```

- **строка 85** — except: pass — тихое подавление ошибок

  ```
         83 |                 sys.stderr.reconfigure(encoding="utf-8", errors="replace")
         84 |                 return
  >>>    85 |         except Exception:
         86 |             pass
         87 |         try:
  ```

- **строка 372** — except: pass — тихое подавление ошибок

  ```
        370 |                 _safe_print("  full list: python main.py --list-genres")
        371 |                 return 2
  >>>   372 |         except ImportError:
        373 |             pass  # движок жанров недоступен — пусть пайплайн сам решит
        374 | 
  ```

- **строка 126** — except: pass — тихое подавление ошибок

  ```
        124 |         try:
        125 |             sys.stdout.buffer.write((msg + "\n").encode("utf-8", "replace"))
  >>>   126 |         except Exception:
        127 |             pass
        128 | 
  ```

- **строка 114** — except: pass — тихое подавление ошибок

  ```
        112 |                     line_buffering=True,
        113 |                 )
  >>>   114 |             except Exception:
        115 |                 pass
        116 |     except Exception:
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 20** — import 'annotations' не используется в теле файла

  ```
         18 | """
         19 | 
  >>>    20 | from __future__ import annotations
         21 | 
         22 | import io
  ```

### MISSING_CLASS_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 50** — public class 'ProjectContext' без docstring

  ```
         48 | 
         49 | 
  >>>    50 | class ProjectContext:
         51 |     def __init__(self):
         52 |         v, b = _load_version_info()
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 417** — main: 164 LOC (>100) — декомпозиция

  ```
        415 | 
        416 | 
  >>>   417 | def main() -> int:
        418 |     _setup_console_encoding()
        419 |     _header()
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 417** — main: сложность ≈ 35 (>15)

  ```
        415 | 
        416 | 
  >>>   417 | def main() -> int:
        418 |     _setup_console_encoding()
        419 |     _header()
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 417** — public function 'main' без docstring

  ```
        415 | 
        416 | 
  >>>   417 | def main() -> int:
        418 |     _setup_console_encoding()
        419 |     _header()
  ```

### SECURITY_EVAL — 1 шт. — 🔴 CRITICAL
**Смысл:** eval()/exec() — вектор RCE
**Fix:** Убрать. ast.literal_eval или явный парсер.

- **строка 182** — exec() — потенциально опасно

  ```
        180 |         w.setWindowTitle(f"ZS Music Maker v{VERSION} — Desktop Wizard")
        181 |         w.show()
  >>>   182 |         rc = app.exec()
        183 |         raise SystemExit(rc)
        184 |     except SystemExit:
  ```
