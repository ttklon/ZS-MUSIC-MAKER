"""Policy tests are not end-to-end generation or a legal rights opinion."""
from __future__ import annotations

from pathlib import Path
import sys

from app.core.entrypoints import ENTRYPOINTS
from app.core.resource_policy import commercial_decision, resource_inventory

ROOT = Path(__file__).resolve().parents[1]


def test_entrypoint_registry_names_real_paths_and_only_one_primary():
    assert len({e['id'] for e in ENTRYPOINTS}) == len(ENTRYPOINTS)
    assert sum(e['policy'] == 'primary_development' for e in ENTRYPOINTS) == 1
    assert all((ROOT / e['path']).exists() for e in ENTRYPOINTS)
    assert all(e['id'] in (ROOT / 'docs/ENTRYPOINTS.md').read_text(encoding='utf-8') for e in ENTRYPOINTS)


def test_default_python_never_starts_legacy_ui_or_downloads(monkeypatch, capsys):
    import main
    from app.cli import gui
    from app.core import bootstrap

    def forbidden(*a, **kw):
        raise AssertionError('Unexpected GUI/download')
    monkeypatch.setattr(gui, 'try_launch_pyside', forbidden)
    monkeypatch.setattr(gui, 'try_launch_gradio', forbidden)
    monkeypatch.setattr(bootstrap, 'auto_bootstrap', forbidden)
    monkeypatch.setenv('ZSMM_ONLINE', '1')
    monkeypatch.setattr(sys, 'argv', ['main.py'])
    assert main.main() == 2
    assert 'releases/latest' in capsys.readouterr().out


def test_explicit_legacy_gui_is_labeled_not_silent_fallback(monkeypatch, capsys):
    import main
    from app.cli import gui
    monkeypatch.setattr(gui, 'try_launch_pyside', lambda: False)
    monkeypatch.setattr(sys, 'argv', ['main.py', '--desktop'])
    assert main.main() == 2
    assert 'LEGACY' in capsys.readouterr().out


def test_readonly_resource_cli_admits_incomplete_review(monkeypatch):
    import main
    monkeypatch.setattr(sys, 'argv', ['main.py', '--resource-policy'])
    assert main.main() == 1


def test_inventory_hashes_real_bank_but_does_not_infer_rights():
    report = resource_inventory()
    samples = [r for r in report['resources'] if r['kind'] == 'bundled_sample']
    assert len(samples) == 32
    assert all(r['integrity_matches'] and r['source'] and r['declared_license'] for r in samples)
    assert not report['coverage_complete']
    assert not commercial_decision(report['resources'])['allowed']
    assert all(not r['commercial_use_verified'] for r in report['resources'])


def test_unknown_nc_local_and_code_mit_are_not_blanket_commercial_permission():
    for record in [{'id': 'unknown'}, {'id': 'local', 'source': 'local'},
                   {'id': 'model', 'declared_license': 'CC-BY-NC'},
                   {'id': 'weights', 'code_license': 'MIT'}]:
        assert not commercial_decision([record])['allowed']
    assert not commercial_decision([])['allowed']


def test_resource_gate_requires_terms_source_and_integrity():
    record = {'id': 'fixture', 'source': 'https://example.test/terms', 'terms_sha256': '0' * 64,
              'terms_reviewed': True, 'commercial_use_verified': True, 'declared_license': 'CC0-1.0'}
    assert commercial_decision([record])['allowed']  # Contract fixture, not a reviewed production resource.
    assert not commercial_decision([{**record, 'integrity_matches': False}])['allowed']
    for license_name in ['CC-BY-NC-4.0', 'unknown', 'royalty-free']:
        assert not commercial_decision([{**record, 'declared_license': license_name}])['allowed']


def test_local_sample_filter_never_certifies_commercial_release():
    from agents.sample_hunter.license import _license_gate
    items = [{'source': 'local', 'license': 'unknown'}]
    passed = _license_gate(items)
    assert passed and passed[0]['commercial_use_verified'] is False
