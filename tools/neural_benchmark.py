"""Small measurement helpers. Python socket blocking is not an OS network sandbox."""
from contextlib import contextmanager
import hashlib
import socket
import threading
import time
from unittest.mock import patch


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def block_python_network():
    attempts = []

    def deny(*args, **kwargs):
        attempts.append(repr(args[:2]))
        raise RuntimeError('Offline benchmark forbids Python socket networking')

    with patch.object(socket.socket, 'connect', deny), patch.object(socket.socket, 'connect_ex', deny), \
            patch.object(socket, 'create_connection', deny), patch.object(socket, 'getaddrinfo', deny), \
            patch.object(socket.socket, 'sendto', deny):
        yield attempts
    if attempts:
        raise RuntimeError(f'Offline inference attempted networking: {attempts}')


@contextmanager
def measure_render(metrics):
    import psutil
    process = psutil.Process()
    baseline = process.memory_info().rss
    samples = [baseline]
    done = threading.Event()

    def sample():
        while not done.wait(0.02):
            samples.append(process.memory_info().rss)

    worker = threading.Thread(target=sample, daemon=True)
    worker.start()
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        done.set()
        worker.join()
        samples.append(process.memory_info().rss)
        metrics.update(wall_seconds=elapsed, rss_baseline_bytes=baseline,
                       rss_peak_sampled_bytes=max(samples), rss_sample_interval_seconds=0.02,
                       rss_sample_count=len(samples))
