"""`modules/analyzer.py` (50 %) и `modules/midi_generator.py` (29 %).

Оба достижимы (`REAL_PASS` в инвентаре): анализатор — мульти-референсный вход
пайплайна, MIDI-генератор — экспорт паттернов. Проверяются на синтетике; веса
моделей и внешних сервисов не нужны.

Найденный дефект: `analyze_multi(weights=[0, 0])` падал `ZeroDivisionError`
(нормализация весов делила на их сумму), а короткий список весов молча
рассинхронизировался с числом референсов — стилевой вектор считался по чужим
весам.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf

from modules import analyzer, midi_generator


SR = 22050


def sine(seconds: float = 2.0, freq: float = 220.0, amp: float = 0.3, sr: int = SR):
    n = int(sr * seconds)
    return (amp * np.sin(2 * np.pi * freq * np.arange(n) / sr)).astype("float32")


def write_wav(path, **kw):
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    y = sine(**kw)
    sf.write(str(path), y, kw.get("sr", SR))
    return str(path)


# --------------------------------------------------------------------------- #
#  анализатор: живой DSP на синтетике
# --------------------------------------------------------------------------- #
class TestAnalyzeSingle:
    def test_real_wav_yields_full_fingerprint(self, tmp_path) -> None:
        path = write_wav(tmp_path / "ref.wav", seconds=3.0)
        res = analyzer.analyze_single(path)
        assert res["filename"] == "ref.wav"
        # постоянный синус — не музыка: librosa честно даёт 0 BPM. Требовать
        # «bpm > 0» значило бы требовать выдуманного значения.
        assert res["bpm"] >= 0
        assert isinstance(res["bpm"], float)
        assert res["key"].split()[1] in ("major", "minor")
        assert res["duration_sec"] == pytest.approx(3.0, abs=0.1)
        assert len(res["section_energies"]) == 8
        assert 0 <= res["drop_section"] < 8
        assert res["vibe_tags"]
        assert res["bass_ratio"] > 1.0  # 220 Гц целиком в низкой полосе

    def test_essentia_absence_is_named_not_hidden(self, tmp_path) -> None:
        # essentia в окружении нет — статус обязан это сказать
        path = write_wav(tmp_path / "ref.wav")
        res = analyzer.analyze_single(path)
        assert res["essentia_status"]["ok"] is False
        assert res["essentia"] == {}

    def test_essentia_present_adds_danceability(self, tmp_path, monkeypatch) -> None:
        # essentia в окружении нет, поэтому подставляем: важно, что при её
        # наличии дескриптор попадает в отчёт как applied, а не игнорируется.
        import sys
        import types

        class FakeEst:
            class MonoLoader:
                def __init__(self, filename=None):
                    pass

                def __call__(self):
                    return np.zeros(1000)

            class Danceability:
                def __call__(self, audio):
                    return (1.42, 0.0)

        module = types.ModuleType("essentia.standard")
        module.MonoLoader = FakeEst.MonoLoader
        module.Danceability = FakeEst.Danceability
        package = types.ModuleType("essentia")
        package.standard = module
        monkeypatch.setitem(sys.modules, "essentia", package)
        monkeypatch.setitem(sys.modules, "essentia.standard", module)

        path = write_wav(tmp_path / "ref.wav")
        res = analyzer.analyze_single(path)
        assert res["essentia_status"] == {"ok": True, "status": "applied"}
        assert res["essentia"]["danceability"] == 1.42

    def test_missing_librosa_is_an_error_not_a_guess(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(analyzer, "librosa", None)
        with pytest.raises(RuntimeError, match="librosa"):
            analyzer.analyze_single(str(tmp_path / "x.wav"))

    def test_missing_file_raises(self, tmp_path) -> None:
        with pytest.raises(Exception):
            analyzer.analyze_single(str(tmp_path / "nope.wav"))


class TestVibeAndRange:
    @pytest.mark.parametrize(
        ("bpm", "tag"),
        [
            (80, "slow"),
            (100, "mid-tempo"),
            (130, "phonk/drift"),
            (150, "trap/hype"),
            (170, "hyper/hardstyle"),
        ],
    )
    def test_bpm_tags(self, bpm, tag) -> None:
        assert tag in analyzer._infer_vibe(bpm, 2000.0, 1.0, "major")

    def test_bass_and_centroid_tags(self) -> None:
        tags = analyzer._infer_vibe(120, 1000.0, 2.5, "minor")
        assert "bass-heavy" in tags
        assert "dark" in tags
        assert "aggressive" in tags
        assert "underground" in tags

    def test_bright_centroid(self) -> None:
        assert "bright" in analyzer._infer_vibe(120, 4000.0, 1.0, "major")

    def test_no_extra_tags_for_plain_track(self) -> None:
        tags = analyzer._infer_vibe(120, 2000.0, 1.0, "major")
        assert tags == ["phonk/drift"]

    def test_bpm_range_keeps_center_and_clamps(self) -> None:
        r = analyzer._bpm_range(130.0)
        assert r["center"] == 130
        assert r["range_low"] == 124
        assert r["range_high"] == 138
        assert r["modes"]["speed_up_edits"] == 140
        assert r["modes"]["slow_lazy"] == 120

    def test_bpm_range_low_end_clamps_to_70(self) -> None:
        r = analyzer._bpm_range(60.0)
        assert r["range_low"] == 60  # max(60, 54)
        assert r["modes"]["slow_lazy"] == 70  # max(70, 55)

    def test_bpm_range_high_end_clamps_to_180(self) -> None:
        r = analyzer._bpm_range(175.0)
        assert r["modes"]["speed_up_edits"] == 180
        assert r["modes"]["club_harder"] == 180
        assert r["suggestions"]["flex_flow"] == 178


class TestAnalyzeMulti:
    @pytest.fixture()
    def fake_single(self, monkeypatch):
        def fake(path):
            return {
                "path": path,
                "filename": path,
                "bpm": 120.0 if "a" in path else 140.0,
                "bass_ratio": 1.0,
                "spectral_centroid": 2000.0,
                "key": "C minor",
                "vibe_tags": ["dark"],
            }

        monkeypatch.setattr(analyzer, "analyze_single", fake)
        saved = []
        monkeypatch.setattr(analyzer, "_save_to_vault", lambda d: saved.append(d))
        return saved

    def test_no_references_is_refused(self) -> None:
        res = analyzer.analyze_multi([])
        assert res["ok"] is False
        assert res["error"] == "no references given"

    def test_equal_weights_by_default(self, fake_single) -> None:
        res = analyzer.analyze_multi(["a.wav", "b.wav"])
        assert res["weights"] == [0.5, 0.5]
        # analyze_multi передаёт filename в отчёты; для расчёта берутся bpm обоих
        assert 120 <= res["target_bpm"] <= 140
        assert res["target_mode"] == "minor"
        assert res["sources"] == ["a.wav", "b.wav"]
        assert len(fake_single) == 1  # в хранилище записано ровно одно измерение

    def test_weights_are_normalised(self, fake_single) -> None:
        res = analyzer.analyze_multi(["a.wav", "b.wav"], weights=[3, 1])
        assert res["weights"] == [0.75, 0.25]
        assert res["target_bass_ratio"] == 1.0  # одинаковый у обоих референсов
        assert res["bpm_range"]["center"] == round(res["target_bpm"])

    def test_zero_weights_do_not_divide_by_zero(self, fake_single) -> None:
        # регрессия: было ZeroDivisionError
        res = analyzer.analyze_multi(["a.wav", "b.wav"], weights=[0, 0])
        assert res["weights"] == [0.5, 0.5]

    def test_short_weight_list_is_repaired(self, fake_single) -> None:
        # регрессия: один вес на два референса молча давал weights=[1.0].
        # Недостающий вес добирается единицей, затем всё нормируется: 0.5:1.
        res = analyzer.analyze_multi(["a.wav", "b.wav"], weights=[0.5])
        assert res["weights"][0] == pytest.approx(1 / 3, abs=1e-9)
        assert res["weights"][1] == pytest.approx(2 / 3, abs=1e-9)
        assert sum(res["weights"]) == pytest.approx(1.0)

    def test_extra_weights_are_truncated(self, fake_single) -> None:
        res = analyzer.analyze_multi(["a.wav", "b.wav"], weights=[1, 1, 1])
        assert res["weights"] == [0.5, 0.5]

    def test_take_notes_only_for_real_references(self, fake_single) -> None:
        res = analyzer.analyze_multi(
            ["a.wav", "b.wav"], take_notes=["бит отсюда", "  ", "лишняя заметка"]
        )
        assert len(res["ref_notes"]) == 1
        assert res["ref_notes"][0]["note"] == "бит отсюда"
        assert res["ref_notes"][0]["ref"] == "a.wav"

    def test_style_vector_has_all_contract_keys(self, fake_single) -> None:
        res = analyzer.analyze_multi(["a.wav", "b.wav"])
        assert set(res) >= {
            "sources",
            "weights",
            "ref_notes",
            "target_bpm",
            "target_mode",
            "target_bass_ratio",
            "target_centroid",
            "vibe_tags",
            "bpm_range",
            "individual",
        }
        assert len(res["individual"]) == 2

    def test_major_mode_by_vote(self, monkeypatch) -> None:
        monkeypatch.setattr(
            analyzer,
            "analyze_single",
            lambda p: {"filename": p, "bpm": 120.0, "bass_ratio": 1.0,
                       "spectral_centroid": 2000.0, "key": "C major",
                       "vibe_tags": []},
        )
        monkeypatch.setattr(analyzer, "_save_to_vault", lambda d: None)
        assert analyzer.analyze_multi(["a.wav"])["target_mode"] == "major"


class TestVault:
    def test_save_appends_and_survives_broken_json(self, tmp_path, monkeypatch) -> None:
        vault = tmp_path / "cache" / "analysis.json"
        monkeypatch.setattr(analyzer, "VAULT", str(vault))
        analyzer._save_to_vault({"a": 1})
        analyzer._save_to_vault({"b": 2})
        assert analyzer.list_cached_analyses() == [{"a": 1}, {"b": 2}]

        vault.write_text("{ не json", encoding="utf-8")
        analyzer._save_to_vault({"c": 3})  # битый файл не должен уронить запись
        assert analyzer.list_cached_analyses() == [{"c": 3}]

    def test_list_without_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(analyzer, "VAULT", str(tmp_path / "нет.json"))
        assert analyzer.list_cached_analyses() == []

    def test_list_with_broken_file(self, tmp_path, monkeypatch) -> None:
        broken = tmp_path / "b.json"
        broken.write_text("не json", encoding="utf-8")
        monkeypatch.setattr(analyzer, "VAULT", str(broken))
        assert analyzer.list_cached_analyses() == []


# --------------------------------------------------------------------------- #
#  MIDI
# --------------------------------------------------------------------------- #
class TestMidiGenerator:
    def test_status_names_mido_availability(self) -> None:
        status = midi_generator.MIDIGenerator.get_status()
        assert set(status) == {"ok", "engine", "reason"}
        assert status["engine"] in ("mido", "BLOCKED")
        # без mido генератор обязан честно назвать причину, а не молчать
        if not status["ok"]:
            assert status["engine"] == "BLOCKED"
            assert "mido not installed" in status["reason"]
        else:
            assert status["reason"] is None

    def test_init_sets_output_dir(self, tmp_path) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path / "midi"))
        gen._ensure_dir()
        assert (tmp_path / "midi").is_dir()

    def test_export_without_mido_refuses_not_crashes(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(midi_generator, "_HAS_MIDO", False)
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        res = gen.export_slot_pattern("drift_phonk", bpm=140, bars=2)
        assert res["ok"] is False
        assert res["status"] == "BLOCKED"
        assert "mido not installed" in res["reason"]
        # события всё равно отдаются — без них пользователь не увидит паттерн
        assert res["events"]

    def test_drum_events_cover_genre_patterns(self) -> None:
        for genre in ("drift_phonk", "trap", "boom_bap", "house", "неизвестный"):
            events = midi_generator.MIDIGenerator._drum_events(genre)
            assert isinstance(events, list)
            assert events  # паттерн не пустой даже для незнакомого жанра
            for note, vel in events:
                assert 0 <= note <= 127
                assert 0 <= vel <= 127

    def test_slot_events_for_genre_shape(self) -> None:
        res = midi_generator.slot_events_for_genre("trap", bars=4)
        assert isinstance(res, dict)
        assert res
        for slot, steps in res.items():
            assert isinstance(steps, list)
            assert all(isinstance(s, int) for s in steps)
            assert all(0 <= s < 4 * 16 for s in steps)

    def test_slot_events_respect_bars(self) -> None:
        two = midi_generator.slot_events_for_genre("drift_phonk", bars=2)
        four = midi_generator.slot_events_for_genre("drift_phonk", bars=4)
        for slot in two:
            assert len(two[slot]) <= len(four.get(slot, []))

    def test_generate_drum_pattern_without_mido_returns_empty(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(midi_generator, "_HAS_MIDO", False)
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        assert gen.generate_drum_pattern("trap", bpm=140) == ""  # BLOCKED, не исключение

    def test_generate_melody_without_mido_returns_empty(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(midi_generator, "_HAS_MIDO", False)
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        assert gen.generate_melody_pattern(genre="trap", key_root="A", mode="minor", bpm=140) == ""

    def test_export_failure_is_reported_with_status(self, tmp_path, monkeypatch) -> None:
        # mido «есть», но падает при записи — статус FAILED с причиной
        class BoomMidiFile:
            ticks_per_beat = 480

            def save(self, target):
                raise OSError("диск переполнен")

            @property
            def tracks(self):
                return []

        class FakeMido:
            @staticmethod
            def bpm2tempo(bpm):
                return 500000

            @staticmethod
            def MetaMessage(*a, **k):
                return ("meta", a, k)

        monkeypatch.setattr(midi_generator, "_HAS_MIDO", True)
        monkeypatch.setattr(midi_generator, "MidiFile", BoomMidiFile)
        monkeypatch.setattr(midi_generator, "MidiTrack", list)
        monkeypatch.setattr(midi_generator, "Message", lambda *a, **k: ("msg", a, k))
        monkeypatch.setattr(midi_generator, "mido", FakeMido)
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        res = gen.export_slot_pattern("drift_phonk", bpm=140, bars=1)
        assert res["ok"] is False
        assert res["status"] == "FAILED"
        assert "диск переполнен" in res["reason"]

    def test_drum_export_exception_returns_empty_path(self, tmp_path, monkeypatch) -> None:
        class BoomMidiFile:
            def save(self, target):
                raise OSError("нет места")

        class FakeMido:
            @staticmethod
            def bpm2tempo(bpm):
                return 500000

            @staticmethod
            def MetaMessage(*a, **k):
                return ("meta", a, k)

        monkeypatch.setattr(midi_generator, "_HAS_MIDO", True)
        monkeypatch.setattr(midi_generator, "MidiFile", BoomMidiFile)
        monkeypatch.setattr(midi_generator, "MidiTrack", list)
        monkeypatch.setattr(midi_generator, "Message", lambda *a, **k: ("msg", a, k))
        monkeypatch.setattr(midi_generator, "mido", FakeMido)
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        assert gen.generate_drum_pattern("trap", bpm=140) == ""

    def test_bars_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="bars must be positive"):
            midi_generator.slot_events_for_genre("trap", bars=0)

    def test_output_dir_created_lazily(self, tmp_path) -> None:
        target = tmp_path / "deep" / "nested"
        gen = midi_generator.MIDIGenerator(output_dir=str(target))
        assert not target.exists()  # не при импорте и не при конструировании
        gen._ensure_dir()
        assert target.is_dir()


class FakeMidoEnv:
    """Подставной mido: пишет маркер вместо настоящего .mid.

    Нужен, чтобы проверить успешные ветки записи (их 4) без установки mido:
    в окружении сборки его нет, а «успех» без проверки — это обещание.
    """

    def __init__(self):
        self.written: list[str] = []
        env = self

        class Track(list):
            pass

        class File:
            ticks_per_beat = 480

            def __init__(self):
                self.tracks = []

            def save(self, target):
                env.written.append(target)
                with open(target, "w", encoding="utf-8") as handle:
                    handle.write("MIDI")

        class MidoModule:
            @staticmethod
            def bpm2tempo(bpm):
                return int(60_000_000 / bpm)

            @staticmethod
            def MetaMessage(kind, **kw):
                return {"meta": kind, **kw}

        self.MidiFile = File
        self.MidiTrack = Track
        self.Message = lambda kind, **kw: {"msg": kind, **kw}
        self.mido = MidoModule


@pytest.fixture()
def fake_mido(monkeypatch):
    env = FakeMidoEnv()
    monkeypatch.setattr(midi_generator, "_HAS_MIDO", True)
    monkeypatch.setattr(midi_generator, "MidiFile", env.MidiFile)
    monkeypatch.setattr(midi_generator, "MidiTrack", env.MidiTrack)
    monkeypatch.setattr(midi_generator, "Message", env.Message)
    monkeypatch.setattr(midi_generator, "mido", env.mido)
    return env


class TestMidiSuccessPaths:
    def test_slot_export_writes_file(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path / "midi"))
        res = gen.export_slot_pattern("drift_phonk", bpm=140, bars=1)
        assert res["ok"] is True
        assert res["status"] == "REAL_PASS"
        assert res["slots"]
        assert res["path"].endswith("drift_phonk_1bars_slots.mid")
        assert fake_mido.written == [res["path"]]

    def test_slot_export_uses_custom_name(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        res = gen.export_slot_pattern("trap", bpm=90, bars=2, out_name="mine.mid")
        assert res["path"].endswith("mine.mid")

    def test_drum_pattern_writes_file(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        path = gen.generate_drum_pattern("trap", bpm=140)
        assert path.endswith("trap_drums.mid")
        assert fake_mido.written

    def test_drum_pattern_bpm_is_clamped(self, tmp_path, fake_mido) -> None:
        seen = {}
        original = fake_mido.mido.bpm2tempo

        def spy(bpm):
            seen["bpm"] = bpm
            return original(bpm)

        fake_mido.mido.bpm2tempo = spy
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        gen.generate_drum_pattern("trap", bpm=999)
        assert seen["bpm"] == 240  # верхняя граница

        seen.clear()
        gen.generate_drum_pattern("trap", bpm=10)
        assert seen["bpm"] == 40  # нижняя граница

    def test_genre_is_sanitised_in_filename(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        path = gen.generate_drum_pattern("../../evil genre", bpm=120)
        assert "evil" in path and ".." not in path

    def test_melody_minor_scale_written(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        path = gen.generate_melody_pattern(genre="trap", key_root="A", mode="minor")
        assert path.endswith("trap_melody.mid")

    def test_melody_major_scale_written(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        path = gen.generate_melody_pattern(genre="pop", key_root="C", mode="major")
        assert path.endswith("pop_melody.mid")

    def test_unknown_key_falls_back_to_a(self, tmp_path, fake_mido) -> None:
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        seen = []
        original = fake_mido.Message

        def spy(kind, **kw):
            if kind == "note_on":
                seen.append(kw["note"])
            return original(kind, **kw)

        midi_generator.Message = spy
        try:
            gen.generate_melody_pattern(genre="pop", key_root="Q", mode="minor")
        finally:
            midi_generator.Message = original
        # A4 = 69 → нота не выше 69+12
        assert seen and max(seen) <= 81

    def test_melody_failure_returns_empty(self, tmp_path, monkeypatch) -> None:
        class BoomFile:
            ticks_per_beat = 480

            def __init__(self):
                self.tracks = []

            def save(self, target):
                raise OSError("нет места")

        env = FakeMidoEnv()
        monkeypatch.setattr(midi_generator, "_HAS_MIDO", True)
        monkeypatch.setattr(midi_generator, "MidiFile", BoomFile)
        monkeypatch.setattr(midi_generator, "MidiTrack", list)
        monkeypatch.setattr(midi_generator, "Message", env.Message)
        monkeypatch.setattr(midi_generator, "mido", env.mido)
        gen = midi_generator.MIDIGenerator(output_dir=str(tmp_path))
        assert gen.generate_melody_pattern(genre="trap") == ""


class TestCommandLine:
    def test_module_cli_without_args_prints_usage(self, monkeypatch, capsys) -> None:
        import runpy

        monkeypatch.setattr("sys.argv", ["analyzer.py"])
        # кода выхода по ТЗ нет: без аргументов печатается подсказка
        runpy.run_module("modules.analyzer", run_name="__main__")
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_module_cli_with_one_file_analyzes_it(self, monkeypatch, capsys, tmp_path) -> None:
        import runpy

        path = write_wav(tmp_path / "one.wav", seconds=2.0)
        monkeypatch.setattr("sys.argv", ["analyzer.py", path])
        runpy.run_module("modules.analyzer", run_name="__main__")
        payload = json.loads(capsys.readouterr().out)
        assert payload["filename"] == "one.wav"
