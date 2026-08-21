# MISSING_DOCSTRING — Public-функция без docstring

**Severity:** 🟢 LOW
**Всего:** 177
**Как чинить:** Добавить """что делает, args, returns""" 3-5 строк.

## Все вхождения

### `agents/sample_hunter_v9.py` — 6 шт.
- **строка 128** — public function 'list_local' без docstring
  ```
        126 | 
        127 | 
  >>>   128 | def list_local(subdir: str = "") -> list[dict]:
        129 |     root = LOCAL_LIB / subdir if subdir else LOCAL_LIB
        130 |     if not root.exists():
  ```
- **строка 191** — public function 'search_wikimedia' без docstring
  ```
        189 | 
        190 | 
  >>>   191 | def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
        192 |     if not HAS_REQ:
        193 |         return []
  ```
- **строка 227** — public function 'search_archive_org' без docstring
  ```
        225 | 
        226 | 
  >>>   227 | def search_archive_org(query: str, limit: int = 5) -> list[dict]:
        228 |     if not HAS_REQ:
        229 |         return []
  ```
- **строка 302** — public function 'search_online' без docstring
  ```
        300 | 
        301 | 
  >>>   302 | def search_online(
        303 |     style_vector: dict, max_per_source: int = 5, max_total: int = 40
        304 | ) -> list[dict]:
  ```
- **строка 326** — public function 'unified_search' без docstring
  ```
        324 | 
        325 | 
  >>>   326 | def unified_search(
        327 |     style_vector: dict,
        328 |     include_local: bool = True,
  ```
- **строка 346** — public function 'save_manifest' без docstring
  ```
        344 | 
        345 | 
  >>>   346 | def save_manifest(items: list[dict], project_id: str) -> str:
        347 |     path = MANIFEST_DIR / f"{project_id}_samples.json"
        348 |     payload = {
  ```

### `app/ai/llm_service.py` — 2 шт.
- **строка 8** — public function 'complete' без docstring
  ```
          6 | 
          7 | 
  >>>     8 | def complete(handle: Any, system: str, user: str, max_tokens: int = 1024,
          9 |              temperature: float = 0.85, top_p: float = 0.95,
         10 |              repeat_penalty: float = 1.1) -> str:
  ```
- **строка 31** — public function 'complete_json' без docstring
  ```
         29 | 
         30 | 
  >>>    31 | def complete_json(handle: Any, system: str, user: str, max_tokens: int = 2048,
         32 |                   temperature: float = 0.4) -> Optional[dict]:
         33 |     txt = complete(handle, system, user, max_tokens=max_tokens, temperature=temperature)
  ```

### `app/ai/prompts.py` — 2 шт.
- **строка 32** — public function 'build_lyrics_prompt' без docstring
  ```
         30 | 
         31 | 
  >>>    32 | def build_lyrics_prompt(theme, genre, bpm, n_verses, bilingual,
         33 |                         user_lines=None, artist_dossier=None, track_reference=None):
         34 |     parts = [f"Тема: {theme}", f"Жанр: {genre}", f"BPM: {bpm}",
  ```
- **строка 75** — public function 'build_music_prompt' без docstring
  ```
         73 | 
         74 | 
  >>>    75 | def build_music_prompt(genre, bpm, key, mood, reference_artist=None,
         76 |                        reference_track_features=None):
         77 |     parts = [f"{genre}", f"{bpm} BPM", f"{key} key", f"mood: {mood}"]
  ```

### `app/ai/registry.py` — 4 шт.
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

### `app/ai/sequential_runner.py` — 1 шт.
- **строка 63** — public function 'run' без docstring
  ```
         61 |         return self._sink
         62 | 
  >>>    63 |     def run(self, context: Optional[Dict[str, Any]] = None) -> RunReport:
         64 |         context = context or {}
         65 |         context["sink"] = self._sink
  ```

### `app/core/cover_gen.py` — 1 шт.
- **строка 9** — public function 'make_cover' без docstring
  ```
          7 | 
          8 | 
  >>>     9 | def make_cover(recipe: dict, out_png: str, size: int = 1500) -> dict:
         10 |     try:
         11 |         from PIL import Image, ImageDraw, ImageFilter
  ```

### `app/core/license_manager.py` — 1 шт.
- **строка 31** — public function 'normalize' без docstring
  ```
         29 | 
         30 | 
  >>>    31 | def normalize(lic: str) -> str:
         32 |     n = (lic or "").strip().lower().replace("_", " ")
         33 |     # v34 FIX: лицензии часто приходят как URL (archive.org licenseurl,
  ```

### `app/core/orchestrator.py` — 3 шт.
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

### `app/core/orchestrator_ai.py` — 8 шт.
- **строка 131** — public function 'run_ai_pipeline' без docstring
  ```
        129 | 
        130 | 
  >>>   131 | def run_ai_pipeline(project_id, wizard_state=None, out_root=None, dry_run=False):
        132 |     ws = dict(wizard_state or {})
        133 |     try:
  ```
- **строка 169** — public function 'stage_lyrics' без docstring
  ```
        167 |                 "track_dossier": mgr.get_track_dossier(artist_slug, ref_track_id) if ref_track_id else None}
        168 | 
  >>>   169 |     def stage_lyrics(handle, ctx):
        170 |         if dry_run:
        171 |             return {"ok": True, "lyrics": "[dry-run]", "source": "dry"}
  ```
- **строка 203** — public function 'stage_metadata' без docstring
  ```
        201 |                 "reason": quality["reason"]}
        202 | 
  >>>   203 |     def stage_metadata(handle, ctx):
        204 |         lyrics = (ctx["sink"].get("lyrics") or {}).get("lyrics") or ""
        205 |         fallback = {
  ```
- **строка 233** — public function 'stage_music' без docstring
  ```
        231 |         return js
        232 | 
  >>>   233 |     def stage_music(handle, ctx):
        234 |         if dry_run:
        235 |             return {"ok": True, "beat_path": "[dry]"}
  ```
- **строка 327** — public function 'stage_vocal' без docstring
  ```
        325 |         return result
        326 | 
  >>>   327 |     def stage_vocal(handle, ctx):
        328 |         if dry_run:
        329 |             return {"skipped": "dry-run"}
  ```
- **строка 347** — public function 'stage_rvc' без docstring
  ```
        345 |         return fallback
        346 | 
  >>>   347 |     def stage_rvc(handle, ctx):
        348 |         if dry_run:
        349 |             return {"skipped": "dry-run"}
  ```
- **строка 367** — public function 'stage_mix' без docstring
  ```
        365 |         )
        366 | 
  >>>   367 |     def stage_mix(_, ctx):
        368 |         beat = (ctx["sink"].get("music") or {}).get("beat_path")
        369 |         vocal = ((ctx["sink"].get("rvc") or {}).get("vocal_path")
  ```
- **строка 416** — public function 'stage_tag' без docstring
  ```
        414 |                                mood=ws["mood"], out_path=str(out_root / "cover.png"))
        415 | 
  >>>   416 |     def stage_tag(bundle, ctx):
        417 |         if bundle is None:
        418 |             return {"skipped": "no clap"}
  ```

### `app/core/orchestrator_async.py` — 2 шт.
- **строка 25** — public function 'run_stage_async' без docstring
  ```
         23 |     reason: Optional[str] = None
         24 | 
  >>>    25 | async def run_stage_async(name: str, coro: Callable) -> AsyncStage:
         26 |     t0 = time.time()
         27 |     stage = AsyncStage(name=name)
  ```
- **строка 57** — public function 'run_pipeline' без docstring
  ```
         55 |             return await run_stage_async(name, coro)
         56 | 
  >>>    57 |     async def run_pipeline(self, wizard_state: dict):
         58 |         t_start = time.time()
         59 | 
  ```

### `app/core/orchestrator_god.py` — 2 шт.
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

### `app/core/orchestrator_v9_patch.py` — 1 шт.
- **строка 38** — public function 'run_pipeline_v9' без docstring
  ```
         36 | 
         37 | 
  >>>    38 | def run_pipeline_v9(orch, recipe: dict, stage_hook=None):
         39 |     log = getattr(orch, "log", lambda *a, **k: None)
         40 |     project_id = recipe.get("track_id") or f"track_{int(time.time())}"
  ```

### `app/core/pipeline_core.py` — 2 шт.
- **строка 42** — public function 'execute' без docstring
  ```
         40 |         self.func = func
         41 | 
  >>>    42 |     def execute(self, context: PipelineContext) -> StageResult:
         43 |         start_time = time.time()
         44 |         logger.info(f"stage={self.name} event=start")
  ```
- **строка 103** — public function 'run' без docstring
  ```
        101 |     CHECKPOINT_TTL_SEC = 24 * 3600
        102 | 
  >>>   103 |     def run(self, use_checkpoints: bool = True) -> Dict[str, Any]:
        104 |         logger.info(f"Launching pipeline for project: {self.context.project_id}")
        105 | 
  ```

### `app/gui/onboarding.py` — 1 шт.
- **строка 180** — public function 'render' без docstring
  ```
        178 |         self.render()
        179 | 
  >>>   180 |     def render(self):
        181 |         s = TOUR_STEPS[self.step]
        182 |         self.title.setText(s["title"])
  ```

### `app/gui/theme.py` — 1 шт.
- **строка 4** — public function 'apply_dark' без docstring
  ```
          2 | 
          3 | 
  >>>     4 | def apply_dark(app):
          5 |     try:
          6 |         from PySide6.QtGui import QColor, QPalette
  ```

### `app/gui/wizard.py` — 12 шт.
- **строка 298** — public function 'commit' без docstring
  ```
        296 |         self.root.addWidget(gb)
        297 | 
  >>>   298 |     def commit(self, recipe):
        299 |         keys = [
        300 |             None,
  ```
- **строка 381** — public function 'search' без docstring
  ```
        379 |         self.root.addLayout(opt)
        380 | 
  >>>   381 |     def search(self):
        382 |         try:
        383 |             from agents import sample_hunter
  ```
- **строка 500** — public function 'enter' без docstring
  ```
        498 |         self.timer.start(2000)
        499 | 
  >>>   500 |     def enter(self):
        501 |         try:
        502 |             from modules.voice_convert import vault_summary
  ```
- **строка 526** — public function 'train_rvc' без docstring
  ```
        524 |             QMessageBox.warning(self, "Караоке", f"Пока недоступно: {e}")
        525 | 
  >>>   526 |     def train_rvc(self, night: bool = False):
        527 |         try:
        528 |             from modules.voice_convert import train_rvc_model
  ```
- **строка 541** — public function 'refresh_status' без docstring
  ```
        539 |             QMessageBox.warning(self, "RVC", f"Ошибка запуска: {e}")
        540 | 
  >>>   541 |     def refresh_status(self):
        542 |         try:
        543 |             from modules.voice_convert import get_training_status
  ```
- **строка 663** — public function 'start' без docstring
  ```
        661 |         self.batch_tids = []
        662 | 
  >>>   663 |     def start(self):
        664 |         recipe = self.wizard.recipe
        665 |         if not recipe.get("references") and not recipe.get("preset"):
  ```
- **строка 676** — public function 'start_batch' без docstring
  ```
        674 |         self.btn_start.setEnabled(False)
        675 | 
  >>>   676 |     def start_batch(self):
        677 |         recipe = self.wizard.recipe
        678 |         if not recipe.get("preset") and not recipe.get("references"):
  ```
- **строка 702** — public function 'tick' без docstring
  ```
        700 |         self.queue_label.setText(f"Очередь: {len(self.batch_tids)} треков в работе")
        701 | 
  >>>   702 |     def tick(self):
        703 |         # обновляем очередь
        704 |         active = list(self.batch_tids) + (
  ```
- **строка 795** — public function 'show_result' без docstring
  ```
        793 |         self.current_job = None
        794 | 
  >>>   795 |     def show_result(self, job):
        796 |         self.current_job = job
        797 |         result = job.result or {}
  ```
- **строка 818** — public function 'open_folder' без docstring
  ```
        816 |             self.detector.setText("🧪 AI-детектор: пока не запускался")
        817 | 
  >>>   818 |     def open_folder(self):
        819 |         if not self.current_job:
        820 |             return
  ```
- **строка 850** — public function 'three_variants' без docstring
  ```
        848 |         QMessageBox.information(self, "Готово", f"«{item}» пойдёт заново в очередь.")
        849 | 
  >>>   850 |     def three_variants(self):
        851 |         if not self.current_job:
        852 |             return
  ```
- **строка 1022** — public function 'launch_gradio_expert' без docstring
  ```
       1020 |             self.log.warning(f"go_to_result failed: {e}")
       1021 | 
  >>>  1022 |     def launch_gradio_expert(self):
       1023 |         self.log.info("Ctrl+E → v5 Gradio")
       1024 | 
  ```

### `app/gui/wizard_v8_extensions.py` — 2 шт.
- **строка 197** — public function 'refresh' без docstring
  ```
        195 |             self.refresh()
        196 | 
  >>>   197 |         def refresh(self):
        198 |             try:
        199 |                 from app.core.hw_autodetect import detect
  ```
- **строка 234** — public function 'set_report' без docstring
  ```
        232 |             self.lay.addWidget(self.actions_area, 1)
        233 | 
  >>>   234 |         def set_report(self, report: dict):
        235 |             for i in reversed(range(self.actions_lay.count())):
        236 |                 w = self.actions_lay.itemAt(i).widget()
  ```

### `app/hw_probe.py` — 1 шт.
- **строка 21** — public function 'probe' без docstring
  ```
         19 | 
         20 | 
  >>>    21 | def probe() -> HW:
         22 |     try:
         23 |         import psutil
  ```

### `app/logger.py` — 1 шт.
- **строка 28** — public function 'setup_logger' без docstring
  ```
         26 | 
         27 | 
  >>>    28 | def setup_logger(name: str = "mmzs") -> logging.Logger:
         29 |     os.makedirs("logs", exist_ok=True)
         30 |     log = logging.getLogger(name)
  ```

### `app/plugins/base.py` — 1 шт.
- **строка 40** — public function 'process' без docstring
  ```
         38 |         return self
         39 | 
  >>>    40 |     def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
         41 |         for plugin in self.plugins:
         42 |             if plugin.enabled:
  ```

### `install.py` — 1 шт.
- **строка 37** — public function 'setup' без docstring
  ```
         35 |         return False
         36 | 
  >>>    37 | def setup():
         38 |     print("=== ZS Music Maker Installer (Singularity Refactored) ===")
         39 |     os_name = platform.system()
  ```

### `main.py` — 1 шт.
- **строка 417** — public function 'main' без docstring
  ```
        415 | 
        416 | 
  >>>   417 | def main() -> int:
        418 |     _setup_console_encoding()
        419 |     _header()
  ```

### `modules/artist_dossier/collectors.py` — 4 шт.
- **строка 13** — public function 'collect' без docstring
  ```
         11 |         self.folder = Path(folder)
         12 | 
  >>>    13 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
         14 |         if not self.folder.exists():
         15 |             return []
  ```
- **строка 32** — public function 'collect' без docstring
  ```
         30 |         self.vault = Path(vault_root)
         31 | 
  >>>    32 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
         33 |         cand = [self.vault / "author_corpus" / artist,
         34 |                 self.vault / "author_corpus" / artist.lower(),
  ```
- **строка 51** — public function 'collect' без docstring
  ```
         49 |         self.max_songs = max_songs
         50 | 
  >>>    51 |     def collect(self, artist: str) -> List[Dict[str, Any]]:
         52 |         if not self.token:
         53 |             return []
  ```
- **строка 75** — public function 'collect' без docstring
  ```
         73 |         self.max_tracks = max_tracks
         74 | 
  >>>    75 |     def collect(self, artist: str, titles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
         76 |         try:
         77 |             import yt_dlp
  ```

### `modules/artist_dossier/manager.py` — 4 шт.
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

### `modules/beat_gen.py` — 2 шт.
- **строка 50** — public function 'build_prompt' без docstring
  ```
         48 | 
         49 | 
  >>>    50 | def build_prompt(
         51 |     style_vector: dict, user_extra: str = "", samples_desc: str = ""
         52 | ) -> str:
  ```
- **строка 132** — public function 'generate_from_samples' без docstring
  ```
        130 | 
        131 | 
  >>>   132 | def generate_from_samples(
        133 |     sample_paths: list, style_vector: dict, duration_sec: int = 90
        134 | ) -> str:
  ```

### `modules/beat_gen_ai.py` — 1 шт.
- **строка 10** — public function 'render_beat_ai' без docstring
  ```
          8 | 
          9 | 
  >>>    10 | def render_beat_ai(prompt: str, bpm: int = 140, duration_sec: int = 120,
         11 |                    out_path: str = "beat.wav", reference_wav: Optional[str] = None,
         12 |                    chunk_sec: int = 20) -> Dict[str, Any]:
  ```

### `modules/cover_art_ai.py` — 1 шт.
- **строка 10** — public function 'render_cover_ai' без docstring
  ```
          8 | 
          9 | 
  >>>    10 | def render_cover_ai(title: str, artist: str, genre: str, mood: str,
         11 |                     out_path: str, size: int = 1024) -> Dict[str, Any]:
         12 |     prompt = P.build_cover_prompt(title, artist, genre, mood)
  ```

### `modules/distribution_export_v11.py` — 7 шт.
- **строка 105** — public function 'build_spotify_package' без docstring
  ```
        103 | 
        104 | 
  >>>   105 | def build_spotify_package(meta, files, out_dir):
        106 |     d = os.path.join(out_dir, "spotify_dsp")
        107 |     os.makedirs(d, exist_ok=True)
  ```
- **строка 170** — public function 'build_yandex_vk_package' без docstring
  ```
        168 | 
        169 | 
  >>>   170 | def build_yandex_vk_package(meta, files, out_dir):
        171 |     d = os.path.join(out_dir, "yandex_vk_ru")
        172 |     os.makedirs(d, exist_ok=True)
  ```
- **строка 234** — public function 'build_tiktok_package' без docstring
  ```
        232 | 
        233 | 
  >>>   234 | def build_tiktok_package(meta, files, out_dir):
        235 |     d = os.path.join(out_dir, "tiktok")
        236 |     os.makedirs(d, exist_ok=True)
  ```
- **строка 309** — public function 'build_youtube_package' без docstring
  ```
        307 | 
        308 | 
  >>>   309 | def build_youtube_package(meta, files, out_dir):
        310 |     d = os.path.join(out_dir, "youtube")
        311 |     os.makedirs(d, exist_ok=True)
  ```
- **строка 382** — public function 'build_shazam_package' без docstring
  ```
        380 | 
        381 | 
  >>>   382 | def build_shazam_package(meta, out_dir):
        383 |     d = os.path.join(out_dir, "shazam_ready")
        384 |     os.makedirs(d, exist_ok=True)
  ```
- **строка 405** — public function 'build_all_distribution_packages' без docstring
  ```
        403 | 
        404 | 
  >>>   405 | def build_all_distribution_packages(meta, files, out_dir):
        406 |     meta.ensure()
        407 |     os.makedirs(out_dir, exist_ok=True)
  ```
- **строка 50** — public function 'ensure' без docstring
  ```
         48 |     lyrics_en_hook: str = ""
         49 | 
  >>>    50 |     def ensure(self):
         51 |         if not self.release_date:
         52 |             self.release_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
  ```

### `modules/expert_mode_v11.py` — 3 шт.
- **строка 196** — public function 'validate' без docstring
  ```
        194 | 
        195 | 
  >>>   196 | def validate(cfg):
        197 |     errors, warnings = [], []
        198 |     if cfg.render.length_sec < 60:
  ```
- **строка 138** — public function 'to_flat_dict' без docstring
  ```
        136 |     render: ExpertRender = field(default_factory=ExpertRender)
        137 | 
  >>>   138 |     def to_flat_dict(self) -> dict[str, Any]:
        139 |         out: dict[str, Any] = {
        140 |             "expert_mode_enabled": self.enabled,
  ```
- **строка 172** — public function 'from_dict' без docstring
  ```
        170 | 
        171 |     @classmethod
  >>>   172 |     def from_dict(cls, raw):
        173 |         def _build(dc_cls, data):
        174 |             if not isinstance(data, dict):
  ```

### `modules/genre_engine.py` — 1 шт.
- **строка 99** — public function 'create_wizard_state' без docstring
  ```
         97 |         self.registry = registry
         98 | 
  >>>    99 |     def create_wizard_state(self, genre_name: str, override: dict = None) -> dict:
        100 |         profile = self.registry.get_profile(genre_name)
        101 |         import random
  ```

### `modules/health_v12.py` — 1 шт.
- **строка 331** — public function 'main' без docstring
  ```
        329 | 
        330 | 
  >>>   331 | def main(argv: list[str] | None = None) -> int:
        332 |     argv = argv or sys.argv[1:]
        333 |     rep = collect()
  ```

### `modules/hit_kpi_monitor_v11.py` — 5 шт.
- **строка 114** — public function 'check_release_completeness' без docstring
  ```
        112 | 
        113 | 
  >>>   114 | def check_release_completeness(release_dir, hw_mode="full_hw"):
        115 |     required = KPI_TARGETS.get(hw_mode, KPI_TARGETS["full_hw"])["release_required"]
        116 |     patterns = {
  ```
- **строка 166** — public function 'check_ai_detector' без docstring
  ```
        164 | 
        165 | 
  >>>   166 | def check_ai_detector(report):
        167 |     if not report:
        168 |         return -1.0
  ```
- **строка 193** — public function 'finalize_session' без docstring
  ```
        191 | 
        192 | 
  >>>   193 | def finalize_session(
        194 |     session, release_dir=None, ai_detector_report=None, save_dir="data"
        195 | ):
  ```
- **строка 267** — public function 'render_kpi_report_md' без docstring
  ```
        265 | 
        266 | 
  >>>   267 | def render_kpi_report_md(session):
        268 |     lines = [
        269 |         "# KPI-отчёт по проекту `" + session.project_id + "`",
  ```
- **строка 301** — public function 'latest_sessions' без docstring
  ```
        299 | 
        300 | 
  >>>   301 | def latest_sessions(save_dir="data", limit=20):
        302 |     p = os.path.join(save_dir, "kpi_history.jsonl")
        303 |     if not os.path.exists(p):
  ```

### `modules/kpi_dashboard_v12.py` — 3 шт.
- **строка 297** — public function 'build' без docstring
  ```
        295 | 
        296 | 
  >>>   297 | def build(save: bool = True) -> Dashboard:
        298 |     health = _load_json(ROOT / "data" / "health_v12.json")
        299 |     pipe_path = _newest("master_pipeline_v12.json", ROOT / "output")
  ```
- **строка 351** — public function 'render_markdown' без docstring
  ```
        349 | 
        350 | 
  >>>   351 | def render_markdown(dash: Dashboard) -> str:
        352 |     lines = [
        353 |         "# KPI Dashboard v12 «Hit Locked Pro»",
  ```
- **строка 380** — public function 'render_text' без docstring
  ```
        378 | 
        379 | 
  >>>   380 | def render_text(dash: Dashboard) -> str:
        381 |     out = [
        382 |         "=" * 72,
  ```

### `modules/llm_clients_v15.py` — 5 шт.
- **строка 127** — public function 'call_ollama' без docstring
  ```
        125 | 
        126 | 
  >>>   127 | def call_ollama(
        128 |     prompt: str,
        129 |     system: str = "",
  ```
- **строка 169** — public function 'call_openrouter' без docstring
  ```
        167 | 
        168 | 
  >>>   169 | def call_openrouter(
        170 |     prompt: str,
        171 |     system: str = "",
  ```
- **строка 212** — public function 'call_grok' без docstring
  ```
        210 | 
        211 | 
  >>>   212 | def call_grok(
        213 |     prompt: str,
        214 |     system: str = "",
  ```
- **строка 253** — public function 'call_gemini' без docstring
  ```
        251 | 
        252 | 
  >>>   253 | def call_gemini(
        254 |     prompt: str,
        255 |     system: str = "",
  ```
- **строка 425** — public function 'complete' без docstring
  ```
        423 |         return r
        424 | 
  >>>   425 |     def complete(
        426 |         self,
        427 |         prompt: str,
  ```

### `modules/lyric_vault_v10.py` — 1 шт.
- **строка 161** — public function 'rebuild_index' без docstring
  ```
        159 | 
        160 | 
  >>>   161 | def rebuild_index() -> dict[str, Any]:
        162 |     all_lines = load_all()
        163 |     idx = {
  ```

### `modules/lyrics_gen_ai.py` — 1 шт.
- **строка 17** — public function 'generate_lyrics_ai' без docstring
  ```
         15 | 
         16 | 
  >>>    17 | def generate_lyrics_ai(theme, style_vector=None, n_verses=2, user_lyrics_lines=None,
         18 |                        bilingual=True, artist_slug=None, track_id=None,
         19 |                        genre="phonk") -> Dict[str, Any]:
  ```

### `modules/mastering_ai.py` — 1 шт.
- **строка 9** — public function 'master_ai' без docstring
  ```
          7 | 
          8 | 
  >>>     9 | def master_ai(input_wav: str, out_wav: str, reference_wav: Optional[str] = None,
         10 |               target_lufs: float = -9.0) -> Dict[str, Any]:
         11 |     Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
  ```

### `modules/presets.py` — 2 шт.
- **строка 128** — public function 'save_user_preset' без docstring
  ```
        126 | 
        127 | 
  >>>   128 | def save_user_preset(key: str, preset: dict) -> dict:
        129 |     user = {}
        130 |     if os.path.exists(PRESETS_FILE):
  ```
- **строка 142** — public function 'preset_to_style_vector' без docstring
  ```
        140 | 
        141 | 
  >>>   142 | def preset_to_style_vector(key: str) -> dict:
        143 |     p = get_preset(key)
        144 |     if "error" in p:
  ```

### `modules/render_queue.py` — 1 шт.
- **строка 181** — public function 'morning_report' без docstring
  ```
        179 | 
        180 |     # ------------------------------------------------------- morning report
  >>>   181 |     def morning_report(self) -> dict:
        182 |         done = [i for i in self.items if i.status == "done"]
        183 |         errs = [i for i in self.items if i.status == "error"]
  ```

### `modules/self_diag_v13.py` — 2 шт.
- **строка 236** — public function 'render_report' без docstring
  ```
        234 | 
        235 | 
  >>>   236 | def render_report(
        237 |     layout: list[dict[str, Any]],
        238 |     health: dict[str, Any] | None,
  ```
- **строка 294** — public function 'run' без docstring
  ```
        292 | 
        293 | 
  >>>   294 | def run(save_to_log: bool = True) -> dict[str, Any]:
        295 |     layout = check_layout()
        296 |     health = check_health()
  ```

### `modules/sidechain.py` — 2 шт.
- **строка 234** — public function 'measure_ducking_effect' без docstring
  ```
        232 | 
        233 | 
  >>>   234 | def measure_ducking_effect(bus_before, bus_after, kick, sr: int) -> float:
        235 |     if _np is None:
        236 |         return 0.0
  ```
- **строка 258** — public function 'apply_sidechain' без docstring
  ```
        256 | 
        257 | 
  >>>   258 | def apply_sidechain(
        259 |     bus_wav: str,
        260 |     kick_wav: str,
  ```

### `modules/tiktok_edit_v9.py` — 1 шт.
- **строка 93** — public function 'cut_slice' без docstring
  ```
         91 | 
         92 | 
  >>>    93 | def cut_slice(
         94 |     input_wav: str, output_wav: str, start_sec: float, end_sec: float, fade: bool = True
         95 | ) -> dict:
  ```

### `modules/track_templates.py` — 1 шт.
- **строка 41** — public function 'save_template' без docstring
  ```
         39 | 
         40 | # ------------------------------------------------------- templates
  >>>    41 | def save_template(name: str, recipe: dict) -> str:
         42 |     tid = uuid.uuid4().hex[:10]
         43 |     data = {
  ```

### `modules/user_profile.py` — 1 шт.
- **строка 37** — public function 'get_profile' без docstring
  ```
         35 | 
         36 | 
  >>>    37 | def get_profile() -> dict:
         38 |     if not PROFILE_FILE.exists():
         39 |         p = dict(DEFAULT_PROFILE)
  ```

### `modules/video_edit_v11.py` — 2 шт.
- **строка 268** — public function 'build_video' без docstring
  ```
        266 | 
        267 | 
  >>>   268 | def build_video(req: VideoEditRequest) -> VideoEditResult:
        269 |     os.makedirs(os.path.dirname(os.path.abspath(req.output_path)) or ".", exist_ok=True)
        270 |     tmp_dir = os.path.join(
  ```
- **строка 423** — public function 'build_release_edits' без docstring
  ```
        421 | 
        422 | 
  >>>   423 | def build_release_edits(
        424 |     master_wav, cover_png, lyrics_lrc, bpm, title, artist, out_dir
        425 | ) -> dict:
  ```

### `modules/voice_onboarding.py` — 5 шт.
- **строка 113** — public function 'build_plan' без docstring
  ```
        111 | 
        112 | 
  >>>   113 | def build_plan() -> list[OnboardingStep]:
        114 |     steps: list[OnboardingStep] = []
        115 |     per_phrase = int(PLAN["phoneme_text"] / len(PHONEME_SCRIPT))
  ```
- **строка 152** — public function 'compute_phoneme_coverage' без docstring
  ```
        150 | 
        151 | 
  >>>   152 | def compute_phoneme_coverage(texts: list[str]) -> dict[str, Any]:
        153 |     seen = set()
        154 |     for t in texts:
  ```
- **строка 183** — public function 'record_step' без docstring
  ```
        181 | 
        182 | 
  >>>   183 | def record_step(step: OnboardingStep, mode: str = "auto") -> OnboardingStep:
        184 |     try:
        185 |         from modules import voice_recording as vr
  ```
- **строка 204** — public function 'compute_progress' без docstring
  ```
        202 | 
        203 | 
  >>>   204 | def compute_progress(steps: list[OnboardingStep]) -> OnboardingProgress:
        205 |     total_rec = sum(s.duration_sec for s in steps)
        206 |     styles_done = sum(
  ```
- **строка 237** — public function 'run_cli' без docstring
  ```
        235 | 
        236 | 
  >>>   237 | def run_cli() -> int:
        238 |     print("=" * 64)
        239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
  ```

### `modules/voice_recording.py` — 6 шт.
- **строка 253** — public function 'split_wav_into_takes' без docstring
  ```
        251 | 
        252 | 
  >>>   253 | def split_wav_into_takes(
        254 |     wav_path: str,
        255 |     min_silence_ms: int = 600,
  ```
- **строка 373** — public function 'capability_report' без docstring
  ```
        371 | 
        372 | 
  >>>   373 | def capability_report() -> dict[str, Any]:
        374 |     devices = []
        375 |     if SD_OK:
  ```
- **строка 142** — public function 'start' без docstring
  ```
        140 |             pass
        141 | 
  >>>   142 |     def start(self) -> dict[str, Any]:
        143 |         self._buf = []
        144 |         self._start_ts = time.time()
  ```
- **строка 174** — public function 'stop' без docstring
  ```
        172 |             return {"ok": False, "backend": self._backend, "reason": str(e)}
        173 | 
  >>>   174 |     def stop(self) -> dict[str, Any]:
        175 |         self._stop_ts = time.time()
        176 |         if not self._active or self._stream is None:
  ```
- **строка 213** — public function 'ingest_wav' без docstring
  ```
        211 |             w.writeframes(x.tobytes())
        212 | 
  >>>   213 |     def ingest_wav(
        214 |         self, wav_path: str, style: str = "conversational"
        215 |     ) -> dict[str, Any]:
  ```
- **строка 239** — public function 'stop_and_split' без docstring
  ```
        237 |             return {"ok": False, "reason": str(e)}
        238 | 
  >>>   239 |     def stop_and_split(
        240 |         self, min_silence_ms: int = 600, min_take_ms: int = 800
        241 |     ) -> list[TakeInfo]:
  ```

### `modules/voice_synth_ai.py` — 1 шт.
- **строка 9** — public function 'synth_vocal_ai' без docstring
  ```
          7 | 
          8 | 
  >>>     9 | def synth_vocal_ai(text: str, out_path: str, speaker_wav: Optional[str] = None,
         10 |                    language: str = "ru", rvc_model: Optional[str] = None) -> Dict[str, Any]:
         11 |     if not text or not text.strip():
  ```

### `modules/voice_vault_v9.py` — 4 шт.
- **строка 170** — public function 'add_recording' без docstring
  ```
        168 | 
        169 | # ============================================================ main API
  >>>   170 | def add_recording(
        171 |     src_path: str,
        172 |     style_hint: str | None = None,
  ```
- **строка 225** — public function 'clean_stats' без docstring
  ```
        223 | 
        224 | 
  >>>   225 | def clean_stats() -> dict:
        226 |     idx = _load_index()
        227 |     items = list(idx.get("items", {}).values())
  ```
- **строка 257** — public function 'export_manifest_for_rvc' без docstring
  ```
        255 | 
        256 | 
  >>>   257 | def export_manifest_for_rvc(out_path: str | None = None) -> str:
        258 |     idx = _load_index()
        259 |     good = []
  ```
- **строка 285** — public function 'maybe_trigger_retrain' без docstring
  ```
        283 | 
        284 | 
  >>>   285 | def maybe_trigger_retrain(rvc_trainer=None) -> dict:
        286 |     stats = clean_stats()
        287 |     if not stats["ready_for_retrain"]:
  ```

### `modules/wizard_v12_integration.py` — 1 шт.
- **строка 249** — public function 'patched' без docstring
  ```
        247 | 
        248 |         # замыкаем чтобы не зациклиться
  >>>   249 |         def patched(*args, **kwargs):
        250 |             project_id = kwargs.get("project_id") or (
        251 |                 args[0] if args else "wizard_project"
  ```

### `tests/test_ai_layer.py` — 3 шт.
- **строка 358** — public function 'test_lyrics_quality_accepts_structured_non_repetitive_text' без docstring
  ```
        356 | 
        357 | 
  >>>   358 | def test_lyrics_quality_accepts_structured_non_repetitive_text() -> None:
        359 |     from app.ai.quality import validate_lyrics
        360 | 
  ```
- **строка 416** — public function 'test_asr_transcribes_reference_with_faster_whisper_contract' без docstring
  ```
        414 | 
        415 | 
  >>>   416 | def test_asr_transcribes_reference_with_faster_whisper_contract(tmp_path) -> None:
        417 |     from types import SimpleNamespace
        418 | 
  ```
- **строка 454** — public function 'test_asr_rejects_invalid_transcript_without_writing_file' без docstring
  ```
        452 | 
        453 | 
  >>>   454 | def test_asr_rejects_invalid_transcript_without_writing_file(tmp_path) -> None:
        455 |     from types import SimpleNamespace
        456 | 
  ```

### `tests/test_ai_quality.py` — 10 шт.
- **строка 14** — public function 'test_metadata_quality_accepts_complete_release_payload' без docstring
  ```
         12 | 
         13 | 
  >>>    14 | def test_metadata_quality_accepts_complete_release_payload() -> None:
         15 |     payload = {
         16 |         "title": "Ночной маршрут",
  ```
- **строка 38** — public function 'test_audio_quality_accepts_signal_and_rejects_silence' без docstring
  ```
         36 | 
         37 | 
  >>>    38 | def test_audio_quality_accepts_signal_and_rejects_silence(tmp_path) -> None:
         39 |     sample_rate = 8_000
         40 |     t = np.arange(sample_rate * 2) / sample_rate
  ```
- **строка 99** — public function 'test_music_stereo_handle_renders_separate_stereo_texture' без docstring
  ```
         97 | 
         98 | 
  >>>    99 | def test_music_stereo_handle_renders_separate_stereo_texture(tmp_path) -> None:
        100 |     from app.core.orchestrator_ai import render_stereo_texture
        101 | 
  ```
- **строка 126** — public function 'test_stereo_texture_quality_rejects_mono_like_audio' без docstring
  ```
        124 | 
        125 | 
  >>>   126 | def test_stereo_texture_quality_rejects_mono_like_audio(tmp_path) -> None:
        127 |     from app.ai.quality import validate_stereo_texture
        128 | 
  ```
- **строка 164** — public function 'test_xtts_handle_saves_vocal_artifact_and_propagates_speaker' без docstring
  ```
        162 | 
        163 | 
  >>>   164 | def test_xtts_handle_saves_vocal_artifact_and_propagates_speaker(tmp_path) -> None:
        165 |     from app.core.orchestrator_ai import render_xtts_vocal
        166 | 
  ```
- **строка 189** — public function 'test_vocal_quality_accounts_for_text_length' без docstring
  ```
        187 | 
        188 | 
  >>>   189 | def test_vocal_quality_accounts_for_text_length(tmp_path) -> None:
        190 |     from app.ai.quality import validate_vocal_artifact
        191 | 
  ```
- **строка 206** — public function 'test_voice_synth_fallback_validates_and_copies_audio' без docstring
  ```
        204 | 
        205 | 
  >>>   206 | def test_voice_synth_fallback_validates_and_copies_audio(tmp_path) -> None:
        207 |     from app.core.orchestrator_ai import render_voice_synth_fallback
        208 | 
  ```
- **строка 256** — public function 'test_rvc_handle_uses_public_infer_contract_and_copies_result' без docstring
  ```
        254 | 
        255 | 
  >>>   256 | def test_rvc_handle_uses_public_infer_contract_and_copies_result(tmp_path) -> None:
        257 |     from app.core.orchestrator_ai import render_rvc_vocal
        258 | 
  ```
- **строка 287** — public function 'test_rvc_quality_requires_duration_preservation' без docstring
  ```
        285 | 
        286 | 
  >>>   287 | def test_rvc_quality_requires_duration_preservation(tmp_path) -> None:
        288 |     from app.ai.quality import validate_rvc_artifact
        289 | 
  ```
- **строка 306** — public function 'test_stem_quality_requires_near_input_duration' без docstring
  ```
        304 | 
        305 | 
  >>>   306 | def test_stem_quality_requires_near_input_duration(tmp_path) -> None:
        307 |     from app.ai.quality import validate_stem_artifact
        308 | 
  ```

### `tests/test_data_inventory.py` — 1 шт.
- **строка 16** — public function 'test_inventory_reports_unknown_and_invalid_assets' без docstring
  ```
         14 | 
         15 | 
  >>>    16 | def test_inventory_reports_unknown_and_invalid_assets(tmp_path) -> None:
         17 |     (tmp_path / "genre_presets").mkdir()
         18 |     (tmp_path / "genre_presets" / "valid.json").write_text("{}", encoding="utf-8")
  ```

### `tools/ab_compare.py` — 2 шт.
- **строка 112** — public function 'compare' без docstring
  ```
        110 | 
        111 | 
  >>>   112 | def compare(user_wav: str, ref_wav: str, out_dir: str) -> dict[str, Any]:
        113 |     out = Path(out_dir)
        114 |     out.mkdir(parents=True, exist_ok=True)
  ```
- **строка 213** — public function 'main' без docstring
  ```
        211 | 
        212 | 
  >>>   213 | def main():
        214 |     p = argparse.ArgumentParser()
        215 |     p.add_argument("user_wav")
  ```

### `tools/ast_dead_imports.py` — 2 шт.
- **строка 82** — public function 'scan_all' без docstring
  ```
         80 | 
         81 | 
  >>>    82 | def scan_all(dirs: list[str]) -> dict[str, list[tuple[int, str]]]:
         83 |     report: dict[str, list[tuple[int, str]]] = {}
         84 |     files: list[Path] = []
  ```
- **строка 107** — public function 'main' без docstring
  ```
        105 | 
        106 | 
  >>>   107 | def main() -> int:
        108 |     dirs = sys.argv[1:] or DEFAULT_DIRS
        109 |     report = scan_all(dirs)
  ```

### `tools/audit_data_inventory.py` — 1 шт.
- **строка 113** — public function 'main' без docstring
  ```
        111 | 
        112 | 
  >>>   113 | def main(argv: list[str] | None = None) -> int:
        114 |     parser = argparse.ArgumentParser(description="Validate and inventory versioned data assets")
        115 |     parser.add_argument("--json", action="store_true", help="print the complete report as JSON")
  ```

### `tools/deep_audit_v40.py` — 2 шт.
- **строка 54** — public function 'audit_file' без docstring
  ```
         52 | 
         53 | 
  >>>    54 | def audit_file(p: Path) -> dict:
         55 |     src = read_src(p)
         56 |     lines = src.splitlines()
  ```
- **строка 259** — public function 'main' без docstring
  ```
        257 | 
        258 | 
  >>>   259 | def main():
        260 |     files = all_py_files()
        261 |     reports = []
  ```

### `tools/fallback_audit.py` — 3 шт.
- **строка 63** — public function 'scan_file' без docstring
  ```
         61 | 
         62 | 
  >>>    63 | def scan_file(path: Path) -> dict[str, list[dict[str, Any]]]:
         64 |     rel = str(path.relative_to(ROOT))
         65 |     if rel in SELF_SKIP:
  ```
- **строка 107** — public function 'scan_all' без docstring
  ```
        105 | 
        106 | 
  >>>   107 | def scan_all() -> dict[str, Any]:
        108 |     all_hits: dict[str, list[dict[str, Any]]] = {}
        109 |     files_scanned = 0
  ```
- **строка 149** — public function 'main' без docstring
  ```
        147 | 
        148 | 
  >>>   149 | def main() -> int:
        150 |     r = scan_all()
        151 |     out_dir = ROOT / "output" / "audit_v14"
  ```

### `tools/genre_validator.py` — 1 шт.
- **строка 17** — public function 'validate_all' без docstring
  ```
         15 | from modules.genre_engine import StyleRegistry, GenreFactory
         16 | 
  >>>    17 | def validate_all():
         18 |     print("=== Genre Integrity Audit (100+ Styles) ===")
         19 |     reg = StyleRegistry()
  ```

### `tools/lazy_dirs_patch.py` — 1 шт.
- **строка 152** — public function 'main' без docstring
  ```
        150 | 
        151 | 
  >>>   152 | def main():
        153 |     modified = []
        154 |     for fname, rules in PATCHES.items():
  ```

### `tools/pull_ai_models.py` — 2 шт.
- **строка 55** — public function 'pull' без docstring
  ```
         53 | 
         54 | 
  >>>    55 | def pull(key):
         56 |     spec = MODEL_REGISTRY[key]
         57 |     eng = spec["engine"]
  ```
- **строка 72** — public function 'main' без docstring
  ```
         70 | 
         71 | 
  >>>    72 | def main():
         73 |     ap = argparse.ArgumentParser()
         74 |     ap.add_argument("--model"); ap.add_argument("--list", action="store_true")
  ```

### `tools/readiness.py` — 7 шт.
- **строка 58** — public function 'probe_architecture' без docstring
  ```
         56 | 
         57 | 
  >>>    58 | def probe_architecture() -> dict[str, str]:
         59 |     p: dict[str, str] = {}
         60 |     stray = list((ROOT).glob("main_v*.py"))
  ```
- **строка 81** — public function 'probe_core_modules' без docstring
  ```
         79 | 
         80 | 
  >>>    81 | def probe_core_modules() -> dict[str, str]:
         82 |     p: dict[str, str] = {}
         83 |     p["analyzer"] = "REAL_PASS" if _module_exists("modules.analyzer") else "MISSING"
  ```
- **строка 112** — public function 'probe_audio_pipeline' без docstring
  ```
        110 | 
        111 | 
  >>>   112 | def probe_audio_pipeline() -> dict[str, str]:
        113 |     p: dict[str, str] = {}
        114 |     try:
  ```
- **строка 151** — public function 'probe_voice_rvc' без docstring
  ```
        149 | 
        150 | 
  >>>   151 | def probe_voice_rvc() -> dict[str, str]:
        152 |     p: dict[str, str] = {}
        153 |     p["voice_recording"] = (
  ```
- **строка 176** — public function 'probe_release' без docstring
  ```
        174 | 
        175 | 
  >>>   176 | def probe_release() -> dict[str, str]:
        177 |     p: dict[str, str] = {}
        178 |     p["release_pack_module"] = (
  ```
- **строка 203** — public function 'probe_testing' без docstring
  ```
        201 | 
        202 | 
  >>>   203 | def probe_testing() -> dict[str, str]:
        204 |     p: dict[str, str] = {}
        205 |     p["smoke_v14"] = "REAL_PASS" if _file_exists("tools/smoke_v14.py") else "MISSING"
  ```
- **строка 226** — public function 'compute' без docstring
  ```
        224 | 
        225 | 
  >>>   226 | def compute() -> tuple[float, dict[str, Any]]:
        227 |     blocks_raw = {
        228 |         "architecture": probe_architecture(),
  ```

### `tools/real_e2e_v14.py` — 1 шт.
- **строка 82** — public function 'main' без docstring
  ```
         80 | 
         81 | 
  >>>    82 | def main() -> int:
         83 |     print("=" * 64)
         84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
  ```

### `tools/smoke_v26.py` — 1 шт.
- **строка 60** — public function 'main' без docstring
  ```
         58 | 
         59 | 
  >>>    60 | def main():
         61 |     print("=" * 64)
         62 |     print("ZS Music Maker v26 — smoke_v26 (stereo + loudness + drop)")
  ```

### `tools/smoke_v29.py` — 4 шт.
- **строка 43** — public function 'test_version_cli' без docstring
  ```
         41 | 
         42 | 
  >>>    43 | def test_version_cli() -> None:
         44 |     try:
         45 |         out = subprocess.run(
  ```
- **строка 57** — public function 'test_midi_generator' без docstring
  ```
         55 | 
         56 | 
  >>>    57 | def test_midi_generator() -> None:
         58 |     from modules import midi_generator
         59 |     st = midi_generator.MIDIGenerator.get_status()
  ```
- **строка 76** — public function 'test_god_mode_e2e' без docstring
  ```
         74 | 
         75 | 
  >>>    76 | def test_god_mode_e2e() -> None:
         77 |     out_root = ROOT / "output" / "smoke_v29" / "god"
         78 |     if out_root.exists():
  ```
- **строка 141** — public function 'main' без docstring
  ```
        139 | 
        140 | 
  >>>   141 | def main() -> int:
        142 |     print("=" * 64)
        143 |     print("ZS Music Maker v29 — smoke_v29 (God Mode E2E)")
  ```

### `tools/validate_final_track.py` — 1 шт.
- **строка 29** — public function 'main' без docstring
  ```
         27 | 
         28 | 
  >>>    29 | def main() -> int:
         30 |     if len(sys.argv) > 1:
         31 |         track_path = Path(sys.argv[1])
  ```

### `ui/tutorial.py` — 1 шт.
- **строка 248** — public function 'next_step' без docstring
  ```
        246 | 
        247 | 
  >>>   248 | def next_step() -> dict:
        249 |     settings = get_tutorial_settings()
        250 |     idx = settings.get("current_step", 0)
  ```

### `updater/updater.py` — 9 шт.
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
