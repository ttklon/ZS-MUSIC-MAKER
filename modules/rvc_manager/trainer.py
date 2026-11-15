# -*- coding: utf-8 -*-
"""
modules/rvc_manager/trainer.py — подготовка набора и обучение RVC.

Обучение запускает **настоящий** тренер (`train_backend`): команда из
`ZSMM_RVC_TRAIN_CMD` либо тренировочный скрипт подтянутого форка в
`models/rvc_forks/`. Если ни того, ни другого нет — `blocked_backend` с
действием, а не тихая эмуляция: модель потом грузит инференс, и подделка
всплыла бы там.
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
from modules.rvc_manager.train_backend import find_trainer, run_training


@dataclass
class TrainingJob:
    voice_name: str
    epochs: int
    device: str
    started_at: float = 0.0
    progress: float = 0.0
    status: str = "queued"  # queued | running | done | error | blocked_backend
    stage: str = ""
    error: str | None = None
    model_path: str | None = None


class RVCTrainer:
    """Подготовка dataset из `voice_vault` и обучение голоса."""

    def train_status_report(self) -> dict:
        """Короткий отчёт для UI: что произошло и куда легла модель."""
        job = self.job
        if job is None:
            return {"status": "idle", "reason": "обучение ещё не запускалось"}
        return {
            "status": job.status,
            "voice_name": job.voice_name,
            "epochs": job.epochs,
            "device": job.device,
            "progress": job.progress,
            "model_path": job.model_path,
            "reason": job.error,
            "log_tail": list(self.last_log_tail[-5:]),
        }


    def __init__(self, backend: RVCBackend | None = None):
        self.backend = backend or detect_backend()
        self.job: TrainingJob | None = None
        self._listeners: list[Callable[[TrainingJob], None]] = []
        self.listener_errors: list[str] = []
        self.dataset_copy_errors: list[str] = []
        self.progress_parse_errors: list[str] = []
        self.last_log_tail: list[str] = []

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
        """Обучить голос настоящим тренером RVC; без тренера — честный blocked.

        Прогресс эпох из лога тренера попадает в `TrainingJob.progress`, а
        `.pth` считается готовой моделью только если тренер её действительно
        записал (проверяет `train_backend`).
        """
        total_epochs = max(epochs, 300) if night_mode else epochs
        self.job = TrainingJob(
            voice_name=voice_name, epochs=total_epochs, device=self.backend.kind,
            started_at=time.time(), status="queued", stage="dataset",
        )
        self._emit()
        dataset_dir = self._dataset_ready(voice_name)
        out_dir = MODELS_DIR / voice_name
        spec = find_trainer(dataset_dir, voice_name, total_epochs, self.backend.kind, out_dir)
        if spec is None:
            self.job.status = "blocked_backend"
            self.job.error = (
                "Встроенное обучение RVC не подключено: rvc-python умеет только инференс. "
                "Подтяни форк (`python main.py --rvc-fork applio`) или укажи "
                "ZSMM_RVC_TRAIN_CMD, затем повтори."
            )
            self._emit()
            return self.job
        self.job.status = "running"
        self.job.stage = f"training ({spec.label})"
        self._emit()
        run = run_training(
            spec, dataset_dir, voice_name, total_epochs, self.backend.kind, out_dir,
            on_progress=self._on_trainer_line,
        )
        self._finish_from_run(run)
        return self.job

    def _on_trainer_line(self, line: str) -> None:
        """Строка лога тренера: обновить эпоху и отдать подписчикам."""
        self._parse_epoch(line)
        self._emit()

    def _parse_epoch(self, line: str) -> None:
        """Разобрать «Epoch 42/100» / «epoch=42» и обновить прогресс."""
        for token in ("Epoch ", "epoch="):
            if token not in line or self.job is None:
                continue
            raw = line.split(token, 1)[1].split()[0].split("/")[0].strip(",=:")
            digits = "".join(char for char in raw if char.isdigit())
            if not digits:
                self.progress_parse_errors.append(f"ValueError: invalid epoch token {raw!r}")
                continue
            epoch = int(digits)
            self.job.progress = min(0.99, epoch / max(1, self.job.epochs))
            self.job.stage = f"epoch {epoch}/{self.job.epochs}"
            return

    def _finish_from_run(self, run) -> None:
        """Перенести итог запуска в `TrainingJob`: статус, модель, хвост лога."""
        if self.job is None:
            return
        if run.ok:
            self.job.status = "done"
            self.job.progress = 1.0
            self.job.stage = f"model: {run.model_path}"
            self.job.model_path = run.model_path
        else:
            self.job.status = "error"
            self.job.error = run.reason
            self.job.stage = f"{run.label}: {run.reason}"
        self.last_log_tail = list(run.log_tail)
        self._emit()

    def _run_with_progress(self, cmd: list[str], job: TrainingJob):
        """Запустить тренер и разобрать прогресс эпох из его вывода."""
        self.progress_parse_errors = []
        self.job = job
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
            self._parse_epoch(line.rstrip())
            self._emit()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"training subprocess exit={ret}")
