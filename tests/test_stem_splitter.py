# -*- coding: utf-8 -*-
"""`modules/stem_splitter.py`: разбор на стемы и энергия стемов.

Модуль достижим (`_stage_stems` вызывает `split_stems`), но покрытия было 16 %:
работал только импорт Demucs. На этой машине Demucs нет и не будет, поэтому
`subprocess` и `librosa.load` подменяются: проверяется наша логика — какие
команды идут, что считается результатом, как отказ называется.

Реальное разделение Demucs здесь не проверено и не может быть проверено:
его нет в окружении. Тест это утверждает, а не изображает.
"""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import modules as modules_pkg

from modules import stem_splitter

SR = 22050


@pytest.fixture
def out_dir(tmp_path, monkeypatch) -> Path:
    target = tmp_path / "stems"
    monkeypatch.setattr(stem_splitter, "OUTPUT_DIR", str(target))
    return target


def _demucs_present(monkeypatch, *, fail: bool = False, stems=("vocals", "drums")) -> dict:
    """Demucs «есть»: импорт проходит, subprocess пишет стемы в ожидаемый каталог."""
    run_calls: dict = {"cmds": []}
    monkeypatch.setitem(sys.modules, "demucs", types.ModuleType("demucs"))
    monkeypatch.setitem(sys.modules, "demucs.separate", types.ModuleType("demucs.separate"))

    def fake_run(cmd, check=False):
        run_calls["cmds"].append(list(cmd))
        if fail:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
        out = Path(cmd[cmd.index("-o") + 1])
        model = cmd[cmd.index("-n") + 1]
        source = Path(cmd[-1])
        stem_dir = out / model / source.stem
        stem_dir.mkdir(parents=True, exist_ok=True)
        for name in stems:
            (stem_dir / f"{name}.mp3").write_bytes(b"ID3" + b"\0" * 64)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(stem_splitter.subprocess, "run", fake_run)
    return run_calls


# --------------------------------------------------------------------------- #
#  split_stems
# --------------------------------------------------------------------------- #

def test_missing_demucs_is_reported_with_hint(out_dir) -> None:
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "demucs", None)
        patch.setitem(sys.modules, "demucs.separate", None)
        result = stem_splitter.split_stems("track.wav")

    assert "error" in result
    assert "Demucs" in result["error"] and "pip install" in result["error"]
    assert out_dir.is_dir(), "каталог создаётся до проверки движка"


def test_command_keeps_expected_flags(out_dir, monkeypatch) -> None:
    calls = _demucs_present(monkeypatch)

    result = stem_splitter.split_stems("mix.wav", model="htdemucs")

    cmd = calls["cmds"][0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "demucs.separate"]
    assert cmd[cmd.index("-n") + 1] == "htdemucs"
    assert cmd[cmd.index("-o") + 1] == str(out_dir)
    assert "--mp3" in cmd
    assert cmd[-1] == "mix.wav"
    assert result["vocals"].endswith("vocals.mp3")


def test_only_existing_stems_are_returned(out_dir, monkeypatch) -> None:
    _demucs_present(monkeypatch, stems=("vocals",))

    result = stem_splitter.split_stems("mix.wav")

    assert set(result) == {"vocals", "note"}
    assert "analytic" in result["note"].lower() or "АНАЛИТИЧЕСКАЯ" in result["note"]


def test_wav_is_accepted_when_mp3_absent(out_dir, monkeypatch) -> None:
    _demucs_present(monkeypatch, stems=())
    monkeypatch.setattr(stem_splitter, "OUTPUT_DIR", str(out_dir))
    stem_dir = out_dir / "htdemucs" / "mix"
    stem_dir.mkdir(parents=True)
    (stem_dir / "bass.wav").write_bytes(b"RIFF" + b"\0" * 64)

    def fake_run(cmd, check=False):
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(stem_splitter.subprocess, "run", fake_run)

    result = stem_splitter.split_stems("mix.wav")

    assert result["bass"].endswith("bass.wav")


def test_demucs_failure_is_named(out_dir, monkeypatch) -> None:
    _demucs_present(monkeypatch, fail=True)

    result = stem_splitter.split_stems("mix.wav")

    assert "error" in result
    assert result["error"].startswith("Demucs failed:")


def test_no_stems_written_still_reports_note(out_dir, monkeypatch) -> None:
    """Demucs «прошёл», но файлов нет — пустой результат, а не выдуманные пути."""
    _demucs_present(monkeypatch, stems=())

    result = stem_splitter.split_stems("mix.wav")

    assert set(result) == {"note"}


# --------------------------------------------------------------------------- #
#  analyze_arrangement
# --------------------------------------------------------------------------- #

def _write(path: Path, seconds: float = 0.5, amp: float = 0.4) -> str:
    t = np.arange(int(SR * seconds)) / SR
    sf.write(path, amp * np.sin(2 * np.pi * 200 * t), SR)
    return str(path)


def test_arrangement_energy_per_stem(tmp_path, monkeypatch) -> None:
    import librosa

    loud = _write(tmp_path / "loud.wav", amp=0.6)
    quiet = _write(tmp_path / "quiet.wav", amp=0.001)
    monkeypatch.setattr(
        stem_splitter, "librosa", None, raising=False
    )
    # модуль импортирует librosa внутри функции — обеспечим тот же путь
    monkeypatch.setitem(sys.modules, "librosa", librosa)

    report = stem_splitter.analyze_arrangement({"vocals": loud, "bass": quiet})

    assert set(report) == {"vocals", "bass"}
    assert report["vocals"]["present"] is True
    assert report["vocals"]["energy"] > report["bass"]["energy"]


def test_arrangement_skips_missing_and_unknown(tmp_path, monkeypatch) -> None:
    import librosa

    present = _write(tmp_path / "v.wav")
    monkeypatch.setitem(sys.modules, "librosa", librosa)

    report = stem_splitter.analyze_arrangement({
        "vocals": present,
        "drums": str(tmp_path / "gone.wav"),
        "other": None,
        "weird": present,
    })

    assert set(report) == {"vocals"}


def test_arrangement_without_librosa_is_reported(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "librosa", None)

    result = stem_splitter.analyze_arrangement({"vocals": "x.wav"})

    assert "error" in result and "librosa" in result["error"]


def test_arrangement_of_empty_dict_is_empty(monkeypatch) -> None:
    import librosa

    monkeypatch.setitem(sys.modules, "librosa", librosa)

    assert stem_splitter.analyze_arrangement({}) == {}


def test_low_energy_stem_is_marked_absent(tmp_path, monkeypatch) -> None:
    """Тихий стем — «не звучит»; порог 0.005 проверяется, а не подразумевается."""
    import librosa

    silent = tmp_path / "silent.wav"
    sf.write(silent, np.zeros(int(SR * 0.3)), SR)
    monkeypatch.setitem(sys.modules, "librosa", librosa)

    report = stem_splitter.analyze_arrangement({"drums": str(silent)})

    assert report["drums"]["present"] is False
    assert report["drums"]["energy"] < 0.005


def test_cli_prints_usage_without_argument(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["stem_splitter.py"])
    import runpy

    # модуль уже импортирован тестами — runpy иначе предупреждает об этом
    monkeypatch.delitem(sys.modules, "modules.stem_splitter", raising=False)
    runpy.run_module("modules.stem_splitter", run_name="__main__")

    assert "Usage:" in capsys.readouterr().out


def test_cli_splits_given_file(monkeypatch, capsys, out_dir) -> None:
    _demucs_present(monkeypatch, stems=("vocals",))
    monkeypatch.setattr(sys, "argv", ["stem_splitter.py", "mix.wav"])
    import runpy

    monkeypatch.delitem(sys.modules, "modules.stem_splitter", raising=False)
    runpy.run_module("modules.stem_splitter", run_name="__main__")

    assert "vocals" in capsys.readouterr().out
