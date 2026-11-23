"""Safety contracts using doubles; these are NOT CPU/GPU inference evidence."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.local_model_benchmark import benchmark, select_device, verify_package, check_tensor_device
from tools.neural_benchmark import sha256


def torch_fixture(*, available=False, hip=None):
    return SimpleNamespace(version=SimpleNamespace(hip=hip),
                           cuda=SimpleNamespace(is_available=lambda: available))


@pytest.mark.parametrize('backend', ['cuda', 'rocm'])
def test_gpu_backend_never_falls_back_to_cpu(backend):
    with pytest.raises(RuntimeError, match='fallback forbidden'):
        select_device(torch_fixture(), backend)


def test_rocm_is_not_nvidia_and_directml_is_not_cuda():
    assert select_device(torch_fixture(available=True), 'cuda') == 'cuda:0'
    assert select_device(torch_fixture(available=True, hip='6.2'), 'rocm') == 'cuda:0'
    for torch, backend in [(torch_fixture(available=True), 'rocm'),
                           (torch_fixture(available=True, hip='6.2'), 'cuda')]:
        with pytest.raises(RuntimeError):
            select_device(torch, backend)
    with pytest.raises(ValueError):
        select_device(torch_fixture(), 'directml')
    assert select_device(torch_fixture(available=True, hip='6.2'), 'cpu') == 'cpu'


def test_package_hash_required_before_executable_load(tmp_path):
    package = tmp_path / 'fixture.pt'
    package.write_bytes(b'test fixture, never executed')
    verify_package(package, sha256(package))
    for digest in (None, True, '', 'f' * 64, 'A' * 64):
        with pytest.raises(ValueError):
            verify_package(package, digest)
    with pytest.raises(ValueError):
        verify_package(tmp_path / 'missing', sha256(package))


@pytest.mark.parametrize('actual,index,requested', [('cpu', None, 'cuda:0'),
    ('cuda', 1, 'cuda:0'), ('cuda', 0, 'cpu')])
def test_output_on_wrong_device_cannot_certify_backend(actual, index, requested):
    tensor = SimpleNamespace(device=SimpleNamespace(type=actual, index=index))
    with pytest.raises(RuntimeError, match='no backend acceptance'):
        check_tensor_device(tensor, requested)


def test_hash_failure_writes_failed_report_and_preserves_previous_audio(tmp_path):
    previous = tmp_path / 'speech.wav'
    previous.write_bytes(b'previous result')
    report = benchmark('cuda', Path('missing'), '0' * 64, tmp_path)
    assert report['ok'] is False and report['inference_verified'] is False
    assert report['product_profile_accepted'] is False
    assert 'SHA-256 mismatch' in report['error']
    assert previous.read_bytes() == b'previous result'
    assert json.loads((tmp_path / 'report.json').read_text(encoding='utf-8'))['ok'] is False


def test_unavailable_backend_rejected_before_model_load(tmp_path, monkeypatch):
    import sys
    import tools.local_model_benchmark as tool
    package = tmp_path / 'fixture.pt'
    package.write_bytes(b'test only, must never execute')
    monkeypatch.setitem(sys.modules, 'torch', torch_fixture())
    monkeypatch.setattr(tool, 'render_on_backend', lambda *a: pytest.fail('must not execute model'))
    report = benchmark('cuda', package, sha256(package), tmp_path / 'run')
    assert report['ok'] is False and report['inference_verified'] is False
    assert 'CPU fallback forbidden' in report['error']
