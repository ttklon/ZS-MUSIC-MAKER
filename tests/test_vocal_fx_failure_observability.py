from __future__ import annotations

from pathlib import Path

import modules.vocal_fx as vocal_fx


def _result(ok: bool, path: str, reason: str | None = None) -> vocal_fx.VocalFxResult:
    return vocal_fx.VocalFxResult(ok, path, "fake", False, ok, 0, -20.0, -20.0, reason=reason)


def test_throw_fallback_copy_failure_is_explicit(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vocal_fx, "_OK", True)
    monkeypatch.setattr(vocal_fx, "apply_delay_throw", lambda *args, **kwargs: _result(False, "", "throw failed"))

    def fail_copy(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(vocal_fx.shutil, "copy", fail_copy)
    result = vocal_fx.process_vocal(
        str(tmp_path / "voice.wav"), str(tmp_path / "out.wav"),
        use_double=False, use_throw=True, clean_before_fx=False,
    )

    assert result["ok"] is False
    assert "fallback copy could not be written: disk full" in result["reason"]


def test_temporary_cleanup_failure_is_returned_as_warning(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vocal_fx, "_OK", True)

    def fake_double(_source, destination, **_kwargs):
        Path(destination).write_bytes(b"temporary")
        return _result(True, destination)

    def fake_throw(_source, destination, **_kwargs):
        Path(destination).write_bytes(b"final")
        return _result(True, destination)

    original_unlink = Path.unlink

    def fail_only_double_cleanup(path: Path, *args, **kwargs):
        if path.name == "_fx_double_tmp.wav":
            raise OSError("locked")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(vocal_fx, "apply_vocal_double", fake_double)
    monkeypatch.setattr(vocal_fx, "apply_delay_throw", fake_throw)
    monkeypatch.setattr(Path, "unlink", fail_only_double_cleanup)
    result = vocal_fx.process_vocal(
        str(tmp_path / "voice.wav"), str(tmp_path / "out.wav"),
        use_double=True, use_throw=True, clean_before_fx=False,
    )

    assert result["ok"] is True
    assert result["cleanup_warnings"] == ["_fx_double_tmp.wav: OSError: locked"]
