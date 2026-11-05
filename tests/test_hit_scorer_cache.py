from __future__ import annotations

import numpy as np

import modules.hit_scorer.audio as scorer


def test_hit_scorer_audio_cache_uses_path_sample_rate_and_mtime(monkeypatch) -> None:
    calls: list[tuple[str, int]] = []
    scorer._load_audio_cached.cache_clear()

    def fake_load(path: str, sr: int):
        calls.append((path, sr))
        return np.zeros(64, dtype=np.float32), sr

    monkeypatch.setattr(scorer, "_load_audio", fake_load)
    first = scorer._load_audio_cached("/tmp/track.wav", 22_050, 1)
    second = scorer._load_audio_cached("/tmp/track.wav", 22_050, 1)
    changed = scorer._load_audio_cached("/tmp/track.wav", 22_050, 2)

    assert first[1] == second[1] == changed[1] == 22_050
    assert calls == [("/tmp/track.wav", 22_050), ("/tmp/track.wav", 22_050)]
