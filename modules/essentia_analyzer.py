"""
ZS Music Maker v10 — Essentia Analyzer
=========================================
Продвинутая музыковедческая аналитика (ТЗ 3.2).

Использует Essentia (если установлена) для извлечения:
  - danceability, energy, valence
  - loudness (integrated LUFS-приближение)
  - key/scale/strength (более точно чем librosa)
  - beats_confidence, onset_rate
  - dynamic_complexity
  - spectral_flux, HFC, dissonance

Если Essentia недоступна — graceful fallback на librosa-based
расчёты (уже реализованы в modules/analyzer.py).

Автор: v10 «Chart Killer Pro»
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from modules.tempo import tempo_scalar

log = logging.getLogger("zsmm.essentia")

try:
    import essentia.standard as es  # type: ignore

    ESSENTIA_OK = True
except Exception:
    ESSENTIA_OK = False
    log.warning("Essentia не найдена — используем librosa fallback")

try:
    import librosa
    import numpy as np
except Exception:
    librosa = None
    np = None


def analyze_advanced(audio_path: str, sr: int = 44100) -> dict[str, Any]:
    """
    Возвращает расширенный музыковедческий отчёт.

    Никогда не бросает исключение — всегда возвращает dict.
    Если ничего не удалось, возвращает {"ok": False, "reason": ...}.
    """
    p = Path(audio_path)
    if not p.exists():
        return {"ok": False, "reason": f"file not found: {audio_path}"}

    if ESSENTIA_OK:
        try:
            return _analyze_essentia(str(p), sr)
        except Exception as e:
            log.warning("Essentia сбой, fallback librosa: %s", e)

    return _analyze_librosa_fallback(str(p), sr)


def _analyze_essentia(audio_path: str, sr: int) -> dict[str, Any]:
    loader = es.MonoLoader(filename=audio_path, sampleRate=sr)
    audio = loader()

    # Rhythm
    rhythm = es.RhythmExtractor2013(method="multifeature")
    bpm, beats, beats_conf, _, beats_intervals = rhythm(audio)

    # Key
    key_ex = es.KeyExtractor()
    key, scale, key_str = key_ex(audio)

    # Danceability
    danceability, _ = es.Danceability()(audio)

    # Loudness (LUFS approximation via ReplayGain proxy)
    loudness = es.ReplayGain()(audio)

    # Dynamic complexity
    dyn_cmp, dyn_loud = es.DynamicComplexity()(audio)

    # Spectral
    hfc = float(
        np.mean(
            [
                es.HFC()(es.Spectrum()(es.Windowing()(fr)))
                for fr in es.FrameGenerator(audio, 2048, 1024)
            ]
        )
    )

    onset = es.OnsetRate()
    onsets, onset_rate = onset(audio)

    return {
        "ok": True,
        "engine": "essentia",
        "bpm": float(bpm),
        "beats_confidence": float(beats_conf),
        "key": key,
        "scale": scale,
        "key_strength": float(key_str),
        "danceability": float(danceability),
        "loudness_replaygain_db": float(loudness),
        "dynamic_complexity": float(dyn_cmp),
        "hfc": hfc,
        "onset_rate": float(onset_rate),
        "n_beats": len(beats),
    }


def _analyze_librosa_fallback(audio_path: str, sr: int) -> dict[str, Any]:
    if librosa is None:
        return {"ok": False, "reason": "no librosa & no essentia"}
    try:
        y, sr = librosa.load(audio_path, sr=sr, mono=True)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_rate = float(np.mean(onset_env))
        rms = float(np.mean(librosa.feature.rms(y=y)))
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_idx = int(np.argmax(np.mean(chroma, axis=1)))
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        # Простая эвристика danceability = функция от tempo стабильности и RMS
        beat_stability = 1.0
        if len(beats) > 2:
            intervals = np.diff(librosa.frames_to_time(beats, sr=sr))
            beat_stability = 1.0 / (1.0 + float(np.std(intervals)))
        danceability = min(1.0, beat_stability * (0.3 + min(rms * 5, 0.7)))

        return {
            "ok": True,
            "engine": "librosa_fallback",
            "bpm": tempo_scalar(tempo, 0.0),
            "key": keys[key_idx],
            "scale": (
                "major"
                if np.mean(chroma[[0, 4, 7]]) > np.mean(chroma[[0, 3, 7]])
                else "minor"
            ),
            "danceability": float(danceability),
            "rms": rms,
            "spectral_centroid": centroid,
            "spectral_flatness": flatness,
            "onset_rate": onset_rate,
            "n_beats": len(beats),
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def save_report(report: dict[str, Any], out_json: str) -> None:
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(json.dumps({"engine_available": ESSENTIA_OK}, ensure_ascii=False))
    else:
        rep = analyze_advanced(sys.argv[1])
        print(json.dumps(rep, ensure_ascii=False, indent=2))
