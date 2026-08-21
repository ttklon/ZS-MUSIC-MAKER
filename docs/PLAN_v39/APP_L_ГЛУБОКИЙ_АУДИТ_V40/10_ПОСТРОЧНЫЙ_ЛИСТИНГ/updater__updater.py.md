# ПОСТРОЧНЫЙ ЛИСТИНГ: `updater/updater.py`

**Всего строк:** 497

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 222 | 44.7 |
| blank | 57 | 11.5 |
| branch | 46 | 9.3 |
| return | 43 | 8.7 |
| docstring | 29 | 5.8 |
| try_block | 29 | 5.8 |
| comment | 21 | 4.2 |
| def | 17 | 3.4 |
| import | 13 | 2.6 |
| loop | 12 | 2.4 |
| stmt | 7 | 1.4 |
| raise | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] r"""
    2 [docstring ] ZS Music Maker v14 — updater/updater.py (P0.10..P0.13, TZ 31)
    3 [docstring ] ==============================================================
    4 [blank     ] 
    5 [docstring ]   P0.10 — разделение program vs user data.
    6 [docstring ]   P0.11 — автообновление из ZIP.
    7 [docstring ]   P0.12 — резервное копирование перед обновлением (последние 3).
    8 [docstring ]   P0.13 — автоматический откат при сбое.
    9 [blank     ] 
   10 [docstring ] Реализовано:
   11 [docstring ]   install_from_zip(zip_path)   — установка новой версии из ZIP;
   12 [docstring ]   rollback_last()              — откат к предыдущей версии;
   13 [docstring ]   check_updates(url)           — проверка новой версии;
   14 [docstring ]   verify_zip(path, sha256)     — проверка SHA-256;
   15 [docstring ]   user_data_dir()              — путь к %LOCALAPPDATA%\ZS Music Maker;
   16 [docstring ]   program_dir()                — путь установки программы.
   17 [blank     ] 
   18 [docstring ] Пользовательские данные (voice_vault, lyric_vault, projects, settings.json,
   19 [docstring ] secrets.enc, presets, prompts, output, cache, logs) НЕ ТРОГАЕМ при обновлении.
   20 [docstring ] """
   21 [blank     ] 
   22 [import    ] from __future__ import annotations
   23 [blank     ] 
   24 [import    ] import hashlib
   25 [import    ] import json
   26 [import    ] import os
   27 [import    ] import shutil
   28 [import    ] import subprocess
   29 [import    ] import sys
   30 [import    ] import time
   31 [import    ] import zipfile
   32 [import    ] from pathlib import Path
   33 [import    ] from typing import Any
   34 [blank     ] 
   35 [blank     ] 
   36 [def       ] def program_dir() -> Path:
   37 [code      ]     env = os.environ.get("ZSMM_PROGRAM_DIR")
   38 [branch    ]     if env:
   39 [return    ]         return Path(env)
   40 [comment   ]     # v37 FIX: раньше на win32 всегда возвращался 'C:\Program Files\ZS Music Maker',
   41 [comment   ]     # хотя репо ставится клонированием в ЛЮБУЮ папку. Это приводило к тому, что
   42 [comment   ]     # backup/rollback/install работали с несуществующим каталогом.
   43 [comment   ]     # Теперь: если текущий корень проекта (рядом с updater/) выглядит как установка
   44 [comment   ]     # (есть main.py) — используем ЕГО; 'Program Files' остаётся только для случая,
   45 [comment   ]     # когда updater вызван не из дерева проекта.
   46 [code      ]     root = Path(__file__).resolve().parents[1]
   47 [branch    ]     if (root / "main.py").exists():
   48 [return    ]         return root
   49 [branch    ]     if sys.platform == "win32":
   50 [code      ]         pf = os.environ.get("ProgramFiles", r"C:\Program Files")
   51 [return    ]         return Path(pf) / "ZS Music Maker"
   52 [return    ]     return root
   53 [blank     ] 
   54 [blank     ] 
   55 [def       ] def user_data_dir() -> Path:
   56 [code      ]     env = os.environ.get("ZSMM_USER_DIR")
   57 [branch    ]     if env:
   58 [return    ]         return Path(env)
   59 [branch    ]     if sys.platform == "win32":
   60 [code      ]         appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
   61 [return    ]         return Path(appdata) / "ZS Music Maker"
   62 [branch    ]     if sys.platform == "darwin":
   63 [return    ]         return Path.home() / "Library" / "Application Support" / "ZS Music Maker"
   64 [code      ]     xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
   65 [return    ]     return Path(xdg) / "zsmm"
   66 [blank     ] 
   67 [blank     ] 
   68 [def       ] def backup_dir() -> Path:
   69 [code      ]     d = program_dir() / "updater" / "backup"
   70 [code      ]     d.mkdir(parents=True, exist_ok=True)
   71 [return    ]     return d
   72 [blank     ] 
   73 [blank     ] 
   74 [def       ] def staging_dir() -> Path:
   75 [code      ]     d = program_dir() / "updater" / "backup" / "staging"
   76 [code      ]     d.mkdir(parents=True, exist_ok=True)
   77 [return    ]     return d
   78 [blank     ] 
   79 [blank     ] 
   80 [comment   ] # Каталоги/файлы ПОЛЬЗОВАТЕЛЯ, которые НЕЛЬЗЯ затирать при обновлении из ZIP.
   81 [comment   ] # v37 FIX: раньше список только объявлялся, но НИГДЕ не применялся — install
   82 [comment   ] # удалял всё подряд. Плюс 'presets'/'prompts' в реальном layout репо лежат в
   83 [comment   ] # data/genre_presets и data/prompts — старые имена сохранить было невозможно.
   84 [code      ] USER_PRESERVED = [
   85 [code      ]     "projects",
   86 [code      ]     "voice_vault",
   87 [code      ]     "lyric_vault",
   88 [code      ]     "data/genre_presets",
   89 [code      ]     "data/prompts",
   90 [code      ]     "data/tutorial_settings.json",
   91 [code      ]     "secrets.enc",
   92 [code      ]     "settings.json",
   93 [code      ]     "output",
   94 [code      ]     "cache",
   95 [code      ]     "logs",
   96 [code      ] ]
   97 [blank     ] 
   98 [blank     ] 
   99 [def       ] def _stash_user_data(prog: Path, stg: Path) -> dict[str, Path]:
  100 [docstring ]     """Перед заменой: переносим USER_PRESERVED из prog в staging-зону.
  101 [blank     ] 
  102 [docstring ]     v37: раньше USER_PRESERVED игнорировался — install просто делал rmtree
  103 [docstring ]     всего каталога и пользователь терял voice_vault/lyric_vault/output.
  104 [docstring ]     Возвращает мапу rel_path -> stash_path, чтобы _restore_user_data вернул всё назад.
  105 [docstring ]     """
  106 [code      ]     stash_root = stg / ".user_stash"
  107 [code      ]     moved: dict[str, Path] = {}
  108 [loop      ]     for rel in USER_PRESERVED:
  109 [code      ]         src = prog / rel
  110 [branch    ]         if not src.exists():
  111 [code      ]             continue
  112 [code      ]         dst = stash_root / rel
  113 [code      ]         dst.parent.mkdir(parents=True, exist_ok=True)
  114 [try_block ]         try:
  115 [code      ]             shutil.move(str(src), str(dst))
  116 [code      ]             moved[rel] = dst
  117 [try_block ]         except Exception:
  118 [comment   ]             # не смогли переместить — оставляем на месте (не валим установку)
  119 [code      ]             pass
  120 [return    ]     return moved
  121 [blank     ] 
  122 [blank     ] 
  123 [def       ] def _restore_user_data(prog: Path, moved: dict[str, Path]) -> list[str]:
  124 [docstring ]     """После распаковки новой версии: возвращаем сохранённые данные на место.
  125 [blank     ] 
  126 [docstring ]     v37: MERGE-семантика вместо затирания. Если новая версия принесла свой
  127 [docstring ]     каталог (например свежие дефолтные пресеты в data/genre_presets) — юзерские
  128 [docstring ]     файлы накладываются ПОВЕРХ, а новые дефолтные СОХРАНЯЮТСЯ. Так не теряются
  129 [docstring ]     ни пользовательские данные, ни обновлённые пресеты из дистрибутива.
  130 [docstring ]     Возвращает список rel-путей, которые удалось восстановить.
  131 [docstring ]     """
  132 [code      ]     restored: list[str] = []
  133 [loop      ]     for rel, stash in moved.items():
  134 [code      ]         dst = prog / rel
  135 [code      ]         dst.parent.mkdir(parents=True, exist_ok=True)
  136 [try_block ]         try:
  137 [branch    ]             if stash.is_dir():
  138 [comment   ]                 # merge: копируем юзерское содержимое поверх нового каталога
  139 [comment   ]                 # (dirs_exist_ok=True — не удаляем новые дефолтные файлы)
  140 [code      ]                 shutil.copytree(str(stash), str(dst), dirs_exist_ok=True)
  141 [code      ]                 shutil.rmtree(str(stash), ignore_errors=True)
  142 [branch    ]             else:
  143 [comment   ]                 # файл: юзерский приоритетнее нового дефолтного
  144 [branch    ]                 if dst.exists():
  145 [code      ]                     dst.unlink()
  146 [code      ]                 shutil.move(str(stash), str(dst))
  147 [code      ]             restored.append(rel)
  148 [try_block ]         except Exception:
  149 [code      ]             pass
  150 [return    ]     return restored
  151 [blank     ] 
  152 [blank     ] 
  153 [def       ] def ensure_user_dirs() -> None:
  154 [code      ]     root = user_data_dir()
  155 [code      ]     root.mkdir(parents=True, exist_ok=True)
  156 [loop      ]     for sub in (
  157 [code      ]         "projects",
  158 [code      ]         "voice_vault",
  159 [code      ]         "lyric_vault",
  160 [code      ]         "presets",
  161 [code      ]         "prompts",
  162 [code      ]         "output",
  163 [code      ]         "cache",
  164 [code      ]         "logs",
  165 [code      ]     ):
  166 [code      ]         (root / sub).mkdir(parents=True, exist_ok=True)
  167 [blank     ] 
  168 [blank     ] 
  169 [def       ] def compute_sha256(path: Path) -> str:
  170 [code      ]     h = hashlib.sha256()
  171 [stmt      ]     with open(path, "rb") as f:
  172 [loop      ]         for chunk in iter(lambda: f.read(8192), b""):
  173 [code      ]             h.update(chunk)
  174 [return    ]     return h.hexdigest()
  175 [blank     ] 
  176 [blank     ] 
  177 [def       ] def verify_zip(zip_path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
  178 [code      ]     result: dict[str, Any] = {"ok": False, "sha256": None, "size": 0, "checks": {}}
  179 [code      ]     p = Path(zip_path)
  180 [branch    ]     if not p.exists():
  181 [code      ]         result["reason"] = "zip not found"
  182 [return    ]         return result
  183 [code      ]     result["size"] = p.stat().st_size
  184 [branch    ]     if result["size"] < 1024:
  185 [code      ]         result["reason"] = "zip too small (<1KB)"
  186 [return    ]         return result
  187 [branch    ]     if result["size"] > 5 * 1024**3:
  188 [code      ]         result["reason"] = "zip too large (>5GB)"
  189 [return    ]         return result
  190 [code      ]     sha = compute_sha256(p)
  191 [code      ]     result["sha256"] = sha
  192 [code      ]     result["checks"]["sha256_computed"] = True
  193 [branch    ]     if expected_sha256:
  194 [branch    ]         if sha.lower() != expected_sha256.lower():
  195 [code      ]             result["reason"] = "sha256 mismatch"
  196 [return    ]             return result
  197 [code      ]         result["checks"]["sha256_match"] = True
  198 [blank     ] 
  199 [try_block ]     try:
  200 [stmt      ]         with zipfile.ZipFile(str(p), "r") as z:
  201 [code      ]             names = set(z.namelist())
  202 [try_block ]     except zipfile.BadZipFile:
  203 [code      ]         result["reason"] = "corrupted zip"
  204 [return    ]         return result
  205 [blank     ] 
  206 [comment   ]     # v37 FIX: раньше verify требовал TZ.txt/PROMPT.txt — этих файлов НЕТ
  207 [comment   ]     # в репозитории, поэтому updater отвергал ЛЮБОЙ реальный дистрибутив.
  208 [comment   ]     # Проверяем реальные маркеры проекта: main.py, version.json, modules/.
  209 [code      ]     has_main = any(n.endswith("main.py") and not n.startswith("docs/") for n in names)
  210 [code      ]     has_version = any(n.endswith("version.json") for n in names)
  211 [code      ]     has_modules = any(n.startswith("modules/") and n.endswith(".py") for n in names)
  212 [code      ]     result["checks"]["has_main_py"] = has_main
  213 [code      ]     result["checks"]["has_version_json"] = has_version
  214 [code      ]     result["checks"]["has_modules"] = has_modules
  215 [branch    ]     if not (has_main and has_version and has_modules):
  216 [code      ]         result["reason"] = "zip missing required files: main.py/version.json/modules/"
  217 [return    ]         return result
  218 [blank     ] 
  219 [code      ]     result["ok"] = True
  220 [return    ]     return result
  221 [blank     ] 
  222 [blank     ] 
  223 [def       ] def make_backup(reason: str = "pre_update") -> Path | None:
  224 [code      ]     src = program_dir()
  225 [branch    ]     if not src.exists():
  226 [return    ]         return None
  227 [code      ]     ts = time.strftime("%Y%m%d_%H%M%S")
  228 [code      ]     dst = backup_dir() / f"backup_{ts}_{reason}.zip"
  229 [stmt      ]     with zipfile.ZipFile(str(dst), "w", zipfile.ZIP_DEFLATED) as z:
  230 [loop      ]         for root, dirs, files in os.walk(src):
  231 [branch    ]             if "updater/backup" in root.replace("\\", "/"):
  232 [code      ]                 continue
  233 [branch    ]             if "__pycache__" in root:
  234 [code      ]                 continue
  235 [loop      ]             for f in files:
  236 [code      ]                 fp = Path(root) / f
  237 [try_block ]                 try:
  238 [code      ]                     z.write(str(fp), fp.relative_to(src))
  239 [try_block ]                 except Exception:
  240 [code      ]                     pass
  241 [code      ]     prune_old_backups(keep=3)
  242 [return    ]     return dst
  243 [blank     ] 
  244 [blank     ] 
  245 [def       ] def prune_old_backups(keep: int = 3) -> list[Path]:
  246 [code      ]     bd = backup_dir()
  247 [code      ]     backups = sorted(
  248 [code      ]         bd.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
  249 [code      ]     )
  250 [code      ]     removed = []
  251 [loop      ]     for old in backups[keep:]:
  252 [try_block ]         try:
  253 [code      ]             old.unlink()
  254 [code      ]             removed.append(old)
  255 [try_block ]         except Exception:
  256 [code      ]             pass
  257 [return    ]     return removed
  258 [blank     ] 
  259 [blank     ] 
  260 [def       ] def list_backups() -> list[dict[str, Any]]:
  261 [code      ]     bd = backup_dir()
  262 [return    ]     return [
  263 [code      ]         {"path": str(p), "size": p.stat().st_size, "mtime": p.stat().st_mtime}
  264 [loop      ]         for p in sorted(
  265 [code      ]             bd.glob("backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True
  266 [code      ]         )
  267 [code      ]     ]
  268 [blank     ] 
  269 [blank     ] 
  270 [def       ] def migrate_settings(old_path: Path, new_path: Path) -> dict[str, Any]:
  271 [code      ]     conflicts = []
  272 [try_block ]     try:
  273 [code      ]         old = (
  274 [code      ]             json.loads(old_path.read_text(encoding="utf-8"))
  275 [branch    ]             if old_path.exists()
  276 [code      ]             else {}
  277 [code      ]         )
  278 [try_block ]     except Exception as e:
  279 [code      ]         old = {}
  280 [code      ]         conflicts.append(f"read old: {e}")
  281 [code      ]     merged = dict(old)
  282 [try_block ]     try:
  283 [code      ]         new_path.parent.mkdir(parents=True, exist_ok=True)
  284 [code      ]         new_path.write_text(
  285 [code      ]             json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
  286 [code      ]         )
  287 [try_block ]     except Exception as e:
  288 [code      ]         conflicts.append(f"write new: {e}")
  289 [code      ]     log_p = user_data_dir() / "logs" / "migration_conflicts.log"
  290 [branch    ]     if conflicts:
  291 [code      ]         log_p.parent.mkdir(parents=True, exist_ok=True)
  292 [stmt      ]         with open(log_p, "a", encoding="utf-8") as f:
  293 [code      ]             f.write(f"=== migration @ {time.ctime()} ===\n")
  294 [code      ]             f.writelines(c + "\n" for c in conflicts)
  295 [return    ]     return {"ok": len(conflicts) == 0, "conflicts": conflicts}
  296 [blank     ] 
  297 [blank     ] 
  298 [def       ] def install_from_zip(
  299 [code      ]     zip_path: str, expected_sha256: str | None = None, smoke_test: bool = True
  300 [code      ] ) -> dict[str, Any]:
  301 [code      ]     zip_p = Path(zip_path)
  302 [code      ]     prog = program_dir()
  303 [blank     ] 
  304 [code      ]     v = verify_zip(zip_p, expected_sha256)
  305 [branch    ]     if not v.get("ok"):
  306 [return    ]         return {
  307 [code      ]             "ok": False,
  308 [code      ]             "stage": "verify",
  309 [code      ]             "error": v.get("reason", "verification failed"),
  310 [code      ]             "verify": v,
  311 [code      ]         }
  312 [blank     ] 
  313 [code      ]     bak = make_backup(reason="pre_install")
  314 [branch    ]     if bak is None:
  315 [return    ]         return {"ok": False, "stage": "backup", "error": "backup failed"}
  316 [blank     ] 
  317 [code      ]     stg = staging_dir()
  318 [branch    ]     if stg.exists():
  319 [code      ]         shutil.rmtree(stg)
  320 [code      ]     stg.mkdir(parents=True, exist_ok=True)
  321 [try_block ]     try:
  322 [stmt      ]         with zipfile.ZipFile(str(zip_p), "r") as z:
  323 [code      ]             z.extractall(str(stg))
  324 [try_block ]     except Exception as e:
  325 [return    ]         return {"ok": False, "stage": "extract", "error": str(e), "backup": str(bak)}
  326 [blank     ] 
  327 [try_block ]     try:
  328 [comment   ]         # v37 FIX: сохраняем пользовательские данные ДО очистки каталога.
  329 [code      ]         moved = _stash_user_data(prog, stg)
  330 [loop      ]         for item in prog.iterdir():
  331 [branch    ]             if item.name == "updater":
  332 [code      ]                 continue
  333 [branch    ]             if item.is_dir():
  334 [code      ]                 shutil.rmtree(item, ignore_errors=True)
  335 [branch    ]             else:
  336 [code      ]                 item.unlink()
  337 [loop      ]         for item in stg.iterdir():
  338 [branch    ]             if item.name == ".user_stash":  # это наши же сохранённые данные, не копируем как часть дистрибутива
  339 [code      ]                 continue
  340 [code      ]             dst = prog / item.name
  341 [branch    ]             if item.is_dir():
  342 [code      ]                 shutil.copytree(str(item), str(dst))
  343 [branch    ]             else:
  344 [code      ]                 shutil.copy2(str(item), str(dst))
  345 [comment   ]         # v37 FIX: возвращаем пользовательские данные поверх новой версии.
  346 [code      ]         restored = _restore_user_data(prog, moved)
  347 [branch    ]         if restored:
  348 [code      ]             print(f"[updater] пользовательские данные сохранены: {', '.join(restored)}")
  349 [try_block ]     except Exception as e:
  350 [code      ]         rb = rollback_last()
  351 [return    ]         return {
  352 [code      ]             "ok": False,
  353 [code      ]             "stage": "replace",
  354 [code      ]             "error": str(e),
  355 [code      ]             "rolled_back": rb.get("ok", False),
  356 [code      ]             "backup": str(bak),
  357 [code      ]         }
  358 [blank     ] 
  359 [branch    ]     if smoke_test:
  360 [try_block ]         try:
  361 [code      ]             r = subprocess.run(
  362 [code      ]                 [sys.executable, str(prog / "main.py"), "--smoke"],
  363 [code      ]                 capture_output=True,
  364 [code      ]                 timeout=180,
  365 [code      ]             )
  366 [branch    ]             if r.returncode != 0:
  367 [code      ]                 rb = rollback_last()
  368 [return    ]                 return {
  369 [code      ]                     "ok": False,
  370 [code      ]                     "stage": "smoke_test",
  371 [code      ]                     "error": f"smoke failed rc={r.returncode}",
  372 [code      ]                     "rolled_back": rb.get("ok", False),
  373 [code      ]                     "backup": str(bak),
  374 [code      ]                 }
  375 [try_block ]         except subprocess.TimeoutExpired:
  376 [code      ]             rb = rollback_last()
  377 [return    ]             return {
  378 [code      ]                 "ok": False,
  379 [code      ]                 "stage": "smoke_test",
  380 [code      ]                 "error": "smoke timeout",
  381 [code      ]                 "rolled_back": rb.get("ok", False),
  382 [code      ]                 "backup": str(bak),
  383 [code      ]             }
  384 [try_block ]         except Exception:
  385 [code      ]             pass
  386 [blank     ] 
  387 [code      ]     ver_p = prog / "version.json"
  388 [code      ]     ver = "unknown"
  389 [try_block ]     try:
  390 [branch    ]         if ver_p.exists():
  391 [code      ]             ver = json.loads(ver_p.read_text(encoding="utf-8")).get(
  392 [code      ]                 "version", "unknown"
  393 [code      ]             )
  394 [try_block ]     except Exception:
  395 [code      ]         pass
  396 [return    ]     return {"ok": True, "version": ver, "backup": str(bak)}
  397 [blank     ] 
  398 [blank     ] 
  399 [def       ] def rollback_last() -> dict[str, Any]:
  400 [code      ]     bd = backup_dir()
  401 [code      ]     backups = sorted(
  402 [code      ]         bd.glob("backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True
  403 [code      ]     )
  404 [branch    ]     if not backups:
  405 [return    ]         return {"ok": False, "error": "no backups"}
  406 [code      ]     last = backups[0]
  407 [code      ]     prog = program_dir()
  408 [try_block ]     try:
  409 [comment   ]         # v37 FIX: rollback тоже не должен затирать пользовательские данные.
  410 [comment   ]         # Стэшим во временный каталог РЯДОМ с prog (не в backup_dir — туда rollback не смотрит).
  411 [code      ]         stash_root = prog / ".rollback_stash"
  412 [branch    ]         if stash_root.exists():
  413 [code      ]             shutil.rmtree(stash_root, ignore_errors=True)
  414 [code      ]         moved: dict[str, Path] = {}
  415 [loop      ]         for rel in USER_PRESERVED:
  416 [code      ]             src = prog / rel
  417 [branch    ]             if not src.exists():
  418 [code      ]                 continue
  419 [code      ]             dst = stash_root / rel
  420 [code      ]             dst.parent.mkdir(parents=True, exist_ok=True)
  421 [try_block ]             try:
  422 [code      ]                 shutil.move(str(src), str(dst))
  423 [code      ]                 moved[rel] = dst
  424 [try_block ]             except Exception:
  425 [code      ]                 pass
  426 [loop      ]         for item in prog.iterdir():
  427 [branch    ]             if item.name in ("updater", ".rollback_stash"):
  428 [code      ]                 continue
  429 [branch    ]             if item.is_dir():
  430 [code      ]                 shutil.rmtree(item, ignore_errors=True)
  431 [branch    ]             else:
  432 [code      ]                 item.unlink()
  433 [stmt      ]         with zipfile.ZipFile(str(last), "r") as z:
  434 [code      ]             z.extractall(str(prog))
  435 [code      ]         restored = _restore_user_data(prog, moved)
  436 [code      ]         shutil.rmtree(stash_root, ignore_errors=True)
  437 [return    ]         return {"ok": True, "restored_from": str(last), "user_data_preserved": restored}
  438 [try_block ]     except Exception as e:
  439 [return    ]         return {"ok": False, "error": str(e)}
  440 [blank     ] 
  441 [blank     ] 
  442 [def       ] def check_updates(release_url: str) -> dict[str, Any]:
  443 [try_block ]     try:
  444 [import    ]         import urllib.request as urlreq
  445 [blank     ] 
  446 [stmt      ]         with urlreq.urlopen(release_url, timeout=15) as resp:
  447 [code      ]             data = json.loads(resp.read().decode("utf-8"))
  448 [try_block ]     except Exception as e:
  449 [return    ]         return {"ok": False, "reason": str(e)}
  450 [return    ]     return {"ok": True, "data": data}
  451 [blank     ] 
  452 [blank     ] 
  453 [def       ] def main() -> int:
  454 [import    ]     import argparse
  455 [blank     ] 
  456 [code      ]     ap = argparse.ArgumentParser("zsmm-updater")
  457 [code      ]     ap.add_argument("--install", help="Установить из ZIP")
  458 [code      ]     ap.add_argument("--sha256", help="Ожидаемый SHA-256")
  459 [code      ]     ap.add_argument("--rollback", action="store_true")
  460 [code      ]     ap.add_argument("--list-backups", action="store_true")
  461 [code      ]     ap.add_argument("--check", help="URL проверки обновлений")
  462 [code      ]     ap.add_argument("--info", action="store_true")
  463 [code      ]     args = ap.parse_args()
  464 [blank     ] 
  465 [branch    ]     if args.info:
  466 [code      ]         print(
  467 [code      ]             json.dumps(
  468 [code      ]                 {
  469 [code      ]                     "program_dir": str(program_dir()),
  470 [code      ]                     "user_data_dir": str(user_data_dir()),
  471 [code      ]                     "backup_dir": str(backup_dir()),
  472 [code      ]                     "user_preserved": USER_PRESERVED,
  473 [code      ]                 },
  474 [code      ]                 indent=2,
  475 [code      ]             )
  476 [code      ]         )
  477 [return    ]         return 0
  478 [branch    ]     if args.install:
  479 [code      ]         r = install_from_zip(args.install, args.sha256, smoke_test=False)
  480 [code      ]         print(json.dumps(r, indent=2, ensure_ascii=False))
  481 [return    ]         return 0 if r.get("ok") else 1
  482 [branch    ]     if args.rollback:
  483 [code      ]         r = rollback_last()
  484 [code      ]         print(json.dumps(r, indent=2, ensure_ascii=False))
  485 [return    ]         return 0 if r.get("ok") else 1
  486 [branch    ]     if args.list_backups:
  487 [code      ]         print(json.dumps(list_backups(), indent=2))
  488 [return    ]         return 0
  489 [branch    ]     if args.check:
  490 [code      ]         print(json.dumps(check_updates(args.check), indent=2))
  491 [return    ]         return 0
  492 [code      ]     ap.print_help()
  493 [return    ]     return 0
  494 [blank     ] 
  495 [blank     ] 
  496 [branch    ] if __name__ == "__main__":
  497 [raise     ]     raise SystemExit(main())
```