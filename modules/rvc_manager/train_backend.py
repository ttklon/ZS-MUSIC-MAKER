# -*- coding: utf-8 -*-
"""
modules/rvc_manager/train_backend.py — запуск **настоящего** обучения RVC.

`rvc-python` умеет только инференс; тренировочных скриптов в pip-пакете нет.
Обучение живёт в форках RVC (WebUI / Applio / Mangio), поэтому здесь — один
честный диспетчер:

  1. `ZSMM_RVC_TRAIN_CMD` — команда пользователя/CI с подстановками
     `{dataset}`, `{voice}`, `{epochs}`, `{device}`, `{out}`, `{batch}`;
  2. известные скрипты форка из `models/rvc_forks/<fork>` (порядок: Applio,
     Mangio, RVC-WebUI) — у них общий набор флагов `-e/-sr/-bs/-te/-pd`;
  3. ничего не найдено → `None`, и вызывающий код обязан сказать «обучение не
     подключено», а не выдать эмуляцию за модель.

Результат считается успешным только если процесс завершился с кодом 0 **и**
на диске появился непустой `.pth`. Иначе — `error` с хвостом лога: выдумывать
модель нельзя, её потом грузит `warnings_only`-инференс.
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from modules.rvc_manager.config import FORKS_DIR, MODELS_DIR

_LOG = logging.getLogger(__name__)

# Файлы-точки входа известных форков: (путь от корня форка, человеческое имя).
KNOWN_ENTRIES: tuple[tuple[str, str], ...] = (
    ("train_nsf_sim_cache_sid_load_pretrain.py", "rvc-webui trainer"),
    ("train.py", "applio trainer"),
    ("infer/modules/train/train.py", "rvc-webui train module"),
)

# Порядок обхода форков: Applio ставится пип-совместимо и живёт на CPU.
FORK_ORDER: tuple[str, ...] = ("applio", "mangio", "rvc-webui")

DEFAULT_ENV_CMD = "ZSMM_RVC_TRAIN_CMD"


@dataclass
class TrainSpec:
    """Найденный способ обучения: чем запускать и как это назвать в отчёте."""

    kind: str  # "env" | "fork"
    label: str
    command: list[str]
    cwd: str | None = None


@dataclass
class TrainRun:
    """Итог запуска обучения — только факты, без обещаний."""

    ok: bool
    status: str  # done | error | missing_backend
    reason: str = ""
    model_path: str | None = None
    log_tail: list[str] = field(default_factory=list)
    device: str = "cpu"
    label: str = ""


def _template_vars(dataset_dir: Path, voice_name: str, epochs: int, device: str, out_dir: Path) -> dict[str, str]:
    """Подстановки для `ZSMM_RVC_TRAIN_CMD` и для сборки флагов форка."""
    return {
        "dataset": str(dataset_dir),
        "voice": voice_name,
        "epochs": str(int(epochs)),
        "device": device,
        "out": str(out_dir),
        "batch": "2" if device == "cpu" else "4",
    }


def _from_env(values: dict[str, str]) -> TrainSpec | None:
    """Команда из `ZSMM_RVC_TRAIN_CMD` — единственный путь без угадывания флагов."""
    raw = os.environ.get(DEFAULT_ENV_CMD, "").strip()
    if not raw:
        return None
    try:
        parts = shlex.split(raw)
    except ValueError as exc:
        _LOG.debug("RVC train cmd unparsable: %s", exc)
        return None
    try:
        command = [part.format(**values) for part in parts]
    except (KeyError, ValueError) as exc:
        _LOG.debug("RVC train cmd placeholders unknown: %s", exc)
        return None
    return TrainSpec(kind="env", label=f"env:{DEFAULT_ENV_CMD}", command=command)


def _fork_flags(values: dict[str, str], entry: Path) -> list[str]:
    """Флаги тренировочного скрипта RVC (общие у WebUI и Applio).

    `-g` — индекс GPU; на CPU форки ждут `-` (стандартная ветка `if args.g != "-"`).
    """
    device = "-" if values["device"] == "cpu" else "0"
    return [
        str(entry),
        "-e", values["voice"],
        "-sr", "40k",
        "-f0", "1",
        "-bs", values["batch"],
        "-g", device,
        "-te", values["epochs"],
        "-se", values["epochs"],
        "-pg", "preprocess",
        "-pd", values["dataset"],
        "-ps", "3.0",
        "-pe", "3.7",
        "-sw", "1",
        "-l", "1",
        "-c", "0",
        "-stop", values["epochs"],
    ]


def _from_forks(values: dict[str, str]) -> TrainSpec | None:
    """Готовый форк с тренировочным скриптом внутри `models/rvc_forks/`."""
    extra = shlex.split(os.environ.get("ZSMM_RVC_TRAIN_EXTRA", "").strip())
    for fork in FORK_ORDER:
        root = FORKS_DIR / fork
        if not root.is_dir():
            continue
        for relative, label in KNOWN_ENTRIES:
            entry = root / relative
            if not entry.is_file():
                continue
            spec = TrainSpec(
                kind="fork",
                label=f"{fork}:{label}",
                command=_fork_flags(values, entry) + extra,
                cwd=str(root),
            )
            return spec
    return None


def find_trainer(
    dataset_dir: Path, voice_name: str, epochs: int, device: str, out_dir: Path
) -> TrainSpec | None:
    """Найти реальный способ обучения. `None` — обучение в этой сборке не подключено."""
    values = _template_vars(dataset_dir, voice_name, epochs, device, out_dir)
    return _from_env(values) or _from_forks(values)


def _model_candidates(out_dir: Path, voice_name: str) -> list[Path]:
    """Куда форки кладут веса: несколько известных раскладок."""
    return [
        out_dir / f"{voice_name}.pth",
        out_dir / voice_name / f"{voice_name}.pth",
        MODELS_DIR / voice_name / f"{voice_name}.pth",
        MODELS_DIR / voice_name / f"{voice_name}_best.pth",
    ]


def _newest_model(out_dir: Path, voice_name: str) -> Path | None:
    """Самое свежее непустое `.pth`: пустой файл моделью не считается."""
    found = [
        path for path in _model_candidates(out_dir, voice_name)
        if path.is_file() and path.stat().st_size > 1024
    ]
    return max(found, key=lambda path: path.stat().st_mtime) if found else None


def _emit_tail(lines: list[str], on_progress: Callable[[str], None] | None) -> None:
    """Показать строку человеку, если он слушает (UI/лог)."""
    if on_progress is None:
        return
    try:
        on_progress(lines[-1])
    except Exception:  # noqa: BLE001 - подписчик не должен ломать обучение
        _LOG.debug("RVC train progress callback failed", exc_info=True)


def _pump(proc: subprocess.Popen, epoch_line: Callable[[str], None], tail: list[str]) -> None:
    """Читать stdout построчно, держа хвост лога для отчёта."""
    for line in proc.stdout or []:
        clean = line.rstrip()
        if not clean:
            continue
        tail.append(clean)
        del tail[:-40]
        epoch_line(clean)


def run_training(
    spec: TrainSpec,
    dataset_dir: Path,
    voice_name: str,
    epochs: int,
    device: str,
    out_dir: Path,
    on_progress: Callable[[str], None] | None = None,
) -> TrainRun:
    """Запустить обучение и проверить, что модель действительно появилась."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tail: list[str] = []
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        proc = subprocess.Popen(
            spec.command,
            cwd=spec.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
    except (OSError, ValueError) as exc:
        return TrainRun(False, "error", f"trainer not startable: {type(exc).__name__}: {exc}",
                        log_tail=tail, device=device, label=spec.label)

    _pump(proc, lambda line: _emit_tail([line], on_progress), tail)
    code = proc.wait()
    model = _newest_model(out_dir, voice_name)
    if code != 0:
        return TrainRun(False, "error", f"trainer exit={code}", log_tail=tail,
                        device=device, label=spec.label)
    if model is None:
        return TrainRun(
            False, "error",
            "trainer exited 0 but produced no .pth; check the fork log before claiming a voice",
            log_tail=tail, device=device, label=spec.label,
        )
    _emit_tail([f"model: {model}"], on_progress)
    return TrainRun(True, "done", f"trained with {spec.label}", model_path=str(model),
                    log_tail=tail, device=device, label=spec.label)
