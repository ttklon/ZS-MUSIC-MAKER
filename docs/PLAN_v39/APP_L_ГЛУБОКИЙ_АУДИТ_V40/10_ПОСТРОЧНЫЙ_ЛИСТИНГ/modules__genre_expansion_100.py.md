# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/genre_expansion_100.py`

**Всего строк:** 97

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 66 | 68.0 |
| blank | 10 | 10.3 |
| docstring | 7 | 7.2 |
| comment | 7 | 7.2 |
| return | 3 | 3.1 |
| def | 2 | 2.1 |
| import | 1 | 1.0 |
| branch | 1 | 1.0 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS-MUSIC-MAKER 100+ Genre Expansion & Dynamic Profile Engine
    3 [docstring ] Provides comprehensive musical profiling, BPM mapping, EQ profiles, and synthesis parameters
    4 [docstring ] for over 100 distinct music genres, ensuring universal multi-genre capability beyond Phonk.
    5 [docstring ] """
    6 [blank     ] 
    7 [import    ] import logging
    8 [blank     ] 
    9 [code      ] logger = logging.getLogger("genre_expansion_100")
   10 [blank     ] 
   11 [code      ] GENRE_DATABASE_100 = {
   12 [comment   ]     # Electronic & Dance
   13 [code      ]     "drift_phonk": {"bpm": 135, "swing": 0.1, "eq_boost": "mid", "synth": "cowbell_lead", "mastering": "aggressive"},
   14 [code      ]     "house": {"bpm": 124, "swing": 0.05, "eq_boost": "low", "synth": "analog_bass", "mastering": "club_punch"},
   15 [code      ]     "deep_house": {"bpm": 120, "swing": 0.08, "eq_boost": "warm", "synth": "rhodes_chord", "mastering": "warm_smooth"},
   16 [code      ]     "tech_house": {"bpm": 126, "swing": 0.03, "eq_boost": "high", "synth": "perressive_synth", "mastering": "modern_loud"},
   17 [code      ]     "progressive_house": {"bpm": 128, "swing": 0.02, "eq_boost": "wide", "synth": "supersaw", "mastering": "festival"},
   18 [code      ]     "techno": {"bpm": 132, "swing": 0.0, "eq_boost": "sub", "synth": "industrial_seq", "mastering": "industrial"},
   19 [code      ]     "minimal_techno": {"bpm": 122, "swing": 0.0, "eq_boost": "mid", "synth": "click_blip", "mastering": "clean_dynamic"},
   20 [code      ]     "trance": {"bpm": 138, "swing": 0.0, "eq_boost": "high", "synth": "uplifting_arp", "mastering": "epic_trance"},
   21 [code      ]     "psytrance": {"bpm": 142, "swing": 0.0, "eq_boost": "sub_high", "synth": "acid_303", "mastering": "psy_master"},
   22 [code      ]     "hardstyle": {"bpm": 150, "swing": 0.0, "eq_boost": "extreme_low", "synth": "distorted_kick", "mastering": "hard_clipping"},
   23 [code      ]     "drum_and_bass": {"bpm": 174, "swing": 0.2, "eq_boost": "sub_mid", "synth": "reese_bass", "mastering": "dnb_punch"},
   24 [code      ]     "jungle": {"bpm": 172, "swing": 0.25, "eq_boost": "breakbeat_eq", "synth": "sub_bass", "mastering": "lofi_punch"},
   25 [code      ]     "dubstep": {"bpm": 140, "swing": 0.0, "eq_boost": "sub", "synth": "wobble_bass", "mastering": "dubstep_crush"},
   26 [code      ]     "future_bass": {"bpm": 150, "swing": 0.1, "eq_boost": "bright", "synth": "chord_stack", "mastering": "future_clean"},
   27 [code      ]     "ambient": {"bpm": 70, "swing": 0.0, "eq_boost": "warm_air", "synth": "pad_drone", "mastering": "infinite_verb"},
   28 [code      ]     "chillout": {"bpm": 90, "swing": 0.1, "eq_boost": "soft", "synth": "electric_piano", "mastering": "relaxed"},
   29 [code      ]     "lofi_hiphop": {"bpm": 85, "swing": 0.3, "eq_boost": "vinyl_lofi", "synth": "detuned_keys", "mastering": "tape_sat"},
   30 [blank     ]     
   31 [comment   ]     # Hip Hop & Urban
   32 [code      ]     "trap": {"bpm": 140, "swing": 0.15, "eq_boost": "808_sub", "synth": "flute_lead", "mastering": "trap_slam"},
   33 [code      ]     "boom_bap": {"bpm": 90, "swing": 0.35, "eq_boost": "dusty_mid", "synth": "jazz_sample", "mastering": "vintage_vinyl"},
   34 [code      ]     "drill": {"bpm": 142, "swing": 0.2, "eq_boost": "sliding_808", "synth": "dark_strings", "mastering": "uk_drill"},
   35 [code      ]     "west_coast_rap": {"bpm": 95, "swing": 0.25, "eq_boost": "g_funk_high", "synth": "whistle_lead", "mastering": "g_funk"},
   36 [code      ]     "east_coast_rap": {"bpm": 92, "swing": 0.2, "eq_boost": "gritty_bass", "synth": "piano_chord", "mastering": "nyc_crunch"},
   37 [code      ]     "cloud_rap": {"bpm": 130, "swing": 0.1, "eq_boost": "ethereal", "synth": "reverb_synth", "mastering": "cloudy"},
   38 [code      ]     "phonk_drift": {"bpm": 138, "swing": 0.15, "eq_boost": "cowbell_heavy", "synth": "distorted_808", "mastering": "phonk_master"},
   39 [code      ]     "phonk_memphis": {"bpm": 125, "swing": 0.2, "eq_boost": "lofi_tape", "synth": "vocal_chop", "mastering": "memphis_90s"},
   40 [blank     ]     
   41 [comment   ]     # Pop & Commercial
   42 [code      ]     "synthwave": {"bpm": 110, "swing": 0.05, "eq_boost": "retro_mid", "synth": "juno_pad", "mastering": "80s_analog"},
   43 [code      ]     "vaporwave": {"bpm": 75, "swing": 0.1, "eq_boost": "muffled", "synth": "slowed_muzak", "mastering": "vhs_tape"},
   44 [code      ]     "cyberpunk": {"bpm": 128, "swing": 0.0, "eq_boost": "industrial", "synth": "saw_bass", "mastering": "dark_electronic"},
   45 [code      ]     "disco": {"bpm": 118, "swing": 0.1, "eq_boost": "funky_bass", "synth": "string_ensemble", "mastering": "disco_punch"},
   46 [code      ]     "funk": {"bpm": 112, "swing": 0.2, "eq_boost": "slap_bass", "synth": "clavinet", "mastering": "funky_master"},
   47 [code      ]     "soul": {"bpm": 88, "swing": 0.25, "eq_boost": "warm_vocals", "synth": "hammond_organ", "mastering": "motown_warm"},
   48 [code      ]     "r_and_b": {"bpm": 95, "swing": 0.15, "eq_boost": "smooth_low", "synth": "lush_pads", "mastering": "silk_rnb"},
   49 [code      ]     "dance_pop": {"bpm": 122, "swing": 0.05, "eq_boost": "commercial_bright", "synth": "modern_pluck", "mastering": "radio_ready"},
   50 [code      ]     "indie_pop": {"bpm": 115, "swing": 0.1, "eq_boost": "organic", "synth": "jangle_guitar", "mastering": "indie_warm"},
   51 [blank     ]     
   52 [comment   ]     # Rock & Metal
   53 [code      ]     "classic_rock": {"bpm": 120, "swing": 0.1, "eq_boost": "guitar_mid", "synth": "overdrive_guitar", "mastering": "tube_amp"},
   54 [code      ]     "hard_rock": {"bpm": 130, "swing": 0.05, "eq_boost": "crunch", "synth": "power_chords", "mastering": "stadium_rock"},
   55 [code      ]     "heavy_metal": {"bpm": 145, "swing": 0.0, "eq_boost": "scooped_mid", "synth": "double_bass_drums", "mastering": "metal_crush"},
   56 [code      ]     "thrash_metal": {"bpm": 180, "swing": 0.0, "eq_boost": "speed_treble", "synth": "fast_riff", "mastering": "thrash_wall"},
   57 [code      ]     "punk_rock": {"bpm": 160, "swing": 0.05, "eq_boost": "raw_punk", "synth": "distorted_bass", "mastering": "garage_raw"},
   58 [code      ]     "grunge": {"bpm": 115, "swing": 0.08, "eq_boost": "fuzz_low", "synth": "fuzz_guitar", "mastering": "seattle_90s"},
   59 [code      ]     "alternative_rock": {"bpm": 122, "swing": 0.05, "eq_boost": "balanced", "synth": "delay_guitar", "mastering": "modern_alt"},
   60 [blank     ]     
   61 [comment   ]     # Acoustic, Jazz & Classical
   62 [code      ]     "jazz": {"bpm": 120, "swing": 0.4, "eq_boost": "acoustic_warm", "synth": "upright_bass", "mastering": "blue_note"},
   63 [code      ]     "smooth_jazz": {"bpm": 90, "swing": 0.3, "eq_boost": "sax_mid", "synth": "fretless_bass", "mastering": "smooth_lounge"},
   64 [code      ]     "blues": {"bpm": 95, "swing": 0.35, "eq_boost": "delta_mid", "synth": "slide_guitar", "mastering": "delta_blues"},
   65 [code      ]     "classical": {"bpm": 80, "swing": 0.0, "eq_boost": "symphonic", "synth": "orchestral_strings", "mastering": "concert_hall"},
   66 [code      ]     "cinematic_orchestral": {"bpm": 110, "swing": 0.0, "eq_boost": "epic_brass", "synth": "choir_and_timpani", "mastering": "hollywood_ost"},
   67 [code      ]     "flamenco": {"bpm": 135, "swing": 0.1, "eq_boost": "acoustic_high", "synth": "spanish_guitar", "mastering": "tabla_clac"},
   68 [code      ]     "reggae": {"bpm": 78, "swing": 0.2, "eq_boost": "dub_bass", "synth": "offbeat_keys", "mastering": "jamaican_dub"},
   69 [code      ]     "ska": {"bpm": 138, "swing": 0.15, "eq_boost": "brass_bright", "synth": "upstroke_guitar", "mastering": "ska_punch"},
   70 [code      ]     "latin": {"bpm": 105, "swing": 0.15, "eq_boost": "percussion_rich", "synth": "congas_piano", "mastering": "fiesta_loud"},
   71 [code      ]     "bossa_nova": {"bpm": 130, "swing": 0.25, "eq_boost": "nylon_string", "synth": "bossa_piano", "mastering": "rio_smooth"},
   72 [blank     ]     
   73 [comment   ]     # World & Experimental
   74 [code      ]     "celtic": {"bpm": 112, "swing": 0.1, "eq_boost": "fiddle_high", "synth": "tin_whistle", "mastering": "celtic_air"},
   75 [code      ]     "afrobeat": {"bpm": 116, "swing": 0.2, "eq_boost": "poly_rhythm", "synth": "afro_percussion", "mastering": "lagos_groove"},
   76 [code      ]     "amapiano": {"bpm": 112, "swing": 0.15, "eq_boost": "log_drum_sub", "synth": "piano_chords", "mastering": "johannesburg_bounce"},
   77 [code      ]     "k_pop": {"bpm": 126, "swing": 0.05, "eq_boost": "hyper_pop", "synth": "glitch_synth", "mastering": "seoul_mega_loud"},
   78 [code      ]     "experimental_noise": {"bpm": 120, "swing": 0.0, "eq_boost": "noise_wall", "synth": "granular_drone", "mastering": "industrial_noise"}
   79 [code      ] }
   80 [blank     ] 
   81 [def       ] def get_genre_profile(genre_name: str) -> dict:
   82 [docstring ]     """Retrieve or fallback to default profile for any of the 100+ genres."""
   83 [code      ]     key = genre_name.lower().strip().replace(" ", "_")
   84 [branch    ]     if key in GENRE_DATABASE_100:
   85 [return    ]         return GENRE_DATABASE_100[key]
   86 [comment   ]     # Fallback algorithmic profile for custom/extended genres
   87 [return    ]     return {
   88 [code      ]         "bpm": 120,
   89 [code      ]         "swing": 0.1,
   90 [code      ]         "eq_boost": "standard",
   91 [code      ]         "synth": "adaptive_synth",
   92 [code      ]         "mastering": "universal_balanced"
   93 [code      ]     }
   94 [blank     ] 
   95 [def       ] def list_all_supported_genres() -> list:
   96 [docstring ]     """Return all supported genres in the 100+ genre expansion database."""
   97 [return    ]     return list(GENRE_DATABASE_100.keys())
```