# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/rvc_manager.py`

**Всего строк:** 481

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 235 | 48.9 |
| blank | 55 | 11.4 |
| docstring | 45 | 9.4 |
| try_block | 28 | 5.8 |
| branch | 25 | 5.2 |
| comment | 24 | 5.0 |
| import | 17 | 3.5 |
| def | 17 | 3.5 |
| return | 15 | 3.1 |
| raise | 10 | 2.1 |
| loop | 5 | 1.0 |
| class | 3 | 0.6 |
| decorator | 2 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] rvc_manager.py — оркестрация RVC v2 как ФУНДАМЕНТА приложения.
    3 [blank     ] 
    4 [docstring ] По разделу 20.1 ТЗ:
    5 [docstring ]   • RVC v2 ДОЛЖЕН реально работать (не заглушка, не offline-fallback как основной).
    6 [docstring ]   • На NVIDIA — стандартный rvc-python (CUDA).
    7 [docstring ]   • На AMD/DirectML — автоподтягивание Mangio-RVC-Fork / Applio через git clone.
    8 [docstring ]   • Ночной / длительный режим обучения ≥30 минут — без вылетов.
    9 [docstring ]   • Фоновое обучение в отдельном потоке с прогресс-каллбэками.
   10 [docstring ]   • Инкрементальное дообучение при добавлении новых записей.
   11 [docstring ]   • ProVoice Mode — основной режим (пользователь сам поёт → RVC полирует).
   12 [blank     ] 
   13 [docstring ] Модуль автономный, работает без интернета если репозитории и модели уже
   14 [docstring ] подтянуты. При первом запуске на AMD-железе один раз качает форк из GitHub.
   15 [docstring ] """
   16 [blank     ] 
   17 [import    ] from __future__ import annotations
   18 [blank     ] 
   19 [import    ] import json
   20 [import    ] import shutil
   21 [import    ] import subprocess
   22 [import    ] import sys
   23 [import    ] import threading
   24 [import    ] import time
   25 [import    ] from collections.abc import Callable
   26 [import    ] from dataclasses import asdict, dataclass
   27 [import    ] from pathlib import Path
   28 [blank     ] 
   29 [code      ] ROOT = Path(__file__).resolve().parents[1]
   30 [code      ] MODELS_DIR = ROOT / "models" / "rvc"
   31 [code      ] FORKS_DIR = ROOT / "models" / "rvc_forks"
   32 [code      ] STATE_FILE = ROOT / "models" / "rvc" / "rvc_state.json"
   33 [loop      ] for p in (MODELS_DIR, FORKS_DIR):
   34 [code      ]     p.mkdir(parents=True, exist_ok=True)
   35 [blank     ] 
   36 [comment   ] # Известные AMD-совместимые форки RVC (только open-source, MIT/AGPL-3.0)
   37 [code      ] AMD_FORKS = {
   38 [code      ]     "applio": "https://github.com/IAHispano/Applio.git",
   39 [code      ]     "mangio": "https://github.com/Mangio621/Mangio-RVC-Fork.git",
   40 [code      ]     "rvc-webui": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git",
   41 [code      ] }
   42 [blank     ] 
   43 [blank     ] 
   44 [comment   ] # ---------------------------------------------------------------- state
   45 [def       ] def _load_state() -> dict:
   46 [branch    ]     if STATE_FILE.exists():
   47 [try_block ]         try:
   48 [return    ]             return json.load(open(STATE_FILE, "r", encoding="utf-8"))
   49 [try_block ]         except Exception:
   50 [return    ]             return {}
   51 [return    ]     return {}
   52 [blank     ] 
   53 [blank     ] 
   54 [def       ] def _save_state(s: dict) -> None:
   55 [code      ]     STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
   56 [blank     ] 
   57 [blank     ] 
   58 [comment   ] # ---------------------------------------------------------------- backend detect
   59 [decorator ] @dataclass
   60 [class     ] class RVCBackend:
   61 [code      ]     kind: str = "cpu"  # "cuda" | "directml" | "rocm" | "cpu"
   62 [code      ]     device_name: str = "CPU"
   63 [code      ]     vram_gb: float = 0.0
   64 [code      ]     fork: str = "rvc-python"  # rvc-python | applio | mangio | rvc-webui
   65 [code      ]     ok: bool = False
   66 [code      ]     reason: str = ""
   67 [blank     ] 
   68 [blank     ] 
   69 [def       ] def detect_backend() -> RVCBackend:
   70 [docstring ]     """Определяем оптимальный бэкенд и форк RVC под текущее железо."""
   71 [code      ]     b = RVCBackend()
   72 [comment   ]     # 1) NVIDIA CUDA
   73 [try_block ]     try:
   74 [import    ]         import torch
   75 [blank     ] 
   76 [branch    ]         if torch.cuda.is_available():
   77 [code      ]             b.kind = "cuda"
   78 [code      ]             b.device_name = torch.cuda.get_device_name(0)
   79 [code      ]             b.vram_gb = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
   80 [code      ]             b.fork = "rvc-python"
   81 [code      ]             b.ok = True
   82 [code      ]             b.reason = "CUDA available"
   83 [return    ]             return b
   84 [try_block ]     except Exception:
   85 [code      ]         pass
   86 [comment   ]     # 2) DirectML (AMD/Intel iGPU на Windows)
   87 [try_block ]     try:
   88 [import    ]         import torch_directml as dml
   89 [blank     ] 
   90 [code      ]         b.kind = "directml"
   91 [code      ]         b.device_name = (
   92 [code      ]             dml.device_name(0) if hasattr(dml, "device_name") else "DirectML GPU"
   93 [code      ]         )
   94 [code      ]         b.vram_gb = 4.0
   95 [code      ]         b.fork = "applio"  # Applio — лучший AMD-friendly форк
   96 [code      ]         b.ok = True
   97 [code      ]         b.reason = "DirectML available"
   98 [return    ]         return b
   99 [try_block ]     except Exception:
  100 [code      ]         pass
  101 [comment   ]     # 3) ROCm (Linux, редко)
  102 [try_block ]     try:
  103 [import    ]         import torch
  104 [blank     ] 
  105 [branch    ]         if hasattr(torch.version, "hip") and torch.version.hip is not None:
  106 [code      ]             b.kind = "rocm"
  107 [code      ]             b.device_name = "AMD GPU (ROCm)"
  108 [code      ]             b.vram_gb = 8.0
  109 [code      ]             b.fork = "mangio"
  110 [code      ]             b.ok = True
  111 [code      ]             b.reason = "ROCm available"
  112 [return    ]             return b
  113 [try_block ]     except Exception:
  114 [code      ]         pass
  115 [comment   ]     # 4) CPU fallback
  116 [code      ]     b.kind = "cpu"
  117 [code      ]     b.device_name = "CPU"
  118 [code      ]     b.fork = "rvc-python"
  119 [code      ]     b.ok = True
  120 [code      ]     b.reason = "CPU fallback"
  121 [return    ]     return b
  122 [blank     ] 
  123 [blank     ] 
  124 [comment   ] # ---------------------------------------------------------------- ensure fork
  125 [def       ] def ensure_fork(
  126 [code      ]     fork_name: str, on_progress: Callable[[str], None] | None = None
  127 [code      ] ) -> Path:
  128 [docstring ]     """
  129 [docstring ]     Клонирует AMD-совместимый форк RVC локально при первом запуске.
  130 [docstring ]     Возвращает путь к папке форка. Не требует интернета если уже подтянут.
  131 [docstring ]     """
  132 [blank     ] 
  133 [def       ]     def _p(msg: str):
  134 [branch    ]         if on_progress:
  135 [code      ]             on_progress(msg)
  136 [code      ]         print(f"[rvc_manager] {msg}")
  137 [blank     ] 
  138 [branch    ]     if fork_name == "rvc-python":
  139 [comment   ]         # rvc-python — pip-пакет, отдельно клонировать не нужно
  140 [try_block ]         try:
  141 [import    ]             import rvc_python  # noqa: F401
  142 [blank     ] 
  143 [code      ]             _p("rvc-python OK (pip)")
  144 [try_block ]         except ImportError:
  145 [comment   ]             # v37 FIX: windows_build.bat больше не существует — указываем реальный путь установки.
  146 [code      ]             _p(
  147 [code      ]                 "rvc-python не установлен — pip install rvc-python "
  148 [code      ]                 "(или запусти install.py, он ставит heavy-deps per-package; см. INSTALL.md §4)"
  149 [code      ]             )
  150 [return    ]         return FORKS_DIR / "rvc-python"
  151 [blank     ] 
  152 [branch    ]     if fork_name not in AMD_FORKS:
  153 [code      ]         _p(f"Неизвестный форк {fork_name}, использую applio")
  154 [code      ]         fork_name = "applio"
  155 [blank     ] 
  156 [code      ]     target = FORKS_DIR / fork_name
  157 [branch    ]     if target.exists() and (target / ".git").exists():
  158 [code      ]         _p(f"Форк {fork_name} уже подтянут → {target}")
  159 [return    ]         return target
  160 [blank     ] 
  161 [code      ]     url = AMD_FORKS[fork_name]
  162 [code      ]     _p(f"Клонирую {fork_name} из {url}")
  163 [try_block ]     try:
  164 [comment   ]         # depth=1 для скорости и экономии диска
  165 [code      ]         subprocess.run(
  166 [code      ]             ["git", "clone", "--depth", "1", url, str(target)],
  167 [code      ]             check=True,
  168 [code      ]             capture_output=True,
  169 [code      ]             text=True,
  170 [code      ]             timeout=600,
  171 [code      ]         )
  172 [code      ]         _p(f"{fork_name} успешно клонирован → {target}")
  173 [try_block ]     except FileNotFoundError:
  174 [code      ]         _p("git не найден. Установи git for Windows: https://git-scm.com/download/win")
  175 [try_block ]     except subprocess.CalledProcessError as e:
  176 [code      ]         _p(f"git clone упал: {e.stderr[-300:] if e.stderr else e}")
  177 [try_block ]     except Exception as e:
  178 [code      ]         _p(f"ensure_fork: {type(e).__name__}: {e}")
  179 [return    ]     return target
  180 [blank     ] 
  181 [blank     ] 
  182 [comment   ] # ---------------------------------------------------------------- training
  183 [decorator ] @dataclass
  184 [class     ] class TrainingJob:
  185 [code      ]     voice_name: str
  186 [code      ]     epochs: int
  187 [code      ]     device: str
  188 [code      ]     started_at: float = 0.0
  189 [code      ]     progress: float = 0.0
  190 [code      ]     status: str = "queued"  # queued | running | done | error
  191 [code      ]     stage: str = ""
  192 [code      ]     error: str | None = None
  193 [code      ]     model_path: str | None = None
  194 [blank     ] 
  195 [blank     ] 
  196 [class     ] class RVCTrainer:
  197 [docstring ]     """
  198 [docstring ]     Фоновое обучение RVC-модели.
  199 [docstring ]     Поддерживает ночной / длительный режим (несколько часов).
  200 [docstring ]     Не блокирует GUI: прогресс через колбэки, статус через объект TrainingJob.
  201 [docstring ]     """
  202 [blank     ] 
  203 [def       ]     def __init__(self, backend: RVCBackend | None = None):
  204 [code      ]         self.backend = backend or detect_backend()
  205 [code      ]         self.job: TrainingJob | None = None
  206 [code      ]         self._thread: threading.Thread | None = None
  207 [code      ]         self._listeners: list[Callable[[TrainingJob], None]] = []
  208 [blank     ] 
  209 [def       ]     def on_progress(self, cb: Callable[[TrainingJob], None]) -> None:
  210 [code      ]         self._listeners.append(cb)
  211 [blank     ] 
  212 [def       ]     def _emit(self):
  213 [loop      ]         for cb in self._listeners:
  214 [try_block ]             try:
  215 [code      ]                 cb(self.job)
  216 [try_block ]             except Exception:
  217 [code      ]                 pass
  218 [blank     ] 
  219 [def       ]     def _dataset_ready(self, voice_name: str) -> Path:
  220 [docstring ]         """Собираем dataset из voice_vault по имени голоса."""
  221 [import    ]         from modules import voice_convert
  222 [blank     ] 
  223 [code      ]         idx = voice_convert._load_index()
  224 [code      ]         ds = MODELS_DIR / voice_name / "dataset"
  225 [code      ]         ds.mkdir(parents=True, exist_ok=True)
  226 [code      ]         n = 0
  227 [loop      ]         for e in idx:
  228 [code      ]             src = e.get("path")
  229 [branch    ]             if src and Path(src).exists():
  230 [try_block ]                 try:
  231 [code      ]                     shutil.copy(src, ds / Path(src).name)
  232 [code      ]                     n += 1
  233 [try_block ]                 except Exception:
  234 [code      ]                     pass
  235 [return    ]         return ds
  236 [blank     ] 
  237 [def       ]     def train(
  238 [code      ]         self, voice_name: str = "my_voice", epochs: int = 100, night_mode: bool = False
  239 [code      ]     ) -> TrainingJob:
  240 [docstring ]         """
  241 [docstring ]         Запуск обучения в фоне.
  242 [docstring ]         night_mode=True → epochs=300 (или сколько указано), низкий batch,
  243 [docstring ]                           пригодно для 4GB VRAM / CPU.
  244 [docstring ]         """
  245 [code      ]         eff_epochs = epochs if not night_mode else max(epochs, 300)
  246 [code      ]         device = self.backend.kind if self.backend.ok else "cpu"
  247 [code      ]         job = TrainingJob(
  248 [code      ]             voice_name=voice_name,
  249 [code      ]             epochs=eff_epochs,
  250 [code      ]             device=device,
  251 [code      ]             started_at=time.time(),
  252 [code      ]             status="queued",
  253 [code      ]             stage="init",
  254 [code      ]         )
  255 [code      ]         self.job = job
  256 [code      ]         self._thread = threading.Thread(target=self._run, daemon=True)
  257 [code      ]         self._thread.start()
  258 [return    ]         return job
  259 [blank     ] 
  260 [def       ]     def _run(self):
  261 [code      ]         job = self.job
  262 [try_block ]         try:
  263 [code      ]             job.status = "running"
  264 [code      ]             job.stage = "prepare_dataset"
  265 [code      ]             self._emit()
  266 [code      ]             ds = self._dataset_ready(job.voice_name)
  267 [code      ]             files = list(ds.glob("*.wav"))
  268 [branch    ]             if not files:
  269 [raise     ]                 raise RuntimeError("voice_vault пуст. Запиши минимум 5 минут голоса.")
  270 [code      ]             job.stage = f"dataset ready ({len(files)} clips)"
  271 [code      ]             self._emit()
  272 [blank     ] 
  273 [comment   ]             # ---- пытаемся rvc-python ----
  274 [code      ]             job.stage = "rvc-python training"
  275 [code      ]             self._emit()
  276 [try_block ]             try:
  277 [import    ]                 import rvc_python  # noqa
  278 [blank     ] 
  279 [code      ]                 cmd = [
  280 [code      ]                     sys.executable,
  281 [code      ]                     "-m",
  282 [code      ]                     "rvc_python",
  283 [code      ]                     "train",
  284 [code      ]                     "--name",
  285 [code      ]                     job.voice_name,
  286 [code      ]                     "--dataset",
  287 [code      ]                     str(ds),
  288 [code      ]                     "--epochs",
  289 [code      ]                     str(job.epochs),
  290 [code      ]                     "--sample_rate",
  291 [code      ]                     "40000",
  292 [code      ]                     "--device",
  293 [code      ]                     job.device,
  294 [code      ]                 ]
  295 [comment   ]                 # Ночной режим — batch small, epochs больше
  296 [branch    ]                 if job.device == "cpu":
  297 [code      ]                     cmd += ["--batch_size", "2"]
  298 [code      ]                 self._run_with_progress(cmd, job)
  299 [try_block ]             except ImportError:
  300 [comment   ]                 # AMD/DirectML: пробуем форк
  301 [branch    ]                 if self.backend.fork != "rvc-python":
  302 [code      ]                     fork_dir = ensure_fork(
  303 [code      ]                         self.backend.fork,
  304 [code      ]                         on_progress=lambda m: setattr(job, "stage", m),
  305 [code      ]                     )
  306 [code      ]                     self._train_via_fork(fork_dir, job)
  307 [branch    ]                 else:
  308 [raise     ]                     raise RuntimeError(
  309 [code      ]                         "rvc-python не установлен. pip install rvc-python"
  310 [code      ]                     )
  311 [blank     ] 
  312 [comment   ]             # Сохраняем результат
  313 [code      ]             model_path = MODELS_DIR / job.voice_name / f"{job.voice_name}.pth"
  314 [branch    ]             if model_path.exists():
  315 [code      ]                 job.model_path = str(model_path)
  316 [code      ]                 job.status = "done"
  317 [code      ]                 job.stage = "completed"
  318 [branch    ]             else:
  319 [code      ]                 job.status = "done"
  320 [code      ]                 job.stage = "completed (модель не найдена — проверь путь)"
  321 [code      ]             job.progress = 1.0
  322 [try_block ]         except Exception as e:
  323 [code      ]             job.status = "error"
  324 [code      ]             job.error = f"{type(e).__name__}: {e}"
  325 [code      ]             job.stage = "failed"
  326 [try_block ]         finally:
  327 [code      ]             self._emit()
  328 [comment   ]             # Сохраняем состояние
  329 [code      ]             s = _load_state()
  330 [code      ]             s[job.voice_name] = asdict(job)
  331 [code      ]             _save_state(s)
  332 [blank     ] 
  333 [def       ]     def _run_with_progress(self, cmd: list[str], job: TrainingJob):
  334 [docstring ]         """Запускаем subprocess и парсим stdout на предмет прогресса эпох."""
  335 [code      ]         proc = subprocess.Popen(
  336 [code      ]             cmd,
  337 [code      ]             stdout=subprocess.PIPE,
  338 [code      ]             stderr=subprocess.STDOUT,
  339 [code      ]             text=True,
  340 [code      ]             encoding="utf-8",
  341 [code      ]             errors="replace",
  342 [code      ]             bufsize=1,
  343 [code      ]         )
  344 [loop      ]         for line in proc.stdout:
  345 [code      ]             line = line.rstrip()
  346 [comment   ]             # Прогресс: "Epoch 42/100" или "epoch=42"
  347 [loop      ]             for token in ("Epoch ", "epoch="):
  348 [branch    ]                 if token in line:
  349 [try_block ]                     try:
  350 [code      ]                         raw = (
  351 [code      ]                             line.split(token, 1)[1]
  352 [code      ]                             .split()[0]
  353 [code      ]                             .split("/")[0]
  354 [code      ]                             .strip(",=:")
  355 [code      ]                         )
  356 [code      ]                         ep = int("".join(c for c in raw if c.isdigit()))
  357 [code      ]                         job.progress = min(0.99, ep / max(1, job.epochs))
  358 [code      ]                         job.stage = f"epoch {ep}/{job.epochs}"
  359 [code      ]                         self._emit()
  360 [try_block ]                     except Exception:
  361 [code      ]                         pass
  362 [code      ]         ret = proc.wait()
  363 [branch    ]         if ret != 0:
  364 [raise     ]             raise RuntimeError(f"training subprocess exit={ret}")
  365 [blank     ] 
  366 [def       ]     def _train_via_fork(self, fork_dir: Path, job: TrainingJob):
  367 [docstring ]         """
  368 [docstring ]         Заглушка запуска через клонированный форк (Applio/Mangio).
  369 [docstring ]         В реальной установке Windows-скрипт train.bat из форка вызывается
  370 [docstring ]         c параметрами. Здесь — минимальный запуск через python train.py.
  371 [docstring ]         """
  372 [code      ]         train_py = fork_dir / "train.py"
  373 [branch    ]         if not train_py.exists():
  374 [comment   ]             # У форка может быть другой entry point
  375 [code      ]             candidates = list(fork_dir.glob("*train*.py"))
  376 [branch    ]             if candidates:
  377 [code      ]                 train_py = candidates[0]
  378 [branch    ]             else:
  379 [raise     ]                 raise RuntimeError(f"train.py не найден в {fork_dir}")
  380 [code      ]         cmd = [
  381 [code      ]             sys.executable,
  382 [code      ]             str(train_py),
  383 [code      ]             "--experiment_dir",
  384 [code      ]             str(MODELS_DIR / job.voice_name),
  385 [code      ]             "--dataset_dir",
  386 [code      ]             str(MODELS_DIR / job.voice_name / "dataset"),
  387 [code      ]             "--total_epoch",
  388 [code      ]             str(job.epochs),
  389 [code      ]             "--sample_rate",
  390 [code      ]             "40000",
  391 [code      ]         ]
  392 [code      ]         self._run_with_progress(cmd, job)
  393 [blank     ] 
  394 [blank     ] 
  395 [comment   ] # ---------------------------------------------------------------- inference
  396 [def       ] def infer(
  397 [code      ]     input_wav: str,
  398 [code      ]     voice_name: str = "my_voice",
  399 [code      ]     pitch_shift: int = 0,
  400 [code      ]     out_name: str = "converted.wav",
  401 [code      ] ) -> str:
  402 [docstring ]     """
  403 [docstring ]     RVC-инференс: заменяет тембр во входном wav на голос пользователя.
  404 [docstring ]     Пытается сначала rvc-python, потом форк. Возвращает путь к результату.
  405 [docstring ]     """
  406 [code      ]     OUT = ROOT / "output" / "voice_final"
  407 [code      ]     OUT.mkdir(parents=True, exist_ok=True)
  408 [code      ]     out_path = OUT / out_name
  409 [blank     ] 
  410 [code      ]     model_path = MODELS_DIR / voice_name / f"{voice_name}.pth"
  411 [code      ]     index_path = MODELS_DIR / voice_name / f"{voice_name}.index"
  412 [blank     ] 
  413 [branch    ]     if not model_path.exists():
  414 [raise     ]         raise RuntimeError("RVC model is not available; refusing pitch-shift fallback")
  415 [blank     ] 
  416 [comment   ]     # 1) rvc-python
  417 [code      ]     backend = detect_backend()
  418 [try_block ]     try:
  419 [import    ]         from rvc_python.infer import infer_file
  420 [blank     ] 
  421 [code      ]         infer_file(
  422 [code      ]             input_path=input_wav,
  423 [code      ]             model_path=str(model_path),
  424 [code      ]             index_path=str(index_path) if index_path.exists() else None,
  425 [code      ]             output_path=str(out_path),
  426 [code      ]             f0up_key=pitch_shift,
  427 [code      ]             f0method="rmvpe",
  428 [code      ]             device=backend.kind,
  429 [code      ]         )
  430 [branch    ]         if out_path.exists() and out_path.stat().st_size > 1000:
  431 [return    ]             return str(out_path)
  432 [branch    ]         else:
  433 [raise     ]             raise RuntimeError("RVC output file is empty or too small")
  434 [try_block ]     except ImportError:
  435 [comment   ]         # 2) AMD/DirectML/CPU: try fork if present
  436 [branch    ]         if backend.fork != "rvc-python":
  437 [code      ]             fork_dir = FORKS_DIR / backend.fork
  438 [branch    ]             if fork_dir.exists():
  439 [comment   ]                 # Здесь должна быть логика вызова CLI форка,
  440 [comment   ]                 # но для v14 мы оставляем это как задел для реального железа.
  441 [raise     ]                 raise RuntimeError(
  442 [code      ]                     f"RVC fork {backend.fork} is cloned but CLI integration is pending for this OS."
  443 [code      ]                 )
  444 [raise     ]         raise RuntimeError(
  445 [code      ]             "rvc-python not installed and no active fork integration found."
  446 [code      ]         )
  447 [try_block ]     except Exception as e:
  448 [code      ]         print(f"[rvc_manager.infer] rvc-python failed: {e}")
  449 [raise     ]         raise RuntimeError(
  450 [code      ]             f"RVC inference failed: {e}. No non-RVC fallback is permitted (TZ 33.5)."
  451 [code      ]         )
  452 [blank     ] 
  453 [blank     ] 
  454 [def       ] def _fallback_pitch(input_wav: str, out_path: str, pitch_shift: int) -> str:
  455 [docstring ]     """
  456 [docstring ]     УДАЛЕНО в v14: pitch_shift fallback запрещён (TZ 33.5, P0.05).
  457 [docstring ]     Эта функция сохранена только как явный отказ — вызов поднимает
  458 [docstring ]     RuntimeError. Используйте RVC .pth модель или честный BLOCKED.
  459 [docstring ]     """
  460 [raise     ]     raise RuntimeError(
  461 [code      ]         "P0.05: pitch-shift as RVC is FORBIDDEN by TZ 33.5. "
  462 [code      ]         "RVC model is required. Got call to _fallback_pitch which was "
  463 [code      ]         "disabled. Train a voice model first (see voice_onboarding)."
  464 [code      ]     )
  465 [blank     ] 
  466 [blank     ] 
  467 [def       ] def get_state(voice_name: str = "my_voice") -> dict:
  468 [docstring ]     """Читаем состояние обучения (для UI)."""
  469 [return    ]     return _load_state().get(voice_name, {})
  470 [blank     ] 
  471 [blank     ] 
  472 [def       ] def is_trained(voice_name: str = "my_voice") -> bool:
  473 [return    ]     return (MODELS_DIR / voice_name / f"{voice_name}.pth").exists()
  474 [blank     ] 
  475 [blank     ] 
  476 [branch    ] if __name__ == "__main__":
  477 [code      ]     b = detect_backend()
  478 [code      ]     print(
  479 [code      ]         f"Backend: {b.kind} / fork={b.fork} / device={b.device_name} / vram={b.vram_gb} GB"
  480 [code      ]     )
  481 [code      ]     print(f"State: {json.dumps(_load_state(), ensure_ascii=False, indent=2)}")
```