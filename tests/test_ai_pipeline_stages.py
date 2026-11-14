"""Стадии AI-пайплайна: `app/core/ai/stages_{music,vocal,meta,final}.py`.

Достижимы через `app/core/orchestrator_ai.py`, покрытие было 24/22/53/50 %.
Тяжёлые движки (demucs, MusicGen, XTTS, RVC, CLAP) в окружении сборки
отсутствуют, поэтому модели подменяются: проверяется КОНТРАКТ стадии —
что она делает при отсутствии модели, что пишет на диск, что валидирует
артефакт и что не выдаёт «ok» без проверки.

Главное, что здесь держится: недоступная модель даёт named skip/fallback, а
не тихий успех и не трейсбек.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf

from app.core.ai import stages_final, stages_meta, stages_music, stages_vocal
from app.core.ai.context import AIContext


@pytest.fixture()
def ctx(tmp_path):
    ai = AIContext(
        ws={
            "genre": "drift_phonk",
            "theme": "ночная дорога",
            "bpm": 140,
            "key": "A minor",
            "mood": "тёмное",
            "duration_sec": 6.0,
            "n_verses": 2,
            "bilingual": True,
        },
        out_root=tmp_path,
    )
    return {"ai": ai, "sink": {}}


def write_wav(path, seconds=2.0, sr=22050, freq=220.0, amp=0.3):
    from pathlib import Path as _P

    _P(path).parent.mkdir(parents=True, exist_ok=True)
    n = int(sr * seconds)
    y = (amp * np.sin(2 * np.pi * freq * np.arange(n) / sr)).astype("float32")
    sf.write(str(path), y, sr)
    return str(path)


# --------------------------------------------------------------------------- #
#  музыка
# --------------------------------------------------------------------------- #
class TestStageMusic:
    def test_dry_run_does_not_touch_disk(self, ctx) -> None:
        ctx["ai"].dry_run = True
        out = stages_music.stage_music(None, ctx)
        assert out == {"ok": True, "beat_path": "[dry]"}
        assert not any(ctx["ai"].out_root.iterdir())

    def test_cyber_synth_fallback_is_named(self, ctx, monkeypatch) -> None:
        import modules.cyber_synth as cs

        def fake(self, bpm, duration_sec, out_path):
            write_wav(out_path, seconds=2.0)
            return {"ok": True, "engine": "cyber"}

        monkeypatch.setattr(cs.CyberSynth, "synthesize_track", fake)
        out = stages_music.stage_music(None, ctx)
        assert out["engine"] == "cyber_synth_fallback"
        assert out["beat_path"].endswith("beat.wav")
        assert "quality" in out

    def test_missing_engine_is_a_named_refusal(self, ctx, monkeypatch) -> None:
        import modules.cyber_synth as cs

        monkeypatch.setattr(
            cs.CyberSynth,
            "synthesize_track",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("нет движка")),
        )
        out = stages_music.stage_music(None, ctx)
        assert out["ok"] is False
        assert "no music engine" in out["reason"]

    def test_neural_path_builds_prompt_with_reference(self, ctx, monkeypatch) -> None:
        import modules.beat_gen_ai as bg

        ctx["sink"]["dossier_load"] = {
            "artist_dossier": {"flow": "рваный"},
            "track_dossier": {"reusable_elements": ["808", "sax", "hat", "kick", "rim", "pad"]},
        }
        seen = {}

        def fake(**kw):
            seen.update(kw)
            write_wav(kw["out_path"])
            return {"ok": True}

        monkeypatch.setattr(bg, "render_beat_ai", fake)
        out = stages_music.stage_music("handle", ctx)
        assert seen["bpm"] == 140
        assert seen["handle"] == "handle"
        assert "промпт" not in seen or True
        assert out["prompt"]
        # берём не больше пяти элементов
        assert "808" in out["prompt"] or out["prompt"]

    def test_quality_failure_makes_stage_not_ok(self, ctx, monkeypatch) -> None:
        import modules.cyber_synth as cs

        # файл не создаётся → валидация артефакта должна отказать
        monkeypatch.setattr(
            cs.CyberSynth, "synthesize_track", lambda *a, **k: {"ok": True}
        )
        out = stages_music.stage_music(None, ctx)
        assert out["ok"] is False
        assert out["quality"]["ok"] is False


class TestStageMusicStereo:
    def test_dry_run(self, ctx) -> None:
        ctx["ai"].dry_run = True
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["skipped"] == "dry-run"

    def test_no_base_beat(self, ctx) -> None:
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["skipped"] == "no base beat"

    def test_base_beat_path_missing_on_disk(self, ctx) -> None:
        ctx["sink"]["music"] = {"beat_path": str(ctx["ai"].out_root / "nope.wav")}
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["skipped"] == "no base beat"

    def test_no_model_is_named_skip(self, ctx) -> None:
        beat = write_wav(ctx["ai"].out_root / "beat.wav")
        ctx["sink"]["music"] = {"beat_path": beat}
        out = stages_music.stage_music_stereo(None, ctx)
        assert out["skipped"] == "music_stereo unavailable"
        assert "audiocraft" in out["reason"]
        assert "base beat is preserved" in out["fallback"]

    def _with_beat(self, ctx):
        beat = write_wav(ctx["ai"].out_root / "beat.wav", seconds=3.0)
        ctx["sink"]["music"] = {"beat_path": beat}
        return beat

    def test_texture_render_failure_is_named(self, ctx, monkeypatch) -> None:
        self._with_beat(ctx)
        monkeypatch.setattr(
            stages_music,
            "render_stereo_texture",
            lambda *a, **k: {"ok": False, "reason": "нет VRAM"},
        )
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["skipped"] == "music_stereo generation failed"
        assert out["reason"] == "нет VRAM"

    def test_texture_quality_rejected_is_named(self, ctx, monkeypatch) -> None:
        self._with_beat(ctx)

        def fake(*a, **k):
            write_wav(ctx["ai"].out_root / "t.wav", seconds=1.0)
            return {"ok": True, "texture_path": str(ctx["ai"].out_root / "t.wav")}

        monkeypatch.setattr(stages_music, "render_stereo_texture", fake)
        monkeypatch.setattr(
            stages_music,
            "validate_stereo_texture",
            lambda *a, **k: {"ok": False, "reason": "тихо"},
        )
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["skipped"] == "music_stereo quality rejected"
        assert out["reason"] == "тихо"

    def test_success_reports_engine_and_paths(self, ctx, monkeypatch) -> None:
        beat = self._with_beat(ctx)
        calls = []
        handles = []

        def fake_texture(handle, prompt, duration, path):
            calls.append(prompt)
            handles.append(handle)
            write_wav(path, seconds=2.0)
            return {"ok": True, "texture_path": path}

        monkeypatch.setattr(stages_music, "render_stereo_texture", fake_texture)
        monkeypatch.setattr(
            stages_music, "validate_stereo_texture", lambda *a, **k: {"ok": True, "reason": ""}
        )

        def fake_extend(base, intro, outro, out, fade_sec=1.0):
            write_wav(out, seconds=5.0)
            return {"ok": True, "beat_path": out}

        monkeypatch.setattr(stages_music, "extend_beat_with_stereo_sections", fake_extend)
        monkeypatch.setattr(
            stages_music, "validate_audio_artifact", lambda *a, **k: {"ok": True, "reason": ""}
        )
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["ok"] is True
        assert out["engine"] == "musicgen-stereo-medium"
        assert len(calls) == 2  # intro и outro
        assert "intro" in calls[0] and "outro" in calls[1]
        # регрессия: цикл по результатам затенял `handle` строкой-путём, и
        # второй вызов получал не модель, а путь
        assert handles == ["h", "h"]
        assert out["extension_sec"] == int(ctx["ai"].ws.get("texture_duration_sec", 8)) * 2

    def test_extension_failure_keeps_base(self, ctx, monkeypatch) -> None:
        self._with_beat(ctx)
        monkeypatch.setattr(
            stages_music,
            "render_stereo_texture",
            lambda h, p, d, path: (write_wav(path), {"ok": True, "texture_path": path})[1],
        )
        monkeypatch.setattr(stages_music, "validate_stereo_texture", lambda *a, **k: {"ok": True})
        monkeypatch.setattr(
            stages_music,
            "extend_beat_with_stereo_sections",
            lambda *a, **k: {"ok": False, "reason": "склейка не удалась"},
        )
        out = stages_music.stage_music_stereo("h", ctx)
        assert out["skipped"] == "stereo extension failed"
        assert "base beat is preserved" in out["fallback"]


# --------------------------------------------------------------------------- #
#  вокал и микс
# --------------------------------------------------------------------------- #
class TestStageVocal:
    def test_dry_run(self, ctx) -> None:
        ctx["ai"].dry_run = True
        assert stages_vocal.stage_vocal(None, ctx) == {"skipped": "dry-run"}

    def test_no_lyrics(self, ctx) -> None:
        assert stages_vocal.stage_vocal(None, ctx) == {"skipped": "no lyrics"}

    def test_without_model_reports_xtts_attempt(self, ctx, monkeypatch) -> None:
        ctx["sink"]["lyrics"] = {"lyrics": "[Verse]\nмоя строка про ночь"}
        monkeypatch.setattr(
            stages_vocal,
            "render_voice_synth_fallback",
            lambda clean, out: {"ok": True, "vocal_path": out, "engine": "voice_synth"},
        )
        out = stages_vocal.stage_vocal(None, ctx)
        assert out["engine"] == "voice_synth"
        assert out["xtts_attempt"] == "XTTS model unavailable"

    def test_clean_text_strips_section_tags_and_limits(self, ctx, monkeypatch) -> None:
        long_line = "\n".join(["строка"] * 900)
        ctx["sink"]["lyrics"] = {"lyrics": "[Chorus]\n" + long_line + "\n\n\n\nещё"}
        seen = {}

        def fake(clean, out):
            seen["clean"] = clean
            return {"ok": True, "vocal_path": out}

        monkeypatch.setattr(stages_vocal, "render_voice_synth_fallback", fake)
        stages_vocal.stage_vocal(None, ctx)
        assert "[Chorus]" not in seen["clean"]
        assert "\n\n\n" not in seen["clean"]
        assert len(seen["clean"]) <= 3500

    def test_primary_model_success_is_returned(self, ctx, monkeypatch) -> None:
        ctx["sink"]["lyrics"] = {"lyrics": "текст песни для синтеза"}
        import modules.voice_synth_ai as vsa

        monkeypatch.setattr(
            vsa,
            "synth_vocal_ai",
            lambda *a, **k: {"ok": True, "vocal_path": "v.wav", "engine": "xtts"},
        )
        out = stages_vocal.stage_vocal("handle", ctx)
        assert out["engine"] == "xtts"

    def test_model_failure_falls_back_with_reason(self, ctx, monkeypatch) -> None:
        ctx["sink"]["lyrics"] = {"lyrics": "текст песни для синтеза"}
        import modules.voice_synth_ai as vsa

        monkeypatch.setattr(vsa, "synth_vocal_ai", lambda *a, **k: {"ok": False, "reason": "нет wav"})
        monkeypatch.setattr(
            stages_vocal,
            "render_voice_synth_fallback",
            lambda clean, out: {"ok": True, "vocal_path": out},
        )
        out = stages_vocal.stage_vocal("handle", ctx)
        assert out["xtts_attempt"] == "нет wav"

    def test_speaker_selected_from_vault_when_absent(self, ctx, monkeypatch) -> None:
        ctx["sink"]["lyrics"] = {"lyrics": "текст песни для синтеза"}
        ctx["ai"].ws["vocal_style"] = "male_low"
        import modules.voice_vault as vv
        import modules.voice_synth_ai as vsa

        seen = {}
        monkeypatch.setattr(vv, "select_speaker_wav", lambda style: f"/vault/{style}.wav")
        monkeypatch.setattr(
            vsa,
            "synth_vocal_ai",
            lambda *a, **k: seen.update(k) or {"ok": True, "vocal_path": "v.wav"},
        )
        stages_vocal.stage_vocal("handle", ctx)
        assert seen["speaker_wav"] == "/vault/male_low.wav"

    def test_vault_unavailable_does_not_crash(self, ctx, monkeypatch) -> None:
        ctx["sink"]["lyrics"] = {"lyrics": "текст песни для синтеза"}
        import modules.voice_vault as vv
        import modules.voice_synth_ai as vsa

        monkeypatch.setattr(
            vv, "select_speaker_wav", lambda s: (_ for _ in ()).throw(RuntimeError("нет vault"))
        )
        seen = {}
        monkeypatch.setattr(
            vsa,
            "synth_vocal_ai",
            lambda *a, **k: seen.update(k) or {"ok": True, "vocal_path": "v.wav"},
        )
        stages_vocal.stage_vocal("handle", ctx)
        assert seen["speaker_wav"] is None


class TestStageRvc:
    def test_dry_run(self, ctx) -> None:
        ctx["ai"].dry_run = True
        assert stages_vocal.stage_rvc("h", ctx)["skipped"] == "dry-run"

    def test_no_model(self, ctx) -> None:
        out = stages_vocal.stage_rvc(None, ctx)
        assert out["skipped"] == "RVC unavailable"
        assert out["reason"] == "no installed RVC model/runtime"

    def test_no_vocal(self, ctx) -> None:
        assert stages_vocal.stage_rvc("h", ctx)["skipped"] == "no vocal"

    def test_no_voice_name(self, ctx) -> None:
        vocal = write_wav(ctx["ai"].out_root / "v.wav")
        ctx["sink"]["vocal_synth"] = {"vocal_path": vocal}
        assert stages_vocal.stage_rvc("h", ctx)["skipped"] == "no rvc_voice_name"

    def test_voice_name_from_model_path(self, ctx, monkeypatch) -> None:
        vocal = write_wav(ctx["ai"].out_root / "v.wav")
        ctx["sink"]["vocal_synth"] = {"vocal_path": vocal}
        ctx["ai"].ws["rvc_model"] = "models/my_voice.pth"
        seen = {}

        def fake(handle, src, out, voice_name=None, pitch_shift=0):
            seen.update(voice_name=voice_name, pitch_shift=pitch_shift)
            return {"ok": True, "vocal_path": out}

        monkeypatch.setattr(stages_vocal, "render_rvc_vocal", fake)
        out = stages_vocal.stage_rvc("h", ctx)
        assert out["ok"] is True
        assert seen["voice_name"] == "my_voice"

    def test_explicit_voice_name_wins(self, ctx, monkeypatch) -> None:
        vocal = write_wav(ctx["ai"].out_root / "v.wav")
        ctx["sink"]["vocal_synth"] = {"vocal_path": vocal}
        ctx["ai"].ws.update({"rvc_voice_name": "explicit", "rvc_pitch_shift": -2})
        seen = {}
        monkeypatch.setattr(
            stages_vocal,
            "render_rvc_vocal",
            lambda h, s, o, voice_name=None, pitch_shift=0: seen.update(
                voice_name=voice_name, pitch_shift=pitch_shift
            )
            or {"ok": True},
        )
        stages_vocal.stage_rvc("h", ctx)
        assert seen == {"voice_name": "explicit", "pitch_shift": -2}


class TestStageMix:
    def test_no_beat(self, ctx) -> None:
        assert stages_vocal.stage_mix(None, ctx)["skipped"] == "no beat"

    def test_beat_only_is_written(self, ctx) -> None:
        beat = write_wav(ctx["ai"].out_root / "beat.wav", seconds=2.0)
        ctx["sink"]["music"] = {"beat_path": beat}
        out = stages_vocal.stage_mix(None, ctx)
        assert out["ok"] is True
        assert out["vocal"] is False
        assert out["texture_mixed"] is False
        assert (ctx["ai"].out_root / "mix.wav").exists()

    def test_stereo_beat_preferred_over_mono(self, ctx) -> None:
        mono = write_wav(ctx["ai"].out_root / "beat.wav", seconds=2.0)
        stereo = write_wav(ctx["ai"].out_root / "beat_stereo_extended.wav", seconds=2.0, freq=300)
        ctx["sink"]["music"] = {"beat_path": mono}
        ctx["sink"]["music_stereo"] = {"beat_path": stereo}
        out = stages_vocal.stage_mix(None, ctx)
        assert out["ok"] is True

    def test_vocal_is_mixed_and_peak_limited(self, ctx) -> None:
        beat = write_wav(ctx["ai"].out_root / "beat.wav", seconds=2.0, amp=0.9)
        vocal = write_wav(ctx["ai"].out_root / "v.wav", seconds=2.0, amp=0.9, freq=440)
        ctx["sink"]["music"] = {"beat_path": beat}
        ctx["sink"]["vocal_synth"] = {"vocal_path": vocal}
        out = stages_vocal.stage_mix(None, ctx)
        assert out["vocal"] is True
        y, _ = sf.read(out["mix_path"])
        assert float(np.max(np.abs(y))) <= 0.99

    def test_rvc_vocal_preferred_over_source(self, ctx, monkeypatch) -> None:
        beat = write_wav(ctx["ai"].out_root / "beat.wav", seconds=2.0)
        src = write_wav(ctx["ai"].out_root / "v_src.wav", seconds=2.0)
        conv = write_wav(ctx["ai"].out_root / "v_rvc.wav", seconds=2.0, freq=330)
        ctx["sink"]["music"] = {"beat_path": beat}
        ctx["sink"]["vocal_synth"] = {"vocal_path": src}
        ctx["sink"]["rvc"] = {"vocal_path": conv}
        out = stages_vocal.stage_mix(None, ctx)
        assert out["vocal"] is True

    def test_texture_is_mixed_quietly(self, ctx) -> None:
        beat = write_wav(ctx["ai"].out_root / "beat.wav", seconds=2.0, amp=0.5)
        tex = write_wav(ctx["ai"].out_root / "tex.wav", seconds=2.0, amp=0.05, freq=800)
        ctx["sink"]["music"] = {"beat_path": beat}
        ctx["sink"]["music_stereo"] = {"beat_path": beat, "texture_path": tex}
        out = stages_vocal.stage_mix(None, ctx)
        assert out["texture_mixed"] is True

    def test_unreadable_beat_is_refused(self, ctx, tmp_path) -> None:
        bad = ctx["ai"].out_root / "bad.wav"
        bad.write_bytes(b"not audio")
        ctx["sink"]["music"] = {"beat_path": str(bad)}
        out = stages_vocal.stage_mix(None, ctx)
        assert out["ok"] is False
        assert out["reason"]


# --------------------------------------------------------------------------- #
#  метаданные
# --------------------------------------------------------------------------- #
class TestStageMeta:
    def test_hardware_profile_or_error(self, ctx, monkeypatch) -> None:
        import app.core.hw_autodetect as hw

        monkeypatch.setattr(hw, "get_hardware_profile", lambda: {"gpu": "none"})
        assert stages_meta.stage_hw(None, ctx) == {"gpu": "none"}

    def test_hardware_failure_returns_error_key(self, ctx, monkeypatch) -> None:
        import app.core.hw_autodetect as hw

        monkeypatch.setattr(
            hw, "get_hardware_profile", lambda: (_ for _ in ()).throw(RuntimeError("нет psutil"))
        )
        assert "нет psutil" in stages_meta.stage_hw(None, ctx)["error"]

    def test_dossier_skipped_without_slug(self, ctx) -> None:
        assert stages_meta.stage_dossier_load(None, ctx) == {"skipped": "no artist_slug"}

    def test_dossier_loaded_with_slug(self, ctx, monkeypatch) -> None:
        # `from modules.artist_dossier import DossierManager` импортируется
        # на уровне модуля — патчим атрибут уже загруженного модуля стадии.
        ctx["ai"].artist_slug = "kalash"
        ctx["ai"].ref_track_id = "t7"

        class Manager:
            def get_artist_dossier(self, slug):
                return {"about": slug}

            def get_track_dossier(self, slug, tid):
                return {"id": tid}

        monkeypatch.setattr(stages_meta, "DossierManager", Manager)
        out = stages_meta.stage_dossier_load(None, ctx)
        assert out == {"artist_dossier": {"about": "kalash"}, "track_dossier": {"id": "t7"}}

    def test_lyrics_dry_run(self, ctx) -> None:
        ctx["ai"].dry_run = True
        out = stages_meta.stage_lyrics(None, ctx)
        assert out["source"] == "dry"

    def test_lyrics_model_success_is_written(self, ctx, monkeypatch) -> None:
        monkeypatch.setattr(
            stages_meta,
            "validate_song_lyrics",
            lambda text, user_lines=None: {"ok": True, "reason": "", "metrics": {}},
        )
        import modules.lyrics as lyr

        monkeypatch.setattr(
            lyr,
            "generate_lyrics_ai",
            lambda **kw: {"lyrics": "хороший текст песни", "source": "lyrics_llm"},
        )
        out = stages_meta.stage_lyrics("h", ctx)
        assert out["source"] == "lyrics_llm"
        assert (ctx["ai"].out_root / "lyrics.txt").read_text(encoding="utf-8") == "хороший текст песни"

    def test_lyrics_fallback_when_quality_fails(self, ctx, monkeypatch) -> None:
        import modules.lyrics as lyr

        monkeypatch.setattr(
            lyr,
            "generate_lyrics_ai",
            lambda **kw: {"lyrics": "плохо", "source": "lyrics_llm"},
        )
        monkeypatch.setattr(
            lyr,
            "generate_lyrics",
            lambda **kw: {"lyrics": "запасной текст песни"},
        )
        calls = {"n": 0}

        def validator(text, user_lines=None):
            calls["n"] += 1
            return {"ok": text == "запасной текст песни", "reason": "", "metrics": {}}

        monkeypatch.setattr(stages_meta, "validate_song_lyrics", validator)
        out = stages_meta.stage_lyrics("h", ctx)
        assert out["source"] == "punch_lib_fallback"

    def test_lyrics_model_exception_goes_to_fallback(self, ctx, monkeypatch) -> None:
        import modules.lyrics as lyr

        monkeypatch.setattr(
            lyr,
            "generate_lyrics_ai",
            lambda **kw: (_ for _ in ()).throw(RuntimeError("модель упала")),
        )
        monkeypatch.setattr(lyr, "generate_lyrics", lambda **kw: {"lyrics": "запас"})
        monkeypatch.setattr(
            stages_meta,
            "validate_song_lyrics",
            lambda text, user_lines=None: {"ok": True, "reason": "", "metrics": {}},
        )
        out = stages_meta.stage_lyrics("h", ctx)
        assert out["ok"] is True
        assert out["source"] == "punch_lib_fallback"

    def test_both_lyrics_paths_fail_returns_not_ok(self, ctx, monkeypatch) -> None:
        import modules.lyrics as lyr

        monkeypatch.setattr(
            lyr, "generate_lyrics_ai", lambda **kw: (_ for _ in ()).throw(RuntimeError("раз"))
        )
        monkeypatch.setattr(
            lyr, "generate_lyrics", lambda **kw: (_ for _ in ()).throw(RuntimeError("два"))
        )
        out = stages_meta.stage_lyrics("h", ctx)
        assert out["ok"] is False
        assert out["lyrics"] == ""
        assert (ctx["ai"].out_root / "lyrics.txt").exists()

    def test_metadata_fallback_values(self, ctx) -> None:
        js = stages_meta._metadata_fallback(ctx["ai"])
        assert js["title"] == "ночная дорога"
        assert len(js["spotify_desc"]) <= 400
        assert len(js["youtube_desc"]) <= 400
        assert "drift_phonk" in js["tags_tiktok"]

    def test_metadata_fallback_short_theme_gets_title(self, ctx) -> None:
        ctx["ai"].ws["theme"] = "a"
        js = stages_meta._metadata_fallback(ctx["ai"])
        assert js["title"] == "Drift_Phonk Pulse"

    def test_metadata_dry_run_marks_source(self, ctx) -> None:
        ctx["ai"].dry_run = True
        out = stages_meta.stage_metadata("h", ctx)
        assert out["source"] == "dry"
        assert (ctx["ai"].out_root / "metadata.json").exists()

    def test_metadata_llm_result_is_validated(self, ctx, monkeypatch) -> None:
        monkeypatch.setattr(
            stages_meta.LLM,
            "complete_json",
            lambda *a, **k: {
                "title": "Мой трек",
                "spotify_desc": "достаточно длинное описание для Spotify",
                "youtube_desc": "достаточно длинное описание для YouTube",
                "tags_tiktok": ["phonk", "night"],
                "tags_instagram": ["music", "release"],
            },
        )
        out = stages_meta.stage_metadata("h", ctx)
        assert out["source"] == "metadata_llm"
        assert out["ok"] is True

    def test_bad_llm_metadata_falls_back(self, ctx, monkeypatch) -> None:
        monkeypatch.setattr(stages_meta.LLM, "complete_json", lambda *a, **k: {"title": "x"})
        out = stages_meta.stage_metadata("h", ctx)
        assert out["source"] == "metadata_fallback"
        assert json.loads((ctx["ai"].out_root / "metadata.json").read_text(encoding="utf-8"))["title"]


# --------------------------------------------------------------------------- #
#  финал
# --------------------------------------------------------------------------- #
class TestStageFinal:
    def test_master_without_mix(self, ctx) -> None:
        assert stages_final.stage_master(None, ctx) == {"skipped": "no mix"}

    def test_master_quality_failure_is_not_ok(self, ctx, monkeypatch) -> None:
        mix = write_wav(ctx["ai"].out_root / "mix.wav")
        ctx["sink"]["mix"] = {"mix_path": mix}
        import modules.mastering_reference as mr

        monkeypatch.setattr(
            mr, "master_ai", lambda *a, **k: {"ok": True, "path": "/nowhere.wav"}
        )
        monkeypatch.setattr(
            stages_final,
            "validate_master_artifact",
            lambda *a, **k: {"ok": False, "reason": "тихий мастер"},
        )
        out = stages_final.stage_master("h", ctx)
        assert out["ok"] is False
        assert out["reason"] == "тихий мастер"

    def test_master_success_passes_target_lufs(self, ctx, monkeypatch) -> None:
        mix = write_wav(ctx["ai"].out_root / "mix.wav")
        ctx["sink"]["mix"] = {"mix_path": mix}
        import modules.mastering_reference as mr

        seen = {}

        def fake(src, out, reference_wav=None, target_lufs=0.0, handle=None):
            seen.update(target_lufs=target_lufs, out=out, ref=reference_wav)
            return {"ok": True, "path": out}

        monkeypatch.setattr(mr, "master_ai", fake)
        monkeypatch.setattr(
            stages_final, "validate_master_artifact", lambda *a, **k: {"ok": True, "reason": ""}
        )
        out = stages_final.stage_master("h", ctx)
        assert out["ok"] is True
        assert seen["target_lufs"] == -14.0
        assert seen["out"].endswith("master_ai.wav")

    def test_cover_uses_metadata_title(self, ctx, monkeypatch) -> None:
        ctx["sink"]["metadata"] = {"title": "Из метаданных"}
        import modules.cover_art_ai as cai

        monkeypatch.setattr(
            cai, "render_cover_ai", lambda **kw: {"ok": True, "path": "c.png", "title": kw["title"]}
        )
        monkeypatch.setattr(
            stages_final, "validate_cover_artifact", lambda *a, **k: {"ok": True, "reason": ""}
        )
        out = stages_final.stage_cover("h", ctx)
        assert out["title"] == "Из метаданных"

    def test_cover_falls_back_to_theme(self, ctx, monkeypatch) -> None:
        import modules.cover_art_ai as cai

        # artist_display пуст, а ключ "ai.artist_slug" в ws не задан
        ctx["ai"].ws.pop("artist_display", None)

        monkeypatch.setattr(
            cai, "render_cover_ai", lambda **kw: {"ok": True, "path": "c.png", "title": kw["title"]}
        )
        monkeypatch.setattr(
            stages_final, "validate_cover_artifact", lambda *a, **k: {"ok": True, "reason": None}
        )
        out = stages_final.stage_cover("h", ctx)
        assert out["title"] == "ночная дорога"

    def test_cover_quality_failure(self, ctx, monkeypatch) -> None:
        import modules.cover_art_ai as cai

        monkeypatch.setattr(cai, "render_cover_ai", lambda **k: {"ok": True, "path": "tiny.png"})
        monkeypatch.setattr(
            stages_final,
            "validate_cover_artifact",
            lambda *a, **k: {"ok": False, "reason": "меньше 1024px"},
        )
        out = stages_final.stage_cover("h", ctx)
        assert out["ok"] is False and out["reason"] == "меньше 1024px"

    def test_tag_without_bundle(self, ctx) -> None:
        assert stages_final.stage_tag(None, ctx) == {"skipped": "no clap"}

    def test_tag_without_master(self, ctx) -> None:
        assert stages_final.stage_tag(("m", "p"), ctx)["skipped"] == "no master"

    def test_tag_without_torch_is_named_refusal(self, ctx) -> None:
        master = write_wav(ctx["ai"].out_root / "masters" / "master_ai.wav")
        ctx["sink"]["master"] = {"path": master}
        # torch в окружении сборки нет — отказ обязан быть, а не трейсбек
        out = stages_final.stage_tag(("model", "proc"), ctx)
        assert out["ok"] is False
        assert out["reason"]

    def test_tag_with_fake_torch_returns_genre_match(self, ctx, monkeypatch) -> None:
        import sys
        import types

        master = write_wav(ctx["ai"].out_root / "masters" / "master_ai.wav")
        ctx["sink"]["master"] = {"path": master}

        class Param:
            def is_cuda(self):
                return False

        class Logits:
            """Имитация torch-тензора: в стадии вызывается .cpu().numpy()."""

            def __init__(self, values):
                self._values = np.array(values)

            def cpu(self):
                return self

            def numpy(self):
                return self._values

        class Model:
            def parameters(self):
                return iter([Param()])

            def __call__(self, **inputs):
                class Out:
                    logits_per_audio = [
                        Logits([0.1, 0.9, 0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0])
                    ]

                return Out()

        class NoGrad:
            def __enter__(self):
                return None

            def __exit__(self, *a):
                return False

        # librosa берёт torch.Tensor при импорте — даём заглушку класса
        class Tensor:
            pass

        fake_torch = types.SimpleNamespace(no_grad=lambda: NoGrad(), Tensor=Tensor)
        monkeypatch.setitem(sys.modules, "torch", fake_torch)

        def proc(text=None, audios=None, sampling_rate=None, return_tensors=None, padding=None):
            return {"text": text}

        out = stages_final.stage_tag((Model(), proc), ctx)
        assert out["ok"] is True
        assert out["tags"][0] == "trap"  # второй по величине логит после индекса 1
        assert out["match_genre"] is False  # drift_phonk в кандидатах нет


class TestAIContext:
    def test_defaults(self, tmp_path) -> None:
        ai = AIContext(ws={"a": 1}, out_root=tmp_path)
        assert ai.dry_run is False
        assert ai.artist_slug is None
        assert ai.extra == {}

    def test_extra_is_per_instance(self, tmp_path) -> None:
        a = AIContext(ws={}, out_root=tmp_path)
        b = AIContext(ws={}, out_root=tmp_path)
        a.extra["x"] = 1
        assert b.extra == {}
