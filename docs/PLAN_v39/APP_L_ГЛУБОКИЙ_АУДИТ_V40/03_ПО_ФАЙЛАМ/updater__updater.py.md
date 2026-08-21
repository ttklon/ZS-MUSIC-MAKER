# АУДИТ ФАЙЛА: `updater/updater.py`

**LOC:** 497  |  **Размер:** 18568 байт  |  **Проблем:** 24  |  **Risk score:** 17

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 22 | `__future__.annotations` | from |
| 24 | `hashlib` | import |
| 25 | `json` | import |
| 26 | `os` | import |
| 27 | `shutil` | import |
| 28 | `subprocess` | import |
| 29 | `sys` | import |
| 30 | `time` | import |
| 31 | `zipfile` | import |
| 32 | `pathlib.Path` | from |
| 33 | `typing.Any` | from |
| 454 | `argparse` | import |
| 444 | `urllib.request` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 36 | `program_dir` | 16 | 3 | ❌ |
| 55 | `user_data_dir` | 10 | 3 | ❌ |
| 68 | `backup_dir` | 3 | 0 | ❌ |
| 74 | `staging_dir` | 3 | 0 | ❌ |
| 99 | `_stash_user_data` | 21 | 3 | ✅ |
| 123 | `_restore_user_data` | 27 | 4 | ✅ |
| 153 | `ensure_user_dirs` | 13 | 1 | ❌ |
| 169 | `compute_sha256` | 5 | 2 | ❌ |
| 177 | `verify_zip` | 43 | 11 | ❌ |
| 223 | `make_backup` | 19 | 7 | ❌ |
| 245 | `prune_old_backups` | 12 | 2 | ❌ |
| 260 | `list_backups` | 7 | 0 | ❌ |
| 270 | `migrate_settings` | 25 | 4 | ❌ |
| 298 | `install_from_zip` | 98 | 18 | ❌ |
| 399 | `rollback_last` | 40 | 10 | ❌ |
| 442 | `check_updates` | 8 | 2 | ❌ |
| 453 | `main` | 40 | 5 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 9 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 36** — public function 'program_dir' без docstring

  ```
         34 | 
         35 | 
  >>>    36 | def program_dir() -> Path:
         37 |     env = os.environ.get("ZSMM_PROGRAM_DIR")
         38 |     if env:
  ```

- **строка 153** — public function 'ensure_user_dirs' без docstring

  ```
        151 | 
        152 | 
  >>>   153 | def ensure_user_dirs() -> None:
        154 |     root = user_data_dir()
        155 |     root.mkdir(parents=True, exist_ok=True)
  ```

- **строка 177** — public function 'verify_zip' без docstring

  ```
        175 | 
        176 | 
  >>>   177 | def verify_zip(zip_path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
        178 |     result: dict[str, Any] = {"ok": False, "sha256": None, "size": 0, "checks": {}}
        179 |     p = Path(zip_path)
  ```

- **строка 223** — public function 'make_backup' без docstring

  ```
        221 | 
        222 | 
  >>>   223 | def make_backup(reason: str = "pre_update") -> Path | None:
        224 |     src = program_dir()
        225 |     if not src.exists():
  ```

- **строка 245** — public function 'prune_old_backups' без docstring

  ```
        243 | 
        244 | 
  >>>   245 | def prune_old_backups(keep: int = 3) -> list[Path]:
        246 |     bd = backup_dir()
        247 |     backups = sorted(
  ```

- **строка 270** — public function 'migrate_settings' без docstring

  ```
        268 | 
        269 | 
  >>>   270 | def migrate_settings(old_path: Path, new_path: Path) -> dict[str, Any]:
        271 |     conflicts = []
        272 |     try:
  ```

- **строка 298** — public function 'install_from_zip' без docstring

  ```
        296 | 
        297 | 
  >>>   298 | def install_from_zip(
        299 |     zip_path: str, expected_sha256: str | None = None, smoke_test: bool = True
        300 | ) -> dict[str, Any]:
  ```

- **строка 399** — public function 'rollback_last' без docstring

  ```
        397 | 
        398 | 
  >>>   399 | def rollback_last() -> dict[str, Any]:
        400 |     bd = backup_dir()
        401 |     backups = sorted(
  ```

- **строка 453** — public function 'main' без docstring

  ```
        451 | 
        452 | 
  >>>   453 | def main() -> int:
        454 |     import argparse
        455 | 
  ```

### SILENT_EXCEPT_PASS — 7 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 394** — except: pass — тихое подавление ошибок

  ```
        392 |                 "version", "unknown"
        393 |             )
  >>>   394 |     except Exception:
        395 |         pass
        396 |     return {"ok": True, "version": ver, "backup": str(bak)}
  ```

- **строка 117** — except: pass — тихое подавление ошибок

  ```
        115 |             shutil.move(str(src), str(dst))
        116 |             moved[rel] = dst
  >>>   117 |         except Exception:
        118 |             # не смогли переместить — оставляем на месте (не валим установку)
        119 |             pass
  ```

- **строка 148** — except: pass — тихое подавление ошибок

  ```
        146 |                 shutil.move(str(stash), str(dst))
        147 |             restored.append(rel)
  >>>   148 |         except Exception:
        149 |             pass
        150 |     return restored
  ```

- **строка 255** — except: pass — тихое подавление ошибок

  ```
        253 |             old.unlink()
        254 |             removed.append(old)
  >>>   255 |         except Exception:
        256 |             pass
        257 |     return removed
  ```

- **строка 384** — except: pass — тихое подавление ошибок

  ```
        382 |                 "backup": str(bak),
        383 |             }
  >>>   384 |         except Exception:
        385 |             pass
        386 | 
  ```

- **строка 424** — except: pass — тихое подавление ошибок

  ```
        422 |                 shutil.move(str(src), str(dst))
        423 |                 moved[rel] = dst
  >>>   424 |             except Exception:
        425 |                 pass
        426 |         for item in prog.iterdir():
  ```

- **строка 239** — except: pass — тихое подавление ошибок

  ```
        237 |                 try:
        238 |                     z.write(str(fp), fp.relative_to(src))
  >>>   239 |                 except Exception:
        240 |                     pass
        241 |     prune_old_backups(keep=3)
  ```

### BARE_PRINT — 6 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

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

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 22** — import 'annotations' не используется в теле файла

  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import hashlib
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 298** — install_from_zip: сложность ≈ 18 (>15)

  ```
        296 | 
        297 | 
  >>>   298 | def install_from_zip(
        299 |     zip_path: str, expected_sha256: str | None = None, smoke_test: bool = True
        300 | ) -> dict[str, Any]:
  ```
