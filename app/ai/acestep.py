"""Opt-in client for a separately installed local ACE-Step 1.5 API.

No model is bundled or started here. The server may continue an accepted task
if this client times out; the API offers no cancellation in this integration.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

MAX_AUDIO_BYTES = 512 * 1024 * 1024


def _local_base(url: str) -> str:
    parts = urlsplit(url)
    if (parts.scheme != "http" or parts.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment):
        raise ValueError("ACE-Step URL must be a local http://localhost or 127.0.0.1 server")
    return url.rstrip("/")


def _data(response):
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("error") or payload.get("code", 200) != 200:
        raise RuntimeError(f"ACE-Step API error: {str(payload)[:400]}")
    return payload.get("data")


def _validate_audio(path: Path, requested_duration: float) -> float:
    import numpy as np
    import soundfile as sf

    info = sf.info(str(path))
    duration = info.frames / info.samplerate if info.samplerate else 0
    if info.format != "WAV" or info.channels not in (1, 2) or info.samplerate < 8000:
        raise ValueError("ACE-Step did not return a supported WAV")
    if duration < requested_duration * 0.8 or duration > requested_duration * 1.2 + 2:
        raise ValueError(f"unexpected audio duration {duration:.1f}s (requested {requested_duration:.1f}s)")
    # Bound analysis memory while checking the entire file for silent/invalid output.
    peak = 0.0
    with sf.SoundFile(str(path)) as audio:
        for block in audio.blocks(blocksize=65536, dtype="float32", always_2d=True):
            if not np.isfinite(block).all():
                raise ValueError("non-finite samples in ACE-Step audio")
            peak = max(peak, float(np.max(np.abs(block))))
    if peak < 1e-5:
        raise ValueError("ACE-Step returned silent audio")
    return duration


def generate_instrumental(prompt: str, out_path: Path, *, duration_sec: float,
                          bpm: int, key: str, seed: int | None = None,
                          base_url: str = "http://127.0.0.1:8001",
                          timeout_sec: float = 7200, poll_sec: float = 2) -> dict:
    """Generate one instrumental WAV. Raises on failure; never substitutes a beat."""
    import requests

    base = _local_base(base_url)
    if not prompt.strip() or not 10 <= duration_sec <= 600 or not 30 <= bpm <= 300:
        raise ValueError("ACE-Step requires a prompt, duration 10–600s and BPM 30–300")
    if timeout_sec <= 0 or poll_sec <= 0:
        raise ValueError("timeout and poll interval must be positive")
    payload = {
        "prompt": prompt, "lyrics": "[Instrumental]", "audio_duration": duration_sec,
        "bpm": bpm, "key_scale": key, "time_signature": "4", "vocal_language": "unknown",
        "thinking": False, "use_cot_caption": False, "use_cot_language": False,
        "inference_steps": 8, "batch_size": 1, "audio_format": "wav",
        "use_random_seed": seed is None, "seed": seed if seed is not None else -1,
    }
    headers = {}
    api_key = os.getenv("ACESTEP_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    deadline = time.monotonic() + timeout_sec
    request_timeout = (3, min(30, timeout_sec))
    with requests.Session() as session:
        session.trust_env = False  # local API must not travel via a configured proxy
        submitted = _data(session.post(base + "/release_task", json=payload, headers=headers,
                                       timeout=request_timeout, allow_redirects=False))
        if not isinstance(submitted, dict) or not submitted.get("task_id"):
            raise ValueError("ACE-Step returned no task_id")
        task_id = str(submitted["task_id"])
        while time.monotonic() < deadline:
            data = _data(session.post(base + "/query_result", json={"task_id_list": [task_id]},
                                      headers=headers, timeout=request_timeout, allow_redirects=False))
            if not isinstance(data, list) or not data or not isinstance(data[0], dict):
                raise ValueError("ACE-Step returned an invalid task status")
            task = data[0]
            if str(task.get("task_id")) != task_id:
                raise ValueError("ACE-Step returned a different task")
            if task.get("status") == 2:
                raise RuntimeError(f"ACE-Step generation failed: {str(task.get('result'))[:400]}")
            if task.get("status") == 1:
                result = task.get("result")
                result = json.loads(result) if isinstance(result, str) else result
                if not isinstance(result, list) or not result or not isinstance(result[0], dict):
                    raise ValueError("ACE-Step returned no audio result")
                file_url = result[0].get("file", "")
                path = urlsplit(file_url)
                if path.scheme or path.netloc or path.path != "/v1/audio" or not path.query:
                    raise ValueError("ACE-Step returned an unsafe audio URL")
                out_path = Path(out_path)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = None
                try:
                    with session.get(base + file_url, headers=headers, timeout=request_timeout,
                                     stream=True, allow_redirects=False) as response:
                        response.raise_for_status()
                        if response.status_code != 200:
                            raise ValueError("unexpected audio response status")
                        with tempfile.NamedTemporaryFile(dir=out_path.parent, suffix=".wav", delete=False) as tmp:
                            temp_path = Path(tmp.name)
                            size = 0
                            for chunk in response.iter_content(1024 * 1024):
                                size += len(chunk)
                                if size > MAX_AUDIO_BYTES:
                                    raise ValueError("ACE-Step audio exceeds size limit")
                                tmp.write(chunk)
                    duration = _validate_audio(temp_path, duration_sec)
                    os.replace(temp_path, out_path)
                finally:
                    if temp_path is not None:
                        temp_path.unlink(missing_ok=True)
                return {"ok": True, "path": str(out_path), "duration_sec": round(duration, 2),
                        "engine": "ace_step_1_5_api", "task_id": task_id,
                        "reason": "ACE-Step instrumental generated; audio quality not independently verified"}
            if task.get("status") != 0:
                raise ValueError("unknown ACE-Step task status")
            time.sleep(min(poll_sec, max(0, deadline - time.monotonic())))
    raise TimeoutError(f"ACE-Step task {task_id} timed out; server may still be generating")
