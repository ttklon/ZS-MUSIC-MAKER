from __future__ import annotations

import json
from pathlib import Path

import modules.phoneme_coverage as coverage


def test_compute_coverage_preserves_valid_transcripts_and_reports_malformed_json(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "voice_vault"
    vault.mkdir()
    (vault / "valid.txt").write_text("абв test", encoding="utf-8")
    (vault / "broken.json").write_text("{not json", encoding="utf-8")
    report_path = vault / "phoneme_coverage.json"
    monkeypatch.setattr(coverage, "VAULT_DIR", vault)
    monkeypatch.setattr(coverage, "COVERAGE_FILE", report_path)

    report = coverage.compute_coverage()

    assert report["transcript_count"] == 1
    assert len(report["transcript_read_errors"]) == 1
    assert report["transcript_read_errors"][0].startswith("broken.json: JSONDecodeError:")
    persisted = json.loads(report_path.read_text(encoding="utf-8"))
    assert persisted["transcript_read_errors"] == report["transcript_read_errors"]
