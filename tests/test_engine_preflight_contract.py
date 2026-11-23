"""Real subprocess/venv protocol, catalogue and preflight; no heavy model inference."""
import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai.engine_profiles import PROFILES, environment_plan, profile
from app.ai.worker_client import probe_worker
from app.core.download_budget import RESERVE_BYTES, space_plan
from app.core.net_policy import network_allowed
from app.ai.weights import download_allowed, ensure_local_weights
from tools import pull_ai_models as puller
from tools.export_model_catalog import ROOT, catalog


def test_profiles_are_fingerprinted_isolated_and_not_claimed_as_locks(tmp_path):
    for name in PROFILES:
        plan = environment_plan(name, tmp_path)
        assert Path(plan['directory']).is_relative_to(tmp_path)
        assert plan['lock_verified'] is False and plan['windows_install_verified'] is False
        assert plan['inference_verified'] is False and len(plan['input_sha256']) == 64
    assert profile('torch')['input_sha256'] != profile('audiocraft')['input_sha256']
    assert 'torch==2.1.0' in profile('audiocraft')['direct_inputs']
    assert 'numpy==1.23.5' in profile('rvc')['direct_inputs']
    with pytest.raises(ValueError):
        environment_plan('../escape', tmp_path)


def test_shared_install_is_blocked_before_subprocess(monkeypatch):
    from app.core.bootstrap import _pip_install
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: pytest.fail('shared pip must not run'))
    assert _pip_install('torch==2.5.1') is False
    assert _pip_install('audiocraft==1.3.0') is False
    assert _pip_install('anything==1') is False


def test_real_worker_probe_and_separate_clean_venv(tmp_path):
    assert probe_worker(Path(sys.executable), 'core')['ok'] is True
    directory = tmp_path / 'worker env'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(directory)], check=True, timeout=60)
    python = directory / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    result = probe_worker(python, 'audiocraft')
    assert result['ok'] and result['isolated'] and result['venv']
    assert result['artifacts'] == [] and result['inference_verified'] is False


@pytest.mark.parametrize('kind', ['version', 'fingerprint', 'nonce', 'extra', 'exit', 'timeout', 'artifacts'])
def test_worker_rejects_malformed_or_foreign_response(monkeypatch, kind):
    import app.ai.worker_client as client
    def response(command, **kw):
        if kind == 'timeout':
            raise subprocess.TimeoutExpired(command, 1)
        request = json.loads(kw['input'])
        hello = dict(schema='zsmm.worker', version=1, type='hello', profile='core',
                     fingerprint=profile('core')['input_sha256'])
        result = dict(hello, type='result', nonce=request['nonce'], ok=True, isolated=True,
                      python_version=[3, 11], artifacts=[], inference_verified=False)
        if kind == 'version': result['version'] = 2
        if kind == 'fingerprint': result['fingerprint'] = '0' * 64
        if kind == 'nonce': result['nonce'] = 'wrong'
        if kind == 'artifacts': result['artifacts'] = ['../secret.wav']
        rows = [hello, result, result] if kind == 'extra' else [hello, result]
        return SimpleNamespace(returncode=1 if kind == 'exit' else 0,
                               stdout='\n'.join(map(json.dumps, rows)))
    monkeypatch.setattr(client.subprocess, 'run', response)
    assert client.probe_worker(Path(sys.executable), 'core')['ok'] is False


def test_catalogue_is_exact_projection_with_explicit_unknowns():
    actual = json.loads((ROOT / 'data/desktop/model-catalog.json').read_text(encoding='utf-8'))
    assert actual == catalog()
    from app.ai.registry import MODEL_REGISTRY
    assert {r['id'] for r in actual['roles']} == set(MODEL_REGISTRY)
    assert all(r['inference_verified'] is False and r['terms_reviewed'] is False for r in actual['roles'])
    assert any(r['revision'] is None and r.get('expected_size_bytes') is None for r in actual['roles'])


@pytest.mark.parametrize('online', [False, True])
def test_explicit_off_overrides_stale_settings_explicit_call_and_weight_flag(tmp_path, monkeypatch, online):
    settings = tmp_path / 'settings.json'
    settings.write_text('{"network":{"online":true}}')
    monkeypatch.setenv('ZSMM_ONLINE', '0'); monkeypatch.setenv('ZSMM_ALLOW_MODEL_DOWNLOAD', '1')
    assert network_allowed(allow_online=online, settings_path=settings) is False
    assert download_allowed() is False


@pytest.mark.parametrize('flag', ['true', 'yes', 'on', '0', ''])
def test_weight_optin_is_literal_and_requires_network(monkeypatch, flag):
    monkeypatch.setenv('ZSMM_ONLINE', '1'); monkeypatch.setenv('ZSMM_ALLOW_MODEL_DOWNLOAD', flag)
    assert not download_allowed()


def test_metadata_alone_is_not_local_weights(tmp_path, monkeypatch):
    monkeypatch.setenv('ZSMM_ONLINE', '0')
    role = tmp_path / 'asr'; role.mkdir(); (role / 'config.json').write_text('{}')
    with pytest.raises(FileNotFoundError):
        ensure_local_weights('asr', tmp_path)


def test_space_plan_counts_cache_temp_and_reserve_on_same_volume(tmp_path, monkeypatch):
    monkeypatch.setattr('app.core.download_budget.shutil.disk_usage', lambda p: SimpleNamespace(free=1000))
    plan = space_plan(100, tmp_path / 'weights', tmp_path / 'cache', tmp_path / 'temp')
    assert not plan['allowed']
    assert len(plan['volumes']) == 1
    assert plan['volumes'][0]['required_bytes'] == RESERVE_BYTES + 300
    monkeypatch.setattr('app.core.download_budget.shutil.disk_usage', lambda p: SimpleNamespace(free=RESERVE_BYTES + 300))
    assert space_plan(100, tmp_path, tmp_path, tmp_path)['allowed']
    assert not space_plan(None, tmp_path)['allowed']


@pytest.mark.parametrize('reason', ['offline', 'space', 'unknown'])
def test_no_network_client_or_write_before_preflight(tmp_path, monkeypatch, reason):
    monkeypatch.setattr(puller, 'AI_MODELS_DIR', tmp_path)
    monkeypatch.setenv('ZSMM_ONLINE', '0' if reason == 'offline' else '1')
    import app.core.download_budget as budget
    monkeypatch.setattr(budget.shutil, 'disk_usage', lambda p: SimpleNamespace(free=0))
    # No HuggingFace import/network call is possible if the helper is never reached.
    monkeypatch.setitem(sys.modules, 'huggingface_hub', SimpleNamespace(
        hf_hub_download=lambda **kw: pytest.fail('network before preflight'),
        snapshot_download=lambda **kw: pytest.fail('network before preflight')))
    role = 'music_generation' if reason == 'unknown' else 'lyrics_llm'
    assert puller.pull(role, allow_online=True) is False
    assert list(tmp_path.iterdir()) == []


def test_manifest_cannot_verify_files_outside_role_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(puller, 'AI_MODELS_DIR', tmp_path)
    (tmp_path / 'outside.gguf').write_bytes(b'secret')
    folder = tmp_path / 'lyrics_llm'; folder.mkdir()
    (folder / 'manifest.json').write_text(json.dumps(dict(files=[dict(path='../outside.gguf', bytes=6, sha256='0'*64)])))
    assert puller.verify('lyrics_llm') is False


def test_implicit_loader_cannot_bypass_unknown_size_guard(tmp_path, monkeypatch):
    monkeypatch.setenv('ZSMM_ONLINE', '1'); monkeypatch.setenv('ZSMM_ALLOW_MODEL_DOWNLOAD', '1')
    with pytest.raises(FileNotFoundError, match='Unknown download size'):
        ensure_local_weights('music_generation', tmp_path)


def test_disk_inspection_failure_blocks_before_transfer(tmp_path, monkeypatch):
    def fail(path):
        raise OSError('fixture inaccessible volume')
    monkeypatch.setattr('app.core.download_budget.shutil.disk_usage', fail)
    result = space_plan(100, tmp_path)
    assert not result['allowed'] and 'Cannot inspect disk' in result['reason']


def test_real_volume_preflight_does_not_create_destination(tmp_path):
    target = tmp_path / 'not-created'
    result = space_plan(1, target, tmp_path / 'cache', tmp_path / 'temp')
    assert result['volumes']
    assert not target.exists()
    assert result['reservation'] is False
