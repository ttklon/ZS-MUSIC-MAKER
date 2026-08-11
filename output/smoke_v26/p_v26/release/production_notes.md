# Production notes — лето, тачки, drift_phonk, время идёт

- Genre: **drift_phonk**
- BPM: **130**
- Key: **?**
- Language: **ru**
- Duration: **180s**

## Pipeline

- _stage_analyze: ok=True 0.006s
- _stage_groove: ok=True 0.0s
- _stage_arrangement: ok=True 0.0s
- _stage_beat: ok=True 2.653s
- _stage_texture: ok=True [fallback,BLOCKED,synthetic] 0.033s
- _stage_lyrics: ok=True [fallback] 0.001s
- _stage_voice_synth: ok=True [fallback,BLOCKED,synthetic] 0.314s
- _stage_rvc: ok=True [BLOCKED] 0.0s
- _stage_vocal_fx: ok=True 0.094s
- _stage_mix_and_sidechain: ok=True 1.461s
- _stage_mastering: ok=True 3.108s
- _stage_polish: ok=True [fallback] 0.167s
- _stage_stems: ok=True [BLOCKED] 0.0s
- _stage_hit_score: ok=True 3.52s

## Hit metrics
- hit_score: 67.46
- verdict: needs_work
- metrics: {'hook_energy': {'score': 36.85, 'raw': 1.1842707761416098, 'hint': 'loud-quiet dynamic between chorus and verse'}, 'hook_repeatability': {'score': 100.0, 'raw': 122, 'hint': 'how many times main motif repeats'}, 'chorus_catchiness': {'score': 55.0, 'raw': {}, 'hint': 'harmonic simplicity + rhythmic regularity'}, 'drop_impact': {'score': 31.39, 'raw': 2.6155323075029373, 'hint': 'biggest RMS jump = drop'}, 'tiktok_hookability': {'score': 71.19, 'raw': {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}, 'hint': 'instant-hook 25 sec slice for TikTok'}, 'bpm_dance_fitness': {'score': 60.0, 'raw': 0.0, 'hint': 'BPM in dance/trap sweet spot'}, 'loudness_lufs': {'score': 95.0, 'raw': -12.548514254002722, 'hint': 'integrated dBFS ≈ LUFS streaming target'}, 'stereo_width': {'score': 40.0, 'raw': 0.95326010378202, 'hint': 'channel correlation 0.6-0.85'}, 'low_end_power': {'score': 70.0, 'raw': 4.347427459352277, 'hint': '20-80 Hz vs 200-2000 Hz ratio'}, 'vocal_presence': {'score': 90.47, 'raw': 0.7273894423043038, 'hint': '2-5 kHz vocal readability'}, 'structure_clarity': {'score': 70.0, 'raw': 44, 'hint': 'distinct intro/verse/chorus/outro'}, 'novelty': {'score': 100.0, 'raw': 26.12348747253418, 'hint': 'non-formulaic spectral variety'}}
- tiktok_slice: {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}
- actions: ['Припев тише куплета — подними RMS припева на +2 dB или сделай drop громче', 'Упрости гармонию припева до 2-3 аккордов, ритм — равномерные 4/4', 'Добавь build-up (риз) перед drop и полусекунду тишины перед first-beat drop', 'BPM вне dance-диапазонов. Целься в 120-140 (dance/phonk) или 70-95 (trap)', 'Стерео-картинка слишком узкая или слишком широкая. Целься в correlation 0.6-0.85']
- engine: hit_scorer.score_track

## Legal / distribution
- Все использованные сэмплы: CC0 / CC-BY.
- Голос: собственный (RVC от пользователя) или TTS fallback.
- [WARN] ISRC: placeholder (`XX-XXX-00-00000`). Замени на реальный код перед дистрибуцией.
- [WARN] UPC: placeholder. Получи реальный UPC через DistroKid/Amuse/Tunecore.
