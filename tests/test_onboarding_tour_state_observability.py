"""Regression coverage for observable onboarding state recovery."""

from modules import onboarding_tour


def test_load_state_warns_and_uses_default_for_malformed_json(monkeypatch, tmp_path, caplog):
    state = tmp_path / "tutorial_settings.json"
    state.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(onboarding_tour, "TOUR_STATE", state)

    result = onboarding_tour.load_state()

    assert result == {"tour_done": False, "last_step": 0}
    assert "tour state unreadable; using default state" in caplog.text
