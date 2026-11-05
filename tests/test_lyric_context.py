"""Reference summaries and user notes: mock LLMs, no ASR or live trend claims."""
from app.core.lyric_context import MAX_NOTES_CHARS, MAX_REFERENCE_CHARS, build_lyric_context
from app.core.recipe import build_recipe
from app.core.stages import lyrics


def test_reference_counts_are_bounded_and_only_summary_reaches_prompt():
    reference = "[Куплет]\nГород спит, горят огни\nГород смотрит на огни"
    report, prompt = build_lyric_context(reference, "мем про чай")
    assert report["lines"] == 2 and report["words"] == 8
    assert report["mean_words_per_line"] == 4.0
    assert report["keywords"][:2] == ["город", "огни"]
    assert report["reference_source"] == "user_supplied_text"
    assert report["trend_source"] == "user_notes_unverified"
    assert report["live_trend_research"] is False
    assert "Город спит, горят огни" not in prompt
    assert "мем про чай" in prompt
    bounded, bounded_prompt = build_lyric_context("слово " * MAX_REFERENCE_CHARS,
                                                  "x" * (MAX_NOTES_CHARS + 100))
    assert bounded["reference_truncated"] and bounded["trend_notes_truncated"]
    assert "x" * (MAX_NOTES_CHARS + 1) not in bounded_prompt


def test_router_receives_manual_context_and_stage_reports_provider(monkeypatch):
    from app.ai.registry import registry
    monkeypatch.setattr(registry, "is_available", lambda key: False)
    calls = {}
    class Router:
        def __init__(self, **kwargs): pass
        def complete(self, prompt, *args, **kwargs):
            calls["prompt"] = prompt
            return {"ok": True, "text": "[Куплет 1]\nМой оригинальный текст", "provider": "ollama"}
    monkeypatch.setattr(lyrics, "LLMRouter", Router)
    recipe = build_recipe({"reference_lyrics": "Небо красное горит\nНебо смотрит вниз",
                           "trend_notes": "чайная культура", "bilingual": False})
    recipe["style_vector"] = {"target_bpm": 96, "target_mode": "minor"}
    stage, _, _ = lyrics._run_lyrics_stage(recipe)
    context = stage.output["creative_context"]
    assert context["provided_to_generator"] is True and context["live_trend_research"] is False
    assert "чайная культура" in calls["prompt"] and "небо" in calls["prompt"]
    assert "Небо красное горит" not in calls["prompt"]
    assert "Билингвальный припев: нет" in calls["prompt"]
    assert "96 BPM" in calls["prompt"] and "Лад: minor" in calls["prompt"]


def test_local_model_receives_context_without_raw_reference(monkeypatch):
    from app.ai.registry import registry
    from modules.lyrics import ai
    monkeypatch.delenv("ZSMM_OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(registry, "is_available", lambda key: True)
    captured = {}
    def generate(theme, **kwargs):
        captured.update(kwargs)
        return {"ok": True, "lyrics": "[Куплет 1]\nСвой текст"}
    monkeypatch.setattr(ai, "generate_lyrics_ai", generate)
    stage, _, _ = lyrics._run_lyrics_stage(build_recipe({
        "reference_lyrics": "Ветер качает листву", "trend_notes": "осень"}))
    assert stage.output["creative_context"]["provided_to_generator"]
    assert "осень" in captured["creative_context"]
    assert "Ветер качает листву" not in captured["creative_context"]


def test_template_and_user_lyrics_do_not_claim_context_generated(monkeypatch):
    from app.ai.registry import registry
    monkeypatch.setattr(registry, "is_available", lambda key: False)
    class Router:
        def __init__(self, **kwargs): pass
        def complete(self, *args, **kwargs):
            return {"ok": True, "text": "template", "provider": "local_template", "fallback_used": True}
    monkeypatch.setattr(lyrics, "LLMRouter", Router)
    recipe = build_recipe({"trend_notes": "осень"})
    stage, _, _ = lyrics._run_lyrics_stage(recipe)
    assert stage.status.value == "FALLBACK" and not stage.output["creative_context"]["provided_to_generator"]
    recipe["user_lyrics_lines"] = ["Моя строка"]
    stage, _, text = lyrics._run_lyrics_stage(recipe)
    assert text == "Моя строка" and stage.output["provider"] == "user_lyrics"
    assert not stage.output["creative_context"]["provided_to_generator"]
