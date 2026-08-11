# -*- coding: utf-8 -*-
"""
[v9] tiktok_edit_v9.py — авто-нарезка TikTok / Reels версий.

По ТЗ разделу «...ЗВУЧАТ В ... ТИКТОКЕ»:
  Для каждого трека нужны 3 короткие нарезки:
    • tiktok_15s.wav  — самый вирусный кусок 15 сек с моментальным входом
    • tiktok_30s.wav  — 30 сек версия для Reels/Shorts
    • hook_loop.wav   — только припев (8-16 bars) для эдитов

Стартовая позиция берётся из:
  1. hit_scorer.score_track()["tiktok_slice"], если передан
  2. arrangement_plan["tiktok_hook"], если передан
  3. Fallback: находим самый громкий 25-сек кусок

Опционально делает вертикальное видео 9:16 с волновой формой через ffmpeg
(если ffmpeg доступен).
"""
from __future__ import annotations
import json, subprocess, shutil
from pathlib import Path
from typing import Optional

try:
    import numpy as np
except Exception:
    np = None

try:
    import soundfile as sf
    HAS_SF = True
except Exception:
    HAS_SF = False


def _read(path: str):
    if not HAS_SF: return None, None
    y, sr = sf.read(path, always_2d=True)
    return y, sr


def _write(path: str, y, sr):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, y, sr)


def _find_hot_slice(y, sr, want_sec: float = 25.0) -> tuple[float, float]:
    """Находим самый громкий кусок нужной длины."""
    if np is None or len(y) == 0:
        return 0.0, want_sec
    if y.ndim == 2:
        mono = y.mean(axis=1)
    else:
        mono = y
    win_len = int(sr * want_sec)
    if len(mono) <= win_len:
        return 0.0, len(mono) / sr
    hop = int(sr * 1.0)
    best_rms = 0.0; best_start = 0
    for i in range(0, len(mono) - win_len, hop):
        r = float(np.sqrt(np.mean(mono[i:i+win_len] ** 2) + 1e-12))
        if r > best_rms:
            best_rms = r; best_start = i
    return best_start / sr, (best_start + win_len) / sr


def _fade_in_out(y, sr, in_ms: float = 40.0, out_ms: float = 120.0):
    if np is None: return y
    in_n = int(sr * in_ms / 1000.0)
    out_n = int(sr * out_ms / 1000.0)
    if in_n < len(y):
        ramp = np.linspace(0.0, 1.0, in_n)
        if y.ndim == 2:
            y[:in_n, :] = y[:in_n, :] * ramp[:, None]
        else:
            y[:in_n] = y[:in_n] * ramp
    if out_n < len(y):
        ramp = np.linspace(1.0, 0.0, out_n)
        if y.ndim == 2:
            y[-out_n:, :] = y[-out_n:, :] * ramp[:, None]
        else:
            y[-out_n:] = y[-out_n:] * ramp
    return y


def cut_slice(input_wav: str, output_wav: str,
              start_sec: float, end_sec: float,
              fade: bool = True) -> dict:
    if not HAS_SF or np is None:
        return {"ok": False, "error": "soundfile/numpy required"}
    y, sr = _read(input_wav)
    if y is None: return {"ok": False, "error": "read failed"}
    s = max(0, int(start_sec * sr))
    e = min(len(y), int(end_sec * sr))
    if e <= s: return {"ok": False, "error": "invalid slice"}
    seg = y[s:e].copy()
    if fade:
        seg = _fade_in_out(seg, sr)
    _write(output_wav, seg, sr)
    return {"ok": True, "output": output_wav,
            "duration_s": round((e - s) / sr, 2),
            "start_sec": start_sec, "end_sec": end_sec}


def make_all_cuts(input_wav: str,
                  out_dir: str,
                  hit_report: Optional[dict] = None,
                  arrangement_plan: Optional[dict] = None) -> dict:
    """Основной API. Делает 15s, 30s и hook_loop."""
    if not HAS_SF or np is None:
        return {"ok": False, "error": "soundfile/numpy required"}
    y, sr = _read(input_wav)
    if y is None: return {"ok": False, "error": "read failed"}

    dur = len(y) / sr
    outd = Path(out_dir); outd.mkdir(parents=True, exist_ok=True)

    # Стартовая точка
    start = None
    if hit_report and "tiktok_slice" in hit_report:
        start = float(hit_report["tiktok_slice"].get("start_sec", 0.0))
    elif arrangement_plan and "tiktok_hook" in arrangement_plan:
        start = float(arrangement_plan["tiktok_hook"].get("start_sec", 0.0))
    if start is None:
        start, _ = _find_hot_slice(y, sr, want_sec=25.0)

    results = {}
    # 15s
    s15 = max(0.0, min(dur - 15.0, start))
    results["tiktok_15s"] = cut_slice(input_wav,
                                       str(outd / "tiktok_15s.wav"),
                                       s15, s15 + 15.0)
    # 30s
    s30 = max(0.0, min(dur - 30.0, start - 2.0))
    results["tiktok_30s"] = cut_slice(input_wav,
                                       str(outd / "tiktok_30s.wav"),
                                       s30, s30 + 30.0)
    # hook_loop — попытка взять припев из аранжировки
    hook_start, hook_end = None, None
    if arrangement_plan and arrangement_plan.get("sections"):
        chorus = [s for s in arrangement_plan["sections"]
                  if s.get("name", "").startswith(("chorus", "drop"))]
        if chorus:
            best = max(chorus, key=lambda s: s.get("energy", 0.5))
            hook_start = float(best["start_sec"])
            hook_end = float(best["end_sec"])
    if hook_start is None:
        hook_start, hook_end = start, min(dur, start + 16.0)
    results["hook_loop"] = cut_slice(input_wav,
                                      str(outd / "hook_loop.wav"),
                                      hook_start, hook_end)

    return {"ok": True, "dir": str(outd), "results": results,
            "auto_start_sec": round(start, 2), "src_duration": round(dur, 2)}


# ============================================================ video (optional)
def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def make_vertical_video(audio_wav: str, output_mp4: str,
                        cover_png: Optional[str] = None,
                        bg_color: str = "black") -> dict:
    """Создаёт вертикальный 9:16 mp4 с волновой формой + обложкой (если есть)."""
    if not _has_ffmpeg():
        return {"ok": False, "error": "ffmpeg not available"}
    Path(output_mp4).parent.mkdir(parents=True, exist_ok=True)
    if cover_png and Path(cover_png).exists():
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(cover_png),
               "-i", str(audio_wav),
               "-c:v", "libx264", "-tune", "stillimage",
               "-c:a", "aac", "-b:a", "192k", "-shortest",
               "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,"
                      "crop=1080:1920",
               "-pix_fmt", "yuv420p", str(output_mp4)]
    else:
        cmd = ["ffmpeg", "-y", "-i", str(audio_wav),
               "-filter_complex",
               "[0:a]showwaves=s=1080x1920:mode=cline:colors=cyan,"
               "format=yuv420p[v]",
               "-map", "[v]", "-map", "0:a", "-c:v", "libx264",
               "-c:a", "aac", "-b:a", "192k", "-shortest",
               str(output_mp4)]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=180)
        if p.returncode != 0:
            return {"ok": False, "error": p.stderr[-500:].decode("utf-8",
                                                                 "ignore")}
        return {"ok": True, "output": output_mp4}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python tiktok_edit_v9.py <in.wav> <out_dir>")
        sys.exit(1)
    r = make_all_cuts(sys.argv[1], sys.argv[2])
    print(json.dumps({k: (v.get("output"), v.get("duration_s"))
                      for k, v in r.get("results", {}).items()}, indent=2))
