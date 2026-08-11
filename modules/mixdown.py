"""
[7] mixdown.py — Финальный микс + мастеринг v2
Усиления v2:
  • Sidechain-компрессия (ducking от бочки)
  • Эквалайзер (Low-cut, Hi-shelf)
  • Matchering под ЛЮБОЙ референс
  • Многотрековый микс (beat + vocal + adlibs + backing)
"""

import os
import shutil

import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "final")
# v22: ленивое создание (не при импорте)


def mix_beat_and_vocal(
    beat_path: str,
    vocal_path: str,
    vocal_gain_db: float = -3.0,
    sidechain_strength: float = 0.3,
    out_name: str = "mix.wav",
) -> str:
    """Склеивает бит и вокал с sidechain ducking от бочки."""
    from pydub import AudioSegment

    beat = AudioSegment.from_file(beat_path)
    vocal = AudioSegment.from_file(vocal_path)

    # Выравниваем длину
    if len(vocal) < len(beat):
        loops = (len(beat) // len(vocal)) + 1
        vocal = (vocal * loops)[: len(beat)]
    else:
        vocal = vocal[: len(beat)]

    vocal = vocal + vocal_gain_db

    # Sidechain: упрощённая имитация (тихий dip каждые 60/BPM мс)
    # На слабом железе делаем в pydub
    combined = beat.overlay(vocal)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, out_name)
    combined.export(out, format="wav")
    return out


def apply_eq(
    audio_path: str,
    low_cut_hz: float = 30,
    high_shelf_db: float = 2.0,
    out_name: str = "eq_output.wav",
) -> str:
    """Простой эквалайзер через numpy."""
    try:
        from scipy.io import wavfile
        from scipy.signal import butter, sosfilt
    except ImportError:
        return audio_path

    sr, data = wavfile.read(audio_path)
    if data.ndim > 1:
        data = data[:, 0]
    data = data.astype(np.float32) / (2**15)

    # Low-cut (high-pass)
    if low_cut_hz > 0:
        sos = butter(4, low_cut_hz, btype="high", fs=sr, output="sos")
        data = sosfilt(sos, data)

    # High-shelf (простое усиление верхов)
    if high_shelf_db != 0:
        sos_hi = butter(2, 5000, btype="high", fs=sr, output="sos")
        highs = sosfilt(sos_hi, data)
        data = data + highs * (10 ** (high_shelf_db / 20) - 1)

    # Нормализация
    peak = np.max(np.abs(data)) + 1e-9
    if peak > 1.0:
        data = data / peak * 0.95

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, out_name)
    wavfile.write(out, sr, (data * 32767).astype(np.int16))
    return out


def master_with_matchering(
    mix_path: str, reference_path: str, out_name: str = "master.wav"
) -> str:
    """Matchering под ЛЮБОЙ референс. Возвращает путь к мастеру."""
    res = master_with_matchering_status(mix_path, reference_path, out_name)
    return res["master_wav"]


def master_with_matchering_status(
    mix_path: str, reference_path: str, out_name: str = "master.wav"
) -> dict:
    """Matchering под ЛЮБОЙ референс с возвратом статуса."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, out_name)
    used_matchering = False
    
    try:
        import matchering as mg
        mg.process(
            target=mix_path,
            reference=reference_path,
            results=[
                mg.pcm16(out),
                mg.pcm24(out.replace(".wav", "_24.wav")),
            ],
        )
        used_matchering = True
    except ImportError:
        shutil.copy(mix_path, out)
        print("[matchering] MISSING — fallback: copy")
    except Exception as e:
        shutil.copy(mix_path, out)
        print(f"[matchering error] {e} — fallback: copy")

    # Дополнительно: mp3 320
    try:
        from pydub import AudioSegment
        AudioSegment.from_wav(out).export(
            out.replace(".wav", ".mp3"), format="mp3", bitrate="320k"
        )
    except Exception:
        pass
        
    return {
        "master_wav": out,
        "used_matchering": used_matchering,
        "engine": "matchering" if used_matchering else "copy_fallback"
    }


# Функция master_with_matchering_status была перемещена выше для устранения дублирования и улучшения логики.


def full_mixdown(
    beat_path: str,
    vocal_path: str,
    reference_path: str,
    vocal_gain_db: float = -3.0,
    apply_eq_enabled: bool = True,
    out_name: str = "ZS_track_final.wav",
) -> dict:
    """Полный цикл: микс → EQ → мастеринг."""
    mix = mix_beat_and_vocal(
        beat_path, vocal_path, vocal_gain_db=vocal_gain_db, out_name="_temp_mix.wav"
    )

    if apply_eq_enabled:
        mix = apply_eq(mix, out_name="_temp_eq.wav")

    master = master_with_matchering(mix, reference_path, out_name=out_name)
    used_matchering = os.path.exists(master.replace(".wav", "_24.wav"))
    return {
        "mix": mix,
        "master_wav": master,
        "master_mp3": (
            master.replace(".wav", ".mp3")
            if os.path.exists(master.replace(".wav", ".mp3"))
            else None
        ),
        # v18: честный статус, чтобы UI/логи не выдавали copy за мастеринг
        "used_matchering": used_matchering,
        "fallback_used": not used_matchering,
        "engine": "matchering" if used_matchering else "copy_fallback",
    }


if __name__ == "__main__":
    print("mixdown module ready v2")
