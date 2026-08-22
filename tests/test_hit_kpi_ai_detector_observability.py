"""Regression coverage for observable KPI AI-detector score coercion."""

from modules.hit_kpi_monitor_v11 import (
    check_ai_detector,
    check_ai_detector_with_diagnostics,
)


def test_ai_detector_reports_malformed_score_before_nested_valid_score():
    report = {"score": "not-a-number", "summary": {"percent": "0.42"}}

    result = check_ai_detector_with_diagnostics(report)

    assert result == {
        "score": 42.0,
        "diagnostics": [
            {"key": "score", "error": "ValueError: could not convert string to float: 'not-a-number'"}
        ],
    }
    assert check_ai_detector(report) == 42.0


def test_ai_detector_reports_malformed_value_without_fake_score():
    result = check_ai_detector_with_diagnostics({"ai_percent": None})

    assert result["score"] == -1.0
    assert result["diagnostics"] == [
        {"key": "ai_percent", "error": "TypeError: float() argument must be a string or a real number, not 'NoneType'"}
    ]
