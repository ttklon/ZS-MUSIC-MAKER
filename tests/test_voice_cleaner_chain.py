from __future__ import annotations

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

from modules.voice_cleaner import clean_vocal_chain


def _band_rms(signal: np.ndarray, sample_rate: int, low_hz: float, high_hz: float) -> float:
    sos = butter(4, [low_hz / (sample_rate / 2), high_hz / (sample_rate / 2)], btype="bandpass", output="sos")
    band = sosfilt(sos, signal)
    return float(np.sqrt(np.mean(band**2)) + 1e-12)


def _synthetic_vocal(path, sample_rate: int = 16_000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(820)
    time_vec = np.arange(sample_rate * 4) / sample_rate
    active = ((time_vec >= 0.8) & (time_vec < 1.8)) | ((time_vec >= 2.2) & (time_vec < 3.2))
    voice = active * (
        0.12 * np.sin(2 * np.pi * 220 * time_vec)
        + 0.080 * np.sin(2 * np.pi * 6_000 * time_vec)
        + 0.025 * np.sin(2 * np.pi * 12_000 * time_vec)
    )
    noisy = voice + rng.normal(0.0, 0.006, len(time_vec))
    sf.write(path, noisy.astype("float32"), sample_rate)
    return noisy.astype("float32"), active


def test_clean_chain_gates_pause_noise_and_de_esses_without_air_rolloff(tmp_path) -> None:
    source = tmp_path / "noisy_vocal.wav"
    cleaned = tmp_path / "vocal_clean.wav"
    original, active = _synthetic_vocal(source, sample_rate=32_000)

    result = clean_vocal_chain(source, cleaned, genre="pop")
    output, sample_rate = sf.read(cleaned)
    pause = output[int(0.2 * sample_rate) : int(0.6 * sample_rate)]
    active_slice = slice(int(0.95 * sample_rate), int(1.65 * sample_rate))
    before_sibilance = _band_rms(original[active_slice], sample_rate, 5_500, 6_500)
    after_sibilance = _band_rms(output[active_slice], sample_rate, 5_500, 6_500)
    before_air = _band_rms(original[active_slice], sample_rate, 11_000, 13_000)
    after_air = _band_rms(output[active_slice], sample_rate, 11_000, 13_000)
    reduction_db = 20.0 * np.log10(after_sibilance / before_sibilance)
    air_change_db = 20.0 * np.log10(after_air / before_air)
    pause_dbfs = 20.0 * np.log10(float(np.sqrt(np.mean(pause**2))) + 1e-12)

    assert result["ok"] is True
    assert cleaned.exists()
    assert output.ndim == 1
    assert pause_dbfs < -60.0
    assert -4.5 <= reduction_db <= -1.5
    assert abs(air_change_db) < 1.0
    assert result["pause_noise_dbfs"] < -60.0
    assert active.any()


def test_vocal_fx_runs_clean_stage_before_optional_polish(tmp_path) -> None:
    from modules.vocal_fx import process_vocal

    source = tmp_path / "input.wav"
    output = tmp_path / "voice_fx.wav"
    _synthetic_vocal(source)

    result = process_vocal(
        source,
        output,
        use_double=False,
        use_throw=False,
        genre="phonk",
        use_tune=False,
        use_deess=False,
        use_prosody=False,
    )

    assert result["ok"] is True
    assert result["stages"] == ["clean"]
    assert result["clean_used"] is True
    assert result["cleaner"]["preset"]["deesser_db"] == 3.0
    assert output.exists()


def test_vocal_fx_reports_tune_deess_prosody_stages(tmp_path) -> None:
    from modules.vocal_fx import process_vocal

    source = tmp_path / "input.wav"
    output = tmp_path / "voice_fx.wav"
    _synthetic_vocal(source)

    result = process_vocal(source, output, use_double=False, use_throw=False, genre="phonk")

    assert result["ok"] is True
    assert {"clean", "tune", "deess", "prosody"} <= set(result["stages"])
    assert result["tune"]["engine"] == "phase_vocoder"
    assert result["deess"]["engine"] == "dynamic_band_deesser"
    assert result["prosody"]["engine"] == "phrase_prosody"


def test_spectral_denoise_reduces_hiss_and_keeps_the_voice_tone(tmp_path) -> None:
    """Де-нойз обязан убирать шипение, но не «съедать» тон голоса."""
    from modules.voice_cleaner import _spectral_denoise

    sample_rate = 16_000
    time_vec = np.arange(sample_rate * 2) / sample_rate
    voiced = (time_vec >= 0.5) & (time_vec < 1.5)  # фраза с паузами до и после
    tone = 0.10 * np.sin(2 * np.pi * 440 * time_vec) * voiced
    rng = np.random.default_rng(11)
    hiss = rng.normal(0.0, 0.01, tone.size)
    noisy = (tone + hiss).astype("float32")

    cleaned, report = _spectral_denoise(noisy, sample_rate)
    assert report["applied"] is True
    assert report["length_preserved"] is True
    cleaned = np.asarray(cleaned).reshape(-1)
    assert cleaned.shape[0] == noisy.shape[0]

    def level(x: np.ndarray, lo: float, hi: float) -> float:
        return 20.0 * np.log10(_band_rms(x, sample_rate, lo, hi))

    phrase = slice(int(0.6 * sample_rate), int(0.9 * sample_rate))
    pause = slice(int(1.6 * sample_rate), int(1.9 * sample_rate))
    # тон 440 Гц остался на месте (в пределах 1 дБ)
    assert abs(level(cleaned[phrase], 420, 460) - level(noisy[phrase], 420, 460)) < 1.0
    # шипение в паузе прижато (не «выключено в ноль» — это не гейт)
    pause_before = level(noisy[pause], 200, 3_000)
    pause_after = level(cleaned[pause], 200, 3_000)
    assert pause_after < pause_before - 4.0
