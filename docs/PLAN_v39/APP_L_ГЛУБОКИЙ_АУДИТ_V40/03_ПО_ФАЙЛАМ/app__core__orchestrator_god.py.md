# АУДИТ ФАЙЛА: `app/core/orchestrator_god.py`

**LOC:** 232  |  **Размер:** 11617 байт  |  **Проблем:** 7  |  **Risk score:** 4

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 9 | `os` | import |
| 10 | `json` | import |
| 11 | `pathlib.Path` | from |
| 12 | `typing.Any` | from |
| 12 | `typing.Optional` | from |
| 14 | `app.core.pipeline_core.ZSPipeline` | from |
| 14 | `app.core.pipeline_core.PipelineContext` | from |
| 15 | `modules.mastering_pro` | from |
| 15 | `modules.voice_cleaner` | from |
| 15 | `modules.beat_constructor` | from |
| 15 | `modules.genre_engine` | from |
| 15 | `modules.ai_arranger` | from |
| 15 | `modules.midi_generator` | from |
| 34 | `numpy` | import |
| 116 | `modules.chanson_engine.ChansonEngine` | from |
| 120 | `modules.cyber_synth.CyberSynth` | from |
| 154 | `modules.lyrics_gen` | from |
| 154 | `modules.voice_synth` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 24 | `_json_safe` | 21 | 5 | ✅ |
| 48 | `_save_project_meta` | 3 | 1 | ❌ |
| 53 | `run_god_pipeline` | 179 | 12 | ✅ |
| 84 | `stage_arr` | 7 | 0 | ❌ |
| 96 | `stage_midi` | 7 | 0 | ❌ |
| 108 | `stage_audio` | 29 | 4 | ❌ |
| 142 | `stage_vocal` | 44 | 5 | ❌ |
| 191 | `stage_master` | 6 | 0 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 3 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

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

### MISSING_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 108** — public function 'stage_audio' без docstring

  ```
        106 | 
        107 |     # 3. Pro Audio Generation using CyberSynth Engine for Cyberpunk & Modern Genres
  >>>   108 |     def stage_audio(ctx: PipelineContext):
        109 |         state = ctx.shared_data["state"]
        110 |         genre_name = state["genre"]
  ```

- **строка 142** — public function 'stage_vocal' без docstring

  ```
        140 | 
        141 |     # 4. Vocal Synthesis & Cleaning (Generates speech/singing if no input vocal)
  >>>   142 |     def stage_vocal(ctx: PipelineContext):
        143 |         state = ctx.shared_data["state"]
        144 |         vocal_wav = ctx.config.get("vocal_input_path")
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 53** — run_god_pipeline: 179 LOC (>100) — декомпозиция

  ```
         51 |         json.dump(_json_safe(data), f, ensure_ascii=False, indent=2, default=str)
         52 | 
  >>>    53 | def run_god_pipeline(
         54 |     project_id: str,
         55 |     wizard_state: Optional[dict] = None,
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 37** — except: pass — тихое подавление ошибок

  ```
         35 |         if isinstance(obj, _np.generic):
         36 |             return obj.item()
  >>>    37 |     except ImportError:
         38 |         pass
         39 |     if isinstance(obj, dict):
  ```
