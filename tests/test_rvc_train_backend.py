# -*- coding: utf-8 -*-
"""Тренер RVC: команда реально запускается, модель — только с диска.

`rvc-python` умеет лишь инференс, поэтому обучение идёт внешней командой
(`ZSMM_RVC_TRAIN_CMD`) или скриптом форка. Здесь проверяется, что:

  * без тренера job честно `blocked_backend` и не выдаёт себя за обучение;
  * команда из окружения запускается с подстановками и её прогресс виден;
  * «успех» без файла `.pth` — ошибка, а не готовый голос;
  * реальный `.pth` на диске становится `model_path` и `done`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from modules.rvc_manager import RVCBackend, RVCTrainer
from modules.rvc_manager import train_backend


def _fake_trainer_script(tmp_path: Path, write_model: bool) -> Path:
    """Скрипт-тренер: печатает эпохи и (опционально) пишет «модель»."""
    script = tmp_path / "trainer.py"
    body = [
        "import sys, pathlib",
        "out = pathlib.Path(sys.argv[1])",
        "out.mkdir(parents=True, exist_ok=True)",
        "for epoch in range(1, 4):",
        "    print(f'Epoch {epoch}/3', flush=True)",
    ]
    if write_model:
        body += [
            "    (out / 'probe.pth').write_bytes(b'x' * 4096)",
        ]
    script.write_text("\n".join(body) + "\n", encoding="utf-8")
    return script


@pytest.fixture()
def trainer(tmp_path, monkeypatch):
    """Тренер с подменённым каталогом датасета: голосовой vault не нужен."""
    monkeypatch.setattr("modules.rvc_manager.trainer.MODELS_DIR", tmp_path / "rvc_models")
    subject = RVCTrainer(backend=RVCBackend(kind="cpu", ok=True))
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    monkeypatch.setattr(subject, "_dataset_ready", lambda _name: dataset)
    return subject


def test_no_trainer_blocks_instead_of_faking_training(trainer, monkeypatch) -> None:
    monkeypatch.delenv("ZSMM_RVC_TRAIN_CMD", raising=False)
    monkeypatch.setattr(train_backend, "FORKS_DIR", Path("/nonexistent/forks"))

    job = trainer.train("probe", epochs=3)

    assert job.status == "blocked_backend"
    assert "не подключено" in job.error
    assert "--rvc-fork" in job.error


def test_env_command_runs_and_reports_epochs(trainer, tmp_path, monkeypatch) -> None:
    script = _fake_trainer_script(tmp_path, write_model=True)
    monkeypatch.setenv(
        "ZSMM_RVC_TRAIN_CMD",
        f'"{sys.executable}" "{script}" "{{out}}" {{epochs}}',
    )

    job = trainer.train("probe", epochs=3)

    assert job.status == "done", job.error
    assert job.model_path and Path(job.model_path).name == "probe.pth"
    assert job.progress == 1.0
    assert any("Epoch" in line for line in trainer.last_log_tail)


def test_epoch_lines_move_progress(trainer) -> None:
    """Прогресс считается по строкам тренера, а не по таймеру."""
    from modules.rvc_manager.trainer import TrainingJob

    trainer.job = TrainingJob(voice_name="probe", epochs=10, device="cpu")
    trainer._parse_epoch("Epoch 5/10")
    assert trainer.job.progress == 0.5 and trainer.job.stage == "epoch 5/10"

    trainer._parse_epoch("epoch=7")
    assert trainer.job.progress == 0.7

    trainer._parse_epoch("Epoch ???/10")
    assert trainer.job.progress == 0.7, "испорченная строка не двигает прогресс"
    assert trainer.progress_parse_errors


def test_exit_zero_without_weights_is_an_error(trainer, tmp_path, monkeypatch) -> None:
    script = _fake_trainer_script(tmp_path, write_model=False)
    monkeypatch.setenv("ZSMM_RVC_TRAIN_CMD", f'"{sys.executable}" "{script}" "{{out}}"')

    job = trainer.train("probe", epochs=3)

    assert job.status == "error"
    assert "no .pth" in job.error
    assert job.model_path is None


def test_failing_command_reports_exit_code(trainer, tmp_path, monkeypatch) -> None:
    script = tmp_path / "boom.py"
    script.write_text("import sys; print('cuda oom', flush=True); sys.exit(3)\n", encoding="utf-8")
    monkeypatch.setenv("ZSMM_RVC_TRAIN_CMD", f'"{sys.executable}" "{script}"')

    job = trainer.train("probe", epochs=2)

    assert job.status == "error"
    assert "exit=3" in job.error
    assert any("cuda oom" in line for line in trainer.last_log_tail)


def test_fork_flags_use_cpu_marker() -> None:
    values = {"dataset": "ds", "voice": "v", "epochs": "10", "device": "cpu",
              "out": "out", "batch": "2"}
    flags = train_backend._fork_flags(values, Path("/fork/train.py"))

    assert flags[flags.index("-g") + 1] == "-", "CPU-ветка форков ждёт дефис"
    assert flags[flags.index("-te") + 1] == "10"
    assert flags[flags.index("-pd") + 1] == "ds"


def test_fork_discovery_prefers_downloaded_trainer(tmp_path, monkeypatch) -> None:
    fork = tmp_path / "applio"
    (fork / "infer" / "modules" / "train").mkdir(parents=True)
    (fork / "infer" / "modules" / "train" / "train.py").write_text("x", encoding="utf-8")
    monkeypatch.setattr(train_backend, "FORKS_DIR", tmp_path)
    monkeypatch.delenv("ZSMM_RVC_TRAIN_CMD", raising=False)

    spec = train_backend.find_trainer(tmp_path / "ds", "v", 10, "cpu", tmp_path / "out")

    assert spec is not None and spec.kind == "fork" and spec.label.startswith("applio:")
    assert spec.cwd == str(fork)


def test_cli_help_lists_voice_training_and_does_not_crash() -> None:
    """`--help` не должен падать: `%` в описаниях argparse принимает за формат."""
    import subprocess
    import sys as _sys

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [_sys.executable, str(root / "main.py"), "--help"],
        capture_output=True, text=True, timeout=180,
    )

    assert result.returncode == 0, result.stderr[-500:]
    assert "--rvc-train" in result.stdout and "--rvc-fork" in result.stdout
