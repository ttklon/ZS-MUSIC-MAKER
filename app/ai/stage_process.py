"""Trusted local stage IPC; model handles never cross the process boundary.

Payloads are private temporary files, never user-supplied pickle documents.
Each worker owns a Windows kill-on-close job or a POSIX process session.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def execute(stage, context, timeout, budget):
    import cloudpickle
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix='zsmm-stage-') as directory:
        request = Path(directory) / 'request.bin'
        response = Path(directory) / 'response.bin'
        request.write_bytes(cloudpickle.dumps((stage, context, budget)))
        command = [sys.executable, str(root / 'app/cli/managed_task_host.py'),
                   str(Path(__file__).resolve()), str(request), str(response)]
        process = subprocess.Popen(command, start_new_session=os.name != 'nt')
        try:
            process.wait(timeout=max(.001, timeout))
            if process.returncode or not response.exists():
                raise RuntimeError(f'stage worker exited without result: {process.returncode}')
            result = cloudpickle.loads(response.read_bytes())
            if 'error' in result:
                raise RuntimeError(result['error'])
            context.clear()
            context.update(result['context'])
            return result
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"stage '{stage.name}' exceeded {timeout}s including model loading") from exc
        finally:
            # Kill the session even after success: stages may have left helpers alive.
            if os.name != 'nt':
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif process.poll() is None:
                process.kill()  # worker's Job Object also reaps detached descendants
            process.wait(timeout=15)


def worker(request, response):
    import cloudpickle
    from app.ai.registry import registry, MODEL_REGISTRY
    from app.ai.sequential_runner import _default_vram_probe
    from app.ai.activity import stage_activity
    stage, context, budget = cloudpickle.loads(Path(request).read_bytes())
    result = {}
    try:
        if stage.model and stage.model not in MODEL_REGISTRY:
            raise KeyError(f"Unknown model role: {stage.model}")
        handle, device, skipped = None, None, None
        if stage.model and not registry.is_available(stage.model):
            reason = f'{stage.model} unavailable (deps/weights missing)'
            if not stage.optional:
                raise RuntimeError(reason)
            skipped = reason
            run = stage.fallback_fn
        else:
            run = True
            if stage.model:
                loaded = registry.load(stage.model)
                handle, device = loaded.handle, loaded.device
        if _default_vram_probe() > budget:
            raise RuntimeError('oom: stage worker exceeds VRAM budget')
        with stage_activity(stage.name):
            output = stage.fn(handle, context) if run else None
        if _default_vram_probe() > budget:
            raise RuntimeError('oom: stage worker exceeds VRAM budget')
        result = dict(output=output, context=context, device=device, skipped=skipped)
    except BaseException as exc:
        result = {'error': f'{type(exc).__name__}: {exc}'}
    Path(response).write_bytes(cloudpickle.dumps(result))


if __name__ == '__main__':
    worker(*sys.argv[1:])
