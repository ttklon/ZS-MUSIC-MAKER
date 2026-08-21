# АУДИТ ФАЙЛА: `modules/artist_dossier/manager.py`

**LOC:** 398  |  **Размер:** 17696 байт  |  **Проблем:** 11  |  **Risk score:** 7

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 4 | `__future__.annotations` | from |
| 5 | `json` | import |
| 5 | `re` | import |
| 5 | `time` | import |
| 5 | `hashlib` | import |
| 5 | `shutil` | import |
| 6 | `dataclasses.dataclass` | from |
| 6 | `dataclasses.field` | from |
| 6 | `dataclasses.asdict` | from |
| 7 | `pathlib.Path` | from |
| 8 | `typing.Any` | from |
| 8 | `typing.Dict` | from |
| 8 | `typing.List` | from |
| 8 | `typing.Optional` | from |
| 9 | `app.ai.registry.registry` | from |
| 10 | `app.ai.sequential_runner.SequentialAIRunner` | from |
| 10 | `app.ai.sequential_runner.AIStage` | from |
| 11 | `app.ai.prompts` | from |
| 12 | `app.ai.llm_service` | from |
| 13 | `app.ai.quality.validate_analysis_json` | from |
| 13 | `app.ai.quality.validate_asr_transcript` | from |
| 13 | `app.ai.quality.validate_stem_artifact` | from |
| 44 | `numpy` | import |
| 194 | `torchaudio` | import |
| 194 | `soundfile` | import |
| 195 | `demucs.apply.apply_model` | from |
| 264 | `torch` | import |
| 264 | `librosa` | import |
| 264 | `numpy` | import |
| 243 | `librosa` | import |
| 243 | `numpy` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 24 | `_slug` | 2 | 2 | ❌ |
| 29 | `_track_id` | 2 | 2 | ❌ |
| 34 | `resolve_vocal_source_index` | 5 | 2 | ✅ |
| 42 | `rank_clap_tags` | 7 | 1 | ✅ |
| 52 | `transcribe_reference_audio` | 28 | 2 | ✅ |
| 108 | `__init__` | 2 | 0 | ❌ |
| 112 | `add_artist` | 17 | 5 | ❌ |
| 131 | `add_track` | 25 | 7 | ❌ |
| 158 | `build_full_dossier` | 23 | 7 | ❌ |
| 183 | `_analyze_single_track` | 131 | 38 | ❌ |
| 316 | `_aggregate_artist_dossier` | 26 | 7 | ❌ |
| 344 | `get_artist_dossier` | 2 | 0 | ❌ |
| 348 | `get_track_dossier` | 2 | 0 | ❌ |
| 352 | `list_artists` | 9 | 3 | ❌ |
| 363 | `list_tracks` | 13 | 4 | ❌ |
| 378 | `_save_artist` | 3 | 0 | ❌ |
| 383 | `_load_artist` | 4 | 1 | ❌ |
| 389 | `_save_track` | 3 | 0 | ❌ |
| 394 | `_load_track` | 4 | 1 | ❌ |
| 188 | `_demucs_stage` | 32 | 7 | ❌ |
| 223 | `_asr_stage` | 13 | 6 | ❌ |
| 239 | `_features_stage` | 15 | 3 | ❌ |
| 257 | `_tag_stage` | 22 | 6 | ❌ |
| 282 | `_llm_stage` | 13 | 6 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 84 | `TrackEntry` | ❌ |
| 98 | `ArtistEntry` | ❌ |
| 107 | `DossierManager` | ❌ |

## Проблемы (детально, с цитатой кода)

### MISSING_DOCSTRING — 4 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 112** — public function 'add_artist' без docstring

  ```
        110 |         self.root.mkdir(parents=True, exist_ok=True)
        111 | 
  >>>   112 |     def add_artist(self, artist: str,
        113 |                    tracks: Optional[List[Dict[str, Any]]] = None) -> ArtistEntry:
        114 |         slug = _slug(artist)
  ```

- **строка 131** — public function 'add_track' без docstring

  ```
        129 |         return entry
        130 | 
  >>>   131 |     def add_track(self, artist: str, title: str,
        132 |                   audio_path: Optional[str] = None,
        133 |                   external_url: Optional[str] = None,
  ```

- **строка 158** — public function 'build_full_dossier' без docstring

  ```
        156 |         return entry
        157 | 
  >>>   158 |     def build_full_dossier(self, artist: str, refresh: bool = False,
        159 |                            progress_cb=None) -> Dict[str, Any]:
        160 |         slug = _slug(artist)
  ```

- **строка 363** — public function 'list_tracks' без docstring

  ```
        361 |         return out
        362 | 
  >>>   363 |     def list_tracks(self, artist: str) -> List[Dict[str, Any]]:
        364 |         slug = _slug(artist)
        365 |         a = self._load_artist(slug)
  ```

### MISSING_CLASS_DOCSTRING — 3 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 84** — public class 'TrackEntry' без docstring

  ```
         82 | 
         83 | @dataclass
  >>>    84 | class TrackEntry:
         85 |     track_id: str
         86 |     title: str
  ```

- **строка 98** — public class 'ArtistEntry' без docstring

  ```
         96 | 
         97 | @dataclass
  >>>    98 | class ArtistEntry:
         99 |     artist: str
        100 |     slug: str
  ```

- **строка 107** — public class 'DossierManager' без docstring

  ```
        105 | 
        106 | 
  >>>   107 | class DossierManager:
        108 |     def __init__(self, root: Optional[Path] = None):
        109 |         self.root = Path(root) if root else DOSSIER_ROOT
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 4** — import 'annotations' не используется в теле файла

  ```
          2 | """ZS Music Maker - modules/artist_dossier/manager.py (v38)
          3 | Последовательный AI-пайплайн на трек: demucs -> whisper -> librosa -> CLAP -> LLM."""
  >>>     4 | from __future__ import annotations
          5 | import json, re, time, hashlib, shutil
          6 | from dataclasses import dataclass, field, asdict
  ```

### LONG_FUNCTION — 1 шт. — 🟡 MEDIUM
**Смысл:** Функция > 100 LOC — сложно тестировать/поддерживать
**Fix:** Декомпозировать: приватные `_helper()`, тестировать по частям.

- **строка 183** — _analyze_single_track: 131 LOC (>100) — декомпозиция

  ```
        181 |         return a.dossier
        182 | 
  >>>   183 |     def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
        184 |         if progress_cb:
        185 |             progress_cb(tr.track_id, "start")
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 183** — _analyze_single_track: сложность ≈ 38 (>15)

  ```
        181 |         return a.dossier
        182 | 
  >>>   183 |     def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
        184 |         if progress_cb:
        185 |             progress_cb(tr.track_id, "start")
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 145** — except: pass — тихое подавление ошибок

  ```
        143 |                 shutil.copy2(audio_path, dst)
        144 |                 entry.audio_path = str(dst)
  >>>   145 |             except Exception:
        146 |                 pass
        147 |         if lyrics:
  ```
