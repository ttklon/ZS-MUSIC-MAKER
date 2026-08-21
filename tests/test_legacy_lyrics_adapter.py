from __future__ import annotations

import importlib
import sys
import warnings

from app.core import orchestrator_v8_patch


def test_lyrics_gen_v8_import_emits_deprecation_warning() -> None:
    sys.modules.pop("modules.lyrics_gen_v8", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.import_module("modules.lyrics_gen_v8")

    assert any(
        item.category is DeprecationWarning and "lyrics_gen_v8 is deprecated" in str(item.message)
        for item in caught
    )


def test_ai_lyrics_adapter_returns_none_when_role_is_unavailable(monkeypatch) -> None:
    from app.ai.registry import registry

    monkeypatch.setattr(registry, "is_available", lambda role: False)
    assert orchestrator_v8_patch._generate_ai_lyrics({"theme": "night"}) is None


def test_ai_lyrics_adapter_converts_current_output_to_legacy_shape(monkeypatch) -> None:
    from app.ai.registry import registry
    from modules import lyrics_gen_ai

    monkeypatch.setattr(registry, "is_available", lambda role: role == "lyrics_llm")
    monkeypatch.setattr(
        lyrics_gen_ai,
        "generate_lyrics_ai",
        lambda **kwargs: {
            "ok": True,
            "lyrics": "[Куплет 1]\nгород не спит\n[Припев]\nnight ride",
            "source": "lyrics_llm",
        },
    )

    result = orchestrator_v8_patch._generate_ai_lyrics(
        {"theme": "night", "bpm": 128, "genre": "phonk", "lang_mix": "ru+en"}
    )

    assert result is not None
    assert result["source"] == "lyrics_gen_ai"
    assert result["chorus_lines"] == ["night ride"]
    assert result["used_slang"] == []


def test_v8_pipeline_prefers_ai_adapter_payload_without_importing_legacy(monkeypatch) -> None:
    class DummyOrchestrator:
        def __init__(self) -> None:
            self.events: list[str] = []

        def log(self, message: str) -> None:
            self.events.append(message)

        def _run_pipeline_v7(self, recipe, stage_hook=None):
            return {"ok": True}

    monkeypatch.setattr(
        orchestrator_v8_patch,
        "_generate_ai_lyrics",
        lambda recipe: {
            "text": "[Припев]\nAI hook",
            "chorus_lines": ["AI hook"],
            "used_slang": [],
            "author_style_used": False,
            "source": "lyrics_gen_ai",
        },
    )
    orch = DummyOrchestrator()
    recipe: dict[str, object] = {}

    result = orchestrator_v8_patch.run_pipeline_v8(orch, recipe)

    assert result == {"ok": True}
    assert recipe["lyrics_source"] == "lyrics_gen_ai"
    assert recipe["lyrics_text"] == "[Припев]\nAI hook"
    assert any("source=lyrics_gen_ai" in message for message in orch.events)
