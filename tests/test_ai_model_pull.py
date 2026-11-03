# -*- coding: utf-8 -*-
"""Контракты локального pull/verify без скачивания многогигабайтных weights."""
from __future__ import annotations

import json
import sys
from unittest.mock import patch

from app.ai.registry import MODEL_REGISTRY
from tools import pull_ai_models as puller


def test_pull_tool_covers_exactly_all_registered_roles() -> None:
    assert len(MODEL_REGISTRY) == 13
    assert set(MODEL_REGISTRY) == {
        "lyrics_llm", "analysis_llm", "metadata_llm", "music_generation",
        "music_stereo", "tts_vocal", "vocal_rvc", "stem_splitter", "asr",
        "audio_tagger", "essentia", "cover_art", "mastering_ai",
    }


def test_local_manifest_sha256_detects_corruption(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(puller, "AI_MODELS_DIR", tmp_path)
    role_dir = tmp_path / "lyrics_llm"
    role_dir.mkdir()
    artifact = role_dir / "fixture.gguf"
    artifact.write_bytes(b"trusted fixture")

    puller._manifest_for_local_files(
        "lyrics_llm",
        status="installed",
        source="fixture://local",
        note="test fixture",
    )
    assert puller.verify("lyrics_llm") is True

    artifact.write_bytes(b"tampered fixture")
    assert puller.verify("lyrics_llm") is False


def test_pip_only_role_writes_honest_manifest_without_weights(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(puller, "AI_MODELS_DIR", tmp_path)

    assert puller.pull("mastering_ai") is True
    manifest = json.loads((tmp_path / "mastering_ai" / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "pip_only"
    assert manifest["files"] == []
    assert puller.verify("mastering_ai") is True


def test_pull_main_rejects_unknown_role_without_network(capsys) -> None:
    assert puller.main(["--role", "not_a_role"]) == 1
    assert "unknown model role" in capsys.readouterr().out


def test_pull_list_includes_per_role_manifest_state(capsys) -> None:
    assert puller.main(["--list"]) == 0
    listed = capsys.readouterr().out
    for role in MODEL_REGISTRY:
        assert role in listed
    assert "NOT_PULLED" in listed or "MANIFEST" in listed


def test_registry_checks_downloaded_gguf_under_role_directory(tmp_path, monkeypatch) -> None:
    import importlib

    registry_module = importlib.import_module("app.ai.registry")
    model_file = tmp_path / "lyrics_llm" / MODEL_REGISTRY["lyrics_llm"]["file"]
    model_file.parent.mkdir(parents=True)
    model_file.write_bytes(b"placeholder")
    monkeypatch.setattr(registry_module, "MODELS_DIR", tmp_path)

    with patch.dict(sys.modules, {"llama_cpp": object()}):
        assert registry_module.registry.is_available("lyrics_llm") is True


def test_verify_rejects_unverified_external_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(puller, "AI_MODELS_DIR", tmp_path)
    puller._write_manifest("stem_splitter", status="installed_external_cache", source="external", files=[])
    assert puller.verify("stem_splitter") is False


def test_pull_all_attempts_remaining_roles_after_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(puller, "MODEL_REGISTRY", {"a": {}, "b": {}, "c": {}})
    monkeypatch.setattr(puller, "pull", lambda key: calls.append(key) or key != "a")
    assert puller.main(["--all"]) == 1
    assert calls == ["a", "b", "c"]


def test_ai_pull_cli_returns_failure_on_download_error(monkeypatch):
    from app.cli.commands import run_ai_pull
    monkeypatch.setattr(puller, "pull", lambda key: False)
    assert run_ai_pull("lyrics_llm") == 2


def test_user_voice_missing_is_not_counted_as_download_success(tmp_path, monkeypatch):
    monkeypatch.setattr(puller, "AI_MODELS_DIR", tmp_path)
    assert puller.pull("vocal_rvc") is False
    assert puller.verify("vocal_rvc") is False
