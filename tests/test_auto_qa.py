"""`modules/auto_qa.py` — авто-приёмка финального мастера («три уха»).

Модуль объявлен частью ТЗ 20.2 п.34, но покрыт не был. При написании тестов
нашлись два дефекта, оба видны пользователю:

- `audit_track` писал отчёт в `output/auto_qa/`, не создавая каталог (в чистой
  установке `output/` в git нет) — удачный аудит завершался `FileNotFoundError`;
- `_structure_check` на коротком фрагменте возвращал только
  `hook_score`/`sections_detected` без `error`, а ниже `audit_track` читает
  `result["structure"]["error"]` → `KeyError`, громкость помечалась как
  `loudness_error` и вердикт врал: «готов к релизу» на нераспознанной структуре.

Плюс уточнение контракта: отчёт об аудите — диагностика, а `ok` теперь значит
«аудит проведён и записан», а не «трек хорош». Раньше `ok=true` стоял рядом с
`verdict=rebuild`.

Кроме того `analyze_track` из `modules.ai_detector_pro` возвращает `error` в
словаре и не бросает — раньше это молча давало `neuronoshnost 0 %`, то есть
«нейросети не найдено» на треке, который не анализировали. Теперь это отдельная
запись в `actions` с явной причиной.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf

from modules import auto_qa


@pytest.fixture(autouse=True)
def qa_dir(tmp_path, monkeypatch):
    """Отчёты в tmp: не мусорим в output/ и не зависим от прошлых прогонов."""
    d = tmp_path / "qa"
    monkeypatch.setattr(auto_qa, "QA_DIR", d)
    return d


@pytest.fixture()
def track(tmp_path):
    def _make(name: str = "master.wav", seconds: float = 24.0, amp: float = 0.5) -> str:
        sr = 22050
        t = np.arange(int(sr * seconds)) / sr
        y = amp * np.sin(2 * np.pi * 110 * t)
        # разные секции: чтобы корреляция окон была не единичной
        y[int(len(y) / 2) :] *= 0.4
        path = tmp_path / name
        sf.write(str(path), y.astype("float32"), sr)
        return str(path)

    return _make


class TestLoudness:
    def test_silence_is_floor_values(self) -> None:
        res = auto_qa._loudness(np.zeros(1000, dtype="float32"), 22050)
        assert res["peak_db"] < -100
        assert res["crest_factor_db"] >= 0.0

    def test_loud_signal_values(self) -> None:
        y = np.full(1000, 0.5, dtype="float32")
        res = auto_qa._loudness(y, 22050)
        assert res["peak_db"] == pytest.approx(-6.02, abs=0.05)
        assert res["rms_db"] == pytest.approx(-6.02, abs=0.05)
        assert res["crest_factor_db"] == pytest.approx(0.0, abs=0.05)
        assert res["lufs_approx"] == pytest.approx(-9.02, abs=0.05)

    def test_stereo_is_mixed_to_mono(self) -> None:
        mono = np.full(500, 0.5, dtype="float32")
        stereo = np.stack([mono, mono], axis=1)
        assert auto_qa._loudness(stereo, 22050) == auto_qa._loudness(mono, 22050)

    def test_empty_audio_does_not_raise(self) -> None:
        res = auto_qa._loudness(np.zeros(0, dtype="float32"), 22050)
        assert res["peak_db"] < -100


class TestStructure:
    def test_short_track_reports_error_not_silent(self) -> None:
        # регрессия: без ключа error ниже падало KeyError
        res = auto_qa._structure_check(np.zeros(1000, dtype="float32"), 22050)
        assert res["hook_score"] == 0.0
        assert "error" in res
        assert "too short" in res["error"]

    def test_20_second_track_is_still_too_short(self) -> None:
        # Порог — 24 с (24 с уже проходят, 20 с нет); граница названа в тексте.
        sr = 22050
        y = np.tile(np.linspace(0.05, 1.0, 512), sr * 20 // 512 + 1)[: sr * 20]
        res = auto_qa._structure_check(y, sr)
        assert "too short" in res["error"]
        assert res["hook_score"] == 0.0

    def test_long_track_scores_hook(self, track) -> None:
        y, sr = sf.read(track(seconds=60.0))
        res = auto_qa._structure_check(y, sr)
        assert "error" not in res
        assert res["sections_detected"] > 3
        assert -1.0 <= res["hook_score"] <= 1.0

    def test_repeated_sections_are_highly_correlated(self) -> None:
        # 60 с: проверке хука нужно минимум 3 окна по 8 с (24 с аудио).
        sr = 22050
        block = np.tile(np.linspace(0.05, 1.0, 512), 44100 // 512 + 1)[:44100]
        y = np.tile(np.concatenate([block] * 2), 8)[: sr * 60]
        res = auto_qa._structure_check(y, sr)
        assert "error" not in res
        assert res["sections_detected"] > 3
        assert res["hook_score"] > 0.9

    def test_garbage_input_returns_error(self) -> None:
        res = auto_qa._structure_check("не аудио", 22050)
        assert res["hook_score"] == 0.0
        assert res["error"]


class TestAuditTrack:
    def test_missing_file_refused(self, tmp_path) -> None:
        res = auto_qa.audit_track(tmp_path / "nope.wav")
        assert res["ok"] is False
        assert "не найден" in res["error"]

    def test_report_directory_created(self, track, qa_dir) -> None:
        # регрессия: в чистой установке output/ отсутствует
        assert not qa_dir.exists()
        res = auto_qa.audit_track(track())
        assert res["ok"] is True, res.get("error")
        assert qa_dir.is_dir()
        saved = json.loads(open(res["report_path"], encoding="utf-8").read())
        assert saved["verdict"] == res["verdict"]

    def test_report_is_written_as_json(self, track) -> None:
        res = auto_qa.audit_track(track())
        data = json.loads(open(res["report_path"], encoding="utf-8").read())
        assert set(data) >= {"master", "ts", "ok", "actions", "verdict"}
        assert data["ok"] is True
        assert data["report_path"] == res["report_path"]

    def test_quiet_track_asks_for_mastering(self, track) -> None:
        res = auto_qa.audit_track(track(amp=0.02))
        targets = [a["target"] for a in res["actions"]]
        assert "mastering" in targets
        assert res["verdict"] in ("patch", "rebuild")
        assert "target" in res["actions"][0]

    def test_loud_track_flags_peaks(self, track) -> None:
        res = auto_qa.audit_track(track(amp=1.0))
        reasons = " ".join(a["reason"] for a in res["actions"])
        assert "Клиппинг" in reasons

    def test_structure_error_does_not_break_audit(self, track, monkeypatch) -> None:
        # регрессия: KeyError в structure превращал аудит громкости в ошибку
        monkeypatch.setattr(
            auto_qa, "_structure_check", lambda y, sr: {"hook_score": 0.0, "error": "boom"}
        )
        res = auto_qa.audit_track(track())
        assert res["ok"] is True
        assert "loudness_error" not in res
        # провал структуры называется своим именем, а не «нет хука»
        assert any(a["target"] == "structure" for a in res["actions"])
        assert not any(a["target"] == "beat" for a in res["actions"])

    def test_hook_action_mentions_beat(self, track) -> None:
        res = auto_qa.audit_track(track())
        beat_actions = [a for a in res["actions"] if a["target"] == "beat"]
        if beat_actions:  # зависит от синтетики, но формат проверяем всегда
            assert "хук" in beat_actions[0]["reason"]

    def test_ai_detector_result_attached(self, track) -> None:
        res = auto_qa.audit_track(track())
        assert "ai_detector" in res

    def test_ai_detector_error_is_reported_as_action(self, track, monkeypatch) -> None:
        from modules import ai_detector_pro

        monkeypatch.setattr(
            ai_detector_pro, "analyze_track", lambda p: {"error": "нет librosa"}
        )
        res = auto_qa.audit_track(track())
        assert res["ai_detector"]["error"] == "нет librosa"
        assert any(a["target"] == "ai_detector" for a in res["actions"])
        assert any("нет librosa" in a["reason"] for a in res["actions"])

    def test_empty_detector_result_is_not_a_verdict(self, track, monkeypatch) -> None:
        from modules import ai_detector_pro

        monkeypatch.setattr(ai_detector_pro, "analyze_track", lambda p: {})
        res = auto_qa.audit_track(track())
        assert any(a["target"] == "ai_detector" for a in res["actions"])

    def test_high_neuronoshnost_asks_voice(self, track, monkeypatch) -> None:
        from modules import ai_detector_pro

        monkeypatch.setattr(
            ai_detector_pro, "analyze_track", lambda p: {"neuronoshnost_percent": 82}
        )
        res = auto_qa.audit_track(track())
        assert any(a["target"] == "voice" for a in res["actions"])

    def test_medium_neuronoshnost_asks_humanization(self, track, monkeypatch) -> None:
        from modules import ai_detector_pro

        monkeypatch.setattr(
            ai_detector_pro, "analyze_track", lambda p: {"neuroness_percent": 55}
        )
        res = auto_qa.audit_track(track())
        targets = [a["target"] for a in res["actions"]]
        assert "vocal_humanization" in targets

    def test_low_neuronoshnost_adds_no_voice_action(self, track, monkeypatch) -> None:
        from modules import ai_detector_pro

        monkeypatch.setattr(
            ai_detector_pro, "analyze_track", lambda p: {"neuronoshnost_percent": 10}
        )
        res = auto_qa.audit_track(track())
        assert not any(a["target"] in ("voice", "vocal_humanization") for a in res["actions"])

    def test_sample_rate_passed_to_loudness(self, track, monkeypatch) -> None:
        seen = {}
        real = auto_qa._loudness

        def spy(y, sr):
            seen["sr"] = sr
            return real(y, sr)

        monkeypatch.setattr(auto_qa, "_loudness", spy)
        auto_qa.audit_track(track())
        assert seen["sr"] == 22050

    def test_unreadable_master_reports_loudness_error(self, tmp_path) -> None:
        bad = tmp_path / "bad.wav"
        bad.write_bytes(b"not audio")
        res = auto_qa.audit_track(bad)
        assert "loudness_error" in res
        assert res["ok"] is True  # аудит проведён и записан
        assert res["verdict"] in ("patch", "rebuild")  # но метрик нет — не release


class TestVerdict:
    def _audit(self, track, monkeypatch, **kw):
        from modules import ai_detector_pro

        monkeypatch.setattr(ai_detector_pro, "analyze_track", lambda p: {})
        return auto_qa.audit_track(track(**kw))

    def test_release_when_no_actions(self, track, monkeypatch) -> None:
        from modules import ai_detector_pro

        # без оценки детектора «релиза» быть не может — даёт 20 %
        monkeypatch.setattr(
            ai_detector_pro, "analyze_track", lambda p: {"neuronoshnost_percent": 20}
        )
        monkeypatch.setattr(auto_qa, "_structure_check", lambda y, sr: {"hook_score": 0.9})
        monkeypatch.setattr(
            auto_qa,
            "_loudness",
            lambda y, sr: {"peak_db": -1.0, "rms_db": -12.0, "lufs_approx": -9.0,
                           "crest_factor_db": 11.0},
        )
        res = auto_qa.audit_track(track())
        assert res["verdict"] == "release"
        assert "Готов к релизу" in res["verdict_text"]


class TestShouldRetry:
    def test_release_stops_loop(self) -> None:
        assert auto_qa.should_retry({"verdict": "release"}) == (False, [])

    def test_patch_returns_targets(self) -> None:
        report = {
            "verdict": "patch",
            "actions": [{"target": "mastering"}, {"target": "mastering"}, {"target": "beat"}],
        }
        retry, targets = auto_qa.should_retry(report)
        assert retry is True
        assert sorted(targets) == ["beat", "mastering"]

    def test_iteration_limit_stops_loop(self) -> None:
        report = {"verdict": "rebuild", "actions": [{"target": "beat"}]}
        assert auto_qa.should_retry(report, max_iterations=2, current_iter=2) == (False, [])

    def test_iteration_limit_allows_earlier(self) -> None:
        report = {"verdict": "rebuild", "actions": [{"target": "beat"}]}
        assert auto_qa.should_retry(report, max_iterations=2, current_iter=1) == (True, ["beat"])

    def test_report_without_actions(self) -> None:
        assert auto_qa.should_retry({"verdict": "patch"}) == (True, [])
