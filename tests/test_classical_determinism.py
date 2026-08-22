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
