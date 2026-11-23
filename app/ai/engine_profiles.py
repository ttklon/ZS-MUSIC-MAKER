"""Isolated engine inputs, NOT resolved transitive locks or inference certification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Exact direct inputs record known incompatible stacks; none is a reviewed lock.
PROFILES = {
    'core': (),
    'torch': ('torch==2.5.1', 'torchaudio==2.5.1'),
    'audiocraft': ('audiocraft==1.3.0', 'torch==2.1.0', 'torchaudio==2.1.0'),
    'demucs': ('demucs==4.0.1',),
    'faster_whisper': ('faster-whisper==1.1.1',),
    'rvc': ('rvc-python==0.1.5', 'numpy==1.23.5'),
}
ENGINE_PROFILE = {'llama_cpp': None, 'audiocraft_musicgen': 'audiocraft',
                  'xtts_v2': None, 'rvc': 'rvc', 'demucs': 'demucs',
                  'faster_whisper': 'faster_whisper', 'clap': None,
                  'diffusers': None, 'essentia_or_librosa': None, 'matchering_plus': None}


def profile(name: str) -> dict:
    if name not in PROFILES:
        raise ValueError('Unknown engine profile')
    inputs = list(PROFILES[name])
    core_hash = hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest() if name == 'core' else None
    digest = hashlib.sha256(json.dumps([inputs, core_hash]).encode()).hexdigest()
    return dict(schema=1, id=name, python='3.11', direct_inputs=inputs, input_sha256=digest, core_requirements_sha256=core_hash,
                lock_verified=False, windows_install_verified=False, inference_verified=False)


def environment_plan(name: str, workspace: Path) -> dict:
    data = profile(name)
    root = Path(workspace).resolve() / '.engine-envs' / name / data['input_sha256'][:16]
    # Immutable fingerprinted location; never pip into the application interpreter.
    import os
    python = root / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    return dict(**data, directory=str(root), executable=str(python),
                blocked_reason='Unresolved transitive lock / clean Windows install not verified')


def shared_install_allowed(spec: str) -> bool:
    """Bootstrap must not mutate shared Torch/NumPy while isolated workers are pending."""
    return False
