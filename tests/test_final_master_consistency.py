"""Один мастер на всё: измерено то же, что измеряется и публикуется.

Регрессия, найденная сквозным аудитом 42.0.11. Хит-фабрика вызывала
`_enhance_master` уже **после** `run_full_pipeline`: файл на диске менялся,
когда hit-score, релизный пакет и `artifact_integrity` были посчитаны по
прежним байтам. Пользователь получал трек с громкостью и звуком, которых нет
ни в одном отчёте, а `hit_report.md` показывал 66.94 против 66.4 в сводке.

Второй слой той же ошибки: `polished.wav` (результат anti-neuro цепочки) не
читал никто — стемы, hit-score и релиз смотрели на сырой streaming-мастер.

Эти тесты держат инвариант: стадии `_stage_stems` и `_stage_hit_score`, а
также релизный пакет получают **один и тот же** путь, и это финальный
мастер после полировки.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from app.core import pipeline_blocks
from app.pipeline import StageResult, StageStatus

ROOT = Path(__file__).resolve().parents[1]


def _wav(path: Path, value: float = 0.1) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, value * np.sin(np.arange(8000) * 0.1), 8000)
    return str(path)


def _fake_polish(src: str, out_root: Path) -> dict[str, Any]:
    """Полировка, которая реально создаёт новый файл, как настоящая стадия."""
    target = Path(out_root) / "polished.wav"
    shutil.copy(src, target)
    return {"ok": True, "path": str(target), "engine": "test.polish"}


def test_stems_and_hit_score_read_polished_master(tmp_path, monkeypatch):
    seen: dict[str, str] = {}

    def stems(master: str, out_root: Path) -> dict[str, Any]:
        seen["stems"] = master
        return {"ok": True, "stems": {}}

    def hit(master: str) -> dict[str, Any]:
        seen["hit"] = master
        return {"ok": True, "hit_score": 50.0}

    monkeypatch.setattr(pipeline_blocks, "_stage_polish", _fake_polish)
    monkeypatch.setattr(pipeline_blocks, "_stage_stems", stems)
    monkeypatch.setattr(pipeline_blocks, "_stage_hit_score", hit)

    raw_master = _wav(tmp_path / "masters" / "streaming.wav")
    stages = pipeline_blocks._run_post_master_stages(
        raw_master, {"export_stems": True, "enhanced_dsp": False}, tmp_path, None
    )

    polished = str(tmp_path / "polished.wav")
    assert seen["hit"] == polished, "hit-score обязан мерить финальный мастер"
    assert seen["stems"] == polished, "стемы обязаны резать финальный мастер"
    assert seen["hit"] != raw_master
    assert [s.name for s in stages] == [
        "_stage_polish",
        "_stage_stems",
        "_stage_auto_qa",
        "_stage_hit_score",
    ]


def test_adaptive_enhance_is_disabled_for_neural_engines(tmp_path):
    """Если бит считала нейросеть, ручной DSP не должен «дорисовывать» мастер."""
    from app.core.stages.master import apply_adaptive_enhance

    master = _wav(tmp_path / "m.wav", value=0.5)
    before = Path(master).read_bytes()
    result = apply_adaptive_enhance(master, adaptive_level=2, enhanced_dsp=True)
    assert result["applied"] is False
    assert Path(master).read_bytes() == before


def test_adaptive_enhance_reports_reason_when_disabled(tmp_path):
    from app.core.stages.master import apply_adaptive_enhance

    master = _wav(tmp_path / "m2.wav", value=0.5)
    before = Path(master).read_bytes()
    result = apply_adaptive_enhance(master, adaptive_level=0, enhanced_dsp=False)
    assert result["applied"] is False
    assert "disabled" in result["reason"]
    assert Path(master).read_bytes() == before


def test_orchestrator_release_receives_final_master(tmp_path, monkeypatch):
    """Сквозная проверка через `run_full_pipeline`: релиз видит финальный мастер.

    Подменяем все стадии макетами, поэтому тест быстрый и не рендерит звук —
    проверяется только то, какой путь получает релизный пакет.
    """
    from app.core import orchestrator

    raw = _wav(tmp_path / "render" / "masters" / "streaming.wav", value=0.2)
    polished = _wav(tmp_path / "render" / "polished.wav", value=0.3)
    released: list[str] = []

    def fake(stage_name, **kwargs):
        return {"ok": True, "blocked": True, "reason": "mock"}

    monkeypatch.setattr(orchestrator, "_prepare_run", lambda *a, **k: (
        # полный набор полей, которые читает отчёт (иначе KeyError дальше)
        {"genre": "house", "theme": "тест", "artist": "Test", "export_stems": False,
         "stands": ["streaming"], "quality_mode": "quality", "n_verses": 2,
         "voice_mode": "pro", "seed": 1, "duration_sec": 5, "bpm_override": None,
         "refs": [], "preset": None},
        tmp_path / "render", None, (None, None),
    ))
    monkeypatch.setattr(orchestrator, "_attach_agent_context", lambda recipe: {})
    monkeypatch.setattr(pipeline_blocks, "_run_input_stages", lambda *a, **k: (
        StageResult(name="_stage_analyze", status=StageStatus.OK, output={"ok": True}),
        StageResult(name="_stage_groove", status=StageStatus.OK, output={"ok": True}),
        {}, {},
    ))
    monkeypatch.setattr(orchestrator, "_run_arrangement_stage", lambda *a, **k:
                        StageResult(name="_stage_arrangement", status=StageStatus.OK, output={"ok": True}))
    monkeypatch.setattr(orchestrator, "build_arrangement_plan", lambda *a, **k: {})
    monkeypatch.setattr(pipeline_blocks, "_run_beat_stage", lambda *a, **k:
                        StageResult(name="_stage_beat", status=StageStatus.OK, output={"ok": True, "path": raw}))
    monkeypatch.setattr(orchestrator, "_run_texture_stage", lambda *a, **k:
                        StageResult(name="_stage_texture", status=StageStatus.OK, output={"ok": True}))
    monkeypatch.setattr(pipeline_blocks, "_run_lyrics_text_stage", lambda *a, **k:
                        StageResult(name="_stage_lyrics", status=StageStatus.OK, output={"ok": True}))
    monkeypatch.setattr(pipeline_blocks, "_run_vocal_stages", lambda *a, **k: ([], None, []))
    monkeypatch.setattr(pipeline_blocks, "_run_mix_stage", lambda *a, **k:
                        StageResult(name="_stage_mix_and_sidechain", status=StageStatus.OK,
                                                    output={"ok": True, "out_wav": raw}))
    monkeypatch.setattr(orchestrator, "_run_mastering_stage", lambda *a, **k:
                        StageResult(name="_stage_mastering", status=StageStatus.OK,
                                                    output={"ok": True, "masters": {"streaming": raw}}))
    monkeypatch.setattr(pipeline_blocks, "_run_post_master_stages", lambda *a, **k: [
        StageResult(name="_stage_polish", status=StageStatus.OK, output={"ok": True, "path": polished}),
        StageResult(name="_stage_stems", status=StageStatus.OK, output={"ok": True}),
        StageResult(name="_stage_hit_score", status=StageStatus.OK, output={"ok": True, "hit_score": 50}),
    ])
    monkeypatch.setattr(pipeline_blocks, "_run_release_stage",
                        lambda master, *a, **k: released.append(str(master))
                        or StageResult(name="_stage_release_pack", status=StageStatus.OK, output={"ok": True}))
    monkeypatch.setattr(orchestrator, "_write_report", lambda *a, **k: None)

    orchestrator.run_full_pipeline("mock-id", {"genre": "house"}, out_root=tmp_path / "render")

    assert released == [polished], f"релиз получил не тот мастер: {released}"


def test_crest_gate_measures_same_metric_as_optimiser():
    """Гейт и оптимизатор обязаны говорить об одном числе.

    `_converge_loudness`/`_control_crest` правят `reference_crest_db` (самый
    громкий участок), а гейт раньше судил по сквозному `crest_db`: мастер с
    reference 13.34 дБ считался провалившим коридор 8…14 по 14.46 дБ.
    """
    from modules.dsp import metrics

    sr = 8000
    # тихая часть + громкая с редкими пиками: сквозной crest и crest самого
    # громкого участка расходятся именно на таком материале
    quiet = 0.02 * np.sin(np.arange(sr * 6) * 0.05)
    loud = 0.1 * np.sin(np.arange(sr * 6) * 0.05)
    loud[::797] = 0.9
    signal = np.concatenate([quiet, loud])
    report = metrics.loudness_report(signal, sr)

    assert "reference_crest_db" in report
    # в отчёте значение округлено до 0.01 дБ
    assert round(metrics.reference_crest_db(signal, sr), 2) == report["reference_crest_db"]
    # метрики действительно разные величины, а не дубликат
    assert report["crest_db"] > report["reference_crest_db"]
