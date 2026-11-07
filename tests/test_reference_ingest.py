"""`modules/reference_ingest.py` — стилевой вектор из 1–7 референсов.

Модуль достижим: он в списке `modules.health.INTERNAL_MODULES` и объявлен в
`self_diag.EXPECTED_PATHS`, но покрыт не был. При написании тестов нашлись два
дефекта, которые делали его бесполезным на реальном аудио:

- `analyze_file` вызывал `float(tempo)` — на librosa 0.11 tempo приходит
  массивом (1,), и ЛЮБОЙ реальный файл возвращал `ok=False` с `TypeError`;
- `_save_cached` писал в `data/reference_cache/`, не создавая каталог. В чистой
  установке (каталог не в git, только `.gitkeep`) запись падала
  `FileNotFoundError` — то есть удачный анализ превращался в ошибку.

Живая проверка на синтезированном WAV: `bpm 112.35`, `key A minor`,
`build_style_vector` → `n_ok 2`, консенсус `120.77 / A minor`.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf

from modules import reference_ingest as ri


@pytest.fixture()
def sine_wav(tmp_path):
    def _make(name: str = "ref.wav", freq: float = 220.0, seconds: float = 2.0) -> str:
        sr = 22050
        y = 0.3 * np.sin(2 * np.pi * freq * np.arange(int(sr * seconds)) / sr)
        path = tmp_path / name
        sf.write(str(path), y.astype("float32"), sr)
        return str(path)

    return _make


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Кэш в tmp, чтобы не трогать data/ и не зависеть от прошлых прогонов."""
    cache = tmp_path / "cache"
    monkeypatch.setattr(ri, "CACHE_DIR", cache)
    return cache


class TestUtils:
    def test_md5_of_file(self, tmp_path) -> None:
        p = tmp_path / "a.txt"
        p.write_bytes(b"abc")
        assert ri._md5(str(p)) == "900150983cd24fb0d6963f7d28e17f72"

    def test_cache_path_keyed_by_content_hash(self, tmp_path) -> None:
        p = tmp_path / "a.txt"
        p.write_bytes(b"abc")
        assert ri._cache_path(str(p)).name == "900150983cd24fb0d6963f7d28e17f72.json"

    def test_save_creates_missing_cache_dir(self, tmp_path) -> None:
        # регрессия: в чистой установке каталога кэша нет
        assert not ri.CACHE_DIR.exists()
        target = tmp_path / "f.wav"
        target.write_bytes(b"x")
        ri._save_cached(str(target), {"ok": True, "bpm": 120.0})
        assert ri.CACHE_DIR.is_dir()
        assert ri._load_cached(str(target)) == {"ok": True, "bpm": 120.0}

    def test_load_cached_returns_none_when_absent(self, tmp_path) -> None:
        p = tmp_path / "b.txt"
        p.write_bytes(b"b")
        assert ri._load_cached(str(p)) is None

    def test_broken_cache_file_is_ignored(self, tmp_path) -> None:
        p = tmp_path / "c.txt"
        p.write_bytes(b"c")
        ri.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        ri._cache_path(str(p)).write_text("{не json", encoding="utf-8")
        assert ri._load_cached(str(p)) is None


class TestKeyFromChroma:
    def test_c_major_chroma_detected(self) -> None:
        chroma = np.zeros((12, 4))
        for idx in (0, 4, 7):
            chroma[idx] = 1.0
        key, mode = ri._key_from_chroma(chroma)
        assert (key, mode) == ("C", "major")

    def test_a_minor_chroma_detected(self) -> None:
        chroma = np.zeros((12, 4))
        for idx in (9, 0, 4):
            chroma[idx] = 1.0
        chroma[9] = 3.0
        key, mode = ri._key_from_chroma(chroma)
        assert key == "A"
        assert mode in ("minor", "major")

    def test_one_dimensional_chroma_accepted(self) -> None:
        chroma = np.zeros(12)
        chroma[2] = 5.0
        key, mode = ri._key_from_chroma(chroma)
        assert key in ri.KEYS
        assert mode in ("major", "minor")

    def test_without_numpy_returns_default(self, monkeypatch) -> None:
        monkeypatch.setattr(ri, "np", None)
        assert ri._key_from_chroma(None) == ("C", "major")


class TestAnalyzeFile:
    def test_missing_file_is_refused_with_reason(self, tmp_path) -> None:
        res = ri.analyze_file(str(tmp_path / "nope.wav"))
        assert res["ok"] is False
        assert "not found" in res["error"]

    def test_real_wav_is_analyzed(self, sine_wav) -> None:
        res = ri.analyze_file(sine_wav())
        assert res["ok"] is True, res.get("error")
        assert res["bpm"] > 0
        assert res["key"] in ri.KEYS
        assert res["mode"] in ("major", "minor")
        assert len(res["mfcc_mean"]) == 13
        assert len(res["chroma_mean"]) == 12
        assert res["sr"] == 22050
        assert res["duration_s"] == pytest.approx(2.0, abs=0.1)
        assert res["harmonic_ratio"] > 0.0

    def test_result_is_cached_and_reused(self, sine_wav) -> None:
        path = sine_wav()
        first = ri.analyze_file(path)
        assert first["ok"] is True
        assert ri._cache_path(path).exists()
        again = ri.analyze_file(path)
        assert again == first

    def test_cache_can_be_disabled(self, sine_wav) -> None:
        path = sine_wav()
        ri.analyze_file(path, use_cache=False)
        assert not ri._cache_path(path).exists()

    def test_fallback_when_librosa_absent(self, sine_wav, monkeypatch) -> None:
        monkeypatch.setattr(ri, "HAS_LIBROSA", False)
        path = sine_wav()
        res = ri.analyze_file(path)
        assert res["ok"] is True
        assert res["fallback"] is True
        assert res["bpm"] == 130.0
        assert "librosa unavailable" in res["note"]
        # fallback тоже кэшируется
        assert ri._load_cached(path)["fallback"] is True

    def test_fallback_not_cached_when_cache_disabled(self, sine_wav, monkeypatch) -> None:
        monkeypatch.setattr(ri, "HAS_LIBROSA", False)
        path = sine_wav()
        ri.analyze_file(path, use_cache=False)
        assert not ri._cache_path(path).exists()

    def test_broken_audio_reports_error_not_raises(self, tmp_path) -> None:
        bad = tmp_path / "bad.wav"
        bad.write_bytes(b"not audio at all")
        res = ri.analyze_file(str(bad))
        assert res["ok"] is False
        assert res["path"] == str(bad)
        assert res["error"]

    def test_array_tempo_becomes_number(self, sine_wav) -> None:
        """Регрессия: `float(tempo)` на массиве (1,) ронял каждый реальный файл."""
        res = ri.analyze_file(sine_wav())
        assert isinstance(res["bpm"], float)


class TestConsensus:
    def test_empty_features_default_bpm(self) -> None:
        assert ri._consensus_bpm([], []) == 130.0

    def test_normalises_low_bpm_by_doubling(self) -> None:
        bpm = ri._consensus_bpm([{"bpm": 40.0}], [1.0])
        assert bpm == 80.0

    def test_normalises_high_bpm_by_halving(self) -> None:
        # цикл останавливается на пороге 200, поэтому 400 → 200, а не 100
        assert ri._consensus_bpm([{"bpm": 800.0}], [1.0]) == 200.0
        assert ri._consensus_bpm([{"bpm": 400.0}], [1.0]) == 200.0

    def test_weights_shift_result(self) -> None:
        features = [{"bpm": 100.0}, {"bpm": 140.0}]
        heavy_low = ri._consensus_bpm(features, [3.0, 1.0])
        heavy_high = ri._consensus_bpm(features, [1.0, 3.0])
        assert heavy_low < heavy_high

    def test_zero_weights_do_not_divide_by_zero(self) -> None:
        assert ri._consensus_bpm([{"bpm": 100.0}], [0.0]) == 0.0

    def test_key_vote_picks_heaviest(self) -> None:
        features = [{"key": "A", "mode": "minor"}, {"key": "C", "mode": "major"}]
        assert ri._consensus_key(features, [0.1, 5.0]) == ("C", "major")

    def test_key_vote_empty_defaults(self) -> None:
        assert ri._consensus_key([], []) == ("C", "minor")

    def test_key_vote_handles_missing_fields(self) -> None:
        assert ri._consensus_key([{}], [1.0]) == ("C", "minor")


class TestBuildStyleVector:
    def test_no_references(self) -> None:
        res = ri.build_style_vector([])
        assert res == {"ok": False, "error": "no references given"}

    def test_more_than_seven_truncated(self, sine_wav) -> None:
        paths = [sine_wav(f"r{i}.wav", 200.0 + i * 10) for i in range(9)]
        res = ri.build_style_vector(paths)
        assert res["ok"] is True
        assert res["n_references"] == 7

    def test_all_failures_refused_with_per_file(self, tmp_path) -> None:
        res = ri.build_style_vector([str(tmp_path / "x.wav")])
        assert res["ok"] is False
        assert res["error"] == "all analyses failed"
        assert res["per_file"][0]["ok"] is False

    def test_two_references_build_vector(self, sine_wav) -> None:
        res = ri.build_style_vector([sine_wav("a.wav", 220.0), sine_wav("b.wav", 262.0)])
        assert res["ok"] is True
        assert res["n_ok"] == 2
        sv = res["style_vector"]
        assert sv["bpm"] > 0
        assert len(sv["mfcc_mean"]) == 13
        assert len(sv["chroma_mean"]) == 12
        assert res["consensus"]["genre_hint"]
        assert res["consensus"]["mood"]
        assert all("weight" in f for f in res["per_file"])

    def test_weights_reach_the_vector(self, sine_wav) -> None:
        a, b = sine_wav("a.wav", 220.0), sine_wav("b.wav", 262.0)
        res = ri.build_style_vector([a, b], weights=[1.0, 0.0])
        assert res["ok"] is True
        assert res["per_file"][1]["weight"] == 0.0

    def test_short_weights_padded(self, sine_wav) -> None:
        res = ri.build_style_vector([sine_wav("a.wav")], weights=[0.4])
        assert res["ok"] is True

    def test_mismatched_weights_are_repaired(self, sine_wav) -> None:
        a, b = sine_wav("a.wav"), sine_wav("b.wav", 262.0)
        res = ri.build_style_vector([a, b], weights=[0.5])
        assert res["ok"] is True
        assert [f["weight"] for f in res["per_file"]] == [0.5, 1.0]

    def test_partial_failure_keeps_good_ones(self, sine_wav, tmp_path) -> None:
        good = sine_wav("ok.wav")
        res = ri.build_style_vector([good, str(tmp_path / "missing.wav")])
        assert res["ok"] is True
        assert res["n_ok"] == 1
        assert res["n_references"] == 2

    def test_style_vector_on_machine_without_librosa(self, sine_wav, monkeypatch) -> None:
        """Fallback без librosa обязан отдавать вектор, а не падать."""
        monkeypatch.setattr(ri, "HAS_LIBROSA", False)
        res = ri.build_style_vector([sine_wav("a.wav"), sine_wav("b.wav", 262.0)])
        assert res["ok"] is True
        assert res["style_vector"]["bpm"] == 130.0
        assert res["style_vector"]["harmonic_ratio"] is None
        assert res["consensus"]["genre_hint"] == "generic hit"

    def test_style_vector_without_optional_fields(self, monkeypatch) -> None:
        """Файл без спектральных полей (fallback) не должен ронять сборку."""
        monkeypatch.setattr(
            ri,
            "analyze_file",
            lambda path, sr=22050: {"ok": True, "bpm": 140.0, "key": "D", "mode": "minor"},
        )
        res = ri.build_style_vector(["a.wav", "b.wav"])
        assert res["ok"] is True
        sv = res["style_vector"]
        assert sv["spectral_centroid"] is None
        assert sv["mfcc_mean"] is None
        assert sv["bpm"] == 140.0

    def test_weighted_average_of_lists_of_different_length(
        self, monkeypatch
    ) -> None:
        features = [
            {"ok": True, "bpm": 120.0, "key": "C", "mode": "major", "mfcc_mean": [1.0, 2.0]},
            {"ok": True, "bpm": 120.0, "key": "C", "mode": "major", "mfcc_mean": [3.0]},
        ]
        monkeypatch.setattr(ri, "analyze_file", lambda path, sr=22050: features.pop(0))
        res = ri.build_style_vector(["a.wav", "b.wav"])
        assert res["ok"] is True
        assert res["style_vector"]["mfcc_mean"] == [2.0, 1.0]


class TestHints:
    @pytest.mark.parametrize(
        ("sv", "expected"),
        [
            ({"bpm": 138.0, "onset_density": 4.0}, "phonk / drift"),
            ({"bpm": 126.0, "harmonic_ratio": 0.7}, "dance / edm"),
            ({"bpm": 85.0, "onset_density": 1.5}, "trap / hip-hop"),
            ({"bpm": 110.0}, "pop / r&b"),
            ({"bpm": 170.0}, "hardstyle / techno"),
            ({"bpm": 60.0}, "generic hit"),
        ],
    )
    def test_genre_hint_branches(self, sv, expected) -> None:
        assert ri._guess_genre(sv) == expected

    @pytest.mark.parametrize(
        ("sv", "expected"),
        [
            ({"mode": "minor", "spectral_centroid": 1200.0}, "dark / moody"),
            ({"mode": "minor", "spectral_centroid": 2500.0}, "energetic / driving"),
            ({"mode": "major", "spectral_centroid": 3000.0}, "bright / summer"),
            ({"mode": "major", "spectral_centroid": 1500.0}, "melancholic"),
        ],
    )
    def test_mood_branches(self, sv, expected) -> None:
        assert ri._guess_mood(sv) == expected

    def test_mood_handles_null_centroid(self) -> None:
        # None центр → запасные 2000 Гц, то есть «энергично», а не падение
        assert ri._guess_mood({"mode": "minor", "spectral_centroid": None}) == "energetic / driving"

    def test_mood_handles_null_mode(self) -> None:
        assert ri._guess_mood({"mode": None, "spectral_centroid": 1000.0}) == "dark / moody"

    def test_genre_handles_null_fields(self) -> None:
        # регрессия: fallback без librosa давал None и ронял разбор стиля
        assert ri._guess_genre({"bpm": None, "harmonic_ratio": None, "onset_density": None}) == (
            "generic hit"
        )
