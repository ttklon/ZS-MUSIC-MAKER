"""Strict offline Silero backend measurement; draft speech, never singing certification.

Executable model packages must be independently trusted. A supplied SHA checks
identity, not provenance or safety. No downloads and no automatic CPU fallback.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import sys
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.neural_benchmark import block_python_network, measure_render, sha256

TEXT = "Это проверка настоящей голосовой модели на явно выбранном устройстве без скачивания весов."


def select_device(torch, backend):
    if backend == 'cpu':
        return 'cpu'
    if backend not in ('cuda', 'rocm'):
        raise ValueError('Only cpu, cuda or rocm are supported; DirectML is not CUDA')
    hip = bool(getattr(torch.version, 'hip', None))
    if not torch.cuda.is_available() or hip != (backend == 'rocm'):
        raise RuntimeError(f'Requested {backend} backend unavailable; CPU fallback forbidden')
    return 'cuda:0'  # PyTorch exposes ROCm through the cuda API.


def verify_package(path, expected_hash):
    if not isinstance(expected_hash, str) or not re.fullmatch('[0-9a-f]{64}', expected_hash):
        raise ValueError('Expected lowercase SHA-256 of independently trusted executable package')
    if not path.is_file() or sha256(path) != expected_hash:
        raise ValueError('Model package missing or SHA-256 mismatch; refusing executable load')


def check_tensor_device(tensor, device):
    actual = tensor.device
    expected_type = device.split(':')[0]
    if actual.type != expected_type or (expected_type == 'cuda' and actual.index != 0):
        raise RuntimeError(f'Model output on {actual}, requested {device}; no backend acceptance')


def render_on_backend(torch, device, metrics, model_path, target):
    import numpy as np
    import soundfile as sf
    from modules.silero_loader import load_silero
    from tools.windows_neural_smoke import check_audio

    gpu = device != 'cpu'
    if gpu:
        torch.cuda.synchronize(0)
        torch.cuda.reset_peak_memory_stats(0)
    with block_python_network() as attempts, patch.dict(os.environ, {
            'ZSMM_SILERO_MODEL': str(model_path), 'ZSMM_ONLINE': '0'}):
        with measure_render(metrics), torch.inference_mode():
            model = load_silero()
            model.to(device)
            tensor = model.apply_tts(text=TEXT, speaker='baya', sample_rate=48000)
            check_tensor_device(tensor, device)
            if gpu:
                torch.cuda.synchronize(0)
            audio = np.asarray(tensor.detach().cpu().numpy(), dtype=np.float32)
            if audio.ndim != 1:
                raise ValueError('Expected mono model output')
            sf.write(target, audio, 48000, subtype='FLOAT')
        metrics.update(check_audio(target), sha256=sha256(target), network_attempts=attempts)
    if gpu:
        metrics.update(vram_peak_allocated_bytes=torch.cuda.max_memory_allocated(0),
                       vram_peak_reserved_bytes=torch.cuda.max_memory_reserved(0))
        if metrics['vram_peak_allocated_bytes'] <= 0:
            raise RuntimeError('No GPU allocation observed; refusing GPU acceptance')
    metrics['real_time_factor'] = metrics['wall_seconds'] / metrics['seconds']


def benchmark(backend, model_path, expected_hash, directory):
    directory.mkdir(parents=True, exist_ok=True)
    report = dict(schema=1, ok=False, inference_verified=False, product_profile_accepted=False,
                  kind='real_silero_draft_speech_not_singing', requested_backend=backend,
                  os=platform.system(), architecture=platform.machine(), python=sys.version,
                  source=os.environ.get('GITHUB_SHA'), text=TEXT,
                  network_guard='python_socket_only_not_os_firewall', measurements={})
    try:
        verify_package(model_path, expected_hash)  # Before any executable package load.
        import torch
        from app.ai.profiles import measure_profile
        device = select_device(torch, backend)
        torch.set_num_threads(2)
        report.update(torch=str(torch.__version__), device=device, model_sha256=expected_hash,
                      hardware=measure_profile(directory))
        render_on_backend(torch, device, report['measurements'], model_path.resolve(), directory / 'speech.wav')
        report.update(ok=True, inference_verified=True)
    except Exception:
        report['error'] = traceback.format_exc()
    (directory / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=('cpu', 'cuda', 'rocm'), required=True)
    parser.add_argument('--trusted-model', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = benchmark(args.backend, args.trusted_model, args.sha256, args.out)
    summary = {key: value for key, value in report.items() if key != 'hardware'}
    print('::notice title=Strict local model benchmark::' + json.dumps(summary, ensure_ascii=True))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
