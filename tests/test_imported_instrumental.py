import numpy as np
import soundfile as sf

from app.core.orchestrator import run_full_pipeline
from app.core.stages.imported_beat import import_instrumental


def test_user_instrumental_is_used_by_mix_without_touching_source(tmp_path):
    source = tmp_path / "source.flac"
    signal = (0.15 * np.sin(np.arange(8000 * 2) * 0.12)).astype("float32")
    sf.write(source, signal, 8000)
    before = source.read_bytes()
    root = tmp_path / "project"
    result = run_full_pipeline("own-beat", {"beat_engine": "user_audio", "beat_input_path": str(source),
                                             "voice_mode": "off"}, out_root=root, only={"beat", "mix"})
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["_stage_beat"]["output"]["engine"] == "user_instrumental"
    assert stages["_stage_beat"]["status"] == "OK"
    assert stages["_stage_mix_and_sidechain"]["status"] == "OK"
    assert sf.info(root / "beat.wav").duration == 2
    assert source.read_bytes() == before


def test_silent_or_missing_input_fails_without_overwriting_existing_result(tmp_path):
    source = tmp_path / "silence.wav"
    sf.write(source, np.zeros(8000), 8000)
    dest = tmp_path / "beat.wav"
    dest.write_bytes(b"previous")
    import pytest
    with pytest.raises(ValueError, match="silent"):
        import_instrumental(str(source), dest)
    with pytest.raises(FileNotFoundError):
        import_instrumental(str(tmp_path / "missing.wav"), dest)
    assert dest.read_bytes() == b"previous"
    assert set(tmp_path.iterdir()) == {source, dest}
