# -*- coding: utf-8 -*-
"""Качественные контракты outputs LLM и генерации аудио."""
from __future__ import annotations

import json

import numpy as np
import soundfile as sf

from app.ai.quality import validate_audio_artifact, validate_metadata_json


def test_metadata_quality_accepts_complete_release_payload() -> None:
    payload = {
        "title": "Ночной маршрут",
        "spotify_desc": "Динамичный phonk-трек для ночной дороги.",
        "youtube_desc": "Премьера независимого трека.",
        "tags_tiktok": ["phonk", "newmusic"],
        "tags_instagram": ["music"],
    }

    result = validate_metadata_json(payload)

    assert result["ok"] is True
    assert result["metrics"]["tags"] == 3


def test_metadata_quality_rejects_incomplete_payload() -> None:
    result = validate_metadata_json({"title": "x", "tags_tiktok": []})

    assert result["ok"] is False
    assert "title" in result["reason"]
    assert "description" in result["reason"]
    assert "tags" in result["reason"]


def test_audio_quality_accepts_signal_and_rejects_silence(tmp_path) -> None:
    sample_rate = 8_000
    t = np.arange(sample_rate * 2) / sample_rate
    signal = (0.2 * np.sin(2 * np.pi * 220 * t)).astype("float32")
    valid_path = tmp_path / "signal.wav"
    silent_path = tmp_path / "silent.wav"
    sf.write(valid_path, np.column_stack([signal, signal]), sample_rate)
    sf.write(silent_path, np.zeros((sample_rate * 2, 2), dtype="float32"), sample_rate)

    valid = validate_audio_artifact(valid_path, min_duration_sec=1.5)
    silent = validate_audio_artifact(silent_path, min_duration_sec=1.0)

    assert valid["ok"] is True
    assert valid["metrics"]["channels"] == 2
    assert silent["ok"] is False
    assert silent["reason"] == "audio is silent"


def test_ai_dry_run_persists_valid_metadata_fallback(tmp_path) -> None:
    from app.core.orchestrator_ai import run_ai_pipeline

    run_ai_pipeline("metadata_quality", out_root=tmp_path, dry_run=True)
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))

    assert metadata["ok"] is True
    assert metadata["source"] == "dry"
    assert metadata["quality"]["ok"] is True
