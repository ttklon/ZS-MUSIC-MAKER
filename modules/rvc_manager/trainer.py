# -*- coding: utf-8 -*-
"""
modules/rvc_manager/trainer.py — подготовка набора и статус обучения RVC.

Проверенный встроенный backend обучения пока не подключён: train возвращает
blocked_backend, не выдавая запуск или веса за готовый результат.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from modules.rvc_manager.backend import RVCBackend, detect_backend
from modules.rvc_manager.config import MODELS_DIR


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
    Подготовка RVC dataset; встроенное обучение пока явно заблокировано.
    """

    def __init__(self, backend: RVCBackend | None = None):
        self.backend = backend or detect_backend()
        self.job: TrainingJob | None = None
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
        """Fail closed: rvc-python exposes inference only; no verified trainer is wired."""
        self.job = TrainingJob(
            voice_name=voice_name, epochs=max(epochs, 300) if night_mode else epochs,
            device=self.backend.kind, started_at=time.time(), status="blocked_backend",
            stage="not started",
            error="Встроенное обучение RVC не подключено. Обучите свой голос во внешней совместимой программе и импортируйте .pth модель.",
        )
        self._emit()
        return self.job

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
