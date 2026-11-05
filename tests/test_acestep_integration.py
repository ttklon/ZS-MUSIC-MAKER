"""Exercise HTTP integration with a fake server, never claim model inference."""
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pytest
import soundfile as sf

from app.ai.acestep import generate_instrumental
from app.core.recipe import build_recipe
from app.core.stages.beat import _stage_ai_beat


@pytest.fixture
def fake_server():
    audio = io.BytesIO()
    samples = 0.2 * np.sin(np.arange(80_000, dtype=np.float32) * 0.04)
    sf.write(audio, samples, 8000, format="WAV", subtype="PCM_16")
    state = {"payloads": [], "mode": "success", "wav": audio.getvalue()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): return
        def _json(self, payload):
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["payloads"].append((self.path, body))
            if self.path == "/release_task":
                self._json({"code": 200, "data": {"task_id": "test-task"}})
            else:
                mode = state["mode"]
                result = [{"file": "http://example.org/audio" if mode == "unsafe" else "/v1/audio?path=test"}]
                task = {"task_id": "test-task", "status": 2 if mode == "failed" else 1, "result": json.dumps(result)}
                self._json({"code": 200, "data": [task]})
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", str(len(state["wav"])))
            self.end_headers()
            self.wfile.write(state["wav"])

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_generation_contract_and_low_memory_request(fake_server, tmp_path):
    state, url = fake_server
    result = generate_instrumental("instrumental house", tmp_path / "beat.wav", duration_sec=10,
                                   bpm=125, key="A minor", seed=42, base_url=url, timeout_sec=5, poll_sec=.01)
    assert result["ok"] and result["engine"] == "ace_step_1_5_api"
    assert sf.info(result["path"]).duration == 10
    request = state["payloads"][0][1]
    assert request["batch_size"] == 1 and request["thinking"] is False
    assert request["lyrics"] == "[Instrumental]" and request["audio_format"] == "wav"
    assert request["bpm"] == 125 and request["key_scale"] == "A minor" and request["seed"] == 42


@pytest.mark.parametrize("mode", ["unsafe", "failed"])
def test_server_failure_and_unsafe_download_are_not_silently_replaced(fake_server, tmp_path, mode):
    state, url = fake_server
    state["mode"] = mode
    with pytest.raises((ValueError, RuntimeError)):
        generate_instrumental("instrumental", tmp_path / "beat.wav", duration_sec=10,
                              bpm=125, key="A minor", base_url=url, timeout_sec=5, poll_sec=.01)
    assert not (tmp_path / "beat.wav").exists()


def test_silent_audio_and_remote_url_are_rejected(fake_server, tmp_path):
    state, url = fake_server
    buf = io.BytesIO()
    sf.write(buf, np.zeros(80_000, dtype=np.float32), 8000, format="WAV")
    state["wav"] = buf.getvalue()
    with pytest.raises(ValueError, match="silent"):
        generate_instrumental("instrumental", tmp_path / "beat.wav", duration_sec=10,
                              bpm=125, key="A minor", base_url=url, timeout_sec=5)
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match="local"):
        generate_instrumental("instrumental", tmp_path / "beat.wav", duration_sec=10,
                              bpm=125, key="A minor", base_url="http://evil.example:8001")


def test_recipe_propagates_opt_in_and_server_unavailable_is_failed(tmp_path, monkeypatch):
    recipe = build_recipe({"beat_engine": "ace_step", "genre": "house", "theme": "пуэр", "duration_sec": 10})
    assert recipe["beat_engine"] == "ace_step"
    monkeypatch.setenv("ZSMM_ACESTEP_URL", "http://127.0.0.1:1")
    result = _stage_ai_beat(recipe, {"duration_sec": 10}, tmp_path, {"target_bpm": 125})
    assert result["ok"] is False and result["engine"] == "ace_step_1_5_api"
    assert not (tmp_path / "beat.wav").exists()
    assert _stage_ai_beat(recipe, {}, tmp_path, {}, dry_run=True)["blocked"] is True


def test_pipeline_routes_selected_model_to_mix(fake_server, tmp_path, monkeypatch):
    from app.core.orchestrator import run_full_pipeline
    state, url = fake_server
    monkeypatch.setenv("ZSMM_ACESTEP_URL", url)
    result = run_full_pipeline("ace-integration", {
        "beat_engine": "ace_step", "genre": "house", "theme": "пуэр",
        "duration_sec": 10, "voice_mode": "off", "export_stems": False,
    }, out_root=tmp_path, only={"beat", "mix"})
    stages = {item["name"]: item for item in result["stages"]}
    assert stages["_stage_beat"]["status"] == "OK"
    assert stages["_stage_beat"]["output"]["engine"] == "ace_step_1_5_api"
    assert stages["_stage_mix_and_sidechain"]["status"] == "OK"
    assert (tmp_path / "beat.wav").is_file()
    assert state["payloads"][0][1]["audio_duration"] == 10
