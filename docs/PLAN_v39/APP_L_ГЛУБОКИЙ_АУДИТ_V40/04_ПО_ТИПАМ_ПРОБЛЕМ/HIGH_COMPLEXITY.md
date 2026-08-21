# HIGH_COMPLEXITY — Цикломатическая сложность > 15

**Severity:** 🟡 MEDIUM
**Всего:** 34
**Как чинить:** Разбить на подфункции; if-цепочки → dict-диспатчер.

## Все вхождения

### `app/core/orchestrator.py` — 6 шт.
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

### `app/core/orchestrator_ai.py` — 2 шт.
- **строка 131** — run_ai_pipeline: сложность ≈ 78 (>15)
  ```
        129 | 
        130 | 
  >>>   131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
        132 |     ws = dict(wizard_state or {})
        133 |     try:
  ```
- **строка 233** — stage_music: сложность ≈ 16 (>15)
  ```
        231 |         return js
        232 | 
  >>>   233 |     def stage_music(handle, ctx):
        234 |         if dry_run:
        235 |             return {"ok": True, "beat_path": "[dry]"}
  ```

### `app/core/orchestrator_v11_patch.py` — 1 шт.
- **строка 52** — run_full_pipeline_v11: сложность ≈ 42 (>15)
  ```
         50 | 
         51 | 
  >>>    52 | def run_full_pipeline_v11(
         53 |     project_id, wizard_state, expert_config=None, progress_cb=None, project_root=None
         54 | ):
  ```

### `app/core/orchestrator_v9_patch.py` — 1 шт.
- **строка 38** — run_pipeline_v9: сложность ≈ 46 (>15)
  ```
         36 | 
         37 | 
  >>>    38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
         39 |     log = getattr(orch, "log", lambda *a, **k: None)
         40 |     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
  ```

### `app/runtime_orchestrator.py` — 1 шт.
- **строка 82** — _process: сложность ≈ 19 (>15)
  ```
         80 |                 self._process(job)
         81 | 
  >>>    82 |     def _process(self, job: Job):
         83 |         out_dir = Path(job.project_dir)
         84 |         out_dir.mkdir(parents=True, exist_ok=True)
  ```

### `main.py` — 1 шт.
- **строка 417** — main: сложность ≈ 35 (>15)
  ```
        415 | 
        416 | 
  >>>   417 | def main() -> int:
        418 |     _setup_console_encoding()
        419 |     _header()
  ```

### `modules/ai_detector_pro.py` — 1 шт.
- **строка 43** — analyze_track: сложность ≈ 19 (>15)
  ```
         41 | 
         42 | 
  >>>    43 | def analyze_track(audio_path: str) -> dict:
         44 |     """
         45 |     Основная функция. Возвращает JSON с метриками, вердиктом и советами.
  ```

### `modules/anti_neuro_v10.py` — 2 шт.
- **строка 128** — _polish_numpy: сложность ≈ 21 (>15)
  ```
        126 | 
        127 | 
  >>>   128 | def _polish_numpy(
        129 |     vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
        130 | ) -> dict[str, Any]:
  ```
- **строка 283** — _apply_stage: сложность ≈ 16 (>15)
  ```
        281 | 
        282 | 
  >>>   283 | def _apply_stage(seg, name: str, rng: random.Random):
        284 |     if name == "breath":
        285 |         breath = WhiteNoise().to_audio_segment(duration=180).apply_gain(-32)
  ```

### `modules/arrangement_engine.py` — 1 шт.
- **строка 137** — build_arrangement: сложность ≈ 24 (>15)
  ```
        135 | 
        136 | # ============================================================ main API
  >>>   137 | def build_arrangement(
        138 |     style_vector: dict,
        139 |     total_seconds: float = 150.0,
  ```

### `modules/artist_dossier/manager.py` — 1 шт.
- **строка 183** — _analyze_single_track: сложность ≈ 38 (>15)
  ```
        181 |         return a.dossier
        182 | 
  >>>   183 |     def _analyze_single_track(self, slug: str, tr: TrackEntry, progress_cb=None) -> None:
        184 |         if progress_cb:
        185 |             progress_cb(tr.track_id, "start")
  ```

### `modules/beat_constructor.py` — 1 шт.
- **строка 394** — build_track: сложность ≈ 25 (>15)
  ```
        392 |         return section_audio
        393 | 
  >>>   394 |     def build_track(
        395 |         self,
        396 |         duration_sec: int = 120,
  ```

### `modules/groove_extractor.py` — 1 шт.
- **строка 22** — extract_groove: сложность ≈ 22 (>15)
  ```
         20 | 
         21 | 
  >>>    22 | def extract_groove(audio_path: str, bpm: float = None) -> dict:
         23 |     """
         24 |     Извлекает ритмический шаблон из трека.
  ```

### `modules/health_v12.py` — 1 шт.
- **строка 221** — collect: сложность ≈ 18 (>15)
  ```
        219 | 
        220 | 
  >>>   221 | def collect(save_to: Path | None = None) -> HealthReport:
        222 |     """Собрать полный health-report."""
        223 |     rep = HealthReport()
  ```

### `modules/kpi_dashboard_v12.py` — 1 шт.
- **строка 177** — _tz_percent: сложность ≈ 18 (>15)
  ```
        175 | 
        176 | 
  >>>   177 | def _tz_percent(
        178 |     health: dict[str, Any] | None,
        179 |     pipe: dict[str, Any] | None,
  ```

### `modules/lyrics_gen_v8.py` — 2 шт.
- **строка 30** — _split_blocks: сложность ≈ 16 (>15)
  ```
         28 | 
         29 | 
  >>>    30 | def _split_blocks(text: str) -> dict[str, list[str]]:
         31 |     """Парсим блоки [Куплет 1] / [Припев] / [Куплет 2] / [Аутро]."""
         32 |     blocks = {
  ```
- **строка 77** — generate_lyrics_v8: сложность ≈ 27 (>15)
  ```
         75 | 
         76 | 
  >>>    77 | def generate_lyrics_v8(
         78 |     theme: str,
         79 |     user_words: list[str] | None = None,
  ```

### `modules/master_pipeline_v12.py` — 1 шт.
- **строка 206** — run_master_pipeline: сложность ≈ 70 (>15)
  ```
        204 | 
        205 | 
  >>>   206 | def run_master_pipeline(
        207 |     project_id: str,
        208 |     wizard_state: dict[str, Any] | None = None,
  ```

### `modules/mastering_pro.py` — 1 шт.
- **строка 65** — process_mastering: сложность ≈ 20 (>15)
  ```
         63 | 
         64 | 
  >>>    65 | def process_mastering(input_wav: str, output_wav: str, vocal_path: str = None, target_lufs: float = -14.0):
         66 |     """
         67 |     Профессиональный мастеринг трека с автоматическими фоллбеками.
  ```

### `modules/midi_generator.py` — 1 шт.
- **строка 65** — generate_drum_pattern: сложность ≈ 24 (>15)
  ```
         63 |     #  DRUM PATTERN
         64 |     # ------------------------------------------------------------------ #
  >>>    65 |     def generate_drum_pattern(self, genre: str, bpm: int) -> str:
         66 |         """Генерирует MIDI барабанный паттерн в зависимости от жанра.
         67 | 
  ```

### `modules/release_export.py` — 1 шт.
- **строка 120** — export_release: сложность ≈ 28 (>15)
  ```
        118 | 
        119 | 
  >>>   120 | def export_release(
        121 |     beat_path: str,
        122 |     vocal_path: str,
  ```

### `modules/release_pack_full.py` — 1 шт.
- **строка 570** — build_pack: сложность ≈ 51 (>15)
  ```
        568 | 
        569 | 
  >>>   570 | def build_pack(
        571 |     master_wav: str,
        572 |     out_dir: str,
  ```

### `modules/release_pack_v9.py` — 1 шт.
- **строка 75** — build_release_v9: сложность ≈ 18 (>15)
  ```
         73 | 
         74 | 
  >>>    75 | def build_release_v9(
         76 |     release_dir: str,
         77 |     project_meta: dict,
  ```

### `modules/self_diag_v13.py` — 1 шт.
- **строка 156** — collect_action_plan: сложность ≈ 26 (>15)
  ```
        154 | 
        155 | 
  >>>   156 | def collect_action_plan(
        157 |     layout: list[dict[str, Any]],
        158 |     health: dict[str, Any] | None,
  ```

### `modules/voice_recording.py` — 1 шт.
- **строка 253** — split_wav_into_takes: сложность ≈ 19 (>15)
  ```
        251 | 
        252 | 
  >>>   253 | def split_wav_into_takes(
        254 |     wav_path: str,
        255 |     min_silence_ms: int = 600,
  ```

### `modules/voice_synth.py` — 1 шт.
- **строка 107** — synth: сложность ≈ 17 (>15)
  ```
        105 | 
        106 | 
  >>>   107 | def synth(
        108 |     text: str,
        109 |     engine: str = "silero",
  ```

### `tools/deep_audit_v40.py` — 1 шт.
- **строка 54** — audit_file: сложность ≈ 60 (>15)
  ```
         52 | 
         53 | 
  >>>    54 | def audit_file(p: Path) -> dict:
         55 |     src = read_src(p)
         56 |     lines = src.splitlines()
  ```

### `updater/updater.py` — 1 шт.
- **строка 298** — install_from_zip: сложность ≈ 18 (>15)
  ```
        296 | 
        297 | 
  >>>   298 | def install_from_zip(
        299 |     zip_path: str, expected_sha256: str | None = None, smoke_test: bool = True
        300 | ) -> dict[str, Any]:
  ```
