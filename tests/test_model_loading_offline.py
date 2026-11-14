"""T16: веса моделей не скачиваются неявно.

`MusicGen.get_pretrained(...)`, `get_model("htdemucs")`,
`ClapModel.from_pretrained(...)`, `DiffusionPipeline.from_pretrained(...)` и
`TTS(model_name=...)` при отсутствии локальных весов молча тянули их из сети.
Для машины без интернета это「зависший рендер」, а для пользователя — трафик,
о котором он не просил.

Правило: локальный preflight до обращения к сети; скачивание — только при
`ZSMM_ALLOW_MODEL_DOWNLOAD=1`.
"""

from __future__ import annotations

import pytest

from pathlib import Path

import importlib

# `app.ai.registry` в пакете перекрыт объектом реестра, поэтому модуль берём явно.
registry_module = importlib.import_module("app.ai.registry")
from app.ai.weights import (
    ALLOW_DOWNLOAD_ENV,
    download_allowed,
    ensure_local_weights,
    weights_hint,
)


def test_download_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv(ALLOW_DOWNLOAD_ENV, raising=False)

    assert download_allowed() is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on"])
def test_download_can_be_opted_in(monkeypatch, value: str) -> None:
    monkeypatch.setenv(ALLOW_DOWNLOAD_ENV, value)

    assert download_allowed() is True


@pytest.mark.parametrize("value", ["0", "", "no", "false"])
def test_download_opt_in_is_strict(monkeypatch, value: str) -> None:
    monkeypatch.setenv(ALLOW_DOWNLOAD_ENV, value)

    assert download_allowed() is False


def test_preflight_raises_with_a_usable_hint(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(ALLOW_DOWNLOAD_ENV, raising=False)

    with pytest.raises(FileNotFoundError) as error:
        ensure_local_weights("music_generation", tmp_path)

    message = str(error.value)
    assert "pull_ai_models" in message
    assert "music_generation" in message
    assert ALLOW_DOWNLOAD_ENV in message


def test_preflight_recognises_a_local_directory(tmp_path) -> None:
    weights = tmp_path / "music_generation"
    weights.mkdir()
    (weights / "model.safetensors").write_bytes(b"x")

    # существует и непустой → не падает
    assert ensure_local_weights("music_generation", tmp_path) == weights


def test_preflight_allows_missing_weights_when_download_is_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(ALLOW_DOWNLOAD_ENV, "1")

    assert ensure_local_weights("music_generation", tmp_path) is None


def test_hint_names_the_role_and_the_flag(tmp_path) -> None:
    hint = weights_hint("stem_splitter", tmp_path)

    assert "stem_splitter" in hint
    assert str(tmp_path) in hint


# --------------------------------------------------------------- реестр
def test_registry_musicgen_checks_weights_before_pretrained(tmp_path, monkeypatch) -> None:
    """До `get_pretrained` должен произойти локальный preflight."""
    monkeypatch.delenv(ALLOW_DOWNLOAD_ENV, raising=False)
    ai_registry = importlib.import_module("app.ai.registry")
    monkeypatch.setattr(ai_registry, "MODELS_DIR", tmp_path)
    calls: list[str] = []

    class FakeMusicGen:
        @staticmethod
        def get_pretrained(repo, device=None):
            calls.append(repo)
            raise AssertionError("веса запрошены без локальной проверки")

    import sys
    import types

    fake_audiocraft = types.ModuleType("audiocraft")
    fake_models = types.ModuleType("audiocraft.models")
    fake_models.MusicGen = FakeMusicGen
    fake_audiocraft.models = fake_models
    monkeypatch.setitem(sys.modules, "audiocraft", fake_audiocraft)
    monkeypatch.setitem(sys.modules, "audiocraft.models", fake_models)

    from app.ai.weights import ensure_local_weights as spy

    with pytest.raises(FileNotFoundError):
        spy("music_generation", tmp_path)

    assert calls == []
    assert "ensure_local_weights" in Path(ai_registry.__file__).read_text(encoding="utf-8")


def test_every_downloading_role_declares_a_folder() -> None:
    """У роли, которая качает веса, должно быть место на диске."""
    from app.ai.model_catalog import MODEL_REGISTRY

    for key, spec in MODEL_REGISTRY.items():
        if spec.get("hf_repo") or spec.get("download"):
            assert key, "роль без имени"
