"""
[v7] voice_synth.py — синтез "рыбы" вокала (draft).

Движки в порядке приоритета:
  1. silero  — русский v3.1, ~50MB, самый лёгкий, быстрый, локальный
  2. xtts    — Coqui XTTS-v2, многоязычный, качественнее
  3. bark    — bark-full от Suno, самый выразительный, но медленный
  4. pyttsx3 — системный TTS Windows (гарантированный fallback)

Все движки graceful: если один не установлен — идём к следующему.
"""

import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "voice_draft"
LOGGER = logging.getLogger(__name__)
# v22: ленивое создание (не при импорте)


def _synth_silero(text: str, out_path: str, speaker: str = "aidar") -> bool:
    """Silero v3.1 RU — быстро и локально."""
    try:
        import torch

        # Silero через torch.hub (первый раз скачивает ~50 MB)
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ru",
            speaker="v3_1_ru",
            trust_repo=True,
        )
        audio = model.apply_tts(text=text, speaker=speaker, sample_rate=48000)
        import torchaudio

        torchaudio.save(out_path, audio.unsqueeze(0), 48000)
        return True
    except Exception as e:
        LOGGER.warning("Silero draft synthesis unavailable: %s", e)
        return False


def _synth_xtts(
    text: str, out_path: str, language: str = "ru", speaker_wav: str | None = None
) -> bool:
    """Coqui XTTS-v2 — многоязычный, поддерживает клонирование по 6+ сек аудио."""
    try:
        from TTS.api import TTS

        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        tts = TTS(model_name=model_name)
        kwargs = dict(text=text, file_path=out_path, language=language)
        if speaker_wav and os.path.exists(speaker_wav):
            kwargs["speaker_wav"] = speaker_wav
        tts.tts_to_file(**kwargs)
        return True
    except Exception as e:
        LOGGER.warning("XTTS draft synthesis unavailable: %s", e)
        return False


def _synth_bark(
    text: str, out_path: str, voice_preset: str = "v2/ru_speaker_0"
) -> bool:
    """Bark-full от Suno — выразительный, но медленный (только под 12GB VRAM)."""
    try:
        import soundfile as sf
        from bark import SAMPLE_RATE, generate_audio

        audio = generate_audio(text, history_prompt=voice_preset)
        sf.write(out_path, audio, SAMPLE_RATE)
        return True
    except Exception as e:
        LOGGER.warning("Bark draft synthesis unavailable: %s", e)
        return False


def _synth_pyttsx3(text: str, out_path: str) -> bool:
    """Гарантированный fallback — системный TTS Windows."""
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
            return True
    except Exception as e:
        LOGGER.warning("pyttsx3 draft synthesis unavailable: %s", e)
    return False


def _synth_gtts(text: str, out_path: str) -> bool:
    """Fallback для Linux через Google TTS (требует интернет)."""
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="ru")
        tts.save(out_path)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 100
    except Exception as e:
        LOGGER.warning("gTTS draft synthesis unavailable: %s", e)
        return False


def _produced(out_path: str) -> bool:
    """Return whether a synthesizer produced a non-empty output file."""
    try:
        return os.path.exists(out_path) and os.path.getsize(out_path) > 100
    except OSError:
        return False


def _run_candidates(candidates: tuple[str, ...], engines: dict[str, object], out_path: str) -> bool:
    """Run candidate backends in order, accepting only verified output files."""
    for candidate in candidates:
        synthesize = engines[candidate]
        if synthesize() and _produced(out_path):
            return True
    return False


def synth(
    text: str,
    engine: str = "silero",
    out_name: str | None = None,
    speaker_wav: str | None = None,
    gender: str = "male",
) -> str:
    """Return a verified draft-vocal file path or an honest empty string."""
    if not text or not text.strip():
        return ""
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        LOGGER.warning("voice draft output directory unavailable: %s", error)
        return ""

    silero_speaker = (
        "kseniya" if str(gender).lower() in ("female", "f", "ж", "жен") else "aidar"
    )
    if not out_name:
        import time as _time

        out_name = f"draft_{int(_time.time() * 1000)}.wav"
    out_path = str(OUT_DIR / out_name)
    engines = {
        "silero": lambda: _synth_silero(text, out_path, speaker=silero_speaker),
        "xtts": lambda: _synth_xtts(text, out_path, speaker_wav=speaker_wav),
        "bark": lambda: _synth_bark(text, out_path),
        "bark_full": lambda: _synth_bark(text, out_path),
        "pyttsx3": lambda: _synth_pyttsx3(text, out_path),
        "gtts": lambda: _synth_gtts(text, out_path),
    }

    if engine == "auto":
        if _run_candidates(("silero", "xtts", "bark", "pyttsx3", "gtts"), engines, out_path):
            return out_path
        LOGGER.warning("all draft voice engines failed or are unavailable; returning empty result")
        return ""

    selected = engine if engine in engines else "silero"
    if selected != engine:
        LOGGER.warning("unknown draft voice engine %s; falling back to silero", engine)
    if _run_candidates((selected,), engines, out_path):
        return out_path

    fallbacks = tuple(name for name in ("silero", "pyttsx3", "gtts") if name != engine)
    if _run_candidates(fallbacks, engines, out_path):
        return out_path
    LOGGER.warning("no draft voice engine produced a verified file; returning empty result")
    return ""


if __name__ == "__main__":
    r = synth(
        "Привет, это ZS Music Maker v7. Первый тест синтеза.",
        engine="pyttsx3",
        out_name="test_v7.wav",
    )
    print(f"WAV: {r}, exists: {os.path.exists(r)}")
