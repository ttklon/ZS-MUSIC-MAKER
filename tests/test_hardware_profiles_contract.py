"""Measurement is not support certification or model inference."""
from app.ai.profiles import measure_profile, preflight_resources


def test_real_measurement_does_not_advertise_unproven_profiles(tmp_path):
    report = measure_profile(tmp_path)
    assert report['kind'] == 'inventory_only'
    assert report['measurements']['disk_free_gib'] is not None
    assert not report['inference_verified'] and not report['product_profile_accepted']
    assert all(p['status'] == 'unverified' for p in report['profiles'])
    assert report['measurements']['gpu'] == 'not_measured'


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
