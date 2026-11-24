"""Measurement is not support certification or model inference."""
from app.ai.profiles import measure_profile, preflight_resources


def test_real_measurement_does_not_advertise_unproven_profiles(tmp_path):
    report = measure_profile(tmp_path)
    assert report['kind'] == 'inventory_only'
    assert report['measurements']['disk_free_gib'] is not None
    assert type(report['measurements']['ram_available_bytes']) is int
    assert type(report['measurements']['disk_free_bytes']) is int
    assert not report['inference_verified'] and not report['product_profile_accepted']
    assert all(p['status'] == 'unverified' for p in report['profiles'])
    assert report['measurements']['gpu']['inference_verified'] is False
    assert 'pytorch_device' in report['measurements']['gpu']


def test_unavailable_disk_is_reported_not_assumed(tmp_path):
    report = measure_profile(tmp_path / 'missing')
    assert report['measurements']['disk_free_gib'] is None
    assert report['errors']


def test_preflight_requires_explicit_budget_and_available_measurements():
    profile = {'measurements': {'ram_available_gib': 8, 'disk_free_gib': 40}}
    assert not preflight_resources(profile)['allowed']
    assert preflight_resources(profile, ram_gib=4, disk_gib=10)['allowed']
    assert not preflight_resources(profile, ram_gib=16, disk_gib=10)['allowed']
    assert not preflight_resources({}, ram_gib=1, disk_gib=1)['allowed']
    for invalid in [float('nan'), float('inf'), -1, True, '4']:
        assert not preflight_resources(profile, ram_gib=invalid, disk_gib=1)['allowed']


def test_malformed_inventory_never_becomes_enough_resources():
    for invalid in (None, [], 'ready', {'measurements': None}, {'measurements': []}):
        assert not preflight_resources(invalid, ram_gib=1, disk_gib=1)['allowed']


def test_installed_amd_does_not_certify_inference(tmp_path, monkeypatch):
    monkeypatch.setattr('app.ai.hardware.detect_system', lambda _: {
        'gpus': [{'name': 'AMD test fixture', 'source': 'mock'}],
        'pytorch_device': None, 'directml_devices': [{'name': 'AMD test fixture'}],
        'cpu_threads': 4, 'ram_total_gib': 16, 'ram_available_gib': 8, 'disk_free_gib': 20})
    report = measure_profile(tmp_path)
    assert report['measurements']['gpu']['adapters'][0]['source'] == 'mock'
    assert report['measurements']['gpu']['pytorch_device'] is None
    assert not report['product_profile_accepted']
    assert all(p['status'] == 'unverified' for p in report['profiles'])


def test_detection_failure_preserves_fail_closed_inventory(tmp_path, monkeypatch):
    def fail(_):
        raise RuntimeError('simulated detection failure')
    monkeypatch.setattr('app.ai.hardware.detect_system', fail)
    report = measure_profile(tmp_path)
    assert report['errors'] and not report['inference_verified']
    assert not preflight_resources(report, ram_gib=1, disk_gib=1)['allowed']
