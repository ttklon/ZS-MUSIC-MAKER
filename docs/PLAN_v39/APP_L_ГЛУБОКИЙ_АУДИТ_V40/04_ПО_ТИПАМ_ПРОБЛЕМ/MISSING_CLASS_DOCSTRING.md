# MISSING_CLASS_DOCSTRING — Public-класс без docstring

**Severity:** 🟢 LOW
**Всего:** 98
**Как чинить:** Добавить """назначение класса, публичные методы""".

## Все вхождения

### `app/ai/registry.py` — 3 шт.
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

### `app/ai/sequential_runner.py` — 4 шт.
- **строка 17** — public class 'AIStage' без docstring
  ```
         15 | 
         16 | @dataclass
  >>>    17 | class AIStage:
         18 |     name: str
         19 |     model: Optional[str]
  ```
- **строка 27** — public class 'StageReport' без docstring
  ```
         25 | 
         26 | @dataclass
  >>>    27 | class StageReport:
         28 |     name: str
         29 |     ok: bool
  ```
- **строка 39** — public class 'RunReport' без docstring
  ```
         37 | 
         38 | @dataclass
  >>>    39 | class RunReport:
         40 |     stages: List[StageReport] = field(default_factory=list)
         41 |     total_sec: float = 0.0
  ```
- **строка 51** — public class 'SequentialAIRunner' без docstring
  ```
         49 | 
         50 | 
  >>>    51 | class SequentialAIRunner:
         52 |     def __init__(self):
         53 |         self.stages: List[AIStage] = []
  ```

### `app/core/license_manager.py` — 1 шт.
- **строка 25** — public class 'LicenseCheck' без docstring
  ```
         23 | 
         24 | @dataclass
  >>>    25 | class LicenseCheck:
         26 |     ok: bool
         27 |     needs_attribution: bool
  ```

### `app/core/model_manager.py` — 1 шт.
- **строка 18** — public class 'ModelManager' без docstring
  ```
         16 | # torch нужен ТОЛЬКО для load_torch_model → ленивый импорт внутри метода.
         17 | 
  >>>    18 | class ModelManager:
         19 |     def __init__(self):
         20 |         self.base_dir = Path(__file__).resolve().parents[2] / "models"
  ```

### `app/core/orchestrator.py` — 2 шт.
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

### `app/core/orchestrator_async.py` — 2 шт.
- **строка 18** — public class 'AsyncStage' без docstring
  ```
         16 | 
         17 | @dataclass
  >>>    18 | class AsyncStage:
         19 |     name: str
         20 |     ok: bool = False
  ```
- **строка 43** — public class 'AsyncOrchestrator' без docstring
  ```
         41 |     return stage
         42 | 
  >>>    43 | class AsyncOrchestrator:
         44 |     def __init__(self, project_id: str, out_root: Path):
         45 |         self.project_id = project_id
  ```

### `app/core/orchestrator_v10_patch.py` — 1 шт.
- **строка 221** — public class 'Dummy' без docstring
  ```
        219 | if __name__ == "__main__":
        220 | 
  >>>   221 |     class Dummy:
        222 |         pass
        223 | 
  ```

### `app/core/pipeline_core.py` — 4 шт.
- **строка 23** — public class 'StageResult' без docstring
  ```
         21 | 
         22 | @dataclass
  >>>    23 | class StageResult:
         24 |     name: str
         25 |     ok: bool
  ```
- **строка 31** — public class 'PipelineContext' без docstring
  ```
         29 | 
         30 | @dataclass
  >>>    31 | class PipelineContext:
         32 |     project_id: str
         33 |     config: Dict[str, Any]
  ```
- **строка 37** — public class 'PipelineStage' без docstring
  ```
         35 |     shared_data: Dict[str, Any] = field(default_factory=dict)
         36 | 
  >>>    37 | class PipelineStage:
         38 |     def __init__(self, name: str, func: Callable[[PipelineContext], Any]):
         39 |         self.name = name
  ```
- **строка 60** — public class 'ZSPipeline' без docstring
  ```
         58 |             return res
         59 | 
  >>>    60 | class ZSPipeline:
         61 |     def __init__(
         62 |         self,
  ```

### `app/gui/onboarding.py` — 1 шт.
- **строка 138** — public class 'OnboardingDialog' без docstring
  ```
        136 | 
        137 | 
  >>>   138 | class OnboardingDialog(QDialog):
        139 |     def __init__(self, parent=None):
        140 |         super().__init__(parent)
  ```

### `app/gui/wizard.py` — 11 шт.
- **строка 91** — public class 'StepBase' без docstring
  ```
         89 | 
         90 | 
  >>>    91 | class StepBase(QWidget):
         92 |     def __init__(self, wizard):
         93 |         super().__init__()
  ```
- **строка 112** — public class 'StepArtist' без docstring
  ```
        110 | # Шаг 0: имя артиста (только при первом запуске)
        111 | # ============================================================
  >>>   112 | class StepArtist(StepBase):
        113 |     def __init__(self, wizard):
        114 |         super().__init__(wizard)
  ```
- **строка 153** — public class 'StepReferences' без docstring
  ```
        151 | # Шаг 1: референсы + тема + длительность
        152 | # ============================================================
  >>>   153 | class StepReferences(StepBase):
        154 |     def __init__(self, wizard):
        155 |         super().__init__(wizard)
  ```
- **строка 239** — public class 'StepPreset' без docstring
  ```
        237 | # Шаг 2: стиль (пресет) + режим генерации + стенды
        238 | # ============================================================
  >>>   239 | class StepPreset(StepBase):
        240 |     def __init__(self, wizard):
        241 |         super().__init__(wizard)
  ```
- **строка 332** — public class 'StepSamples' без docstring
  ```
        330 | # Шаг 3: Sample Browser — split-view local vs online
        331 | # ============================================================
  >>>   332 | class StepSamples(StepBase):
        333 |     def __init__(self, wizard):
        334 |         super().__init__(wizard)
  ```
- **строка 414** — public class 'StepLyrics' без docstring
  ```
        412 | # Шаг 4: Текст (bilingual + user_lyrics_lines)
        413 | # ============================================================
  >>>   414 | class StepLyrics(StepBase):
        415 |     def __init__(self, wizard):
        416 |         super().__init__(wizard)
  ```
- **строка 457** — public class 'StepVoice' без docstring
  ```
        455 | # Шаг 5: Голос — ProVoice основной
        456 | # ============================================================
  >>>   457 | class StepVoice(StepBase):
        458 |     def __init__(self, wizard):
        459 |         super().__init__(wizard)
  ```
- **строка 571** — public class 'StepExpert' без docstring
  ```
        569 | # Шаг 6: Экспертные опции
        570 | # ============================================================
  >>>   571 | class StepExpert(StepBase):
        572 |     def __init__(self, wizard):
        573 |         super().__init__(wizard)
  ```
- **строка 620** — public class 'StepRun' без docstring
  ```
        618 | # Шаг 7: Запуск + очередь
        619 | # ============================================================
  >>>   620 | class StepRun(StepBase):
        621 |     def __init__(self, wizard):
        622 |         super().__init__(wizard)
  ```
- **строка 754** — public class 'StepResult' без docstring
  ```
        752 | # Шаг 8: Результат — 3 кнопки (Пересобрать / Переделать часть / 3 варианта)
        753 | # ============================================================
  >>>   754 | class StepResult(StepBase):
        755 |     def __init__(self, wizard):
        756 |         super().__init__(wizard)
  ```
- **строка 879** — public class 'Wizard' без docstring
  ```
        877 | # Wizard — главное окно
        878 | # ============================================================
  >>>   879 | class Wizard(QMainWindow):
        880 |     def __init__(self, orch, hw, log):
        881 |         super().__init__()
  ```

### `app/gui/wizard_v8_extensions.py` — 5 шт.
- **строка 49** — public class 'AuthorPickerPanel' без docstring
  ```
         47 | if PYSIDE_OK:
         48 | 
  >>>    49 |     class AuthorPickerPanel(QGroupBox):
         50 |         author_changed = Signal(str)
         51 | 
  ```
- **строка 137** — public class 'FemaleBackingPanel' без docstring
  ```
        135 |     # FemaleBackingPanel
        136 |     # ============================================================
  >>>   137 |     class FemaleBackingPanel(QGroupBox):
        138 |         def __init__(self, parent=None):
        139 |             super().__init__("Женский бэк-вокал (Silero v4 — Ksenia/Baya)", parent)
  ```
- **строка 190** — public class 'QualityBadge' без docstring
  ```
        188 |     # QualityBadge
        189 |     # ============================================================
  >>>   190 |     class QualityBadge(QLabel):
        191 |         def __init__(self, parent=None):
        192 |             super().__init__(parent)
  ```
- **строка 218** — public class 'AutoQAResultPanel' без docstring
  ```
        216 |     # AutoQAResultPanel
        217 |     # ============================================================
  >>>   218 |     class AutoQAResultPanel(QGroupBox):
        219 |         rebuild_requested = Signal(list)  # список targets
        220 | 
  ```
- **строка 276** — public class 'TemplateManagerDialog' без docstring
  ```
        274 |     # TemplateManagerDialog
        275 |     # ============================================================
  >>>   276 |     class TemplateManagerDialog(QDialog):
        277 |         def __init__(self, parent=None):
        278 |             super().__init__(parent)
  ```

### `app/hw_probe.py` — 1 шт.
- **строка 11** — public class 'HW' без docstring
  ```
          9 | 
         10 | @dataclass
  >>>    11 | class HW:
         12 |     gpu_name: str = "CPU"
         13 |     vram_gb: float = 0.0
  ```

### `app/plugins/advanced.py` — 5 шт.
- **строка 47** — public class 'PedalboardPlugin' без docstring
  ```
         45 |     PitchShift = TimeStretch = AddGaussianNoise = RoomSimulator = object  # type: ignore
         46 | 
  >>>    47 | class PedalboardPlugin(AudioPlugin):
         48 |     def __init__(self, name: str, effects: list):
         49 |         super().__init__(name)
  ```
- **строка 61** — public class 'PhonkDistortion' без docstring
  ```
         59 |             return self.board(audio, sr)
         60 | 
  >>>    61 | class PhonkDistortion(PedalboardPlugin):
         62 |     def __init__(self, drive_db: float = 20.0):
         63 |         super().__init__("PhonkDistortion", [
  ```
- **строка 69** — public class 'AntiAINeuroObfuscator' без docstring
  ```
         67 |         ])
         68 | 
  >>>    69 | class AntiAINeuroObfuscator(AudioPlugin):
         70 |     def __init__(self, intensity: float = 0.5):
         71 |         super().__init__("AntiAINeuroObfuscator")
  ```
- **строка 23** — public class 'Pedalboard' без docstring
  ```
         21 |             pass
         22 | 
  >>>    23 |     class Pedalboard:  # type: ignore
         24 |         def __init__(self, effects=None):
         25 |             self.effects = effects or []
  ```
- **строка 38** — public class 'Compose' без docstring
  ```
         36 |     _HAS_AUG = False
         37 | 
  >>>    38 |     class Compose:  # type: ignore
         39 |         def __init__(self, transforms=None):
         40 |             self.transforms = transforms or []
  ```

### `app/plugins/base.py` — 2 шт.
- **строка 16** — public class 'AudioPlugin' без docstring
  ```
         14 | import numpy as np
         15 | 
  >>>    16 | class AudioPlugin(ABC):
         17 |     def __init__(self, name: str):
         18 |         self.name = name
  ```
- **строка 32** — public class 'PluginChain' без docstring
  ```
         30 |         return f"<Plugin: {self.name} ({'Enabled' if self.enabled else 'Disabled'})>"
         31 | 
  >>>    32 | class PluginChain:
         33 |     def __init__(self):
         34 |         self.plugins = []
  ```

### `app/runtime_orchestrator.py` — 2 шт.
- **строка 16** — public class 'Job' без docstring
  ```
         14 | 
         15 | @dataclass
  >>>    16 | class Job:
         17 |     track_id: str
         18 |     recipe: dict[str, Any]
  ```
- **строка 29** — public class 'RuntimeOrchestrator' без docstring
  ```
         27 | 
         28 | 
  >>>    29 | class RuntimeOrchestrator:
         30 |     def __init__(self, log=None):
         31 |         self.log = log
  ```

### `main.py` — 1 шт.
- **строка 50** — public class 'ProjectContext' без docstring
  ```
         48 | 
         49 | 
  >>>    50 | class ProjectContext:
         51 |     def __init__(self):
         52 |         v, b = _load_version_info()
  ```

### `modules/ai_arranger.py` — 1 шт.
- **строка 10** — public class 'AIArranger' без docstring
  ```
          8 | 
          9 | from typing import List, Dict, Any
  >>>    10 | class AIArranger:
         11 |     def __init__(self):
         12 |         # Шаблоны структур для разных типов жанров
  ```

### `modules/artist_dossier/collectors.py` — 4 шт.
- **строка 9** — public class 'LocalFolderCollector' без docstring
  ```
          7 | 
          8 | 
  >>>     9 | class LocalFolderCollector:
         10 |     def __init__(self, folder: str):
         11 |         self.folder = Path(folder)
  ```
- **строка 28** — public class 'LyricVaultCollector' без docstring
  ```
         26 | 
         27 | 
  >>>    28 | class LyricVaultCollector:
         29 |     def __init__(self, vault_root: str):
         30 |         self.vault = Path(vault_root)
  ```
- **строка 46** — public class 'GeniusCollector' без docstring
  ```
         44 | 
         45 | 
  >>>    46 | class GeniusCollector:
         47 |     def __init__(self, token: Optional[str] = None, max_songs: int = 25):
         48 |         self.token = token or os.environ.get("GENIUS_TOKEN")
  ```
- **строка 70** — public class 'YouTubeCollector' без docstring
  ```
         68 | 
         69 | 
  >>>    70 | class YouTubeCollector:
         71 |     def __init__(self, out_dir: str, max_tracks: int = 10):
         72 |         self.out_dir = Path(out_dir)
  ```

### `modules/artist_dossier/manager.py` — 3 шт.
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

### `modules/distribution_export_v11.py` — 2 шт.
- **строка 28** — public class 'TrackMetadata' без docstring
  ```
         26 | 
         27 | @dataclass
  >>>    28 | class TrackMetadata:
         29 |     title: str
         30 |     artist: str
  ```
- **строка 75** — public class 'ReleaseFiles' без docstring
  ```
         73 | 
         74 | @dataclass
  >>>    75 | class ReleaseFiles:
         76 |     master_wav: str = ""
         77 |     mp3_320: str = ""
  ```

### `modules/expert_mode_v11.py` — 9 шт.
- **строка 25** — public class 'ExpertBeat' без docstring
  ```
         23 | 
         24 | @dataclass
  >>>    25 | class ExpertBeat:
         26 |     bpm_override: float | None = None
         27 |     swing_percent: float = 15.0
  ```
- **строка 37** — public class 'ExpertLyrics' без docstring
  ```
         35 | 
         36 | @dataclass
  >>>    37 | class ExpertLyrics:
         38 |     llm_temperature: float = 0.85
         39 |     llm_top_p: float = 0.92
  ```
- **строка 53** — public class 'ExpertVoice' без docstring
  ```
         51 | 
         52 | @dataclass
  >>>    53 | class ExpertVoice:
         54 |     mode: str = "rap"
         55 |     tts_engine: str = "silero"
  ```
- **строка 68** — public class 'ExpertMix' без docstring
  ```
         66 | 
         67 | @dataclass
  >>>    68 | class ExpertMix:
         69 |     eq_low_db: float = 0.0
         70 |     eq_mid_db: float = 0.0
  ```
- **строка 80** — public class 'ExpertMaster' без docstring
  ```
         78 | 
         79 | @dataclass
  >>>    80 | class ExpertMaster:
         81 |     target_lufs: float = -9.0
         82 |     stand_car_lufs: float = -8.5
  ```
- **строка 91** — public class 'ExpertMusicGen' без docstring
  ```
         89 | 
         90 | @dataclass
  >>>    91 | class ExpertMusicGen:
         92 |     variant: str = "auto"
         93 |     duration_sec: float = 8.0
  ```
- **строка 102** — public class 'ExpertAntiNeuro' без docstring
  ```
        100 | 
        101 | @dataclass
  >>>   102 | class ExpertAntiNeuro:
        103 |     preset: str = "standard"
        104 |     timing_jitter_ms: int = 10
  ```
- **строка 112** — public class 'ExpertRender' без docstring
  ```
        110 | 
        111 | @dataclass
  >>>   112 | class ExpertRender:
        113 |     length_sec: int = 150
        114 |     quality_mode: str = "quality"
  ```
- **строка 126** — public class 'ExpertConfig' без docstring
  ```
        124 | 
        125 | @dataclass
  >>>   126 | class ExpertConfig:
        127 |     enabled: bool = False
        128 |     version: str = "v11"
  ```

### `modules/genre_engine.py` — 3 шт.
- **строка 15** — public class 'GenreProfile' без docstring
  ```
         13 | 
         14 | @dataclass
  >>>    15 | class GenreProfile:
         16 |     name: str
         17 |     bpm_range: tuple = (120, 140)
  ```
- **строка 24** — public class 'StyleRegistry' без docstring
  ```
         22 |     tags: List[str] = field(default_factory=list)
         23 | 
  >>>    24 | class StyleRegistry:
         25 |     _instance = None
         26 | 
  ```
- **строка 95** — public class 'GenreFactory' без docstring
  ```
         93 |         return list(self.genres.keys())
         94 | 
  >>>    95 | class GenreFactory:
         96 |     def __init__(self, registry: StyleRegistry):
         97 |         self.registry = registry
  ```

### `modules/health_v12.py` — 2 шт.
- **строка 111** — public class 'ProbeResult' без docstring
  ```
        109 | 
        110 | @dataclass
  >>>   111 | class ProbeResult:
        112 |     key: str
        113 |     name: str
  ```
- **строка 124** — public class 'HealthReport' без docstring
  ```
        122 | 
        123 | @dataclass
  >>>   124 | class HealthReport:
        125 |     generated_at: float = field(default_factory=lambda: time.time())
        126 |     generated_at_human: str = ""
  ```

### `modules/hit_kpi_monitor_v11.py` — 2 шт.
- **строка 67** — public class 'KpiStage' без docstring
  ```
         65 | 
         66 | @dataclass
  >>>    67 | class KpiStage:
         68 |     name: str
         69 |     started_at: float = 0.0
  ```
- **строка 80** — public class 'KpiSession' без docstring
  ```
         78 | 
         79 | @dataclass
  >>>    80 | class KpiSession:
         81 |     project_id: str
         82 |     hw_mode: str = "full_hw"
  ```

### `modules/kpi_dashboard_v12.py` — 2 шт.
- **строка 66** — public class 'DashboardSection' без docstring
  ```
         64 | 
         65 | @dataclass
  >>>    66 | class DashboardSection:
         67 |     title: str
         68 |     ok: bool
  ```
- **строка 74** — public class 'Dashboard' без docstring
  ```
         72 | 
         73 | @dataclass
  >>>    74 | class Dashboard:
         75 |     generated_at: str = ""
         76 |     percent_tz: int = 0
  ```

### `modules/llm_clients_v15.py` — 1 шт.
- **строка 102** — public class 'ProviderResult' без docstring
  ```
        100 | 
        101 | 
  >>>   102 | class ProviderResult:
        103 |     __slots__ = ("error", "model", "ok", "provider", "raw", "text", "tokens")
        104 | 
  ```

### `modules/master_pipeline_v12.py` — 2 шт.
- **строка 83** — public class 'StageResult' без docstring
  ```
         81 | 
         82 | @dataclass
  >>>    83 | class StageResult:
         84 |     name: str
         85 |     tz_ref: str  # секция ТЗ, к которой привязана стадия
  ```
- **строка 101** — public class 'MasterResult' без docstring
  ```
         99 | 
        100 | @dataclass
  >>>   101 | class MasterResult:
        102 |     project_id: str
        103 |     started_at: float = field(default_factory=lambda: time.time())
  ```

### `modules/musical_intelligence.py` — 1 шт.
- **строка 28** — public class 'MusicalIntelligence' без docstring
  ```
         26 | 
         27 | 
  >>>    28 | class MusicalIntelligence:
         29 |     def __init__(self, sr: int = 44100):
         30 |         self.sr = sr
  ```

### `modules/phonk_engine_v2.py` — 1 шт.
- **строка 19** — public class 'PhonkEngineV2' без docstring
  ```
         17 | from modules.musical_intelligence import MusicalIntelligence
         18 | 
  >>>    19 | class PhonkEngineV2:
         20 |     def __init__(self, sr: int = 44100, drive_db: float = 25.0, obfuscation: float = 0.3):
         21 |         self.sr = sr
  ```

### `modules/render_queue.py` — 1 шт.
- **строка 28** — public class 'QueueItem' без docstring
  ```
         26 | 
         27 | @dataclass
  >>>    28 | class QueueItem:
         29 |     id: str
         30 |     recipe: dict
  ```

### `modules/rvc_manager.py` — 2 шт.
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

### `modules/sidechain.py` — 1 шт.
- **строка 55** — public class 'SidechainResult' без docstring
  ```
         53 | 
         54 | @dataclass
  >>>    55 | class SidechainResult:
         56 |     ok: bool
         57 |     engine: str
  ```

### `modules/video_edit_v11.py` — 2 шт.
- **строка 34** — public class 'VideoEditRequest' без docstring
  ```
         32 | 
         33 | @dataclass
  >>>    34 | class VideoEditRequest:
         35 |     master_wav: str
         36 |     cover_png: str | None = None
  ```
- **строка 57** — public class 'VideoEditResult' без docstring
  ```
         55 | 
         56 | @dataclass
  >>>    57 | class VideoEditResult:
         58 |     ok: bool
         59 |     output_path: str
  ```

### `modules/vocal_fx.py` — 1 шт.
- **строка 144** — public class 'VocalFxResult' без docstring
  ```
        142 | 
        143 | @dataclass
  >>>   144 | class VocalFxResult:
        145 |     ok: bool
        146 |     out_wav: str
  ```

### `modules/voice_onboarding.py` — 2 шт.
- **строка 79** — public class 'OnboardingStep' без docstring
  ```
         77 | 
         78 | @dataclass
  >>>    79 | class OnboardingStep:
         80 |     step_id: str
         81 |     kind: str
  ```
- **строка 99** — public class 'OnboardingProgress' без docstring
  ```
         97 | 
         98 | @dataclass
  >>>    99 | class OnboardingProgress:
        100 |     total_target_sec: int = 300
        101 |     total_recorded_sec: float = 0.0
  ```

### `modules/voice_recording.py` — 2 шт.
- **строка 47** — public class 'RecorderMetrics' без docstring
  ```
         45 | 
         46 | @dataclass
  >>>    47 | class RecorderMetrics:
         48 |     rms_db: float = -100.0
         49 |     peak_db: float = -100.0
  ```
- **строка 58** — public class 'TakeInfo' без docstring
  ```
         56 | 
         57 | @dataclass
  >>>    58 | class TakeInfo:
         59 |     take_id: str
         60 |     path: str
  ```

### `modules/wizard_v12_integration.py` — 1 шт.
- **строка 52** — public class 'WizardBridgeResult' без docstring
  ```
         50 | 
         51 | @dataclass
  >>>    52 | class WizardBridgeResult:
         53 |     project_id: str
         54 |     started_at: float = field(default_factory=lambda: time.time())
  ```

### `tests/test_ai_layer.py` — 7 шт.
- **строка 184** — public class 'TestRegistry' без docstring
  ```
        182 | 
        183 | 
  >>>   184 | class TestRegistry(unittest.TestCase):
        185 |     def test_roles(self):
        186 |         from app.ai.registry import MODEL_REGISTRY, registry
  ```
- **строка 211** — public class 'TestRunner' без docstring
  ```
        209 | 
        210 | 
  >>>   211 | class TestRunner(unittest.TestCase):
        212 |     def test_pure(self):
        213 |         from app.ai.sequential_runner import SequentialAIRunner, AIStage
  ```
- **строка 238** — public class 'TestDossier' без docstring
  ```
        236 | 
        237 | 
  >>>   238 | class TestDossier(unittest.TestCase):
        239 |     def setUp(self):
        240 |         self.tmp = Path(tempfile.mkdtemp(prefix="zsmm_d_"))
  ```
- **строка 265** — public class 'TestOrchestrator' без docstring
  ```
        263 | 
        264 | 
  >>>   265 | class TestOrchestrator(unittest.TestCase):
        266 |     def test_dry(self):
        267 |         from app.core.orchestrator_ai import run_ai_pipeline
  ```
- **строка 421** — public class 'FakeASR' без docstring
  ```
        419 |     from modules.artist_dossier.manager import transcribe_reference_audio
        420 | 
  >>>   421 |     class FakeASR:
        422 |         def __init__(self):
        423 |             self.kwargs = None
  ```
- **строка 443** — public class 'FailingASR' без docstring
  ```
        441 |     from modules.artist_dossier.manager import transcribe_reference_audio
        442 | 
  >>>   443 |     class FailingASR:
        444 |         def transcribe(self, *args, **kwargs):
        445 |             raise RuntimeError("model load failed")
  ```
- **строка 459** — public class 'RepetitiveASR' без docstring
  ```
        457 |     from modules.artist_dossier.manager import transcribe_reference_audio
        458 | 
  >>>   459 |     class RepetitiveASR:
        460 |         def transcribe(self, *args, **kwargs):
        461 |             return iter([SimpleNamespace(text="эй эй эй эй")]), SimpleNamespace(language="ru")
  ```
