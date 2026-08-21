# АУДИТ ФАЙЛА: `app/core/orchestrator.py`

**LOC:** 2064  |  **Размер:** 82812 байт  |  **Проблем:** 30  |  **Risk score:** 49

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 19 | `__future__.annotations` | from |
| 21 | `json` | import |
| 22 | `time` | import |
| 23 | `collections.abc.Callable` | from |
| 24 | `dataclasses.dataclass` | from |
| 24 | `dataclasses.field` | from |
| 25 | `pathlib.Path` | from |
| 26 | `typing.Any` | from |
| 29 | `modules.llm_clients_v15.LLMRouter` | from |
| 245 | `modules.analyzer` | from |
| 276 | `modules.groove_extractor` | from |
| 307 | `modules.arrangement_engine` | from |
| 324 | `modules.beat_constructor` | from |
| 379 | `numpy` | import |
| 380 | `soundfile` | import |
| 638 | `numpy` | import |
| 639 | `soundfile` | import |
| 694 | `app.core.musicgen_texture` | from |
| 914 | `modules.voice_synth` | from |
| 938 | `pyttsx3` | import |
| 959 | `numpy` | import |
| 960 | `soundfile` | import |
| 1108 | `modules.rvc_manager` | from |
| 1138 | `numpy` | import |
| 1139 | `soundfile` | import |
| 1202 | `modules.vocal_fx` | from |
| 1239 | `modules.sidechain` | from |
| 1264 | `modules.mastering` | from |
| 1341 | `shutil` | import |
| 1364 | `demucs` | import |
| 1374 | `modules.stem_splitter` | from |
| 1431 | `modules.hit_scorer` | from |
| 1482 | `modules.release_pack_full.build_pack` | from |
| 1497 | `modules.release_pack_v13` | from |
| 1513 | `shutil` | import |
| 2043 | `gradio` | import |
| 576 | `scipy.signal.butter` | from |
| 577 | `scipy.signal.sosfilt` | from |
| 1165 | `scipy.signal.butter` | from |
| 1165 | `scipy.signal.sosfilt` | from |
| 1299 | `modules.anti_neuro_v10` | from |
| 1316 | `modules.anti_ai_polish` | from |
| 1521 | `pydub.AudioSegment` | from |
| 1530 | `PIL.Image` | from |
| 1530 | `PIL.ImageDraw` | from |
| 1592 | `modules.presets` | from |
| 1148 | `scipy.signal.resample_poly` | from |
| 1183 | `shutil` | import |
| 1035 | `scipy.signal.butter` | from |
| 1035 | `scipy.signal.sosfilt` | from |
| 342 | `shutil` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 38 | `_mark_legacy_result` | 5 | 0 | ✅ |
| 84 | `_timed` | 16 | 3 | ❌ |
| 103 | `_is_simulation_result` | 22 | 6 | ✅ |
| 128 | `_is_blocked_result` | 4 | 1 | ✅ |
| 135 | `_normalize_path_map` | 15 | 9 | ❌ |
| 232 | `_default_style_for_genre` | 2 | 1 | ❌ |
| 237 | `_stage_analyze` | 30 | 3 | ✅ |
| 270 | `_stage_groove` | 32 | 4 | ✅ |
| 305 | `_stage_arrangement` | 7 | 1 | ❌ |
| 315 | `_stage_beat` | 51 | 18 | ✅ |
| 369 | `_synth_beat` | 253 | 29 | ✅ |
| 625 | `_texture_scaffold` | 59 | 2 | ✅ |
| 687 | `_stage_texture` | 14 | 3 | ✅ |
| 704 | `_text_to_struct` | 35 | 18 | ❌ |
| 742 | `_struct_to_text` | 13 | 4 | ❌ |
| 848 | `_fallback_lyrics` | 16 | 5 | ✅ |
| 867 | `_stage_lyrics` | 35 | 4 | ✅ |
| 905 | `_stage_voice_synth` | 28 | 11 | ❌ |
| 936 | `_pyttsx3_speak` | 153 | 19 | ❌ |
| 1092 | `_stage_rvc` | 35 | 4 | ✅ |
| 1130 | `_mix_beat_and_vocal` | 58 | 11 | ✅ |
| 1191 | `_stage_vocal_fx` | 34 | 6 | ✅ |
| 1228 | `_stage_mix_and_sidechain` | 25 | 3 | ✅ |
| 1256 | `_stage_mastering` | 31 | 3 | ✅ |
| 1290 | `_stage_polish` | 65 | 17 | ✅ |
| 1358 | `_stage_stems` | 63 | 7 | ✅ |
| 1424 | `_stage_hit_score` | 43 | 6 | ✅ |
| 1470 | `_stage_release_pack` | 36 | 4 | ❌ |
| 1509 | `_minimal_release_pack` | 53 | 3 | ❌ |
| 1568 | `run_full_pipeline` | 470 | 101 | ❌ |
| 2041 | `build_gradio_ui` | 23 | 3 | ❌ |
| 70 | `to_dict` | 11 | 0 | ❌ |
| 1980 | `_stage_is_blocked` | 1 | 2 | ❌ |
| 2047 | `_run` | 7 | 1 | ❌ |
| 440 | `_kick` | 12 | 0 | ❌ |
| 454 | `_snare` | 6 | 0 | ❌ |
| 462 | `_hat` | 5 | 0 | ❌ |
| 469 | `_808` | 5 | 0 | ❌ |
| 476 | `_riser` | 9 | 1 | ❌ |
| 983 | `_extract_vowel` | 5 | 2 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 47 | `PipelineStage` | ❌ |
| 59 | `PipelineResult` | ❌ |

## Проблемы (детально, с цитатой кода)

### SILENT_EXCEPT_PASS — 15 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 951** — except: pass — тихое подавление ошибок

  ```
        949 |                 "reason": "primary TTS unavailable; using pyttsx3",
        950 |             }
  >>>   951 |     except Exception:
        952 |         pass
        953 |     # v19: честный numpy-fallback — короткая "рыба" вокала с формантной
  ```

- **строка 1494** — except: pass — тихое подавление ошибок

  ```
       1492 |             hit_metrics=hit_metrics,
       1493 |         )
  >>>  1494 |     except Exception:
       1495 |         pass
       1496 |     try:
  ```

- **строка 1504** — except: pass — тихое подавление ошибок

  ```
       1502 |             if isinstance(r, dict):
       1503 |                 return r
  >>>  1504 |     except Exception:
       1505 |         pass
       1506 |     return _minimal_release_pack(master_wav, meta, out)
  ```

- **строка 892** — except: pass — тихое подавление ошибок

  ```
        890 |                     ),
        891 |                 }
  >>>   892 |         except Exception:
        893 |             pass
        894 |     fb = _fallback_lyrics(theme, genre)
  ```

- **строка 1171** — except: pass — тихое подавление ошибок

  ```
       1169 |                 [sosfilt(sos, voc[:, c]) for c in range(voc.shape[1])], axis=1
       1170 |             )
  >>>  1171 |         except Exception:
       1172 |             pass
       1173 |         gain = 10 ** (vocal_gain_db / 20.0)
  ```

- **строка 1311** — except: pass — тихое подавление ошибок

  ```
       1309 |                     legacy_attempt,
       1310 |                 )
  >>>  1311 |         except Exception:
       1312 |             # Для надежного fallback сохраняем имя attempted legacy-ветки,
       1313 |             # но не помечаем результат LEGACY, если её обработка не удалась.
  ```

- **строка 1339** — except: pass — тихое подавление ошибок

  ```
       1337 |                     except Exception:
       1338 |                         continue
  >>>  1339 |         except Exception:
       1340 |             pass
       1341 |         import shutil
  ```

- **строка 1527** — except: pass — тихое подавление ошибок

  ```
       1525 |             seg.export(mp3, format="mp3", bitrate="320k")
       1526 |             files.append(str(mp3))
  >>>  1527 |         except Exception:
       1528 |             pass
       1529 |         try:
  ```

- **строка 1538** — except: pass — тихое подавление ошибок

  ```
       1536 |             img.save(cov)
       1537 |             files.append(str(cov))
  >>>  1538 |         except Exception:
       1539 |             pass
       1540 |         (out / "lyrics.txt").write_text(meta.get("lyrics_text", ""), encoding="utf-8")
  ```

- **строка 1599** — except: pass — тихое подавление ошибок

  ```
       1597 |                 # жанр берём из ключа пресета (brazilian_phonk и т.п.)
       1598 |                 _preset_genre = preset_key
  >>>  1599 |         except Exception:
       1600 |             pass
       1601 |     genre = wizard_state.get("genre") or _preset_genre or "drift_phonk"
  ```

- **строка 1937** — except: pass — тихое подавление ошибок

  ```
       1935 |                     ],
       1936 |                 )
  >>>  1937 |         except Exception:
       1938 |             pass
       1939 |         try:
  ```

- **строка 1950** — except: pass — тихое подавление ошибок

  ```
       1948 |                     raw_stems, ["drums", "bass", "vocals", "other"]
       1949 |                 )
  >>>  1950 |         except Exception:
       1951 |             pass
       1952 |         _hit = {}
  ```

- **строка 1958** — except: pass — тихое подавление ошибок

  ```
       1956 |                     k: v for k, v in s13.output.items() if k not in ("ok", "reason")
       1957 |                 }
  >>>  1958 |         except Exception:
       1959 |             pass
       1960 |         s14 = _timed(
  ```

- **строка 923** — except: pass — тихое подавление ошибок

  ```
        921 |                 if path and Path(path).exists() and Path(path).stat().st_size > 1000:
        922 |                     return {"ok": True, "path": path, "engine": "voice_synth.synth"}
  >>>   923 |             except Exception:
        924 |                 pass
        925 |         if hasattr(voice_synth, "synthesize"):
  ```

- **строка 1044** — except: pass — тихое подавление ошибок

  ```
       1042 |                         )
       1043 |                         seg = seg + sosfilt(sos, seg) * 0.6
  >>>  1044 |                 except Exception:
       1045 |                     # fallback: просто нормализуем
       1046 |                     pass
  ```

### HIGH_COMPLEXITY — 6 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 315** — _stage_beat: сложность ≈ 18 (>15)

  ```
        313 | 
        314 | 
  >>>   315 | def _stage_beat(
        316 |     plan: Any,
        317 |     out_dir: Path,
  ```

- **строка 369** — _synth_beat: сложность ≈ 29 (>15)

  ```
        367 | 
        368 | 
  >>>   369 | def _synth_beat(
        370 |     out_wav: str, duration: int = 90, bpm: int = 128, key_root: str = "A"
        371 | ) -> dict[str, Any]:
  ```

- **строка 704** — _text_to_struct: сложность ≈ 18 (>15)

  ```
        702 | 
        703 | 
  >>>   704 | def _text_to_struct(text: str, genre: str) -> dict[str, Any]:
        705 |     lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        706 |     title = ""
  ```

- **строка 936** — _pyttsx3_speak: сложность ≈ 19 (>15)

  ```
        934 | 
        935 | 
  >>>   936 | def _pyttsx3_speak(text: str, out_wav: str) -> dict[str, Any]:
        937 |     try:
        938 |         import pyttsx3
  ```

- **строка 1290** — _stage_polish: сложность ≈ 17 (>15)

  ```
       1288 | 
       1289 | 
  >>>  1290 | def _stage_polish(input_wav: str, out_dir: Path) -> dict[str, Any]:
       1291 |     """Полировка вокала с явно отмеченной legacy-v10 веткой и новым fallback."""
       1292 |     try:
  ```

- **строка 1568** — run_full_pipeline: сложность ≈ 101 (>15)

  ```
       1566 | 
       1567 | 
  >>>  1568 | def run_full_pipeline(
       1569 |     project_id: str,
       1570 |     wizard_state: dict[str, Any],
  ```

### LONG_FUNCTION — 3 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 369** — _synth_beat: 253 LOC (>100) — декомпозиция

  ```
        367 | 
        368 | 
  >>>   369 | def _synth_beat(
        370 |     out_wav: str, duration: int = 90, bpm: int = 128, key_root: str = "A"
        371 | ) -> dict[str, Any]:
  ```

- **строка 936** — _pyttsx3_speak: 153 LOC (>100) — декомпозиция

  ```
        934 | 
        935 | 
  >>>   936 | def _pyttsx3_speak(text: str, out_wav: str) -> dict[str, Any]:
        937 |     try:
        938 |         import pyttsx3
  ```

- **строка 1568** — run_full_pipeline: 470 LOC (>100) — декомпозиция

  ```
       1566 | 
       1567 | 
  >>>  1568 | def run_full_pipeline(
       1569 |     project_id: str,
       1570 |     wizard_state: dict[str, Any],
  ```

### MISSING_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 1568** — public function 'run_full_pipeline' без docstring

  ```
       1566 | 
       1567 | 
  >>>  1568 | def run_full_pipeline(
       1569 |     project_id: str,
       1570 |     wizard_state: dict[str, Any],
  ```

- **строка 2041** — public function 'build_gradio_ui' без docstring

  ```
       2039 | 
       2040 | 
  >>>  2041 | def build_gradio_ui():
       2042 |     try:
       2043 |         import gradio as gr
  ```

- **строка 70** — public function 'to_dict' без docstring

  ```
         68 |     warnings: list[str] = field(default_factory=list)
         69 | 
  >>>    70 |     def to_dict(self) -> dict[str, Any]:
         71 |         return {
         72 |             "project_id": self.project_id,
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 47** — public class 'PipelineStage' без docstring

  ```
         45 | 
         46 | @dataclass
  >>>    47 | class PipelineStage:
         48 |     name: str
         49 |     ok: bool = False
  ```

- **строка 59** — public class 'PipelineResult' без docstring

  ```
         57 | 
         58 | @dataclass
  >>>    59 | class PipelineResult:
         60 |     project_id: str
         61 |     started_at: float
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 19** — import 'annotations' не используется в теле файла

  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import json
  ```
