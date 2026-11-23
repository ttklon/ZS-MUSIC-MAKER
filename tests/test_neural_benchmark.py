"""Guard and measurement contracts; these tests do not run model inference."""
import socket
import time
import pytest
from tools.neural_benchmark import block_python_network, measure_render, sha256


def test_network_guard_restores_socket_after_exception():
    original = socket.socket.connect
    with pytest.raises(RuntimeError, match='forbids'):
        with block_python_network():
            socket.create_connection(('example.invalid', 443))
    assert socket.socket.connect is original


def test_swallowed_network_attempt_still_fails():
    with pytest.raises(RuntimeError, match='attempted networking'):
        with block_python_network():
            try:
                socket.getaddrinfo('example.invalid', 80)
            except RuntimeError:
                pass


def test_metrics_and_hash(tmp_path):
    metrics = {}
    with measure_render(metrics):
        time.sleep(0.03)
    assert metrics['wall_seconds'] >= 0.03
    assert metrics['rss_peak_sampled_bytes'] >= metrics['rss_baseline_bytes'] > 0
    assert metrics['rss_sample_count'] >= 2
    file = tmp_path / 'bytes'
    file.write_bytes(b'abc')
    assert sha256(file) == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
