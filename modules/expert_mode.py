"""
ZS Music Maker v11 — expert_mode.py

ТЗ 20.2 п.21 «Экспертный режим» + 20.3 скрытая кнопка «⋯».
8 секций, 4 пресета, validate, safe-merge.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from typing import Any


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))


@dataclass
class ExpertBeat:
    bpm_override: float | None = None
    swing_percent: float = 15.0
    kick_pattern: str = "trap_v2"
    snare_layer: str = "auto"
    hihat_density: float = 1.0
    bass_style: str = "808_sub"
    fills_intensity: float = 0.5
    dropout_bars: list[int] = field(default_factory=list)


@dataclass
class ExpertLyrics:
    llm_temperature: float = 0.85
    llm_top_p: float = 0.92
    llm_max_tokens: int = 2048
    llm_model: str = "llama3:8b"
    syllable_target: str = "auto"
    verse_count: int = 2
    chorus_count: int = 2
    include_en_hook: bool = True
    female_backing: bool = True
    reference_authors: list[str] = field(default_factory=list)
    forbidden_words: list[str] = field(default_factory=list)
    forced_words: list[str] = field(default_factory=list)


@dataclass
class ExpertVoice:
    mode: str = "rap"
    tts_engine: str = "silero"
    tts_speaker: str = "aidar"
    tts_prosody: float = 1.0
    rvc_enabled: bool = True
    rvc_model: str = "user"
    rvc_pitch_shift: int = 0
    rvc_index_rate: float = 0.66
    rvc_epochs: int = 200
    rvc_batch_size: int = 4
    provoice_mode: bool = False


@dataclass
class ExpertMix:
    eq_low_db: float = 0.0
    eq_mid_db: float = 0.0
    eq_high_db: float = 0.0
    sidechain_amount: float = 0.35
    reverb_wet: float = 0.15
    delay_wet: float = 0.1
    stereo_width: float = 1.15
    limiter_ceiling_db: float = -0.3


@dataclass
class ExpertMaster:
    target_lufs: float = -9.0
    stand_car_lufs: float = -8.5
    stand_club_lufs: float = -6.5
    stand_stream_lufs: float = -14.0
    stand_tiktok_lufs: float = -13.0
    matchering_ref: str | None = None
    true_peak_max_db: float = -1.0


@dataclass
class ExpertMusicGen:
    variant: str = "auto"
    duration_sec: float = 8.0
    top_k: int = 250
    top_p: float = 0.9
    temperature: float = 1.0
    guidance_scale: float = 3.0
    prompt_lang: str = "en"


@dataclass
class ExpertAntiNeuro:
    preset: str = "standard"
    timing_jitter_ms: int = 10
    breath_enabled: bool = True
    formant_shift_cents: int = 5
    consonant_boost_db: float = 3.0
    fade_out_ms: int = 1200


@dataclass
class ExpertRender:
    length_sec: int = 150
    quality_mode: str = "quality"
    make_tiktok: bool = True
    make_reels: bool = True
    make_shorts: bool = True
    make_stems: bool = True
    make_instrumental: bool = True
    make_acapella: bool = True
    auto_qa_loop: bool = True
    auto_qa_max_iters: int = 2


@dataclass
class ExpertConfig:
    enabled: bool = False
    version: str = "v11"
    beat: ExpertBeat = field(default_factory=ExpertBeat)
    lyrics: ExpertLyrics = field(default_factory=ExpertLyrics)
    voice: ExpertVoice = field(default_factory=ExpertVoice)
    mix: ExpertMix = field(default_factory=ExpertMix)
    master: ExpertMaster = field(default_factory=ExpertMaster)
    musicgen: ExpertMusicGen = field(default_factory=ExpertMusicGen)
    anti_neuro: ExpertAntiNeuro = field(default_factory=ExpertAntiNeuro)
    render: ExpertRender = field(default_factory=ExpertRender)

    def to_flat_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "expert_mode_enabled": self.enabled,
            "expert_mode_version": self.version,
        }
        for sn, sec in [
            ("beat", self.beat),
            ("lyrics", self.lyrics),
            ("voice", self.voice),
            ("mix", self.mix),
            ("master", self.master),
            ("musicgen", self.musicgen),
            ("anti_neuro", self.anti_neuro),
            ("render", self.render),
        ]:
            for fld in fields(sec):
                out[f"{sn}.{fld.name}"] = getattr(sec, fld.name)
        return out

    def to_dict(self):
        return asdict(self)

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_dict(cls, raw):
        def _build(dc_cls, data):
            if not isinstance(data, dict):
                return dc_cls()
            kw = {}
            for fld in fields(dc_cls):
                if fld.name in data:
                    kw[fld.name] = data[fld.name]
            return dc_cls(**kw)

        return cls(
            enabled=bool(raw.get("enabled", False)),
            version=str(raw.get("version", "v11")),
            beat=_build(ExpertBeat, raw.get("beat", {})),
            lyrics=_build(ExpertLyrics, raw.get("lyrics", {})),
            voice=_build(ExpertVoice, raw.get("voice", {})),
            mix=_build(ExpertMix, raw.get("mix", {})),
            master=_build(ExpertMaster, raw.get("master", {})),
            musicgen=_build(ExpertMusicGen, raw.get("musicgen", {})),
            anti_neuro=_build(ExpertAntiNeuro, raw.get("anti_neuro", {})),
            render=_build(ExpertRender, raw.get("render", {})),
        )


def validate(cfg):
    errors, warnings = [], []
    if cfg.render.length_sec < 60:
        errors.append("render.length_sec < 60 (мин. 1:30)")
    if cfg.render.length_sec > 400:
        warnings.append("render.length_sec > 400 очень длинно")
    if cfg.beat.bpm_override is not None:
        if not (40 <= cfg.beat.bpm_override <= 220):
            errors.append("beat.bpm_override вне 40..220")
    if not (0 <= cfg.beat.swing_percent <= 60):
        warnings.append("beat.swing_percent вне 0..60")
    if cfg.voice.rvc_epochs < 10:
        warnings.append("rvc_epochs < 10 — плохое качество")
    if cfg.voice.rvc_epochs > 1000:
        warnings.append("rvc_epochs > 1000 — очень долго")
    if not (-60 <= cfg.master.target_lufs <= 0):
        errors.append("master.target_lufs вне -60..0 dB")
    if cfg.master.true_peak_max_db > 0:
        errors.append("master.true_peak_max_db > 0 dB — клиппы")
    if cfg.anti_neuro.preset not in ("gentle", "standard", "aggressive"):
        errors.append("anti_neuro.preset должен быть gentle|standard|aggressive")
    if cfg.render.quality_mode not in ("fast", "quality", "max"):
        errors.append("render.quality_mode должен быть fast|quality|max")
    if cfg.voice.mode not in ("rap", "sing", "mix"):
        errors.append("voice.mode должен быть rap|sing|mix")
    if cfg.musicgen.variant not in ("auto", "small", "medium", "large"):
        errors.append("musicgen.variant должен быть auto|small|medium|large")
    return {"errors": errors, "warnings": warnings}


def preset_default():
    return ExpertConfig()


def preset_phonk_car():
    c = ExpertConfig(enabled=True)
    c.beat.kick_pattern = "phonk_808"
    c.beat.bass_style = "808_sub"
    c.beat.hihat_density = 1.4
    c.mix.sidechain_amount = 0.55
    c.mix.stereo_width = 1.25
    c.master.target_lufs = -8.5
    c.anti_neuro.preset = "aggressive"
    c.render.length_sec = 150
    return c


def preset_hyperpop_tiktok():
    c = ExpertConfig(enabled=True)
    c.beat.kick_pattern = "hyperpop"
    c.beat.hihat_density = 1.6
    c.lyrics.include_en_hook = True
    c.lyrics.female_backing = True
    c.voice.tts_prosody = 1.15
    c.mix.reverb_wet = 0.25
    c.master.target_lufs = -13.0
    c.render.length_sec = 105
    return c


def preset_trap_summer():
    c = ExpertConfig(enabled=True)
    c.beat.kick_pattern = "trap_v2"
    c.beat.bass_style = "808_sub"
    c.beat.swing_percent = 22.0
    c.lyrics.syllable_target = "dense"
    c.master.target_lufs = -9.5
    c.render.length_sec = 175
    return c


BUILTIN_PRESETS = {
    "default": preset_default,
    "phonk_car": preset_phonk_car,
    "hyperpop_tiktok": preset_hyperpop_tiktok,
    "trap_summer": preset_trap_summer,
}


def apply_preset(name):
    fn = BUILTIN_PRESETS.get(name, preset_default)
    return fn()


def merge_with_wizard_state(wizard_state, expert):
    if not expert.enabled:
        wizard_state["expert_mode_enabled"] = False
        return wizard_state
    merged = dict(wizard_state)
    merged.update(expert.to_flat_dict())
    return merged


def _self_test():
    import tempfile

    ok = True
    c = preset_default()
    ok &= c.enabled is False
    ok &= c.render.length_sec == 150
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "cfg.json")
        c2 = preset_phonk_car()
        c2.save(p)
        c3 = ExpertConfig.load(p)
        ok &= c3.beat.kick_pattern == "phonk_808"
        ok &= c3.enabled is True
    bad = ExpertConfig()
    bad.render.length_sec = 30
    bad.master.target_lufs = 5.0
    bad.anti_neuro.preset = "xxx"
    v = validate(bad)
    ok &= len(v["errors"]) >= 3
    good = preset_hyperpop_tiktok()
    ok &= len(validate(good)["errors"]) == 0
    flat = good.to_flat_dict()
    ok &= "beat.kick_pattern" in flat
    ok &= flat["expert_mode_enabled"] is True
    ws = {"length_sec": 120, "some_thing": True}
    m1 = merge_with_wizard_state(ws, preset_default())
    ok &= m1["expert_mode_enabled"] is False
    ok &= m1["length_sec"] == 120
    m2 = merge_with_wizard_state(ws, good)
    ok &= m2["render.length_sec"] == 105
    return ok


if __name__ == "__main__":
    print("expert_mode self-test:", "OK" if _self_test() else "FAIL")
