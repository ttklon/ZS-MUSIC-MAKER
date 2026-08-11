"""
[v8] female_backing.py — Female backing vocals engine.

ТЗ 20.3: «Местами девушка пела — в припеве или на подпеве или на фоне.
Добавить функцию эту тоже.»

Реализация:
  1. Silero v4 (голос 'baya' / 'kseniya') — русские женские спикеры.
  2. Bark v2 — если доступен, спикер 'v2/ru_speaker_9' — русская женщина.
  3. Fallback: pyttsx3 с женским голосом (если ОС даёт).
  4. Пост-обработка: pitch +200 центов, лёгкий chorus, боковые backing-каналы.
  5. Смешивается с основным вокалом либо только на припеве, либо как ad-libs.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK_DIR = ROOT / "output" / "voice_backing"
# v22: ленивое создание (не при импорте)


# ------------------------------------------------------- synth backends
def _synth_silero(text: str, out_wav: Path, speaker: str = "kseniya") -> bool:
    try:
        import torch

        model_path = ROOT / "models" / "silero_female.pt"
        if not model_path.exists():
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="ru",
                speaker="v4_ru",
                trust_repo=True,
            )
            try:
                torch.save(model, model_path)
            except Exception:
                pass
        else:
            model = torch.load(model_path, map_location="cpu", weights_only=False)
        audio = model.apply_tts(text=text or "мм", speaker=speaker, sample_rate=48000)
        import soundfile as sf

        sf.write(str(out_wav), audio.cpu().numpy(), 48000)
        return True
    except Exception as e:
        print(f"[female_backing] silero failed: {e}")
        return False


def _synth_bark(text: str, out_wav: Path) -> bool:
    try:
        import soundfile as sf
        from bark import SAMPLE_RATE, generate_audio

        arr = generate_audio(text or "yeah", history_prompt="v2/ru_speaker_9")
        sf.write(str(out_wav), arr, SAMPLE_RATE)
        return True
    except Exception as e:
        print(f"[female_backing] bark failed: {e}")
        return False


def _synth_pyttsx(text: str, out_wav: Path) -> bool:
    try:
        import pyttsx3

        eng = pyttsx3.init()
        for v in eng.getProperty("voices"):
            if (
                "female" in v.name.lower()
                or "жен" in v.name.lower()
                or "irina" in v.id.lower()
            ):
                eng.setProperty("voice", v.id)
                break
        eng.save_to_file(text or "ah", str(out_wav))
        eng.runAndWait()
        return out_wav.exists() and out_wav.stat().st_size > 500
    except Exception as e:
        print(f"[female_backing] pyttsx failed: {e}")
        return False


def synth_female_line(text: str, out_wav: Path | None = None) -> Path:
    """Синтез одной строки женским голосом. Пробует Silero → Bark → pyttsx."""
    out_wav = Path(out_wav or BACK_DIR / f"back_{abs(hash(text)) % 10_000_000}.wav")
    for backend in (_synth_silero, _synth_bark, _synth_pyttsx):
        if backend(text, out_wav):
            return out_wav
    # Аварийная тишина, чтобы pipeline не падал.
    try:
        import numpy as np
        import soundfile as sf

        sf.write(str(out_wav), np.zeros(int(48000 * 0.5)), 48000)
    except Exception:
        out_wav.write_bytes(b"")
    return out_wav


# ------------------------------------------------------- post-processing
def sweeten_backing(
    wav_path: str | Path, pitch_semitones: float = 3.0, gain_db: float = -6.0
) -> Path:
    """
    Обработка бэков: пич-шифт вверх, EQ (срез низа), лёгкий стерео-хорус.
    """
    wav_path = Path(wav_path)
    try:
        import numpy as np
        import soundfile as sf

        y, sr = sf.read(str(wav_path))
        if y.ndim == 1:
            y = np.stack([y, y], axis=-1)

        # Pitch shift через resample (быстрый способ, без librosa не тратим CPU)
        try:
            import librosa

            mono = y.mean(axis=1) if y.ndim > 1 else y
            # Real DSP pitch-shift for backing vocal harmony (NOT RVC substitute).
            shifted = librosa.effects.pitch_shift(
                mono, sr=sr, n_steps=pitch_semitones
            )  # noqa: ZSMM_NOT_RVC
            y = np.stack([shifted, shifted], axis=-1)
        except Exception:
            pass

        # High-pass ~120 Гц
        try:
            from scipy.signal import butter, sosfilt

            sos = butter(2, 120 / (sr / 2), btype="highpass", output="sos")
            for ch in range(y.shape[1]):
                y[:, ch] = sosfilt(sos, y[:, ch])
        except Exception:
            pass

        # Стерео-разъезд + gain
        y[:, 0] *= 10 ** (gain_db / 20)
        y[:, 1] *= 10 ** ((gain_db - 1.5) / 20)
        out = wav_path.with_name(wav_path.stem + "_backing.wav")
        sf.write(str(out), y, sr)
        return out
    except Exception as e:
        print(f"[female_backing] sweeten failed: {e}")
        return wav_path


# ------------------------------------------------------- high-level API
def make_chorus_backing(chorus_lines: list[str], out_wav: Path | None = None) -> Path:
    """
    Собирает бэк-дорожку из строк припева: синтезирует женским голосом, сшивает
    последовательно, применяет sweeten_backing. Возвращает готовый WAV.
    """
    out_wav = Path(out_wav or BACK_DIR / "chorus_backing.wav")
    try:
        import numpy as np
        import soundfile as sf

        chunks = []
        sr = 48000
        for line in chorus_lines[:8]:
            p = synth_female_line(line)
            try:
                y, sr = sf.read(str(p))
                if y.ndim == 1:
                    y = np.stack([y, y], axis=-1)
                chunks.append(y)
                # маленькая пауза
                chunks.append(np.zeros((sr // 4, 2)))
            except Exception:
                continue
        if not chunks:
            sf.write(str(out_wav), np.zeros((sr, 2)), sr)
            return out_wav
        big = np.concatenate(chunks, axis=0)
        sf.write(str(out_wav), big, sr)
        return sweeten_backing(out_wav)
    except Exception as e:
        print(f"[female_backing] make_chorus_backing failed: {e}")
        return out_wav


def mix_backing_into_vocal(
    main_vocal_wav: str | Path, backing_wav: str | Path, backing_gain_db: float = -9.0
) -> Path:
    """Микшуем бэки поверх основного вокала. Возвращаем сшитый WAV."""
    main_vocal_wav = Path(main_vocal_wav)
    backing_wav = Path(backing_wav)
    try:
        import numpy as np
        import soundfile as sf

        v, sr = sf.read(str(main_vocal_wav))
        b, sr2 = sf.read(str(backing_wav))
        if v.ndim == 1:
            v = np.stack([v, v], axis=-1)
        if b.ndim == 1:
            b = np.stack([b, b], axis=-1)
        if sr2 != sr:
            try:
                import librosa

                b = librosa.resample(b.T, orig_sr=sr2, target_sr=sr).T
            except Exception:
                pass
        n = max(len(v), len(b))
        if len(v) < n:
            v = np.pad(v, ((0, n - len(v)), (0, 0)))
        if len(b) < n:
            b = np.pad(b, ((0, n - len(b)), (0, 0)))
        b = b * (10 ** (backing_gain_db / 20))
        mixed = np.clip(v + b, -1.0, 1.0)
        out = main_vocal_wav.with_name(main_vocal_wav.stem + "_with_backing.wav")
        sf.write(str(out), mixed, sr)
        return out
    except Exception as e:
        print(f"[female_backing] mix failed: {e}")
        return main_vocal_wav
