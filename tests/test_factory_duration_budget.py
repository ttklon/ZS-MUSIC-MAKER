"""Evolution may alter sound, but not the user's render duration budget."""
import copy
import json
import random

import pytest

from modules.hit_factory.evolver import mutate


def test_mutation_preserves_duration_across_seeds_and_lengths():
    for duration in (4, 10, 15, 30, 45, 65, 90, 120, 180):
        recipe = {"genre": "trap", "seed": 42, "bpm_override": 140,
                  "aggression": .7, "duration_sec": duration}
        original = copy.deepcopy(recipe)
        for seed in range(100):
            result = mutate(recipe, None, random.Random(seed))
            assert result["duration_sec"] == duration
        assert recipe == original


def test_former_duration_mutation_branch_cannot_override_request():
    class AlwaysMutate(random.Random):
        def random(self):
            return 0.0

    result = mutate({"genre": "trap", "seed": 42, "duration_sec": 33}, rng=AlwaysMutate(1))
    assert result["duration_sec"] == 33
    assert result["seed"] != 42


def test_absent_duration_is_not_replaced_with_arbitrary_length():
    for seed in range(30):
        assert "duration_sec" not in mutate({"genre": "trap", "seed": 42}, rng=random.Random(seed))


def test_duration_preservation_remains_seed_deterministic():
    recipe = {"genre": "trap", "seed": 42, "duration_sec": 15}
    assert mutate(recipe, rng=random.Random(5)) == mutate(recipe, rng=random.Random(5))


@pytest.mark.parametrize("duration", [15, 45])
def test_factory_preserves_duration_in_all_attempts_and_summary(tmp_path, monkeypatch, duration):
    from modules.hit_factory import generator

    monkeypatch.setattr(generator, "_maybe_auto_genre", lambda genre, theme: genre)
    monkeypatch.setattr("modules.hit_factory.kpi.build_kpi", lambda *a, **kw: {})
    factory = generator.HitFactory(output_root=tmp_path, adaptive=False, max_attempts=4, verbose=False)
    observed = []

    def render(project_id, state, rng):
        observed.append(copy.deepcopy(state))
        return {"project_id": project_id, "out_root": str(tmp_path), "master_path": None,
                "hit_score": 40, "verdict": "needs_work", "report": {"verdict": "PARTIAL"}}

    monkeypatch.setattr(factory, "_run_pipeline_once", render)
    factory.make_one(genre="trap", theme="test", seed=42, duration_sec=duration)
    assert len(observed) == 4
    assert all(state["duration_sec"] == duration for state in observed)
    assert len({state["seed"] for state in observed}) == 4
    summary = json.loads((tmp_path / "factory_summary.json").read_text())
    assert all(row["wizard_state"]["duration_sec"] == duration for row in summary["attempts"])
