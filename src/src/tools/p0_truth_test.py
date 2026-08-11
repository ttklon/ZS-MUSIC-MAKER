from pathlib import Path
import sys
import tempfile, wave, struct

# FIX v16 (P0): при запуске «python3 tools/p0_truth_test.py» корень проекта
# не попадает в sys.path — «from modules import ...» падал с
# ModuleNotFoundError без PYTHONPATH. Гарантируем доступность корня.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

def wav(path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(struct.pack("<8000h", *([0]*8000)))

with tempfile.TemporaryDirectory() as d:
    src=Path(d)/"in.wav"; wav(src)
    from modules import rvc_manager, matchering_master
    try:
        rvc_manager.infer(str(src), voice_name="definitely_missing")
        print("RVC_FAIL: fallback still active")
    except RuntimeError as e:
        print("RVC_HONEST_FAIL_PASS:", e)
    out=Path(d)/"master.wav"
    r=matchering_master.master_to_stand(str(src), str(out), "streaming")
    print("MASTER_RESULT:", r)
    from app.core import musicgen_texture
    m=musicgen_texture.generate_texture("test", duration_sec=1, vram_gb=0.0)
    print("MUSICGEN_RESULT:", m)
    from modules import master_pipeline_v12
    x=master_pipeline_v12.run("api_test", {"references": []}, dry_run=True)
    print("PIPELINE_API:", x.get("verdict"), x.get("percent_ready"))
