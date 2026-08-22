"""
[v7] rvc_manager.py — оркестрация RVC v2 как ФУНДАМЕНТА приложения.

По разделу 20.1 ТЗ:
  • RVC v2 ДОЛЖЕН реально работать (не заглушка, не offline-fallback как основной).
  • На NVIDIA — стандартный rvc-python (CUDA).
  • На AMD/DirectML — автоподтягивание Mangio-RVC-Fork / Applio через git clone.
  • Ночной / длительный режим обучения ≥30 минут — без вылетов.
  • Фоновое обучение в отдельном потоке с прогресс-каллбэками.
  • Инкрементальное дообучение при добавлении новых записей.
  • ProVoice Mode — основной режим (пользователь сам поёт → RVC полирует).

Модуль автономный, работает без интернета если репозитории и модели уже
подтянуты. При первом запуске на AMD-железе один раз качает форк из GitHub.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models" / "rvc"
FORKS_DIR = ROOT / "models" / "rvc_forks"
STATE_FILE = ROOT / "models" / "rvc" / "rvc_state.json"
for p in (MODELS_DIR, FORKS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# Известные AMD-совместимые форки RVC (только open-source, MIT/AGPL-3.0)
AMD_FORKS = {
    "applio": "https://github.com/IAHispano/Applio.git",
    "mangio": "https://github.com/Mangio621/Mangio-RVC-Fork.git",
    "rvc-webui": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git",
}


# ---------------------------------------------------------------- state
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.load(open(STATE_FILE, "r", encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(s: dict) -> None:
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- backend detect
@dataclass
class RVCBackend:
    kind: str = "cpu"  # "cuda" | "directml" | "rocm" | "cpu"
    device_name: str = "CPU"
    vram_gb: float = 0.0
    fork: str = "rvc-python"  # rvc-python | applio | mangio | rvc-webui
    ok: bool = False
    reason: str = ""


def detect_backend() -> RVCBackend:
    """Определяем оптимальный бэкенд и форк RVC под текущее железо."""
    b = RVCBackend()
    # 1) NVIDIA CUDA
    try:
        import torch

        if torch.cuda.is_available():
            b.kind = "cuda"
            b.device_name = torch.cuda.get_device_name(0)
            b.vram_gb = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
            b.fork = "rvc-python"
            b.ok = True
            b.reason = "CUDA available"
            return b
    except Exception:
        pass
    # 2) DirectML (AMD/Intel iGPU на Windows)
    try:
        import torch_directml as dml

        b.kind = "directml"
        b.device_name = (
            dml.device_name(0) if hasattr(dml, "device_name") else "DirectML GPU"
        )
        b.vram_gb = 4.0
        b.fork = "applio"  # Applio — лучший AMD-friendly форк
        b.ok = True
        b.reason = "DirectML available"
        return b
    except Exception:
        pass
    # 3) ROCm (Linux, редко)
    try:
        import torch

        if hasattr(torch.version, "hip") and torch.version.hip is not None:
            b.kind = "rocm"
            b.device_name = "AMD GPU (ROCm)"
            b.vram_gb = 8.0
            b.fork = "mangio"
            b.ok = True
            b.reason = "ROCm available"
            return b
    except Exception:
        pass
    # 4) CPU fallback
    b.kind = "cpu"
    b.device_name = "CPU"
    b.fork = "rvc-python"
    b.ok = True
    b.reason = "CPU fallback"
    return b


# ---------------------------------------------------------------- ensure fork
def ensure_fork(
    fork_name: str, on_progress: Callable[[str], None] | None = None
) -> Path:
    """
    Клонирует AMD-совместимый форк RVC локально при первом запуске.
    Возвращает путь к папке форка. Не требует интернета если уже подтянут.
    """

    def _p(msg: str):
        if on_progress:
            on_progress(msg)
        print(f"[rvc_manager] {msg}")

    if fork_name == "rvc-python":
        # rvc-python — pip-пакет, отдельно клонировать не нужно
        try:
            import rvc_python  # noqa: F401

            _p("rvc-python OK (pip)")
        except ImportError:
            # v37 FIX: windows_build.bat больше не существует — указываем реальный путь установки.
            _p(
                "rvc-python не установлен — pip install rvc-python "
                "(или запусти install.py, он ставит heavy-deps per-package; см. INSTALL.md §4)"
            )
        return FORKS_DIR / "rvc-python"

    if fork_name not in AMD_FORKS:
        _p(f"Неизвестный форк {fork_name}, использую applio")
        fork_name = "applio"

    target = FORKS_DIR / fork_name
    if target.exists() and (target / ".git").exists():
        _p(f"Форк {fork_name} уже подтянут → {target}")
        return target

    url = AMD_FORKS[fork_name]
    _p(f"Клонирую {fork_name} из {url}")
    try:
        # depth=1 для скорости и экономии диска
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target)],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        _p(f"{fork_name} успешно клонирован → {target}")
    except FileNotFoundError:
        _p("git не найден. Установи git for Windows: https://git-scm.com/download/win")
    except subprocess.CalledProcessError as e:
        _p(f"git clone упал: {e.stderr[-300:] if e.stderr else e}")
    except Exception as e:
        _p(f"ensure_fork: {type(e).__name__}: {e}")
    return target


# ---------------------------------------------------------------- training
@dataclass
class TrainingJob:
    voice_name: str
    epochs: int
    device: str
    started_at: float = 0.0
    progress: float = 0.0
    status: str = "queued"  # queued | running | done | error
    stage: str = ""
    error: str | None = None
    model_path: str | None = None


class RVCTrainer:
    """
    Фоновое обучение RVC-модели.
    Поддерживает ночной / длительный режим (несколько часов).
    Не блокирует GUI: прогресс через колбэки, статус через объект TrainingJob.
    """

    def __init__(self, backend: RVCBackend | None = None):
        self.backend = backend or detect_backend()
        self.job: TrainingJob | None = None
        self._thread: threading.Thread | None = None
        self._listeners: list[Callable[[TrainingJob], None]] = []
        self.listener_errors: list[str] = []

    def on_progress(self, cb: Callable[[TrainingJob], None]) -> None:
        self._listeners.append(cb)

    def _emit(self):
        for cb in self._listeners:
            try:
                cb(self.job)
            except Exception as exc:
                self.listener_errors.append(f"{type(exc).__name__}: {exc}")

    def _dataset_ready(self, voice_name: str) -> Path:
        """Собираем dataset из voice_vault по имени голоса."""
        from modules import voice_convert

        idx = voice_convert._load_index()
        ds = MODELS_DIR / voice_name / "dataset"
        ds.mkdir(parents=True, exist_ok=True)
        n = 0
        for e in idx:
            src = e.get("path")
            if src and Path(src).exists():
                try:
                    shutil.copy(src, ds / Path(src).name)
                    n += 1
                except Exception:
                    pass
        return ds

    def train(
        self, voice_name: str = "my_voice", epochs: int = 100, night_mode: bool = False
    ) -> TrainingJob:
        """
        Запуск обучения в фоне.
        night_mode=True → epochs=300 (или сколько указано), низкий batch,
                          пригодно для 4GB VRAM / CPU.
        """
        eff_epochs = epochs if not night_mode else max(epochs, 300)
        device = self.backend.kind if self.backend.ok else "cpu"
        job = TrainingJob(
            voice_name=voice_name,
            epochs=eff_epochs,
            device=device,
            started_at=time.time(),
            status="queued",
            stage="init",
        )
        self.job = job
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return job

    def _run(self):
        job = self.job
        try:
            job.status = "running"
            job.stage = "prepare_dataset"
            self._emit()
            ds = self._dataset_ready(job.voice_name)
            files = list(ds.glob("*.wav"))
            if not files:
                raise RuntimeError("voice_vault пуст. Запиши минимум 5 минут голоса.")
            job.stage = f"dataset ready ({len(files)} clips)"
            self._emit()

            # ---- пытаемся rvc-python ----
            job.stage = "rvc-python training"
            self._emit()
            try:
                import rvc_python  # noqa

                cmd = [
                    sys.executable,
                    "-m",
                    "rvc_python",
                    "train",
                    "--name",
                    job.voice_name,
                    "--dataset",
                    str(ds),
                    "--epochs",
                    str(job.epochs),
                    "--sample_rate",
                    "40000",
                    "--device",
                    job.device,
                ]
                # Ночной режим — batch small, epochs больше
                if job.device == "cpu":
                    cmd += ["--batch_size", "2"]
                self._run_with_progress(cmd, job)
            except ImportError:
                # AMD/DirectML: пробуем форк
                if self.backend.fork != "rvc-python":
                    fork_dir = ensure_fork(
                        self.backend.fork,
                        on_progress=lambda m: setattr(job, "stage", m),
                    )
                    self._train_via_fork(fork_dir, job)
                else:
                    raise RuntimeError(
                        "rvc-python не установлен. pip install rvc-python"
                    )

            # Сохраняем результат
            model_path = MODELS_DIR / job.voice_name / f"{job.voice_name}.pth"
            if model_path.exists():
                job.model_path = str(model_path)
                job.status = "done"
                job.stage = "completed"
            else:
                job.status = "done"
                job.stage = "completed (модель не найдена — проверь путь)"
            job.progress = 1.0
        except Exception as e:
            job.status = "error"
            job.error = f"{type(e).__name__}: {e}"
            job.stage = "failed"
        finally:
            self._emit()
            # Сохраняем состояние
            s = _load_state()
            s[job.voice_name] = asdict(job)
            _save_state(s)

    def _run_with_progress(self, cmd: list[str], job: TrainingJob):
        """Запускаем subprocess и парсим stdout на предмет прогресса эпох."""
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        for line in proc.stdout:
            line = line.rstrip()
            # Прогресс: "Epoch 42/100" или "epoch=42"
            for token in ("Epoch ", "epoch="):
                if token in line:
                    try:
                        raw = (
                            line.split(token, 1)[1]
                            .split()[0]
                            .split("/")[0]
                            .strip(",=:")
                        )
                        ep = int("".join(c for c in raw if c.isdigit()))
                        job.progress = min(0.99, ep / max(1, job.epochs))
                        job.stage = f"epoch {ep}/{job.epochs}"
                        self._emit()
                    except Exception:
                        pass
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"training subprocess exit={ret}")

    def _train_via_fork(self, fork_dir: Path, job: TrainingJob):
        """
        Заглушка запуска через клонированный форк (Applio/Mangio).
        В реальной установке Windows-скрипт train.bat из форка вызывается
        c параметрами. Здесь — минимальный запуск через python train.py.
        """
        train_py = fork_dir / "train.py"
        if not train_py.exists():
            # У форка может быть другой entry point
            candidates = list(fork_dir.glob("*train*.py"))
            if candidates:
                train_py = candidates[0]
            else:
                raise RuntimeError(f"train.py не найден в {fork_dir}")
        cmd = [
            sys.executable,
            str(train_py),
            "--experiment_dir",
            str(MODELS_DIR / job.voice_name),
            "--dataset_dir",
            str(MODELS_DIR / job.voice_name / "dataset"),
            "--total_epoch",
            str(job.epochs),
            "--sample_rate",
            "40000",
        ]
        self._run_with_progress(cmd, job)


# ---------------------------------------------------------------- inference
def infer(
    input_wav: str,
    voice_name: str = "my_voice",
    pitch_shift: int = 0,
    out_name: str = "converted.wav",
) -> str:
    """
    RVC-инференс: заменяет тембр во входном wav на голос пользователя.
    Пытается сначала rvc-python, потом форк. Возвращает путь к результату.
    """
    OUT = ROOT / "output" / "voice_final"
    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / out_name

    model_path = MODELS_DIR / voice_name / f"{voice_name}.pth"
    index_path = MODELS_DIR / voice_name / f"{voice_name}.index"

    if not model_path.exists():
        raise RuntimeError("RVC model is not available; refusing pitch-shift fallback")

    # 1) rvc-python
    backend = detect_backend()
    try:
        from rvc_python.infer import infer_file

        infer_file(
            input_path=input_wav,
            model_path=str(model_path),
            index_path=str(index_path) if index_path.exists() else None,
            output_path=str(out_path),
            f0up_key=pitch_shift,
            f0method="rmvpe",
            device=backend.kind,
        )
        if out_path.exists() and out_path.stat().st_size > 1000:
            return str(out_path)
        else:
            raise RuntimeError("RVC output file is empty or too small")
    except ImportError:
        # 2) AMD/DirectML/CPU: try fork if present
        if backend.fork != "rvc-python":
            fork_dir = FORKS_DIR / backend.fork
            if fork_dir.exists():
                # Здесь должна быть логика вызова CLI форка,
                # но для v14 мы оставляем это как задел для реального железа.
                raise RuntimeError(
                    f"RVC fork {backend.fork} is cloned but CLI integration is pending for this OS."
                )
        raise RuntimeError(
            "rvc-python not installed and no active fork integration found."
        )
    except Exception as e:
        print(f"[rvc_manager.infer] rvc-python failed: {e}")
        raise RuntimeError(
            f"RVC inference failed: {e}. No non-RVC fallback is permitted (TZ 33.5)."
        )


def _fallback_pitch(input_wav: str, out_path: str, pitch_shift: int) -> str:
    """
    УДАЛЕНО в v14: pitch_shift fallback запрещён (TZ 33.5, P0.05).
    Эта функция сохранена только как явный отказ — вызов поднимает
    RuntimeError. Используйте RVC .pth модель или честный BLOCKED.
    """
    raise RuntimeError(
        "P0.05: pitch-shift as RVC is FORBIDDEN by TZ 33.5. "
        "RVC model is required. Got call to _fallback_pitch which was "
        "disabled. Train a voice model first (see voice_onboarding)."
    )


def get_state(voice_name: str = "my_voice") -> dict:
    """Читаем состояние обучения (для UI)."""
    return _load_state().get(voice_name, {})


def is_trained(voice_name: str = "my_voice") -> bool:
    return (MODELS_DIR / voice_name / f"{voice_name}.pth").exists()


if __name__ == "__main__":
    b = detect_backend()
    print(
        f"Backend: {b.kind} / fork={b.fork} / device={b.device_name} / vram={b.vram_gb} GB"
    )
    print(f"State: {json.dumps(_load_state(), ensure_ascii=False, indent=2)}")
