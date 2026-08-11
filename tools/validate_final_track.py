import sys
import os
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_audio_quality import validate_audio_file
import soundfile as sf
import numpy as np

track_path = "/home/ubuntu/ZS-MUSIC-MAKER/output/god_cli/masters/master_god.wav"

print(f"--- Final Quality Audit for: {track_path} ---")
try:
    validate_audio_file(track_path)
    data, sr = sf.read(track_path)
    peak = np.max(np.abs(data))
    rms = np.sqrt(np.mean(data**2))
    duration = len(data) / sr
    
    print(f"STATUS: PASS ✅")
    print(f"Peak Level: {peak:.4f} (Target <= 1.0)")
    print(f"RMS Level: {rms:.4f}")
    print(f"Duration: {duration:.2f}s")
    print(f"Sample Rate: {sr}Hz")
except Exception as e:
    print(f"STATUS: FAIL ❌")
    print(f"Error: {e}")
