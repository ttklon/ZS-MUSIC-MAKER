"""Regression coverage for observable KPI Dashboard persistence fallback."""

from modules import kpi_dashboard as dashboard
from modules.kpi_dashboard import report as dashboard_report


def test_dashboard_reports_saved_report_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(dashboard_report, "ROOT", tmp_path)

    result = dashboard.build(save=True)

    assert result.persistence["requested"] is True
    assert result.persistence["ok"] is True
    assert result.persistence["status"] == "saved"
    assert (tmp_path / "data" / "kpi_dashboard.json").exists()
    assert (tmp_path / "docs" / "KPI_DASHBOARD_v12.md").exists()


def test_dashboard_reports_failed_report_write(monkeypatch, tmp_path):
    monkeypatch.setattr(dashboard_report, "ROOT", tmp_path)
    import pathlib

    original_write_text = pathlib.Path.write_text

    def fail_markdown(self, text, *args, **kwargs):
        if self.name == "KPI_DASHBOARD_v12.md":
            raise OSError("disk full")
        return original_write_text(self, text, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "write_text", fail_markdown)

    result = dashboard.build(save=True)

    assert result.persistence == {
        "requested": True,
        "ok": False,
        "status": "failed",
        "error": "OSError: disk full",
    }
    assert not (tmp_path / "data" / "kpi_dashboard.json").exists()
