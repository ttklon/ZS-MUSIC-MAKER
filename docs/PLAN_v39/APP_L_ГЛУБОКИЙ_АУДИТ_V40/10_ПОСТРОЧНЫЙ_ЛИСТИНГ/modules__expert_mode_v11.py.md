# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/expert_mode_v11.py`

**Всего строк:** 324

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 186 | 57.4 |
| blank | 50 | 15.4 |
| branch | 17 | 5.2 |
| return | 16 | 4.9 |
| def | 15 | 4.6 |
| decorator | 11 | 3.4 |
| class | 9 | 2.8 |
| import | 7 | 2.2 |
| docstring | 5 | 1.5 |
| loop | 3 | 0.9 |
| stmt | 3 | 0.9 |
| try_block | 2 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v11 — expert_mode_v11.py
    3 [blank     ] 
    4 [docstring ] ТЗ 20.2 п.21 «Экспертный режим» + 20.3 скрытая кнопка «⋯».
    5 [docstring ] 8 секций, 4 пресета, validate, safe-merge.
    6 [docstring ] """
    7 [blank     ] 
    8 [import    ] from __future__ import annotations
    9 [blank     ] 
   10 [import    ] import json
   11 [import    ] import os
   12 [import    ] import sys
   13 [import    ] from dataclasses import asdict, dataclass, field, fields
   14 [import    ] from typing import Any
   15 [blank     ] 
   16 [blank     ] 
   17 [def       ] def _safe_print(msg):
   18 [try_block ]     try:
   19 [code      ]         print(msg)
   20 [try_block ]     except UnicodeEncodeError:
   21 [code      ]         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
   22 [blank     ] 
   23 [blank     ] 
   24 [decorator ] @dataclass
   25 [class     ] class ExpertBeat:
   26 [code      ]     bpm_override: float | None = None
   27 [code      ]     swing_percent: float = 15.0
   28 [code      ]     kick_pattern: str = "trap_v2"
   29 [code      ]     snare_layer: str = "auto"
   30 [code      ]     hihat_density: float = 1.0
   31 [code      ]     bass_style: str = "808_sub"
   32 [code      ]     fills_intensity: float = 0.5
   33 [code      ]     dropout_bars: list[int] = field(default_factory=list)
   34 [blank     ] 
   35 [blank     ] 
   36 [decorator ] @dataclass
   37 [class     ] class ExpertLyrics:
   38 [code      ]     llm_temperature: float = 0.85
   39 [code      ]     llm_top_p: float = 0.92
   40 [code      ]     llm_max_tokens: int = 2048
   41 [code      ]     llm_model: str = "llama3:8b"
   42 [code      ]     syllable_target: str = "auto"
   43 [code      ]     verse_count: int = 2
   44 [code      ]     chorus_count: int = 2
   45 [code      ]     include_en_hook: bool = True
   46 [code      ]     female_backing: bool = True
   47 [code      ]     reference_authors: list[str] = field(default_factory=list)
   48 [code      ]     forbidden_words: list[str] = field(default_factory=list)
   49 [code      ]     forced_words: list[str] = field(default_factory=list)
   50 [blank     ] 
   51 [blank     ] 
   52 [decorator ] @dataclass
   53 [class     ] class ExpertVoice:
   54 [code      ]     mode: str = "rap"
   55 [code      ]     tts_engine: str = "silero"
   56 [code      ]     tts_speaker: str = "aidar"
   57 [code      ]     tts_prosody: float = 1.0
   58 [code      ]     rvc_enabled: bool = True
   59 [code      ]     rvc_model: str = "user"
   60 [code      ]     rvc_pitch_shift: int = 0
   61 [code      ]     rvc_index_rate: float = 0.66
   62 [code      ]     rvc_epochs: int = 200
   63 [code      ]     rvc_batch_size: int = 4
   64 [code      ]     provoice_mode: bool = False
   65 [blank     ] 
   66 [blank     ] 
   67 [decorator ] @dataclass
   68 [class     ] class ExpertMix:
   69 [code      ]     eq_low_db: float = 0.0
   70 [code      ]     eq_mid_db: float = 0.0
   71 [code      ]     eq_high_db: float = 0.0
   72 [code      ]     sidechain_amount: float = 0.35
   73 [code      ]     reverb_wet: float = 0.15
   74 [code      ]     delay_wet: float = 0.1
   75 [code      ]     stereo_width: float = 1.15
   76 [code      ]     limiter_ceiling_db: float = -0.3
   77 [blank     ] 
   78 [blank     ] 
   79 [decorator ] @dataclass
   80 [class     ] class ExpertMaster:
   81 [code      ]     target_lufs: float = -9.0
   82 [code      ]     stand_car_lufs: float = -8.5
   83 [code      ]     stand_club_lufs: float = -6.5
   84 [code      ]     stand_stream_lufs: float = -14.0
   85 [code      ]     stand_tiktok_lufs: float = -13.0
   86 [code      ]     matchering_ref: str | None = None
   87 [code      ]     true_peak_max_db: float = -1.0
   88 [blank     ] 
   89 [blank     ] 
   90 [decorator ] @dataclass
   91 [class     ] class ExpertMusicGen:
   92 [code      ]     variant: str = "auto"
   93 [code      ]     duration_sec: float = 8.0
   94 [code      ]     top_k: int = 250
   95 [code      ]     top_p: float = 0.9
   96 [code      ]     temperature: float = 1.0
   97 [code      ]     guidance_scale: float = 3.0
   98 [code      ]     prompt_lang: str = "en"
   99 [blank     ] 
  100 [blank     ] 
  101 [decorator ] @dataclass
  102 [class     ] class ExpertAntiNeuro:
  103 [code      ]     preset: str = "standard"
  104 [code      ]     timing_jitter_ms: int = 10
  105 [code      ]     breath_enabled: bool = True
  106 [code      ]     formant_shift_cents: int = 5
  107 [code      ]     consonant_boost_db: float = 3.0
  108 [code      ]     fade_out_ms: int = 1200
  109 [blank     ] 
  110 [blank     ] 
  111 [decorator ] @dataclass
  112 [class     ] class ExpertRender:
  113 [code      ]     length_sec: int = 150
  114 [code      ]     quality_mode: str = "quality"
  115 [code      ]     make_tiktok: bool = True
  116 [code      ]     make_reels: bool = True
  117 [code      ]     make_shorts: bool = True
  118 [code      ]     make_stems: bool = True
  119 [code      ]     make_instrumental: bool = True
  120 [code      ]     make_acapella: bool = True
  121 [code      ]     auto_qa_loop: bool = True
  122 [code      ]     auto_qa_max_iters: int = 2
  123 [blank     ] 
  124 [blank     ] 
  125 [decorator ] @dataclass
  126 [class     ] class ExpertConfig:
  127 [code      ]     enabled: bool = False
  128 [code      ]     version: str = "v11"
  129 [code      ]     beat: ExpertBeat = field(default_factory=ExpertBeat)
  130 [code      ]     lyrics: ExpertLyrics = field(default_factory=ExpertLyrics)
  131 [code      ]     voice: ExpertVoice = field(default_factory=ExpertVoice)
  132 [code      ]     mix: ExpertMix = field(default_factory=ExpertMix)
  133 [code      ]     master: ExpertMaster = field(default_factory=ExpertMaster)
  134 [code      ]     musicgen: ExpertMusicGen = field(default_factory=ExpertMusicGen)
  135 [code      ]     anti_neuro: ExpertAntiNeuro = field(default_factory=ExpertAntiNeuro)
  136 [code      ]     render: ExpertRender = field(default_factory=ExpertRender)
  137 [blank     ] 
  138 [def       ]     def to_flat_dict(self) -> dict[str, Any]:
  139 [code      ]         out: dict[str, Any] = {
  140 [code      ]             "expert_mode_enabled": self.enabled,
  141 [code      ]             "expert_mode_version": self.version,
  142 [code      ]         }
  143 [loop      ]         for sn, sec in [
  144 [code      ]             ("beat", self.beat),
  145 [code      ]             ("lyrics", self.lyrics),
  146 [code      ]             ("voice", self.voice),
  147 [code      ]             ("mix", self.mix),
  148 [code      ]             ("master", self.master),
  149 [code      ]             ("musicgen", self.musicgen),
  150 [code      ]             ("anti_neuro", self.anti_neuro),
  151 [code      ]             ("render", self.render),
  152 [code      ]         ]:
  153 [loop      ]             for fld in fields(sec):
  154 [code      ]                 out[f"{sn}.{fld.name}"] = getattr(sec, fld.name)
  155 [return    ]         return out
  156 [blank     ] 
  157 [def       ]     def to_dict(self):
  158 [return    ]         return asdict(self)
  159 [blank     ] 
  160 [def       ]     def save(self, path):
  161 [code      ]         os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
  162 [stmt      ]         with open(path, "w", encoding="utf-8") as f:
  163 [code      ]             json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
  164 [return    ]         return path
  165 [blank     ] 
  166 [decorator ]     @classmethod
  167 [def       ]     def load(cls, path):
  168 [stmt      ]         with open(path, encoding="utf-8") as f:
  169 [return    ]             return cls.from_dict(json.load(f))
  170 [blank     ] 
  171 [decorator ]     @classmethod
  172 [def       ]     def from_dict(cls, raw):
  173 [def       ]         def _build(dc_cls, data):
  174 [branch    ]             if not isinstance(data, dict):
  175 [return    ]                 return dc_cls()
  176 [code      ]             kw = {}
  177 [loop      ]             for fld in fields(dc_cls):
  178 [branch    ]                 if fld.name in data:
  179 [code      ]                     kw[fld.name] = data[fld.name]
  180 [return    ]             return dc_cls(**kw)
  181 [blank     ] 
  182 [return    ]         return cls(
  183 [code      ]             enabled=bool(raw.get("enabled", False)),
  184 [code      ]             version=str(raw.get("version", "v11")),
  185 [code      ]             beat=_build(ExpertBeat, raw.get("beat", {})),
  186 [code      ]             lyrics=_build(ExpertLyrics, raw.get("lyrics", {})),
  187 [code      ]             voice=_build(ExpertVoice, raw.get("voice", {})),
  188 [code      ]             mix=_build(ExpertMix, raw.get("mix", {})),
  189 [code      ]             master=_build(ExpertMaster, raw.get("master", {})),
  190 [code      ]             musicgen=_build(ExpertMusicGen, raw.get("musicgen", {})),
  191 [code      ]             anti_neuro=_build(ExpertAntiNeuro, raw.get("anti_neuro", {})),
  192 [code      ]             render=_build(ExpertRender, raw.get("render", {})),
  193 [code      ]         )
  194 [blank     ] 
  195 [blank     ] 
  196 [def       ] def validate(cfg):
  197 [code      ]     errors, warnings = [], []
  198 [branch    ]     if cfg.render.length_sec < 60:
  199 [code      ]         errors.append("render.length_sec < 60 (мин. 1:30)")
  200 [branch    ]     if cfg.render.length_sec > 400:
  201 [code      ]         warnings.append("render.length_sec > 400 очень длинно")
  202 [branch    ]     if cfg.beat.bpm_override is not None:
  203 [branch    ]         if not (40 <= cfg.beat.bpm_override <= 220):
  204 [code      ]             errors.append("beat.bpm_override вне 40..220")
  205 [branch    ]     if not (0 <= cfg.beat.swing_percent <= 60):
  206 [code      ]         warnings.append("beat.swing_percent вне 0..60")
  207 [branch    ]     if cfg.voice.rvc_epochs < 10:
  208 [code      ]         warnings.append("rvc_epochs < 10 — плохое качество")
  209 [branch    ]     if cfg.voice.rvc_epochs > 1000:
  210 [code      ]         warnings.append("rvc_epochs > 1000 — очень долго")
  211 [branch    ]     if not (-60 <= cfg.master.target_lufs <= 0):
  212 [code      ]         errors.append("master.target_lufs вне -60..0 dB")
  213 [branch    ]     if cfg.master.true_peak_max_db > 0:
  214 [code      ]         errors.append("master.true_peak_max_db > 0 dB — клиппы")
  215 [branch    ]     if cfg.anti_neuro.preset not in ("gentle", "standard", "aggressive"):
  216 [code      ]         errors.append("anti_neuro.preset должен быть gentle|standard|aggressive")
  217 [branch    ]     if cfg.render.quality_mode not in ("fast", "quality", "max"):
  218 [code      ]         errors.append("render.quality_mode должен быть fast|quality|max")
  219 [branch    ]     if cfg.voice.mode not in ("rap", "sing", "mix"):
  220 [code      ]         errors.append("voice.mode должен быть rap|sing|mix")
  221 [branch    ]     if cfg.musicgen.variant not in ("auto", "small", "medium", "large"):
  222 [code      ]         errors.append("musicgen.variant должен быть auto|small|medium|large")
  223 [return    ]     return {"errors": errors, "warnings": warnings}
  224 [blank     ] 
  225 [blank     ] 
  226 [def       ] def preset_default():
  227 [return    ]     return ExpertConfig()
  228 [blank     ] 
  229 [blank     ] 
  230 [def       ] def preset_phonk_car():
  231 [code      ]     c = ExpertConfig(enabled=True)
  232 [code      ]     c.beat.kick_pattern = "phonk_808"
  233 [code      ]     c.beat.bass_style = "808_sub"
  234 [code      ]     c.beat.hihat_density = 1.4
  235 [code      ]     c.mix.sidechain_amount = 0.55
  236 [code      ]     c.mix.stereo_width = 1.25
  237 [code      ]     c.master.target_lufs = -8.5
  238 [code      ]     c.anti_neuro.preset = "aggressive"
  239 [code      ]     c.render.length_sec = 150
  240 [return    ]     return c
  241 [blank     ] 
  242 [blank     ] 
  243 [def       ] def preset_hyperpop_tiktok():
  244 [code      ]     c = ExpertConfig(enabled=True)
  245 [code      ]     c.beat.kick_pattern = "hyperpop"
  246 [code      ]     c.beat.hihat_density = 1.6
  247 [code      ]     c.lyrics.include_en_hook = True
  248 [code      ]     c.lyrics.female_backing = True
  249 [code      ]     c.voice.tts_prosody = 1.15
  250 [code      ]     c.mix.reverb_wet = 0.25
  251 [code      ]     c.master.target_lufs = -13.0
  252 [code      ]     c.render.length_sec = 105
  253 [return    ]     return c
  254 [blank     ] 
  255 [blank     ] 
  256 [def       ] def preset_trap_summer():
  257 [code      ]     c = ExpertConfig(enabled=True)
  258 [code      ]     c.beat.kick_pattern = "trap_v2"
  259 [code      ]     c.beat.bass_style = "808_sub"
  260 [code      ]     c.beat.swing_percent = 22.0
  261 [code      ]     c.lyrics.syllable_target = "dense"
  262 [code      ]     c.master.target_lufs = -9.5
  263 [code      ]     c.render.length_sec = 175
  264 [return    ]     return c
  265 [blank     ] 
  266 [blank     ] 
  267 [code      ] BUILTIN_PRESETS = {
  268 [code      ]     "default": preset_default,
  269 [code      ]     "phonk_car": preset_phonk_car,
  270 [code      ]     "hyperpop_tiktok": preset_hyperpop_tiktok,
  271 [code      ]     "trap_summer": preset_trap_summer,
  272 [code      ] }
  273 [blank     ] 
  274 [blank     ] 
  275 [def       ] def apply_preset(name):
  276 [code      ]     fn = BUILTIN_PRESETS.get(name, preset_default)
  277 [return    ]     return fn()
  278 [blank     ] 
  279 [blank     ] 
  280 [def       ] def merge_with_wizard_state(wizard_state, expert):
  281 [branch    ]     if not expert.enabled:
  282 [code      ]         wizard_state["expert_mode_enabled"] = False
  283 [return    ]         return wizard_state
  284 [code      ]     merged = dict(wizard_state)
  285 [code      ]     merged.update(expert.to_flat_dict())
  286 [return    ]     return merged
  287 [blank     ] 
  288 [blank     ] 
  289 [def       ] def _self_test():
  290 [import    ]     import tempfile
  291 [blank     ] 
  292 [code      ]     ok = True
  293 [code      ]     c = preset_default()
  294 [code      ]     ok &= c.enabled is False
  295 [code      ]     ok &= c.render.length_sec == 150
  296 [stmt      ]     with tempfile.TemporaryDirectory() as tmp:
  297 [code      ]         p = os.path.join(tmp, "cfg.json")
  298 [code      ]         c2 = preset_phonk_car()
  299 [code      ]         c2.save(p)
  300 [code      ]         c3 = ExpertConfig.load(p)
  301 [code      ]         ok &= c3.beat.kick_pattern == "phonk_808"
  302 [code      ]         ok &= c3.enabled is True
  303 [code      ]     bad = ExpertConfig()
  304 [code      ]     bad.render.length_sec = 30
  305 [code      ]     bad.master.target_lufs = 5.0
  306 [code      ]     bad.anti_neuro.preset = "xxx"
  307 [code      ]     v = validate(bad)
  308 [code      ]     ok &= len(v["errors"]) >= 3
  309 [code      ]     good = preset_hyperpop_tiktok()
  310 [code      ]     ok &= len(validate(good)["errors"]) == 0
  311 [code      ]     flat = good.to_flat_dict()
  312 [code      ]     ok &= "beat.kick_pattern" in flat
  313 [code      ]     ok &= flat["expert_mode_enabled"] is True
  314 [code      ]     ws = {"length_sec": 120, "some_thing": True}
  315 [code      ]     m1 = merge_with_wizard_state(ws, preset_default())
  316 [code      ]     ok &= m1["expert_mode_enabled"] is False
  317 [code      ]     ok &= m1["length_sec"] == 120
  318 [code      ]     m2 = merge_with_wizard_state(ws, good)
  319 [code      ]     ok &= m2["render.length_sec"] == 105
  320 [return    ]     return ok
  321 [blank     ] 
  322 [blank     ] 
  323 [branch    ] if __name__ == "__main__":
  324 [code      ]     print("expert_mode_v11 self-test:", "OK" if _self_test() else "FAIL")
```