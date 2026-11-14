"""T11: режим качества (Fast/Quality/Max) реально влияет на результат.

Гейт из `docs/IMPROVEMENT_PLAN.md`. До этой доработки `quality_mode` сохранялся
в рецепт вместе с `quality_profile`, но ни один модуль его не читал: переключатель
в визарде ничего не менял, а отчёт показывал «настройка применена».

Проверяются три достижимые из пайплайна точки:
1. MusicGen — размер модели через `choose_size(vram, quality_mode)`;
2. мастеринг — число итераций доводки громкости (`iterations → search_iterations`);
3. RVC — число эпох дотрена (`epochs=` перекрывает профиль).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from app.core.recipe import QUALITY_PROFILES, build_recipe


# --------------------------------------------------------------- рецепт/профили
def test_profiles_expose_the_knobs_the_pipeline_reads() -> None:
    for mode in ("fast", "quality", "max"):
        profile = QUALITY_PROFILES[mode]
        assert "mastering_iterations" in profile, (mode, profile)
        assert profile["mastering_iterations"] >= 1

    iterations = [QUALITY_PROFILES[mode]["mastering_iterations"] for mode in ("fast", "quality", "max")]
    assert iterations == sorted(iterations) and len(set(iterations)) == 3, iterations


def test_recipe_carries_profile_without_duplication() -> None:
    recipe = build_recipe({"quality_mode": "max"})

    assert recipe["quality_mode"] == "max"
    assert recipe["quality_profile"]["mastering_iterations"] == QUALITY_PROFILES["max"]["mastering_iterations"]


# --------------------------------------------------------------- 1) MusicGen
def test_musicgen_size_follows_quality_mode() -> None:
    from app.core.musicgen_texture import choose_size

    assert choose_size(24.0, "max") == "large"
    assert choose_size(24.0, "fast") == "medium"
    assert choose_size(8.0, "quality") == "medium"
    assert choose_size(8.0, "fast") == "small"
    # на CPU режим не может «поднять» модель выше доступной памяти
    assert choose_size(0.0, "max") == "small"


def test_texture_stage_passes_quality_mode_to_engine(monkeypatch, tmp_path) -> None:
    """`_stage_texture` обязана передать режим в MusicGen, а не глотать его."""
    from app.core import musicgen_texture
    from app.core.stages import texture as texture_stage

    seen: dict = {}

    def fake_generate(prompt, **kwargs):
        seen.update(kwargs)
        out = tmp_path / "neural.wav"
        out.write_bytes(b"RIFF")
        return {"ok": True, "path": str(out), "size": "large"}

    monkeypatch.setattr(
        texture_stage,
        "_texture_device_plan",
        lambda *a, **k: {"ready": True, "device": "cuda", "vram_gb": 15.0},
    )
    monkeypatch.setattr(musicgen_texture, "generate_texture", fake_generate)
    monkeypatch.setattr(musicgen_texture, "unload_all", lambda: None)

    result = texture_stage._stage_texture("drift atmosphere", tmp_path, quality_mode="max")

    assert result["ok"] is True
    assert seen.get("quality_mode") == "max", seen


# --------------------------------------------------------------- 2) мастеринг
def test_master_one_accepts_iterations_and_defaults_to_six(monkeypatch, tmp_path) -> None:
    from modules.mastering import chain

    calls: list[int | None] = []
    real = chain._converge_loudness

    def spy(*args, **kwargs):
        calls.append(kwargs.get("search_iterations"))
        return real(*args, **kwargs)

    monkeypatch.setattr(chain, "_converge_loudness", spy)
    sr = 44100
    t = np.arange(sr) / sr
    y = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    import soundfile as sf

    tmp = tmp_path
    mix_path = str(tmp / "mix.wav")
    sf.write(mix_path, np.stack([y, y], axis=1), sr)

    chain.master_one(mix_path, str(tmp / "a.wav"), stand="streaming")
    assert calls and all(value == 6 for value in calls), calls

    calls.clear()
    chain.master_one(mix_path, str(tmp / "b.wav"), stand="streaming", iterations=1)
    assert calls and all(value == 1 for value in calls), calls


def test_master_all_stands_forwards_iterations(monkeypatch, tmp_path) -> None:
    from modules.mastering import stands as stands_mod

    seen: list[int | None] = []

    def fake_master(mix_wav, out_wav, stand="streaming", iterations=None):
        seen.append(iterations)
        return {"ok": True, "path": out_wav, "gates": {"true_peak": True}, "gates_passed": True,
                "report": {}}

    monkeypatch.setattr(stands_mod, "_current_master_one", lambda: fake_master)

    stands_mod.master_all_stands("mix.wav", str(tmp_path), stands=["streaming", "car"], iterations=3)

    assert seen == [3, 3], seen


def test_stage_mastering_passes_iterations_from_profile(monkeypatch, tmp_path) -> None:
    from app.core.stages import master as master_stage
    from modules import mastering

    seen: dict = {}

    def fake_all(mix_wav, out_dir, stands=None, iterations=None):
        seen["iterations"] = iterations
        seen["stands"] = stands
        return {"ok": True, "masters": {"streaming": "m.wav"}, "summary": {"fallback": 0}}

    monkeypatch.setattr(mastering, "master_all_stands", fake_all)

    result = master_stage._stage_mastering(
        "mix.wav", tmp_path, stands=["car"], iterations=5
    )

    assert seen["iterations"] == 5
    assert result["ok"] is True


# --------------------------------------------------------------- 3) RVC-эпохи
def test_retrain_incremental_epochs_override(tmp_path) -> None:
    from modules import rvc_trainer

    manifest = tmp_path / "voice_manifest.json"
    manifest.write_text(
        json.dumps({"n_items": 4, "total_sec": 12, "items": []}), encoding="utf-8"
    )

    quick = rvc_trainer.retrain_incremental(str(manifest), mode="quick", dry_run=True)
    fast = rvc_trainer.retrain_incremental(str(manifest), mode="quick", dry_run=True, epochs=12)

    assert quick["plan"]["epochs"] == rvc_trainer.DEFAULT_EPOCHS_QUICK
    assert fast["plan"]["epochs"] == 12
    assert fast["plan"]["quality_profile_epochs"] == rvc_trainer.DEFAULT_EPOCHS_QUICK


def test_retrain_incremental_rejects_nonsense_epochs(tmp_path) -> None:
    from modules import rvc_trainer

    manifest = tmp_path / "voice_manifest.json"
    manifest.write_text(json.dumps({"n_items": 1, "total_sec": 3, "items": []}), encoding="utf-8")

    with pytest.raises(ValueError):
        rvc_trainer.retrain_incremental(str(manifest), mode="quick", dry_run=True, epochs=0)
