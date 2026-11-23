# -*- coding: utf-8 -*-
"""Агентик-проводник: 4 вопроса → план → прогон → честный отчёт.

Проверяется то, что обещает интерфейс: ответы доходят до плана, жанр
выбирается автономно, а отсутствие LLM/голоса даёт `BLOCKED` с действием,
а не тихую подстановку.
"""

from __future__ import annotations

import pytest

from modules.agent_guide import (
    QUESTIONS,
    answer_summary,
    build_plan,
    narrate,
    parse_answers,
    run_conversation_hit,
    verdict,
)


def test_four_questions_are_the_contract_with_the_window() -> None:
    """Окно рисует ровно эти четыре вопроса — ключи менять нельзя."""
    assert [question["id"] for question in QUESTIONS] == ["mood", "artist", "refs", "voice"]
    for question in QUESTIONS:
        assert question["label"] and question["placeholder"] and question["hint"]


def test_empty_answers_mean_trends_not_constants() -> None:
    answers = parse_answers({})
    assert answers == {
        "mood": "",
        "artist": "",
        "refs": [],
        "voice": {"mode": "none", "path": ""},
    }


def test_refs_accept_string_list_and_semicolons() -> None:
    from_string = parse_answers({"refs": "a.wav, b.wav; c.wav"})
    from_list = parse_answers({"refs": ["a.wav", " b.wav "]})
    assert from_string["refs"] == ["a.wav", "b.wav", "c.wav"]
    assert from_list["refs"] == ["a.wav", "b.wav"]


def test_refs_are_capped_at_seven() -> None:
    answers = parse_answers({"refs": ",".join(f"{index}.wav" for index in range(20))})
    assert len(answers["refs"]) == 7


def test_voice_question_maps_to_three_modes() -> None:
    assert parse_answers({"voice": "record"})["voice"]["mode"] == "record"
    assert parse_answers({"voice": "C:/take.wav"})["voice"] == {
        "mode": "file", "path": "C:/take.wav",
    }
    assert parse_answers({"voice": ""})["voice"]["mode"] == "none"


def test_long_mood_is_trimmed_not_rejected() -> None:
    answers = parse_answers({"mood": "  ночь\n\n город " + "x" * 500})
    assert "\n" not in answers["mood"]
    assert len(answers["mood"]) == 300


def test_answer_summary_names_voice_source() -> None:
    summary = answer_summary(parse_answers({"voice": "record"}))
    assert "микрофон → RVC" in summary


def test_plan_takes_genre_from_references_first() -> None:
    plan = build_plan(
        parse_answers({"mood": "ночь"}),
        trend={"hype_words": ["phonk"]},
        style={"consensus": {"genre_hint": "trap / hip-hop", "bpm": 132}},
    )
    assert plan["genre"] == "trap"
    assert plan["bpm_override"] == 132
    assert plan["theme"] == "ночь"


def test_plan_falls_back_to_trends_then_default() -> None:
    from_trend = build_plan(parse_answers({}), trend={"hype_words": ["drift"]})
    assert from_trend["genre"] == "drift"
    default = build_plan(parse_answers({}), trend={}, style={})
    assert default["genre"] == "drift_phonk"
    assert default["theme"]


def test_plan_marks_rvc_only_for_a_real_file() -> None:
    record = build_plan(parse_answers({"voice": "record"}))
    file_plan = build_plan(parse_answers({"voice": "C:/take.wav"}))
    assert record["use_rvc"] is False and record["own_vocal_wav"] == ""
    assert file_plan["use_rvc"] is True and file_plan["own_vocal_wav"] == "C:/take.wav"


def _allow_unverified_preflight(monkeypatch, runner):
    adaptive = {"level": 0, "use_acestep": False, "use_musicgen": False,
                "use_texture": False, "gpu": {}}
    record = {"schema": 1, "status": "inventory_only", "decision": "continue_unverified",
              "can_attempt": True, "selected_backend": "procedural_dsp",
              "resource_budget_status": "not_established",
              "texture_route": {"selected_backend": "disabled", "inference_verified": False},
              "reasons": [], "inference_verified": False, "product_profile_accepted": False}
    monkeypatch.setattr(runner, "_hardware_preflight", lambda recipe, root: (record, adaptive))
    return adaptive


def test_run_reports_blocked_lyrics_and_voice_without_engines(monkeypatch, tmp_path) -> None:
    """Без LLM и без записи трек собирается, но честно говорит, чего нет."""
    from modules.agent_guide import runner

    _allow_unverified_preflight(monkeypatch, runner)
    monkeypatch.setattr(runner, "_trend", lambda _theme: {"ok": True, "hype_words": []})
    monkeypatch.setattr(runner, "_references", lambda _paths: {"ok": False, "reason": "не заданы"})
    monkeypatch.setattr(runner, "_dossier", lambda _artist: {"ok": False, "reason": "нет"})
    monkeypatch.setattr(runner, "_samples", lambda _genre: {"ok": False, "reason": "нет"})
    monkeypatch.setattr(runner, "_lyrics", lambda *_a: {
        "ok": False, "source": "BLOCKED", "text": "", "reason": "Ollama не запущена",
    })
    monkeypatch.setattr(runner, "_run_pipeline", lambda *_a: {
        "master_path": str(tmp_path / "master.wav"), "hit_score": 61.0, "verdict": "solid",
        "out_root": str(tmp_path),
    })

    report = run_conversation_hit({"mood": "ночь"}, output_root=str(tmp_path))

    assert report["ok"] is False
    assert report["master_reported"] is True
    assert report["artifact_available"] is False
    assert not report["result"]["succeeded"]
    blocked = {item["stage"] for item in report["blocked"]}
    assert {"lyrics", "voice", "references", "samples"} <= blocked
    assert verdict(report) == "FAILED", "несуществующий файл мастера не является результатом"
    text = narrate(report)
    assert "Ollama" in text and "RVC" in text


def test_run_is_failed_when_pipeline_gives_no_master(monkeypatch, tmp_path) -> None:
    from modules.agent_guide import runner

    _allow_unverified_preflight(monkeypatch, runner)
    monkeypatch.setattr(runner, "_lyrics", lambda *_a: {"ok": False, "reason": "нет"})
    monkeypatch.setattr(runner, "_run_pipeline", lambda *_a: {"error": "движок упал"})

    report = run_conversation_hit({}, output_root=str(tmp_path))

    assert report["ok"] is False
    assert verdict(report) == "FAILED"
    assert "не собрался" in narrate(report)


def test_preflight_refusal_stops_every_generation_stage(monkeypatch, tmp_path):
    from modules.agent_guide import runner

    record = {"schema": 1, "status": "blocked", "decision": "refuse", "can_attempt": False,
              "reasons": ["missing measured disk space"], "inference_verified": False,
              "product_profile_accepted": False}
    monkeypatch.setattr(runner, "_hardware_preflight", lambda *_a: (record, {}))
    for name in ("_trend", "_references", "_dossier", "_samples", "_lyrics", "_voice", "_run_pipeline"):
        monkeypatch.setattr(runner, name, lambda *_a, _name=name, **_kw: pytest.fail(f"{_name} must not run"))
    output_root = tmp_path / "not-created"
    report = run_conversation_hit({"mood": "ночь"}, output_root=str(output_root))

    assert report["master_path"] is None and report["ok"] is False
    assert report["hardware_preflight"]["decision"] == "refuse"
    assert report["blocked"][0]["stage"] == "hardware_preflight"
    assert "missing measured disk space" in report["blocked"][0]["reason"]
    assert not output_root.exists()


def test_malformed_preflight_record_is_visible_refusal(monkeypatch, tmp_path):
    from modules.agent_guide import runner

    monkeypatch.setattr(runner, "_hardware_preflight", lambda *_a: None)
    monkeypatch.setattr(runner, "_trend", lambda *_a: pytest.fail("no stages before a valid preflight"))
    report = run_conversation_hit({}, output_root=str(tmp_path / "not-created"))

    assert report["hardware_preflight"]["decision"] == "refuse"
    assert any("hardware preflight failed" in reason
               for reason in report["hardware_preflight"]["reasons"])


def test_agent_passes_preflight_route_to_pipeline(monkeypatch, tmp_path):
    from modules.agent_guide import runner

    adaptive = _allow_unverified_preflight(monkeypatch, runner)
    events = []
    monkeypatch.setattr(runner, "_trend", lambda _theme: events.append("trend") or {"ok": True})
    monkeypatch.setattr(runner, "_references", lambda _paths: {"ok": False})
    monkeypatch.setattr(runner, "_dossier", lambda _artist: {"ok": False})
    monkeypatch.setattr(runner, "_samples", lambda _genre: {"ok": False})
    monkeypatch.setattr(runner, "_lyrics", lambda *_a: {"ok": False, "reason": "no LLM"})
    monkeypatch.setattr(runner, "_run_pipeline", lambda _plan, _root, _progress, cfg:
                        events.append("pipeline") or (pytest.fail("route changed") if cfg is not adaptive else {
                            "master_path": None, "error": "test only"}))

    report = run_conversation_hit({}, output_root=str(tmp_path))

    assert events == ["trend", "pipeline"]
    assert report["hardware_preflight"]["decision"] == "continue_unverified"
    assert report["ok"] is False


def test_verdict_hit_requires_master_lyrics_and_voice(monkeypatch, tmp_path) -> None:
    from modules.agent_guide import runner

    _allow_unverified_preflight(monkeypatch, runner)
    monkeypatch.setattr(runner, "_lyrics", lambda *_a: {"ok": True, "text": "текст", "source": "ollama"})
    monkeypatch.setattr(runner, "_voice", lambda *_a: {"ok": True, "source": "rvc", "path": "v.wav"})
    monkeypatch.setattr(runner, "_samples", lambda _genre: {"ok": True, "count": 1})
    monkeypatch.setattr(runner, "_references", lambda _paths: {"ok": True})
    monkeypatch.setattr(runner, "_trend", lambda _theme: {"ok": True})
    monkeypatch.setattr(runner, "_run_pipeline", lambda *_a: {
        "master_path": str(tmp_path / "m.wav"), "hit_score": 80.0, "out_root": str(tmp_path),
    })

    progress = []
    report = run_conversation_hit({"voice": "C:/take.wav"}, output_root=str(tmp_path), progress=progress.append)

    assert report["blocked"] == []
    assert report["ok"] is False
    assert not any(line.startswith("Готово") for line in progress)
    assert verdict(report) == "FAILED", "одних флагов текста/RVC и пути недостаточно"
    assert report["plan"]["reference_lyrics"] == "текст"


@pytest.mark.parametrize("stage", ["trend_scout", "sample_hunter"])
def test_agents_failure_does_not_raise(stage, monkeypatch) -> None:
    """Агенты бесплатные и необязательные: их отказ — строка в отчёте."""
    from app.core import agent_wiring

    if stage == "trend_scout":
        monkeypatch.setattr(agent_wiring, "trend_context", lambda *_a, **_k: {"ok": False, "reason": "нет сети"})
        result = agent_wiring.prepare_run_context({"theme": "ночь", "genre": "trap"})
        assert "trends" in result["blocked"]
    else:
        monkeypatch.setattr(agent_wiring, "sample_context", lambda *_a, **_k: {"ok": False, "reason": "пусто"})
        result = agent_wiring.prepare_run_context({"theme": "ночь", "genre": "trap"})
        assert "samples" in result["blocked"]
