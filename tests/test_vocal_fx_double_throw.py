# -*- coding: utf-8 -*-
"""Double-tracking и delay throw: реальные файлы, реальные проверки.

Проверяем не «функция не упала», а физику: длина сохраняется, пик не
пробивает потолок, дабл реально добавляет энергию, эхо действительно
заполняет паузу после фразы, а отсутствие входа даёт честный отказ.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

from modules.vocal_fx.double import apply_vocal_double
from modules.vocal_fx.pipeline import process_vocal
from modules.vocal_fx.throw import apply_delay_throw

SR = 22050


def _write(path, data: np.ndarray) -> str:
    sf.write(str(path), data.astype(np.float32), SR, subtype="FLOAT")
    return str(path)


def _read(path) -> np.ndarray:
    data, _ = sf.read(str(path), dtype="float32", always_2d=True)
    return data


def _voice_like(seconds: float = 2.0) -> np.ndarray:
    t = np.arange(int(SR * seconds)) / SR
    tone = 0.25 * np.sin(2 * np.pi * 220.0 * t) * (1.0 + 0.15 * np.sin(2 * np.pi * 5.0 * t))
    return np.stack([tone, tone * 0.9], axis=1)


def _peak(x: np.ndarray) -> float:
    return float(np.max(np.abs(x)) + 1e-12)


def test_double_keeps_length_and_stays_under_ceiling(tmp_path) -> None:
    src = _write(tmp_path / "v.wav", _voice_like())
    out = tmp_path / "v_double.wav"
    result = apply_vocal_double(src, str(out), double_level_db=-6.0)

    assert result.ok and result.double_used
    assert result.engine == "numpy_double_tracking"
    got = _read(out)
    assert got.shape == _read(src).shape
    assert _peak(got) <= 1.0
    # дабл подмешан — суммарная энергия выросла, но не в разы
    assert result.out_rms_db > result.in_rms_db
    assert result.out_rms_db - result.in_rms_db < 6.0


def test_double_is_not_a_plain_copy(tmp_path) -> None:
    src = _write(tmp_path / "v.wav", _voice_like(1.0))
    out = tmp_path / "v_double.wav"
    apply_vocal_double(src, str(out))
    original = _read(src)
    processed = _read(out)
    # pre-delay + детюн: сигналы не совпадают
    assert not np.allclose(original, processed, atol=1e-4)


def test_double_handles_mono_input(tmp_path) -> None:
    mono = np.sin(2 * np.pi * 180.0 * np.arange(SR) / SR) * 0.3
    src = _write(tmp_path / "mono.wav", mono)
    out = tmp_path / "mono_double.wav"
    result = apply_vocal_double(src, str(out))
    assert result.ok
    assert _read(out).shape[0] == mono.shape[0]


def test_double_reports_missing_file_instead_of_raising(tmp_path) -> None:
    result = apply_vocal_double(str(tmp_path / "nope.wav"), str(tmp_path / "o.wav"))
    assert result.ok is False
    assert result.reason
    assert result.out_wav == ""


def test_throw_fills_the_pause_after_a_phrase(tmp_path) -> None:
    phrase = _voice_like(0.5)
    silence = np.zeros((int(SR * 1.0), 2), dtype=np.float32)
    src = _write(tmp_path / "phrase.wav", np.concatenate([phrase, silence]))
    out = tmp_path / "phrase_throw.wav"
    result = apply_delay_throw(src, str(out), delay_ms=200.0, throw_level_db=-6.0)

    assert result.ok and result.throw_used
    assert result.throws_applied >= 1
    got = _read(out)
    assert got.shape == _read(src).shape
    assert _peak(got) <= 1.0
    # в паузе после фразы появилась энергия — это и есть бросок
    tail = got[int(SR * 0.6) :]
    assert float(np.sqrt(np.mean(tail**2))) > 1e-3


def test_vocal_chain_writes_32bit_float_intermediates(tmp_path) -> None:
    src = _write(tmp_path / "v.wav", _voice_like(0.3))
    out = tmp_path / "v_fx.wav"
    result = apply_vocal_double(src, str(out))
    assert result.ok
    info = sf.info(str(out))
    assert info.subtype == "FLOAT", "промежуточный файл цепочки не должен терять 16 бит"


def test_throw_on_continuous_signal_adds_nothing(tmp_path) -> None:
    src = _write(tmp_path / "cont.wav", _voice_like(1.0))
    out = tmp_path / "cont_throw.wav"
    result = apply_delay_throw(src, str(out))
    assert result.ok
    assert result.throws_applied == 0
    assert np.allclose(_read(src), _read(out), atol=1e-6)


def test_throw_ping_pong_and_mono_agree_on_length(tmp_path) -> None:
    phrase = _voice_like(0.4)
    silence = np.zeros((int(SR * 0.8), 2), dtype=np.float32)
    stereo_src = _write(tmp_path / "st.wav", np.concatenate([phrase, silence]))
    mono = np.concatenate([phrase[:, 0], silence[:, 0]])
    mono_src = _write(tmp_path / "mono.wav", mono)

    stereo_out = tmp_path / "st_throw.wav"
    mono_out = tmp_path / "mono_throw.wav"
    assert apply_delay_throw(stereo_src, str(stereo_out), ping_pong=True).ok
    assert apply_delay_throw(mono_src, str(mono_out), ping_pong=True).ok
    assert _read(stereo_out).shape[0] == len(mono)
    assert _read(mono_out).shape[0] == len(mono)


def test_pipeline_runs_double_without_throw(tmp_path) -> None:
    src = _write(tmp_path / "v.wav", _voice_like(1.0))
    out = tmp_path / "v_fx.wav"
    result = process_vocal(
        src,
        str(out),
        use_double=True,
        use_throw=False,
        clean_before_fx=False,
        use_tune=False,
        use_deess=False,
        use_prosody=False,
    )
    assert result["ok"] is True
    assert "double" in result["stages"]
    assert "throw" not in result["stages"]
    assert out.exists()


def test_pipeline_refuses_when_everything_is_switched_off(tmp_path) -> None:
    src = _write(tmp_path / "v.wav", _voice_like(0.5))
    out = tmp_path / "v_fx.wav"
    result = process_vocal(
        src,
        str(out),
        use_double=False,
        use_throw=False,
        clean_before_fx=False,
        use_tune=False,
        use_deess=False,
        use_prosody=False,
    )
    assert result["ok"] is False
    assert "failed" in result["reason"]
