from __future__ import annotations

from pathlib import Path

import modules.cyber_synth as cyber_module
from modules.beat_constructor import BeatConstructor


def test_seeded_classic_beat_is_byte_identical_and_seed_sensitive(tmp_path, monkeypatch) -> None:
    import modules.beat_constructor as beat_module

    monkeypatch.setattr(beat_module, "OUTPUT_DIR", str(tmp_path))
    common = {"bpm": 130, "genre": "phonk", "seed": 91, "groove": {"hihat_density": 0.7, "swing": 0.12}}
    first = BeatConstructor(**common).build_track(duration_sec=8, include_intro=False, include_outro=False, out_name="first.wav")
    second = BeatConstructor(**common).build_track(duration_sec=8, include_intro=False, include_outro=False, out_name="second.wav")
    third = BeatConstructor(**{**common, "seed": 92}).build_track(duration_sec=8, include_intro=False, include_outro=False, out_name="third.wav")

    assert Path(first["beat_path"]).read_bytes() == Path(second["beat_path"]).read_bytes()
    assert Path(first["beat_path"]).read_bytes() != Path(third["beat_path"]).read_bytes()
    assert first["seed"] == 91
    assert first["deterministic"] is True


def test_seeded_cyber_synth_local_dsp_is_byte_identical(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cyber_module, "HAS_PEDALBOARD", False)
    first_path = tmp_path / "cyber_first.wav"
    second_path = tmp_path / "cyber_second.wav"
    first = cyber_module.CyberSynth(seed=91).synthesize_track(bpm=135, duration_sec=4, out_path=str(first_path))
    second = cyber_module.CyberSynth(seed=91).synthesize_track(bpm=135, duration_sec=4, out_path=str(second_path))

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["seed"] == second["seed"] == 91
    assert first["deterministic"] is True
    assert first["determinism_scope"] == "classical_local_dsp_only"


def test_classical_pipeline_creates_valid_cpu_master_without_torch(tmp_path, monkeypatch) -> None:
    import sys

    import numpy as np
    import soundfile as sf
    from app.core.orchestrator import run_full_pipeline

    # The classical reference must not accidentally acquire or require Torch.
    monkeypatch.setitem(sys.modules, "torch", None)
    result = run_full_pipeline(
        "cpu_classical_regression",
        {
            "genre": "drift_phonk",
            "theme": "CPU regression pulse",
            "duration_sec": 4,
            "voice_mode": "off",
            "user_lyrics_lines": ["CPU baseline carries the night"],
        },
        dry_run=False,
        out_root=tmp_path,
    )
    mastering = next(stage for stage in result["stages"] if stage["name"] == "_stage_mastering")
    masters = mastering["output"]["masters"]
    streaming = Path(masters["streaming"])
    audio, sample_rate = sf.read(streaming, always_2d=True)

    assert result["dry_run"] is False
    assert result["master_path"] == str(streaming)
    assert streaming.exists() and streaming.suffix == ".wav"
    assert sample_rate >= 22_050
    assert audio.shape[0] >= sample_rate * 3
    assert audio.shape[1] in (1, 2)
    assert np.isfinite(audio).all()
    assert float(np.max(np.abs(audio))) > 0.001
