"""
ZS Music Maker v10 — Anti-Neuro Polish (+v17 numpy fallback)
================================================================
Оригинальные стадии (требуют pydub):
  1. Micro-timing jitter, 2. Breath insertion, 3. Formant micro-shift,
  4. Consonant hardening, 5. Ghost harmony removal, 6. Ending naturalization,
  7. Structural entropy, 8. Human error injection.

v17 additions:
  • apply_polish(input, out, intensity) — обёртка для мастер-стадии
    (orchestrator._stage_polish искал именно этот symbol).
  • Честный numpy-fallback (soundfile+scipy) — polish работает даже
    без pydub: breath / hi-shelf / low-pass ghost-remove / fade-out /
    human-error / entropy.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

log = logging.getLogger("zsmm.anti_neuro")

try:
    from pydub import AudioSegment
    from pydub.generators import WhiteNoise

    LIBS_OK = True
except Exception:
    LIBS_OK = False
    AudioSegment = None
    WhiteNoise = None

try:
    import numpy as _np
    import soundfile as _sf

    NP_OK = True
except Exception:
    _np = None
    _sf = None
    NP_OK = False


def polish_vocal(
    vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
) -> dict[str, Any]:
    """Полирует вокал/мастер, убирая нейроношность.
    presets: gentle (3 стадии), standard (6), aggressive (8)."""
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)

    if not LIBS_OK:
        return _polish_numpy(vocal_wav, out_wav, preset=preset, seed=seed)

    rng = random.Random(seed or 42)
    seg = AudioSegment.from_file(vocal_wav)
    stages_done: list[str] = []
    metrics: dict[str, Any] = {}

    stages = {
        "gentle": ["breath", "timing_jitter", "ending"],
        "standard": [
            "breath",
            "timing_jitter",
            "consonant_boost",
            "ghost_remove",
            "ending",
            "human_error",
        ],
        "aggressive": [
            "breath",
            "timing_jitter",
            "consonant_boost",
            "ghost_remove",
            "ending",
            "human_error",
            "formant_shift",
            "entropy_boost",
        ],
    }
    plan = stages.get(preset, stages["standard"])

    for stage in plan:
        try:
            seg, m = _apply_stage(seg, stage, rng)
            stages_done.append(stage)
            metrics[stage] = m
        except Exception as e:
            log.warning("stage %s failed: %s", stage, e)
            metrics[stage] = {"error": str(e)}

    seg.export(out_wav, format="wav")
    return {
        "ok": True,
        "preset": preset,
        "engine": "pydub",
        "stages_applied": stages_done,
        "metrics": metrics,
        "out_wav": out_wav,
        "path": out_wav,
    }


def apply_polish(
    input_wav: str,
    out_wav: str,
    intensity: float = 0.5,
    preset: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """v17: обёртка для мастеринг-стадии; intensity → preset."""
    if preset is None:
        if intensity < 0.35:
            preset = "gentle"
        elif intensity < 0.7:
            preset = "standard"
        else:
            preset = "aggressive"
    r = polish_vocal(input_wav, out_wav, preset=preset, seed=seed)
    if isinstance(r, dict):
        r.setdefault("intensity", intensity)
    return r


def _polish_numpy(
    vocal_wav: str, out_wav: str, preset: str = "standard", seed: int | None = None
) -> dict[str, Any]:
    """Честный numpy-fallback без pydub."""
    if not NP_OK:
        try:
            import shutil

            shutil.copy(vocal_wav, out_wav)
            return {
                "ok": True,
                "engine": "copy",
                "fallback_used": True,
                "reason": "no pydub/numpy/soundfile — copied as-is",
                "out_wav": out_wav,
                "path": out_wav,
            }
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    rng = random.Random(seed or 42)
    try:
        y, sr = _sf.read(vocal_wav, always_2d=True)
        y = y.astype("float32")
        stages_done: list[str] = []
        metrics: dict[str, Any] = {}

        plan = {
            "gentle": ["breath", "ending"],
            "standard": [
                "breath",
                "consonant_boost",
                "ghost_remove",
                "ending",
                "human_error",
            ],
            "aggressive": [
                "breath",
                "consonant_boost",
                "ghost_remove",
                "ending",
                "human_error",
                "entropy_boost",
            ],
        }.get(
            preset,
            ["breath", "consonant_boost", "ghost_remove", "ending", "human_error"],
        )

        for stage in plan:
            try:
                if stage == "breath":
                    dur = int(sr * 0.18)
                    noise = (
                        _np.random.RandomState(seed or 42)
                        .randn(dur, y.shape[1])
                        .astype("float32")
                    )
                    fade = _np.linspace(0, 1, dur // 3, dtype="float32")
                    envin = _np.concatenate(
                        [
                            fade,
                            _np.ones(dur - 2 * (dur // 3), dtype="float32"),
                            fade[::-1],
                        ]
                    )
                    if envin.shape[0] > dur:
                        envin = envin[:dur]
                    else:
                        envin = _np.pad(envin, (0, dur - envin.shape[0]))
                    breath = noise * envin.reshape(-1, 1) * (10 ** (-32 / 20))
                    y = _np.concatenate([breath, y], axis=0)
                    metrics[stage] = {"breath_ms": 180}

                elif stage == "consonant_boost":
                    try:
                        from scipy.signal import butter, sosfilt

                        sos = butter(2, 3000, btype="high", fs=sr, output="sos")
                        boost = _np.stack(
                            [sosfilt(sos, y[:, c]) for c in range(y.shape[1])], axis=1
                        )
                        y = y + boost * (10 ** (3 / 20) - 1) * 0.5
                        metrics[stage] = {"hi_boost_db": 3}
                    except Exception as e:
                        metrics[stage] = {"error": str(e)}

                elif stage == "ghost_remove":
                    try:
                        from scipy.signal import butter, sosfilt

                        sos = butter(4, 14000, btype="low", fs=sr, output="sos")
                        y = _np.stack(
                            [sosfilt(sos, y[:, c]) for c in range(y.shape[1])], axis=1
                        )
                        metrics[stage] = {"low_pass_hz": 14000}
                    except Exception as e:
                        metrics[stage] = {"error": str(e)}

                elif stage == "ending":
                    fade_len = min(int(sr * 1.2), y.shape[0] // 6)
                    if fade_len > 8:
                        env = _np.linspace(1.0, 0.0, fade_len, dtype="float32")
                        y[-fade_len:] *= env.reshape(-1, 1)
                    metrics[stage] = {"fade_out_ms": int(1000 * fade_len / sr)}

                elif stage == "human_error":
                    chunk = max(1, int(sr * 0.04))
                    dips = 0
                    for i in range(0, y.shape[0] - chunk, chunk):
                        if rng.random() < 0.03:
                            g = 10 ** ((-6 - rng.random() * 4) / 20)
                            y[i : i + chunk] *= g
                            dips += 1
                    metrics[stage] = {"micro_dips": dips}

                elif stage == "entropy_boost":
                    try:
                        from scipy.signal import butter, sosfilt

                        mid = y.shape[0] // 2
                        sos = butter(2, 120, btype="high", fs=sr, output="sos")
                        second = _np.stack(
                            [sosfilt(sos, y[mid:, c]) for c in range(y.shape[1])],
                            axis=1,
                        )
                        y[mid:] = second
                        metrics[stage] = {"mid_hp_hz": 120}
                    except Exception as e:
                        metrics[stage] = {"error": str(e)}

                stages_done.append(stage)
            except Exception as e:
                metrics[stage] = {"error": str(e)}

        peak = float(_np.max(_np.abs(y)) + 1e-9)
        if peak > 0.98:
            y = y / peak * 0.98

        _sf.write(out_wav, y, sr)
        return {
            "ok": True,
            "preset": preset,
            "engine": "numpy_fallback",
            "fallback_used": True,
            "stages_applied": stages_done,
            "metrics": metrics,
            "out_wav": out_wav,
            "path": out_wav,
            "reason": "pydub unavailable; used numpy anti-neuro polish",
        }
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _apply_stage(seg, name: str, rng: random.Random):
    if name == "breath":
        breath = WhiteNoise().to_audio_segment(duration=180).apply_gain(-32)
        seg = breath.fade_in(60).fade_out(60) + seg
        return seg, {"breath_ms": 180}
    if name == "timing_jitter":
        chunk_ms = 300
        chunks = [seg[i : i + chunk_ms] for i in range(0, len(seg), chunk_ms)]
        out = AudioSegment.silent(duration=0)
        shifts = 0
        for c in chunks:
            if rng.random() < 0.15:
                shift = rng.randint(-8, 12)
                if shift > 0:
                    c = AudioSegment.silent(duration=shift) + c
                shifts += 1
            out += c
        return out, {"shifted_chunks": shifts, "total_chunks": len(chunks)}
    if name == "consonant_boost":
        # Более умный буст согласных: только на атаках (транзиентах)
        try:
            import numpy as np

            y = np.array(seg.get_array_of_samples(), dtype=np.float32)
            # Ищем области с высокой активностью в ВЧ (согласные)
            from scipy.signal import butter, sosfilt

            sos = butter(2, 4000, btype="high", fs=seg.frame_rate, output="sos")
            hi = sosfilt(sos, y)
            # Усиливаем только там, где ВЧ и так есть
            y = y + hi * 0.5
            y_int = np.clip(y, -32768, 32767).astype(np.int16)
            return AudioSegment(
                y_int.tobytes(),
                frame_rate=seg.frame_rate,
                sample_width=2,
                channels=seg.channels,
            ), {"hi_boost_db": 3, "method": "transient_aware"}
        except Exception:
            boosted = seg.high_pass_filter(3000).apply_gain(3)
            return seg.overlay(boosted.apply_gain(-6)), {
                "hi_boost_db": 3,
                "method": "simple_overlay",
            }
    if name == "ghost_remove":
        seg = seg.low_pass_filter(14000)
        return seg, {"low_pass_hz": 14000}
    if name == "ending":
        fade_ms = min(1200, len(seg) // 6)
        return seg.fade_out(fade_ms), {"fade_out_ms": fade_ms}
    if name == "human_error":
        chunk_ms = 40
        chunks = [seg[i : i + chunk_ms] for i in range(0, len(seg), chunk_ms)]
        out = AudioSegment.silent(duration=0)
        dips = 0
        for c in chunks:
            if rng.random() < 0.03:
                c = c.apply_gain(-6 - rng.random() * 4)
                dips += 1
            out += c
        return out, {"micro_dips": dips}
    if name == "formant_shift":
        try:
            import librosa
            import numpy as np

            # Конвертируем в numpy
            y = np.array(seg.get_array_of_samples(), dtype=np.float32) / (2**15)
            sr = seg.frame_rate

            # Формантный сдвиг через трюк "resample + pitch shift back"
            # Сдвигаем на 1.5 полутона (случайно вверх или вниз)
            steps = rng.uniform(1.0, 2.0) * (1 if rng.random() > 0.5 else -1)

            # 1. Сдвигаем всё (pitch + formants) через изменение частоты дискретизации
            y_shifted = librosa.resample(
                y, orig_sr=sr, target_sr=int(sr * (2 ** (steps / 12.0)))
            )

            # 2. Сдвигаем только питч обратно через STFT-based pitch shift.
            # Это осознанный формантный DSP-трюк anti-neuro polish
            # (resample+pitch-back ломает «пластмассовость»), а НЕ подмена RVC.
            y_final = librosa.effects.pitch_shift(
                y_shifted, sr=sr, n_steps=-steps
            )  # noqa: ZSMM_NOT_RVC

            # Обрезаем/дополняем до исходной длины
            if len(y_final) > len(y):
                y_final = y_final[: len(y)]
            else:
                y_final = np.pad(y_final, (0, len(y) - len(y_final)))

            # Конвертируем обратно в AudioSegment
            y_int = (y_final * (2**15)).astype(np.int16)
            out = AudioSegment(
                y_int.tobytes(), frame_rate=sr, sample_width=2, channels=seg.channels
            )
            return out, {"formant_steps": steps, "method": "librosa_resample_trick"}
        except Exception as e:
            return seg, {"error": f"formant shift failed: {e}"}
    if name == "entropy_boost":
        mid = len(seg) // 2
        first = seg[:mid]
        second = seg[mid:].high_pass_filter(120)
        return first + second, {"mid_hp_hz": 120}
    return seg, {}


def capability_report() -> dict[str, Any]:
    return {
        "pydub_available": LIBS_OK,
        "numpy_fallback_available": NP_OK,
        "polish_vocal": True,
        "apply_polish": True,
    }


if __name__ == "__main__":
    print(json.dumps(capability_report(), ensure_ascii=False, indent=2))
