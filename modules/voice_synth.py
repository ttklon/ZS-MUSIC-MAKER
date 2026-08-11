"""
[v7] voice_synth.py — синтез "рыбы" вокала (draft).

Движки в порядке приоритета:
  1. silero  — русский v3.1, ~50MB, самый лёгкий, быстрый, локальный
  2. xtts    — Coqui XTTS-v2, многоязычный, качественнее
  3. bark    — bark-full от Suno, самый выразительный, но медленный
  4. pyttsx3 — системный TTS Windows (гарантированный fallback)

Все движки graceful: если один не установлен — идём к следующему.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "voice_draft"
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
        print(f"[voice_synth.silero] {e}")
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
        print(f"[voice_synth.xtts] {e}")
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
        print(f"[voice_synth.bark] {e}")
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
        print(f"[voice_synth.pyttsx3] {e}")
    return False


def _synth_gtts(text: str, out_path: str) -> bool:
    """Fallback для Linux через Google TTS (требует интернет)."""
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="ru")
        tts.save(out_path)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 100
    except Exception as e:
        print(f"[voice_synth.gtts] {e}")
        return False


def synth(
    text: str,
    engine: str = "silero",
    out_name: str | None = None,
    speaker_wav: str | None = None,
) -> str:
    """
    Синтезируем draft-вокал. Возвращаем путь к WAV.
    engine: silero | xtts | bark | pyttsx3 | auto
    speaker_wav — путь к записи пользователя для XTTS-клонирования (опционально).
    """
    if not text or not text.strip():
        return ""
    # v22: ленивое создание каталога — только при реальном вызове
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    out_path = str(OUT_DIR / (out_name or "draft.wav"))

    engines = {
        "silero": lambda: _synth_silero(text, out_path),
        "xtts": lambda: _synth_xtts(text, out_path, speaker_wav=speaker_wav),
        "bark": lambda: _synth_bark(text, out_path),
        "bark_full": lambda: _synth_bark(text, out_path),
        "pyttsx3": lambda: _synth_pyttsx3(text, out_path),
        "gtts": lambda: _synth_gtts(text, out_path),
    }

    if engine == "auto":
        # Пробуем от быстрого к качественному
        for e in ("silero", "xtts", "bark", "pyttsx3", "gtts"):
            if engines[e]():
                return out_path
        return out_path

    fn = engines.get(engine)
    if not fn:
        print(f"[voice_synth] unknown engine={engine}, fallback silero")
        fn = engines["silero"]

    ok = fn()
    if not ok:
        # цепочка fallback
        for backup in ("silero", "pyttsx3", "gtts"):
            if backup != engine:
                if engines[backup]():
                    return out_path

    return out_path


if __name__ == "__main__":
    r = synth(
        "Привет, это ZS Music Maker v7. Первый тест синтеза.",
        engine="pyttsx3",
        out_name="test_v7.wav",
    )
    print(f"WAV: {r}, exists: {os.path.exists(r)}")
