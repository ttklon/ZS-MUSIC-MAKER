"""`modules/artist_dossier/collectors.py` (54 %) и `modules/essentia_analyzer.py` (51 %).

Оба достижимы: коллекторы зовёт `--dossier-add`, анализатор — модуль метрик.

Здесь действует правило проекта «внешний сервис недоступен — это отказ, а не
тихий успех». У всех трёх сетевых коллекторов (Genius, YouTube) сейчас отказ
возвращает `[]` — то есть пользователь не может отличить «у артиста нет
текстов» от «нет токена» и от «сервис упал». Тесты фиксируют это как
известное ограничение, а не как норму: проверяется, что отказ не бросает
исключение и не выдаёт выдуманных данных.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from modules import essentia_analyzer
from modules.artist_dossier import collectors


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def touch_audio(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF0000")
    return path


# --------------------------------------------------------------------------- #
#  LocalFolderCollector
# --------------------------------------------------------------------------- #
class TestLocalFolder:
    def test_missing_folder_is_empty(self, tmp_path) -> None:
        assert collectors.LocalFolderCollector(str(tmp_path / "нет")).collect("X") == []

    def test_audio_and_lyrics_are_paired_by_title(self, tmp_path) -> None:
        touch_audio(tmp_path / "intro.wav")
        write(tmp_path / "intro.txt", "текст песни")
        (tmp_path / "notes.md").write_text("не собирается", encoding="utf-8")

        res = collectors.LocalFolderCollector(str(tmp_path)).collect("artist")
        assert len(res) == 1
        assert res[0]["title"] == "intro"
        assert res[0]["lyrics"] == "текст песни"
        assert res[0]["audio_path"].endswith("intro.wav")

    def test_pairing_is_case_insensitive(self, tmp_path) -> None:
        touch_audio(tmp_path / "Track.WAV")
        write(tmp_path / "track.txt", "текст")
        res = collectors.LocalFolderCollector(str(tmp_path)).collect("artist")
        # оба файла дали один ключ casefold → одна запись, а не две
        assert len(res) == 1
        assert res[0]["audio_path"].endswith("Track.WAV")
        assert res[0]["lyrics"] == "текст"

    def test_artist_prefix_is_stripped_from_title(self, tmp_path) -> None:
        touch_audio(tmp_path / "Kalash - Ночная дорога.mp3")
        res = collectors.LocalFolderCollector(str(tmp_path)).collect("kalash")
        assert res[0]["title"] == "Ночная дорога"

    def test_other_artist_prefix_is_kept(self, tmp_path) -> None:
        touch_audio(tmp_path / "Someone - Песня.mp3")
        res = collectors.LocalFolderCollector(str(tmp_path)).collect("kalash")
        assert res[0]["title"] == "Someone - Песня"

    def test_nested_folders_are_scanned(self, tmp_path) -> None:
        touch_audio(tmp_path / "album" / "deep" / "song.flac")
        res = collectors.LocalFolderCollector(str(tmp_path)).collect("artist")
        assert len(res) == 1

    def test_empty_lyrics_file_is_not_stored(self, tmp_path) -> None:
        touch_audio(tmp_path / "song.wav")
        write(tmp_path / "song.txt", "   \n  ")
        res = collectors.LocalFolderCollector(str(tmp_path)).collect("artist")
        assert "lyrics" not in res[0]

    def test_unsupported_suffix_is_ignored(self, tmp_path) -> None:
        (tmp_path / "cover.jpg").write_bytes(b"\xff\xd8")
        (tmp_path / "readme.md").write_text("x", encoding="utf-8")
        assert collectors.LocalFolderCollector(str(tmp_path)).collect("a") == []

    def test_results_are_sorted_by_title(self, tmp_path) -> None:
        touch_audio(tmp_path / "b.wav")
        touch_audio(tmp_path / "a.wav")
        touch_audio(tmp_path / "c.wav")
        titles = [t["title"] for t in collectors.LocalFolderCollector(str(tmp_path)).collect("a")]
        assert titles == ["a", "b", "c"]

    def test_lyrics_only_file_is_returned(self, tmp_path) -> None:
        write(tmp_path / "только_текст.txt", "слова")
        res = collectors.LocalFolderCollector(str(tmp_path)).collect("a")
        assert res == [{"title": "только_текст", "lyrics": "слова"}]


# --------------------------------------------------------------------------- #
#  LyricVaultCollector
# --------------------------------------------------------------------------- #
class TestLyricVault:
    def test_missing_vault_is_empty(self, tmp_path) -> None:
        assert collectors.LyricVaultCollector(str(tmp_path / "нет")).collect("X") == []

    def test_artist_folder_exact_name(self, tmp_path) -> None:
        write(tmp_path / "author_corpus" / "Kalash" / "song1.txt", "текст 1")
        write(tmp_path / "author_corpus" / "Kalash" / "song2.txt", "текст 2")
        res = collectors.LyricVaultCollector(str(tmp_path)).collect("Kalash")
        assert sorted(t["title"] for t in res) == ["song1", "song2"]

    def test_lowercase_folder_is_found(self, tmp_path) -> None:
        write(tmp_path / "author_corpus" / "kalash" / "s.txt", "т")
        assert len(collectors.LyricVaultCollector(str(tmp_path)).collect("Kalash")) == 1

    def test_underscore_folder_is_found(self, tmp_path) -> None:
        write(tmp_path / "author_corpus" / "two_words" / "s.txt", "т")
        assert len(collectors.LyricVaultCollector(str(tmp_path)).collect("two words")) == 1

    def test_same_folder_is_not_read_twice(self, tmp_path) -> None:
        # "Kalash" и "kalash" на регистронезависимой ФС — один и тот же каталог,
        # поэтому текст не должен попасть в досье дважды.
        write(tmp_path / "author_corpus" / "Kalash" / "s.txt", "1")
        res = collectors.LyricVaultCollector(str(tmp_path)).collect("Kalash")
        assert len(res) == 1

    def test_distinct_folders_are_both_read(self, tmp_path) -> None:
        write(tmp_path / "author_corpus" / "Kalash" / "s1.txt", "1")
        write(tmp_path / "author_corpus" / "kalash" / "s2.txt", "2")
        res = collectors.LyricVaultCollector(str(tmp_path)).collect("Kalash")
        assert sorted(t["title"] for t in res) == ["s1", "s2"]

    def test_non_txt_files_ignored(self, tmp_path) -> None:
        write(tmp_path / "author_corpus" / "A" / "s.md", "x")
        assert collectors.LyricVaultCollector(str(tmp_path)).collect("A") == []


# --------------------------------------------------------------------------- #
#  GeniusCollector
# --------------------------------------------------------------------------- #
class TestGenius:
    def test_without_token_returns_empty_without_import(self, monkeypatch) -> None:
        monkeypatch.delenv("GENIUS_TOKEN", raising=False)
        # если бы импорт случился, тест упал бы на отсутствии lyricsgenius
        assert collectors.GeniusCollector().collect("X") == []

    def test_token_from_env(self, monkeypatch) -> None:
        monkeypatch.setenv("GENIUS_TOKEN", "env-token")
        assert collectors.GeniusCollector().token == "env-token"

    def test_explicit_token_wins(self, monkeypatch) -> None:
        monkeypatch.setenv("GENIUS_TOKEN", "env")
        assert collectors.GeniusCollector("explicit").token == "explicit"

    def test_songs_are_mapped(self, monkeypatch) -> None:
        class Song:
            def __init__(self, title, lyrics, url):
                self.title, self.lyrics, self.url = title, lyrics, url

        class Artist:
            songs = [Song("A", "текст", "http://x/a"), Song("B", "", "http://x/b")]

        class Genius:
            def __init__(self, *a, **k):
                self.verbose = True
                self.skip_non_songs = False

            def search_artist(self, artist, max_songs=None, sort=None, get_full_info=None):
                assert max_songs == 25
                return Artist()

        module = types.ModuleType("lyricsgenius")
        module.Genius = Genius
        monkeypatch.setitem(sys.modules, "lyricsgenius", module)

        res = collectors.GeniusCollector("t").collect("X")
        # песня без текста отбрасывается — обещание «только с текстом»
        assert len(res) == 1
        assert res[0] == {"title": "A", "lyrics": "текст", "external_url": "http://x/a"}

    def test_no_artist_found_returns_empty(self, monkeypatch) -> None:
        class Genius:
            def __init__(self, *a, **k):
                pass

            def search_artist(self, *a, **k):
                return None

        module = types.ModuleType("lyricsgenius")
        module.Genius = Genius
        monkeypatch.setitem(sys.modules, "lyricsgenius", module)
        assert collectors.GeniusCollector("t").collect("X") == []

    def test_service_failure_is_swallowed_but_named(self, monkeypatch) -> None:
        class Genius:
            def __init__(self, *a, **k):
                raise ConnectionError("нет сети")

        module = types.ModuleType("lyricsgenius")
        module.Genius = Genius
        monkeypatch.setitem(sys.modules, "lyricsgenius", module)
        # известное ограничение: причина не доходит до вызывающего, но и
        # исключения нет — досье не падает из-за внешнего сервиса
        assert collectors.GeniusCollector("t").collect("X") == []


# --------------------------------------------------------------------------- #
#  YouTubeCollector
# --------------------------------------------------------------------------- #
class TestYouTube:
    def test_missing_yt_dlp_returns_empty(self, monkeypatch) -> None:
        monkeypatch.setitem(sys.modules, "yt_dlp", None)
        assert collectors.YouTubeCollector("/tmp/x").collect("A") == []

    def test_download_entries_are_mapped(self, tmp_path, monkeypatch) -> None:
        calls = []

        class YDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def extract_info(self, query, download=False):
                calls.append((query, download, self.opts))
                return {"entries": [{"webpage_url": "http://yt/1"}]}

        module = types.ModuleType("yt_dlp")
        module.YoutubeDL = YDL
        monkeypatch.setitem(sys.modules, "yt_dlp", module)

        res = collectors.YouTubeCollector(str(tmp_path / "dl"), max_tracks=2).collect(
            "Artist", titles=["a", "b", "c"]
        )
        assert len(res) == 2  # max_tracks
        assert res[0]["title"] == "a"
        assert res[0]["external_url"] == "http://yt/1"
        assert res[0]["audio_path"].endswith(".wav")
        assert calls[0][0] == "ytsearch1:Artist a"
        assert calls[0][1] is True
        assert calls[0][2]["postprocessors"][0]["preferredcodec"] == "wav"

    def test_default_title_is_artist(self, tmp_path, monkeypatch) -> None:
        queries = []

        class YDL:
            def __init__(self, opts):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def extract_info(self, query, download=False):
                queries.append(query)
                return {"webpage_url": "http://yt/x"}

        module = types.ModuleType("yt_dlp")
        module.YoutubeDL = YDL
        monkeypatch.setitem(sys.modules, "yt_dlp", module)

        collectors.YouTubeCollector(str(tmp_path)).collect("Solo")
        assert queries == ["ytsearch1:Solo Solo"]

    def test_failed_track_does_not_stop_others(self, tmp_path, monkeypatch) -> None:
        class YDL:
            def __init__(self, opts):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def extract_info(self, query, download=False):
                if "bad" in query:
                    raise RuntimeError("видео недоступно")
                return {"webpage_url": "http://ok"}

        module = types.ModuleType("yt_dlp")
        module.YoutubeDL = YDL
        monkeypatch.setitem(sys.modules, "yt_dlp", module)

        res = collectors.YouTubeCollector(str(tmp_path)).collect("A", titles=["bad", "good"])
        assert len(res) == 1
        assert res[0]["title"] == "good"

    def test_output_dir_is_created(self, tmp_path, monkeypatch) -> None:
        class YDL:
            def __init__(self, opts):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def extract_info(self, query, download=False):
                return {"webpage_url": "u"}

        module = types.ModuleType("yt_dlp")
        module.YoutubeDL = YDL
        monkeypatch.setitem(sys.modules, "yt_dlp", module)

        target = tmp_path / "deep" / "dir"
        collectors.YouTubeCollector(str(target)).collect("A", titles=["t"])
        assert target.is_dir()


# --------------------------------------------------------------------------- #
#  Essentia analyzer
# --------------------------------------------------------------------------- #
def audio_file(tmp_path, seconds=2.0, sr=22050):
    path = tmp_path / "a.wav"
    n = int(sr * seconds)
    y = (0.3 * np.sin(2 * np.pi * 220 * np.arange(n) / sr)).astype("float32")
    sf.write(str(path), y, sr)
    return str(path)


def click_track(tmp_path, seconds=6.0, sr=22050, step=0.5):
    """Клики с ровным шагом: у librosa появляются биты → работает beat_stability."""
    path = tmp_path / "clicks.wav"
    y = np.zeros(int(sr * seconds), dtype="float32")
    for t in np.arange(0.0, seconds, step):
        i = int(t * sr)
        y[i:i + 200] += 0.9
    sf.write(str(path), y, sr)
    return str(path)


class TestAnalyzeAdvanced:
    def test_missing_file_is_refused(self, tmp_path) -> None:
        res = essentia_analyzer.analyze_advanced(str(tmp_path / "нет.wav"))
        assert res["ok"] is False
        assert "file not found" in res["reason"]

    def test_librosa_fallback_returns_metrics(self, tmp_path) -> None:
        path = audio_file(tmp_path)
        res = essentia_analyzer.analyze_advanced(path)
        assert res["ok"] is True
        assert res["engine"] == "librosa_fallback"
        assert res["key"] in ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
        assert res["scale"] in ("major", "minor")
        assert 0.0 <= res["danceability"] <= 1.0
        assert res["rms"] > 0
        assert res["n_beats"] >= 0
        assert isinstance(res["bpm"], float)

    def test_essentia_failure_falls_back_to_librosa(self, tmp_path, monkeypatch) -> None:
        def boom(path, sr):
            raise RuntimeError("essentia сломалась")

        monkeypatch.setattr(essentia_analyzer, "ESSENTIA_OK", True)
        monkeypatch.setattr(essentia_analyzer, "_analyze_essentia", boom)
        res = essentia_analyzer.analyze_advanced(audio_file(tmp_path))
        # сбой первой модели не должен лишать пользователя отчёта вообще
        assert res["ok"] is True
        assert res["engine"] == "librosa_fallback"

    def test_beats_make_danceability_beat_stable(self, tmp_path) -> None:
        # >2 бита → считается стабильность интервалов, а не заглушка 1.0
        res = essentia_analyzer.analyze_advanced(click_track(tmp_path))
        assert res["ok"] is True
        assert res["engine"] == "librosa_fallback"
        assert res["n_beats"] > 2
        assert 0.0 <= res["danceability"] <= 1.0

    def test_no_engine_at_all_is_named(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(essentia_analyzer, "librosa", None)
        res = essentia_analyzer._analyze_librosa_fallback(audio_file(tmp_path), 22050)
        assert res == {"ok": False, "reason": "no librosa & no essentia"}

    def test_broken_audio_reports_error(self, tmp_path) -> None:
        # soundfile/audioread бросают NoBackendError с пустым str(e): раньше
        # отчёт получался {"ok": false, "reason": ""} — причина не названа.
        bad = tmp_path / "bad.wav"
        bad.write_bytes(b"not audio at all")
        res = essentia_analyzer.analyze_advanced(str(bad))
        assert res["ok"] is False
        assert res["reason"].strip()


class TestEssentiaPath:
    """Ветка с настоящим Essentia: сам движок подменён фейком."""

    class _Spectrum:
        def __call__(self, frame):
            return frame

    class _Windowing:
        def __call__(self, frame):
            return frame

    class _HFC:
        def __call__(self, spectrum):
            return 42.0

    class _FrameGenerator:
        def __init__(self, audio, size, hop):
            self.n = 4

        def __iter__(self):
            return iter([[0.1, 0.2, 0.3]] * self.n)

    class _MonoLoader:
        def __init__(self, filename=None, sampleRate=None):
            self.filename = filename
            self.sampleRate = sampleRate

        def __call__(self):
            return np.zeros(4410)

    class _RhythmExtractor2013:
        def __init__(self, method=None):
            self.method = method

        def __call__(self, audio):
            return 128.5, np.array([1, 2, 3]), 3.14, None, np.array([0.4, 0.5])

    class _KeyExtractor:
        def __call__(self, audio):
            return "A", "minor", 0.87

    class _Danceability:
        def __call__(self, audio):
            return 1.65, 0.0

    class _ReplayGain:
        def __call__(self, audio):
            return -9.4

    class _DynamicComplexity:
        def __call__(self, audio):
            return 8.8, -12.1

    class _OnsetRate:
        def __call__(self, audio):
            return np.array([0.1, 0.2]), 3.5

    def _fake_essentia(self, monkeypatch) -> None:
        fake = types.SimpleNamespace(
            MonoLoader=self._MonoLoader,
            RhythmExtractor2013=self._RhythmExtractor2013,
            KeyExtractor=self._KeyExtractor,
            Danceability=self._Danceability,
            ReplayGain=self._ReplayGain,
            DynamicComplexity=self._DynamicComplexity,
            HFC=self._HFC,
            Spectrum=self._Spectrum,
            Windowing=self._Windowing,
            FrameGenerator=self._FrameGenerator,
            OnsetRate=self._OnsetRate,
        )
        # при отсутствующей essentia имя "es" в модуле не связано вообще,
        # поэтому создаём его через raising=False
        monkeypatch.setattr(essentia_analyzer, "es", fake, raising=False)
        monkeypatch.setattr(essentia_analyzer, "ESSENTIA_OK", True)

    def test_essentia_report_has_all_descriptors(self, tmp_path, monkeypatch) -> None:
        self._fake_essentia(monkeypatch)
        res = essentia_analyzer.analyze_advanced(audio_file(tmp_path))
        assert res["ok"] is True
        assert res["engine"] == "essentia"
        assert res["bpm"] == 128.5
        assert res["key"] == "A"
        assert res["scale"] == "minor"
        assert res["key_strength"] == pytest.approx(0.87)
        assert res["danceability"] == pytest.approx(1.65)
        assert res["loudness_replaygain_db"] == pytest.approx(-9.4)
        assert res["beats_confidence"] == pytest.approx(3.14)


class TestSaveReport:
    def test_creates_parents_and_writes_json(self, tmp_path) -> None:
        import json

        target = tmp_path / "deep" / "report.json"
        essentia_analyzer.save_report({"ok": True, "bpm": 130.0}, str(target))
        assert json.loads(target.read_text(encoding="utf-8"))["bpm"] == 130.0

    def test_non_ascii_is_preserved(self, tmp_path) -> None:
        target = tmp_path / "r.json"
        essentia_analyzer.save_report({"note": "тёмный"}, str(target))
        assert "тёмный" in target.read_text(encoding="utf-8")


class TestEssentiaCli:
    def test_without_args_reports_availability(self, monkeypatch, capsys) -> None:
        import runpy

        monkeypatch.setattr("sys.argv", ["essentia_analyzer.py"])
        runpy.run_module("modules.essentia_analyzer", run_name="__main__")
        out = capsys.readouterr().out
        assert "engine_available" in out

    def test_with_file_argument_prints_report(self, tmp_path, monkeypatch, capsys) -> None:
        import runpy

        path = audio_file(tmp_path)
        monkeypatch.setattr("sys.argv", ["essentia_analyzer.py", path])
        runpy.run_module("modules.essentia_analyzer", run_name="__main__")
        out = capsys.readouterr().out
        assert '"ok": true' in out
        assert "librosa_fallback" in out or "essentia" in out
