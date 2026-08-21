# -*- coding: utf-8 -*-
"""ZS Music Maker - tests/test_ai_layer.py (v38): smoke AI-слоя."""
import os, shutil, tempfile, unittest
from pathlib import Path


class TestRegistry(unittest.TestCase):
    def test_roles(self):
        from app.ai.registry import MODEL_REGISTRY, registry
        exp = {"lyrics_llm","analysis_llm","metadata_llm","music_generation",
               "music_stereo","tts_vocal","vocal_rvc","stem_splitter","asr",
               "audio_tagger","essentia","cover_art","mastering_ai"}
        self.assertTrue(exp.issubset(set(MODEL_REGISTRY.keys())))
        self.assertGreaterEqual(registry.hw.vram_gb, 8.0)
    def test_status(self):
        from app.ai.registry import registry
        st = registry.status()
        self.assertIn("registry", st)
        self.assertIsNone(st["current"])
    def test_essentia_avail(self):
        from app.ai.registry import registry
        self.assertTrue(registry.is_available("essentia"))


class TestRunner(unittest.TestCase):
    def test_pure(self):
        from app.ai.sequential_runner import SequentialAIRunner, AIStage
        r = SequentialAIRunner()
        r.add(AIStage("pure", None, lambda h,c: {"v":1}))
        rep = r.run({}).to_dict()
        self.assertTrue(rep["stages"][0]["ok"])
    def test_skip(self):
        from app.ai.sequential_runner import SequentialAIRunner, AIStage
        r = SequentialAIRunner()
        r.add(AIStage("x", "lyrics_llm", lambda h,c: "nope", optional=True, fallback_fn=False))
        rep = r.run({}).to_dict()
        self.assertTrue(rep["stages"][0]["ok"])
        self.assertIn("unavailable", rep["stages"][0]["skipped_reason"])
    def test_fallback(self):
        from app.ai.sequential_runner import SequentialAIRunner, AIStage
        calls = []
        r = SequentialAIRunner()
        r.add(AIStage("y", "lyrics_llm", lambda h,c: calls.append(h) or "ok",
                      optional=True, fallback_fn=True))
        rep = r.run({}).to_dict()
        self.assertTrue(rep["stages"][0]["ok"])
        self.assertEqual(calls, [None])


class TestDossier(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="zsmm_d_"))
    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
    def test_add_list(self):
        from modules.artist_dossier import DossierManager
        mgr = DossierManager(root=self.tmp)
        mgr.add_artist("Artist X", tracks=[
            {"title":"A","lyrics":"ветер северный"},
            {"title":"B","lyrics":"ночь горит"}])
        arts = mgr.list_artists()
        self.assertEqual(len(arts), 1)
        self.assertEqual(arts[0]["tracks"], 2)
        titles = sorted(t["title"] for t in mgr.list_tracks("Artist X"))
        self.assertEqual(titles, ["A","B"])
    def test_dossier_deferred(self):
        from modules.artist_dossier import DossierManager
        mgr = DossierManager(root=self.tmp)
        mgr.add_artist("Artist Y", tracks=[{"title":"S1","lyrics":"движ и жизнь"}])
        d = mgr.build_full_dossier("Artist Y")
        self.assertIn("note", d)


class TestOrchestrator(unittest.TestCase):
    def test_dry(self):
        from app.core.orchestrator_ai import run_ai_pipeline
        out = run_ai_pipeline("test_ai_dry",
            {"genre":"phonk","theme":"dry","bpm":130,"duration_sec":5},
            dry_run=True)
        self.assertIn("report", out)
        self.assertGreaterEqual(len(out["report"]["stages"]), 8)
        for st in out["report"]["stages"]:
            self.assertTrue(st["ok"] or st["skipped_reason"],
                msg=f"stage {st['name']} unexpected fail: {st}")


if __name__ == "__main__":
    unittest.main()
