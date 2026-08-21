# LONG_FUNCTION — Функция > 100 LOC — сложно тестировать/поддерживать

**Severity:** 🟡 MEDIUM
**Всего:** 29
**Как чинить:** Декомпозировать: приватные `_helper()`, тестировать по частям.

## Все вхождения

### `app/ai/registry.py` — 1 шт.
- **строка 245** — _register_default_loaders: 117 LOC (>100) — декомпозиция
  ```
        243 |         return "cpu"
        244 | 
  >>>   245 |     def _register_default_loaders(self) -> None:
        246 |         def _llama(key):
        247 |             def _do():
  ```

### `app/core/orchestrator.py` — 3 шт.
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

### `app/core/orchestrator_ai.py` — 1 шт.
- **строка 131** — run_ai_pipeline: 339 LOC (>100) — декомпозиция
  ```
        129 | 
        130 | 
  >>>   131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
        132 |     ws = dict(wizard_state or {})
        133 |     try:
  ```

### `app/core/orchestrator_god.py` — 1 шт.
- **строка 53** — run_god_pipeline: 179 LOC (>100) — декомпозиция
  ```
         51 |         json.dump(_json_safe(data), f, ensure_ascii=False, indent=2, default=str)
         52 | 
  >>>    53 | def run_god_pipeline(
         54 |     project_id: str,
         55 |     wizard_state: Optional[dict] = None,
  ```

### `app/core/orchestrator_v11_patch.py` — 1 шт.
- **строка 52** — run_full_pipeline_v11: 269 LOC (>100) — декомпозиция
  ```
         50 | 
         51 | 
  >>>    52 | def run_full_pipeline_v11(
         53 |     project_id, wizard_state, expert_config=None, progress_cb=None, project_root=None
         54 | ):
  ```

### `app/core/orchestrator_v9_patch.py` — 1 шт.
- **строка 38** — run_pipeline_v9: 232 LOC (>100) — декомпозиция
  ```
         36 | 
         37 | 
  >>>    38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
         39 |     log = getattr(orch, "log", lambda *a, **k: None)
         40 |     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
  ```

### `app/gui/theme_v12.py` — 1 шт.
- **строка 55** — qss: 189 LOC (>100) — декомпозиция
  ```
         53 | 
         54 | 
  >>>    55 | def qss() -> str:
         56 |     """Возвращает QSS для PySide6/PyQt6. Без градиентов, без картинок."""
         57 |     t = TOKENS
  ```

### `main.py` — 1 шт.
- **строка 417** — main: 164 LOC (>100) — декомпозиция
  ```
        415 | 
        416 | 
  >>>   417 | def main() -> int:
        418 |     _setup_console_encoding()
        419 |     _header()
  ```

### `modules/ai_detector_pro.py` — 1 шт.
- **строка 43** — analyze_track: 138 LOC (>100) — декомпозиция
  ```
         41 | 
         42 | 
  >>>    43 | def analyze_track(audio_path: str) -> dict:
         44 |     """
         45 |     Основная функция. Возвращает JSON с метриками, вердиктом и советами.
  ```

### `modules/anti_neuro_v10.py` — 2 шт.
- **строка 128** — _polish_numpy: 152 LOC (>100) — декомпозиция
  ```
        126 | 
        127 | 
  >>>   128 | def _polish_numpy(
        129 |     vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
        130 | ) -> dict[str, Any]:
  ```
- **строка 283** — _apply_stage: 105 LOC (>100) — декомпозиция
  ```
        281 | 
        282 | 
  >>>   283 | def _apply_stage(seg, name: str, rng: random.Random):
        284 |     if name == "breath":
        285 |         breath = WhiteNoise().to_audio_segment(duration=180).apply_gain(-32)
  ```

### `modules/arrangement_engine.py` — 1 шт.
- **строка 137** — build_arrangement: 152 LOC (>100) — декомпозиция
  ```
        135 | 
        136 | # ============================================================ main API
  >>>   137 | def build_arrangement(
        138 |     style_vector: dict,
        139 |     total_seconds: float = 150.0,
  ```

### `modules/artist_dossier/manager.py` — 1 шт.
- **строка 183** — _analyze_single_track: 131 LOC (>100) — декомпозиция
  ```
        181 |         return a.dossier
        182 | 
  >>>   183 |     def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
        184 |         if progress_cb:
        185 |             progress_cb(tr.track_id, "start")
  ```

### `modules/auto_qa.py` — 1 шт.
- **строка 87** — audit_track: 101 LOC (>100) — декомпозиция
  ```
         85 | 
         86 | 
  >>>    87 | def audit_track(master_wav: str | Path, target_lufs: float = -9.0) -> dict:
         88 |     """
         89 |     Полный аудит финального трека. Возвращает dict с 3 блоками:
  ```

### `modules/beat_constructor.py` — 1 шт.
- **строка 394** — build_track: 224 LOC (>100) — декомпозиция
  ```
        392 |         return section_audio
        393 | 
  >>>   394 |     def build_track(
        395 |         self,
        396 |         duration_sec: int = 120,
  ```

### `modules/groove_extractor.py` — 1 шт.
- **строка 22** — extract_groove: 160 LOC (>100) — декомпозиция
  ```
         20 | 
         21 | 
  >>>    22 | def extract_groove(audio_path: str, bpm: float = None) -> dict:
         23 |     """
         24 |     Извлекает ритмический шаблон из трека.
  ```

### `modules/kpi_dashboard_v12.py` — 1 шт.
- **строка 177** — _tz_percent: 117 LOC (>100) — декомпозиция
  ```
        175 | 
        176 | 
  >>>   177 | def _tz_percent(
        178 |     health: dict[str, Any] | None,
        179 |     pipe: dict[str, Any] | None,
  ```

### `modules/llm_clients_v15.py` — 1 шт.
- **строка 425** — complete: 113 LOC (>100) — декомпозиция
  ```
        423 |         return r
        424 | 
  >>>   425 |     def complete(
        426 |         self,
        427 |         prompt: str,
  ```

### `modules/lyrics_gen_v8.py` — 1 шт.
- **строка 77** — generate_lyrics_v8: 119 LOC (>100) — декомпозиция
  ```
         75 | 
         76 | 
  >>>    77 | def generate_lyrics_v8(
         78 |     theme: str,
         79 |     user_words: list[str] | None = None,
  ```

### `modules/master_pipeline_v12.py` — 1 шт.
- **строка 206** — run_master_pipeline: 437 LOC (>100) — декомпозиция
  ```
        204 | 
        205 | 
  >>>   206 | def run_master_pipeline(
        207 |     project_id: str,
        208 |     wizard_state: dict[str, Any] | None = None,
  ```

### `modules/mastering_pro.py` — 1 шт.
- **строка 65** — process_mastering: 123 LOC (>100) — декомпозиция
  ```
         63 | 
         64 | 
  >>>    65 | def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
         66 |     """
         67 |     Профессиональный мастеринг трека с автоматическими фоллбеками.
  ```

### `modules/release_export.py` — 1 шт.
- **строка 120** — export_release: 143 LOC (>100) — декомпозиция
  ```
        118 | 
        119 | 
  >>>   120 | def export_release(
        121 |     beat_path: str,
        122 |     vocal_path: str,
  ```

### `modules/release_pack_full.py` — 1 шт.
- **строка 570** — build_pack: 285 LOC (>100) — декомпозиция
  ```
        568 | 
        569 | 
  >>>   570 | def build_pack(
        571 |     master_wav: str,
        572 |     out_dir: str,
  ```

### `modules/voice_recording.py` — 1 шт.
- **строка 253** — split_wav_into_takes: 117 LOC (>100) — декомпозиция
  ```
        251 | 
        252 | 
  >>>   253 | def split_wav_into_takes(
        254 |     wav_path: str,
        255 |     min_silence_ms: int = 600,
  ```

### `modules/wizard_v12_integration.py` — 1 шт.
- **строка 94** — bridge_wizard_to_v12: 137 LOC (>100) — декомпозиция
  ```
         92 | 
         93 | 
  >>>    94 | def bridge_wizard_to_v12(
         95 |     project_id: str,
         96 |     ui_state: dict[str, Any] | None = None,
  ```

### `tools/deep_audit_v40.py` — 1 шт.
- **строка 54** — audit_file: 202 LOC (>100) — декомпозиция
  ```
         52 | 
         53 | 
  >>>    54 | def audit_file(p: Path) -> dict:
         55 |     src = read_src(p)
         56 |     lines = src.splitlines()
  ```

### `tools/smoke_v26.py` — 1 шт.
- **строка 60** — main: 122 LOC (>100) — декомпозиция
  ```
         58 | 
         59 | 
  >>>    60 | def main():
         61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
  ```
