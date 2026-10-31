# -*- coding: utf-8 -*-
"""
modules/rvc_manager/trainer.py — фоновое обучение RVC-модели голоса.

Обучение идёт в отдельном потоке, прогресс парсится из stdout форка и
раздаётся слушателям. Инкрементальное дообучение: новые записи копируются в
dataset голоса, тренировка стартует от существующего состояния.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from modules.rvc_manager.config import MODELS_DIR, _load_state, _save_state


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
        self.dataset_copy_errors: list[str] = []
        self.progress_parse_errors: list[str] = []

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
        self.dataset_copy_errors = []
        for e in idx:
            src = e.get("path")
            if src and Path(src).exists():
                try:
                    shutil.copy(src, ds / Path(src).name)
                    n += 1
                except Exception as exc:
                    self.dataset_copy_errors.append(f"{type(exc).__name__}: {exc}")
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
        self.progress_parse_errors = []
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
                    except Exception as exc:
                        self.progress_parse_errors.append(f"{type(exc).__name__}: {exc}")
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
