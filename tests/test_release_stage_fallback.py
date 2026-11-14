"""`app/core/stages/release.py`: пакет либо полный, либо честно минимальный.

Стадия релиза — последнее, что видит пользователь. Здесь два пути:

* полный пакет из `modules.release.build_pack`;
* минимальный пакет, если движок упал или вернул не то.

Минимальный путь был покрыт на 40 %: никто не проверял, что при отказе
движка пользователь получает хотя бы мастер, текст, лицензионное
предупреждение и `fallback_used: True` — а не пустой `ok=True`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from app.core.stages import release as release_stage


def _master(tmp_path: Path) -> str:
    path = tmp_path / "master.wav"
    t = np.arange(4000) / 8000
    sf.write(path, 0.2 * np.sin(2 * np.pi * 220 * t), 8000)
    return str(path)


META = {"title": "Ночь", "artist": "ZS Producer", "hit_score": 71.0, "verdict": "PASS"}


# --------------------------------------------------------------------------- #
#  Полный путь
# --------------------------------------------------------------------------- #

def test_full_pack_is_used_when_engine_works(tmp_path, monkeypatch) -> None:
    calls: list[dict] = []

    def fake_build_pack(*args, **kwargs):
        calls.append(kwargs)
        return {"ok": True, "engine": "modules.release.pack", "n_files": 5}

    import modules.release as release_module

    monkeypatch.setattr(release_module, "build_pack", fake_build_pack)

    result = release_stage._stage_release_pack(
        _master(tmp_path), META, tmp_path, lyrics_text="строка", hit_metrics={"hit_score": 71.0}
    )

    assert result["ok"] is True
    assert result["engine"] == "modules.release.pack"
    assert calls and calls[0]["lyrics_text"] == "строка"


def test_engine_exception_falls_back_to_minimal_pack(tmp_path, monkeypatch) -> None:
    import modules.release as release_module

    def explode(*args, **kwargs):
        raise RuntimeError("zip writer unavailable")

    monkeypatch.setattr(release_module, "build_pack", explode)

    result = release_stage._stage_release_pack(_master(tmp_path), META, tmp_path)

    assert result["ok"] is True
    assert result["fallback_used"] is True
    assert "minimal pack" in result["reason"]
    assert result["fallback_attempts"][0]["error"] == "RuntimeError: zip writer unavailable"


def test_non_dict_result_is_not_accepted_as_success(tmp_path, monkeypatch) -> None:
    import modules.release as release_module

    monkeypatch.setattr(release_module, "build_pack", lambda *a, **k: "готово")

    result = release_stage._stage_release_pack(_master(tmp_path), META, tmp_path)

    assert result["fallback_used"] is True
    assert result["fallback_attempts"][0]["status"] == "invalid_result"


# --------------------------------------------------------------------------- #
#  Минимальный пакет
# --------------------------------------------------------------------------- #

def test_minimal_pack_contains_master_lyrics_and_licenses(tmp_path) -> None:
    master = _master(tmp_path)
    meta = dict(META, lyrics_text="первая строка\nвторая строка")

    result = release_stage._minimal_release_pack(master, meta, tmp_path / "release")

    out = tmp_path / "release"
    assert result["ok"] is True
    assert (out / "full_master_streaming.wav").is_file()
    assert (out / "lyrics.txt").read_text(encoding="utf-8") == meta["lyrics_text"]
    assert (out / "metadata.json").is_file()
    licenses = (out / "licenses.txt").read_text(encoding="utf-8")
    assert "not been verified" in licenses, "минимальный пакет обязан предупреждать о правах"
    hit = (out / "hit_report.md").read_text(encoding="utf-8")
    assert "71" in hit and "PASS" in hit


def test_minimal_pack_metadata_is_valid_json(tmp_path) -> None:
    release_stage._minimal_release_pack(_master(tmp_path), META, tmp_path / "release")

    payload = json.loads((tmp_path / "release" / "metadata.json").read_text(encoding="utf-8"))

    assert payload["title"] == "Ночь"


def test_minimal_pack_survives_missing_pydub_and_pillow(tmp_path, monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name in {"pydub", "PIL", "PIL.Image", "PIL.ImageDraw"}:
            raise ImportError(f"{name} unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)

    result = release_stage._minimal_release_pack(_master(tmp_path), META, tmp_path / "release")

    assert result["ok"] is True
    assert (tmp_path / "release" / "full_master_streaming.wav").is_file()
    # без pydub и Pillow mp3 и обложки нет — и это не выдаётся за успех
    names = {Path(item).name for item in result["files"]}
    assert "full_master.mp3" not in names
    assert "cover.png" not in names


def test_minimal_pack_reports_failure_for_missing_master(tmp_path) -> None:
    result = release_stage._minimal_release_pack(
        str(tmp_path / "nope.wav"), META, tmp_path / "release"
    )

    assert result["ok"] is False
    assert result["reason"]


def _install_fake_audio_and_image_libs(monkeypatch, exported: dict, saved: dict) -> None:
    """Стабы pydub/Pillow: проверяется наша ветка «всё есть», не кодировщики."""
    import sys
    import types

    class _FakeSegment:
        @staticmethod
        def from_file(path):
            exported["source"] = path
            return _FakeSegment()

        def export(self, target, format="mp3", bitrate=None):
            exported["format"] = format
            exported["bitrate"] = bitrate
            Path(target).write_bytes(b"ID3" + b"\0" * 2048)

    class _FakeImage:
        @staticmethod
        def new(mode, size, color):
            saved["size"] = size
            return _FakeImage()

        def save(self, target):
            saved["target"] = str(target)
            Path(target).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 1024)

    class _FakeDraw:
        @staticmethod
        def Draw(image):
            return types.SimpleNamespace(text=lambda *a, **k: saved.setdefault("text", a))

    monkeypatch.setitem(
        sys.modules, "pydub", types.SimpleNamespace(AudioSegment=_FakeSegment)
    )
    monkeypatch.setitem(
        sys.modules, "PIL", types.SimpleNamespace(Image=_FakeImage, ImageDraw=_FakeDraw)
    )
    monkeypatch.setitem(
        sys.modules, "PIL.Image", types.SimpleNamespace(Image=_FakeImage)
    )
    monkeypatch.setitem(
        sys.modules, "PIL.ImageDraw", types.SimpleNamespace(Draw=_FakeDraw.Draw)
    )


def test_minimal_pack_builds_mp3_and_cover_when_libraries_present(
    tmp_path, monkeypatch
) -> None:
    """С pydub mp3 и с Pillow обложка действительно попадают в пакет.

    Библиотеки подменены стабами, поэтому проверено только наше поведение:
    реальное кодирование mp3 на этой машине не проверено.
    """
    exported: dict = {}
    saved: dict = {}
    _install_fake_audio_and_image_libs(monkeypatch, exported, saved)

    out = tmp_path / "release"
    result = release_stage._minimal_release_pack(_master(tmp_path), META, out)

    names = {Path(item).name for item in result["files"]}
    assert "full_master.mp3" in names and "cover.png" in names
    assert exported["format"] == "mp3" and exported["bitrate"] == "320k"
    assert saved["size"] == (1400, 1400)
    assert (out / "full_master.mp3").stat().st_size > 1000
