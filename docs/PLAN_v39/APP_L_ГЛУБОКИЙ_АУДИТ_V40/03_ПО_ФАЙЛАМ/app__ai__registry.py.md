# АУДИТ ФАЙЛА: `app/ai/registry.py`

**LOC:** 365  |  **Размер:** 14894 байт  |  **Проблем:** 18  |  **Risk score:** 20

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 5 | `__future__.annotations` | from |
| 6 | `gc` | import |
| 6 | `os` | import |
| 6 | `time` | import |
| 6 | `threading` | import |
| 7 | `dataclasses.dataclass` | from |
| 8 | `pathlib.Path` | from |
| 9 | `typing.Any` | from |
| 9 | `typing.Callable` | from |
| 9 | `typing.Dict` | from |
| 9 | `typing.Optional` | from |
| 231 | `torch` | import |
| 238 | `torch_directml` | import |
| 281 | `TTS.api.TTS` | from |
| 294 | `modules.rvc_manager` | from |
| 300 | `demucs.pretrained.get_model` | from |
| 313 | `faster_whisper.WhisperModel` | from |
| 323 | `transformers.ClapModel` | from |
| 323 | `transformers.ClapProcessor` | from |
| 339 | `diffusers.DiffusionPipeline` | from |
| 340 | `torch` | import |
| 360 | `matchering` | import |
| 138 | `llama_cpp` | import |
| 141 | `audiocraft` | import |
| 144 | `TTS.api.TTS` | from |
| 150 | `demucs` | import |
| 153 | `faster_whisper.WhisperModel` | from |
| 156 | `transformers` | import |
| 159 | `librosa` | import |
| 162 | `diffusers` | import |
| 165 | `matchering` | import |
| 201 | `torch` | import |
| 248 | `llama_cpp.Llama` | from |
| 269 | `audiocraft.models.MusicGen` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 25 | `from_env` | 7 | 0 | ❌ |
| 114 | `__init__` | 5 | 1 | ❌ |
| 121 | `status` | 8 | 0 | ❌ |
| 131 | `is_available` | 38 | 13 | ❌ |
| 171 | `load` | 17 | 6 | ❌ |
| 190 | `unload` | 16 | 5 | ❌ |
| 222 | `use` | 1 | 0 | ❌ |
| 225 | `pick_device` | 18 | 8 | ❌ |
| 245 | `_register_default_loaders` | 117 | 14 | ❌ |
| 209 | `__init__` | 2 | 0 | ❌ |
| 213 | `__enter__` | 2 | 0 | ❌ |
| 217 | `__exit__` | 3 | 1 | ❌ |
| 246 | `_llama` | 17 | 1 | ❌ |
| 267 | `_musicgen` | 9 | 2 | ❌ |
| 280 | `_xtts` | 10 | 2 | ❌ |
| 293 | `_rvc` | 3 | 0 | ❌ |
| 299 | `_demucs` | 10 | 2 | ❌ |
| 312 | `_wh` | 7 | 0 | ❌ |
| 322 | `_clap` | 11 | 2 | ❌ |
| 338 | `_sdxl` | 18 | 4 | ❌ |
| 359 | `_match` | 2 | 0 | ❌ |
| 247 | `_do` | 15 | 1 | ❌ |
| 268 | `_do` | 7 | 2 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 17 | `HardwareBudget` | ❌ |
| 104 | `LoadedModel` | ❌ |
| 113 | `ModelRegistry` | ❌ |
| 208 | `_UseCtx` | ❌ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 8 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 235** — except: pass — тихое подавление ошибок

  ```
        233 |                 if need <= self.hw.vram_gb:
        234 |                     return "cuda"
  >>>   235 |         except Exception:
        236 |             pass
        237 |         try:
  ```

- **строка 241** — except: pass — тихое подавление ошибок

  ```
        239 |             if pref in ("dml", "auto") and need <= self.hw.vram_gb:
        240 |                 return "dml"
  >>>   241 |         except Exception:
        242 |             pass
        243 |         return "cpu"
  ```

- **строка 196** — except: pass — тихое подавление ошибок

  ```
        194 |             try:
        195 |                 del self._current.handle
  >>>   196 |             except Exception:
        197 |                 pass
        198 |             self._current = None
  ```

- **строка 205** — except: pass — тихое подавление ошибок

  ```
        203 |                     torch.cuda.empty_cache()
        204 |                     torch.cuda.ipc_collect()
  >>>   205 |             except Exception:
        206 |                 pass
        207 | 
  ```

- **строка 288** — except: pass — тихое подавление ошибок

  ```
        286 |                 try:
        287 |                     t.to("cuda")
  >>>   288 |                 except Exception:
        289 |                     pass
        290 |             return t, device
  ```

- **строка 307** — except: pass — тихое подавление ошибок

  ```
        305 |                 try:
        306 |                     m.to("cuda")
  >>>   307 |                 except Exception:
        308 |                     pass
        309 |             return m, device
  ```

- **строка 331** — except: pass — тихое подавление ошибок

  ```
        329 |                 try:
        330 |                     m = m.to("cuda")
  >>>   331 |                 except Exception:
        332 |                     pass
        333 |             return (m, p), device
  ```

- **строка 354** — except: pass — тихое подавление ошибок

  ```
        352 |                     pipe.enable_attention_slicing()
        353 |                     pipe.enable_vae_tiling()
  >>>   354 |                 except Exception:
        355 |                     pass
        356 |             return pipe, device
  ```

### MISSING_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 131** — public function 'is_available' без docstring

  ```
        129 |                 "registry": list(MODEL_REGISTRY.keys())}
        130 | 
  >>>   131 |     def is_available(self, key: str) -> bool:
        132 |         spec = MODEL_REGISTRY.get(key)
        133 |         if not spec:
  ```

- **строка 171** — public function 'load' без docstring

  ```
        169 |         return False
        170 | 
  >>>   171 |     def load(self, key: str) -> LoadedModel:
        172 |         with self._lock:
        173 |             if self._current and self._current.key == key:
  ```

- **строка 190** — public function 'unload' без docstring

  ```
        188 |             return self._current
        189 | 
  >>>   190 |     def unload(self) -> None:
        191 |         with self._lock:
        192 |             if self._current is None:
  ```

- **строка 225** — public function 'pick_device' без docstring

  ```
        223 |         return ModelRegistry._UseCtx(self, key, unload_after)
        224 | 
  >>>   225 |     def pick_device(self, spec: Dict[str, Any]) -> str:
        226 |         pref = spec.get("device_pref", "auto")
        227 |         need = float(spec.get("vram_est_gb", 0.0))
  ```

### MISSING_CLASS_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 17** — public class 'HardwareBudget' без docstring

  ```
         15 | 
         16 | @dataclass
  >>>    17 | class HardwareBudget:
         18 |     vram_gb: float = 12.0
         19 |     ram_gb: float = 32.0
  ```

- **строка 104** — public class 'LoadedModel' без docstring

  ```
        102 | 
        103 | @dataclass
  >>>   104 | class LoadedModel:
        105 |     key: str
        106 |     handle: Any
  ```

- **строка 113** — public class 'ModelRegistry' без docstring

  ```
        111 | 
        112 | 
  >>>   113 | class ModelRegistry:
        114 |     def __init__(self, hw: Optional[HardwareBudget] = None):
        115 |         self.hw = hw or HardwareBudget.from_env()
  ```

### DEAD_IMPORT — 2 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 5** — import 'annotations' не используется в теле файла

  ```
          3 | Реестр локальных AI-моделей. Одна тяжёлая модель в VRAM за раз.
          4 | Бюджет: VRAM<=12GB, RAM<=32GB, CPU 2xXeon(40 threads). Только серьёзные модели (>=8B)."""
  >>>     5 | from __future__ import annotations
          6 | import gc, os, time, threading
          7 | from dataclasses import dataclass
  ```

- **строка 238** — import 'torch_directml' не используется в теле файла

  ```
        236 |             pass
        237 |         try:
  >>>   238 |             import torch_directml  # noqa
        239 |             if pref in ("dml", "auto") and need <= self.hw.vram_gb:
        240 |                 return "dml"
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 245** — _register_default_loaders: 117 LOC (>100) — декомпозиция

  ```
        243 |         return "cpu"
        244 | 
  >>>   245 |     def _register_default_loaders(self) -> None:
        246 |         def _llama(key):
        247 |             def _do():
  ```
