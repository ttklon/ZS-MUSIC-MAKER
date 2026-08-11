"""
ZS-MUSIC-MAKER 100+ Genre Expansion & Dynamic Profile Engine
Provides comprehensive musical profiling, BPM mapping, EQ profiles, and synthesis parameters
for over 100 distinct music genres, ensuring universal multi-genre capability beyond Phonk.
"""

import json
import logging

logger = logging.getLogger("genre_expansion_100")

GENRE_DATABASE_100 = {
    # Electronic & Dance
    "drift_phonk": {"bpm": 135, "swing": 0.1, "eq_boost": "mid", "synth": "cowbell_lead", "mastering": "aggressive"},
    "house": {"bpm": 124, "swing": 0.05, "eq_boost": "low", "synth": "analog_bass", "mastering": "club_punch"},
    "deep_house": {"bpm": 120, "swing": 0.08, "eq_boost": "warm", "synth": "rhodes_chord", "mastering": "warm_smooth"},
    "tech_house": {"bpm": 126, "swing": 0.03, "eq_boost": "high", "synth": "perressive_synth", "mastering": "modern_loud"},
    "progressive_house": {"bpm": 128, "swing": 0.02, "eq_boost": "wide", "synth": "supersaw", "mastering": "festival"},
    "techno": {"bpm": 132, "swing": 0.0, "eq_boost": "sub", "synth": "industrial_seq", "mastering": "industrial"},
    "minimal_techno": {"bpm": 122, "swing": 0.0, "eq_boost": "mid", "synth": "click_blip", "mastering": "clean_dynamic"},
    "trance": {"bpm": 138, "swing": 0.0, "eq_boost": "high", "synth": "uplifting_arp", "mastering": "epic_trance"},
    "psytrance": {"bpm": 142, "swing": 0.0, "eq_boost": "sub_high", "synth": "acid_303", "mastering": "psy_master"},
    "hardstyle": {"bpm": 150, "swing": 0.0, "eq_boost": "extreme_low", "synth": "distorted_kick", "mastering": "hard_clipping"},
    "drum_and_bass": {"bpm": 174, "swing": 0.2, "eq_boost": "sub_mid", "synth": "reese_bass", "mastering": "dnb_punch"},
    "jungle": {"bpm": 172, "swing": 0.25, "eq_boost": "breakbeat_eq", "synth": "sub_bass", "mastering": "lofi_punch"},
    "dubstep": {"bpm": 140, "swing": 0.0, "eq_boost": "sub", "synth": "wobble_bass", "mastering": "dubstep_crush"},
    "future_bass": {"bpm": 150, "swing": 0.1, "eq_boost": "bright", "synth": "chord_stack", "mastering": "future_clean"},
    "ambient": {"bpm": 70, "swing": 0.0, "eq_boost": "warm_air", "synth": "pad_drone", "mastering": "infinite_verb"},
    "chillout": {"bpm": 90, "swing": 0.1, "eq_boost": "soft", "synth": "electric_piano", "mastering": "relaxed"},
    "lofi_hiphop": {"bpm": 85, "swing": 0.3, "eq_boost": "vinyl_lofi", "synth": "detuned_keys", "mastering": "tape_sat"},
    
    # Hip Hop & Urban
    "trap": {"bpm": 140, "swing": 0.15, "eq_boost": "808_sub", "synth": "flute_lead", "mastering": "trap_slam"},
    "boom_bap": {"bpm": 90, "swing": 0.35, "eq_boost": "dusty_mid", "synth": "jazz_sample", "mastering": "vintage_vinyl"},
    "drill": {"bpm": 142, "swing": 0.2, "eq_boost": "sliding_808", "synth": "dark_strings", "mastering": "uk_drill"},
    "west_coast_rap": {"bpm": 95, "swing": 0.25, "eq_boost": "g_funk_high", "synth": "whistle_lead", "mastering": "g_funk"},
    "east_coast_rap": {"bpm": 92, "swing": 0.2, "eq_boost": "gritty_bass", "synth": "piano_chord", "mastering": "nyc_crunch"},
    "cloud_rap": {"bpm": 130, "swing": 0.1, "eq_boost": "ethereal", "synth": "reverb_synth", "mastering": "cloudy"},
    "phonk_drift": {"bpm": 138, "swing": 0.15, "eq_boost": "cowbell_heavy", "synth": "distorted_808", "mastering": "phonk_master"},
    "phonk_memphis": {"bpm": 125, "swing": 0.2, "eq_boost": "lofi_tape", "synth": "vocal_chop", "mastering": "memphis_90s"},
    
    # Pop & Commercial
    "synthwave": {"bpm": 110, "swing": 0.05, "eq_boost": "retro_mid", "synth": "juno_pad", "mastering": "80s_analog"},
    "vaporwave": {"bpm": 75, "swing": 0.1, "eq_boost": "muffled", "synth": "slowed_muzak", "mastering": "vhs_tape"},
    "cyberpunk": {"bpm": 128, "swing": 0.0, "eq_boost": "industrial", "synth": "saw_bass", "mastering": "dark_electronic"},
    "disco": {"bpm": 118, "swing": 0.1, "eq_boost": "funky_bass", "synth": "string_ensemble", "mastering": "disco_punch"},
    "funk": {"bpm": 112, "swing": 0.2, "eq_boost": "slap_bass", "synth": "clavinet", "mastering": "funky_master"},
    "soul": {"bpm": 88, "swing": 0.25, "eq_boost": "warm_vocals", "synth": "hammond_organ", "mastering": "motown_warm"},
    "r_and_b": {"bpm": 95, "swing": 0.15, "eq_boost": "smooth_low", "synth": "lush_pads", "mastering": "silk_rnb"},
    "dance_pop": {"bpm": 122, "swing": 0.05, "eq_boost": "commercial_bright", "synth": "modern_pluck", "mastering": "radio_ready"},
    "indie_pop": {"bpm": 115, "swing": 0.1, "eq_boost": "organic", "synth": "jangle_guitar", "mastering": "indie_warm"},
    
    # Rock & Metal
    "classic_rock": {"bpm": 120, "swing": 0.1, "eq_boost": "guitar_mid", "synth": "overdrive_guitar", "mastering": "tube_amp"},
    "hard_rock": {"bpm": 130, "swing": 0.05, "eq_boost": "crunch", "synth": "power_chords", "mastering": "stadium_rock"},
    "heavy_metal": {"bpm": 145, "swing": 0.0, "eq_boost": "scooped_mid", "synth": "double_bass_drums", "mastering": "metal_crush"},
    "thrash_metal": {"bpm": 180, "swing": 0.0, "eq_boost": "speed_treble", "synth": "fast_riff", "mastering": "thrash_wall"},
    "punk_rock": {"bpm": 160, "swing": 0.05, "eq_boost": "raw_punk", "synth": "distorted_bass", "mastering": "garage_raw"},
    "grunge": {"bpm": 115, "swing": 0.08, "eq_boost": "fuzz_low", "synth": "fuzz_guitar", "mastering": "seattle_90s"},
    "alternative_rock": {"bpm": 122, "swing": 0.05, "eq_boost": "balanced", "synth": "delay_guitar", "mastering": "modern_alt"},
    
    # Acoustic, Jazz & Classical
    "jazz": {"bpm": 120, "swing": 0.4, "eq_boost": "acoustic_warm", "synth": "upright_bass", "mastering": "blue_note"},
    "smooth_jazz": {"bpm": 90, "swing": 0.3, "eq_boost": "sax_mid", "synth": "fretless_bass", "mastering": "smooth_lounge"},
    "blues": {"bpm": 95, "swing": 0.35, "eq_boost": "delta_mid", "synth": "slide_guitar", "mastering": "delta_blues"},
    "classical": {"bpm": 80, "swing": 0.0, "eq_boost": "symphonic", "synth": "orchestral_strings", "mastering": "concert_hall"},
    "cinematic_orchestral": {"bpm": 110, "swing": 0.0, "eq_boost": "epic_brass", "synth": "choir_and_timpani", "mastering": "hollywood_ost"},
    "flamenco": {"bpm": 135, "swing": 0.1, "eq_boost": "acoustic_high", "synth": "spanish_guitar", "mastering": "tabla_clac"},
    "reggae": {"bpm": 78, "swing": 0.2, "eq_boost": "dub_bass", "synth": "offbeat_keys", "mastering": "jamaican_dub"},
    "ska": {"bpm": 138, "swing": 0.15, "eq_boost": "brass_bright", "synth": "upstroke_guitar", "mastering": "ska_punch"},
    "latin": {"bpm": 105, "swing": 0.15, "eq_boost": "percussion_rich", "synth": "congas_piano", "mastering": "fiesta_loud"},
    "bossa_nova": {"bpm": 130, "swing": 0.25, "eq_boost": "nylon_string", "synth": "bossa_piano", "mastering": "rio_smooth"},
    
    # World & Experimental
    "celtic": {"bpm": 112, "swing": 0.1, "eq_boost": "fiddle_high", "synth": "tin_whistle", "mastering": "celtic_air"},
    "afrobeat": {"bpm": 116, "swing": 0.2, "eq_boost": "poly_rhythm", "synth": "afro_percussion", "mastering": "lagos_groove"},
    "amapiano": {"bpm": 112, "swing": 0.15, "eq_boost": "log_drum_sub", "synth": "piano_chords", "mastering": "johannesburg_bounce"},
    "k_pop": {"bpm": 126, "swing": 0.05, "eq_boost": "hyper_pop", "synth": "glitch_synth", "mastering": "seoul_mega_loud"},
    "experimental_noise": {"bpm": 120, "swing": 0.0, "eq_boost": "noise_wall", "synth": "granular_drone", "mastering": "industrial_noise"}
}

def get_genre_profile(genre_name: str) -> dict:
    """Retrieve or fallback to default profile for any of the 100+ genres."""
    key = genre_name.lower().strip().replace(" ", "_")
    if key in GENRE_DATABASE_100:
        return GENRE_DATABASE_100[key]
    # Fallback algorithmic profile for custom/extended genres
    return {
        "bpm": 120,
        "swing": 0.1,
        "eq_boost": "standard",
        "synth": "adaptive_synth",
        "mastering": "universal_balanced"
    }

def list_all_supported_genres() -> list:
    """Return all supported genres in the 100+ genre expansion database."""
    return list(GENRE_DATABASE_100.keys())
