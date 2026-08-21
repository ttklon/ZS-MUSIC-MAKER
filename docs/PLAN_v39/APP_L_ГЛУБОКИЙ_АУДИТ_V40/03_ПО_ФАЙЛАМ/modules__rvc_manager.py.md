# АУДИТ ФАЙЛА: `modules/rvc_manager.py`

**LOC:** 481  |  **Размер:** 18163 байт  |  **Проблем:** 13  |  **Risk score:** 13

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 17 | `__future__.annotations` | from |
| 19 | `json` | import |
| 20 | `shutil` | import |
| 21 | `subprocess` | import |
| 22 | `sys` | import |
| 23 | `threading` | import |
| 24 | `time` | import |
| 25 | `collections.abc.Callable` | from |
| 26 | `dataclasses.asdict` | from |
| 26 | `dataclasses.dataclass` | from |
| 27 | `pathlib.Path` | from |
| 74 | `torch` | import |
| 88 | `torch_directml` | import |
| 103 | `torch` | import |
| 221 | `modules.voice_convert` | from |
| 419 | `rvc_python.infer.infer_file` | from |
| 141 | `rvc_python` | import |
| 277 | `rvc_python` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 45 | `_load_state` | 6 | 2 | ❌ |
| 54 | `_save_state` | 1 | 0 | ❌ |
| 69 | `detect_backend` | 52 | 6 | ✅ |
| 125 | `ensure_fork` | 54 | 7 | ✅ |
| 396 | `infer` | 55 | 6 | ✅ |
| 454 | `_fallback_pitch` | 10 | 0 | ✅ |
| 467 | `get_state` | 2 | 0 | ✅ |
| 472 | `is_trained` | 1 | 0 | ❌ |
| 133 | `_p` | 3 | 1 | ❌ |
| 203 | `__init__` | 4 | 1 | ❌ |
| 209 | `on_progress` | 1 | 0 | ❌ |
| 212 | `_emit` | 5 | 2 | ❌ |
| 219 | `_dataset_ready` | 16 | 4 | ✅ |
| 237 | `train` | 21 | 0 | ✅ |
| 260 | `_run` | 71 | 6 | ❌ |
| 333 | `_run_with_progress` | 31 | 5 | ✅ |
| 366 | `_train_via_fork` | 26 | 2 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 60 | `RVCBackend` | ❌ |
| 184 | `TrainingJob` | ❌ |
| 196 | `RVCTrainer` | ✅ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 6 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 84** — except: pass — тихое подавление ошибок

  ```
         82 |             b.reason = "CUDA available"
         83 |             return b
  >>>    84 |     except Exception:
         85 |         pass
         86 |     # 2) DirectML (AMD/Intel iGPU на Windows)
  ```

- **строка 99** — except: pass — тихое подавление ошибок

  ```
         97 |         b.reason = "DirectML available"
         98 |         return b
  >>>    99 |     except Exception:
        100 |         pass
        101 |     # 3) ROCm (Linux, редко)
  ```

- **строка 113** — except: pass — тихое подавление ошибок

  ```
        111 |             b.reason = "ROCm available"
        112 |             return b
  >>>   113 |     except Exception:
        114 |         pass
        115 |     # 4) CPU fallback
  ```

- **строка 216** — except: pass — тихое подавление ошибок

  ```
        214 |             try:
        215 |                 cb(self.job)
  >>>   216 |             except Exception:
        217 |                 pass
        218 | 
  ```

- **строка 233** — except: pass — тихое подавление ошибок

  ```
        231 |                     shutil.copy(src, ds / Path(src).name)
        232 |                     n += 1
  >>>   233 |                 except Exception:
        234 |                     pass
        235 |         return ds
  ```

- **строка 360** — except: pass — тихое подавление ошибок

  ```
        358 |                         job.stage = f"epoch {ep}/{job.epochs}"
        359 |                         self._emit()
  >>>   360 |                     except Exception:
        361 |                         pass
        362 |         ret = proc.wait()
  ```

### BARE_PRINT — 4 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

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

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 60** — public class 'RVCBackend' без docstring

  ```
         58 | # ---------------------------------------------------------------- backend detect
         59 | @dataclass
  >>>    60 | class RVCBackend:
         61 |     kind: str = "cpu"  # "cuda" | "directml" | "rocm" | "cpu"
         62 |     device_name: str = "CPU"
  ```

- **строка 184** — public class 'TrainingJob' без docstring

  ```
        182 | # ---------------------------------------------------------------- training
        183 | @dataclass
  >>>   184 | class TrainingJob:
        185 |     voice_name: str
        186 |     epochs: int
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 17** — import 'annotations' не используется в теле файла

  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import json
  ```
