# Production notes — лето, тачки, drift_phonk, время идёт

- Genre: **drift_phonk**
- BPM: **130**
- Key: **?**
- Language: **ru**
- Duration: **180s**

## Pipeline

- _stage_analyze: ok=True 0.003s
- _stage_groove: ok=True 0.0s
- _stage_arrangement: ok=True 0.0s
- _stage_beat: ok=True 1.199s
- _stage_texture: ok=True [fallback,BLOCKED,synthetic] 0.015s
- _stage_lyrics: ok=True [fallback] 0.0s
- _stage_voice_synth: ok=True [fallback,BLOCKED,synthetic] 0.127s
- _stage_rvc: ok=True [BLOCKED] 0.0s
- _stage_vocal_fx: ok=True 0.036s
- _stage_mix_and_sidechain: ok=True 0.537s
- _stage_mastering: ok=True 2.872s
- _stage_polish: ok=True 0.528s
- _stage_stems: ok=True [BLOCKED] 0.0s
- _stage_hit_score: ok=True 1.44s

## Hit metrics
- hit_score: 71.52
- verdict: solid
- metrics: {'hook_energy': {'score': 70.67, 'raw': 1.353366925177391, 'hint': 'loud-quiet dynamic between chorus and verse'}, 'hook_repeatability': {'score': 100.0, 'raw': 144, 'hint': 'how many times main motif repeats'}, 'chorus_catchiness': {'score': 55.0, 'raw': {}, 'hint': 'harmonic simplicity + rhythmic regularity'}, 'drop_impact': {'score': 35.19, 'raw': 2.9326500148047234, 'hint': 'biggest RMS jump = drop'}, 'tiktok_hookability': {'score': 71.37, 'raw': {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}, 'hint': 'instant-hook 25 sec slice for TikTok'}, 'bpm_dance_fitness': {'score': 60.0, 'raw': 0.0, 'hint': 'BPM in dance/trap sweet spot'}, 'loudness_lufs': {'score': 75.0, 'raw': -15.545639799151548, 'hint': 'integrated dBFS ≈ LUFS streaming target'}, 'stereo_width': {'score': 65.0, 'raw': 0.9497310145636214, 'hint': 'channel correlation 0.6-0.85'}, 'low_end_power': {'score': 70.0, 'raw': 6.050439973958294, 'hint': '20-80 Hz vs 200-2000 Hz ratio'}, 'vocal_presence': {'score': 91.32, 'raw': 0.7368858260732413, 'hint': '2-5 kHz vocal readability'}, 'structure_clarity': {'score': 70.0, 'raw': 49, 'hint': 'distinct intro/verse/chorus/outro'}, 'novelty': {'score': 100.0, 'raw': 13.685775756835938, 'hint': 'non-formulaic spectral variety'}}
- tiktok_slice: {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}
- actions: ['Упрости гармонию припева до 2-3 аккордов, ритм — равномерные 4/4', 'Добавь build-up (риз) перед drop и полусекунду тишины перед first-beat drop', 'BPM вне dance-диапазонов. Целься в 120-140 (dance/phonk) или 70-95 (trap)']
- engine: hit_scorer.score_track

## Legal / distribution
- Все использованные сэмплы: CC0 / CC-BY.
- Голос: собственный (RVC от пользователя) или TTS fallback.
- [WARN] ISRC: placeholder (`XX-XXX-00-00000`). Замени на реальный код перед дистрибуцией.
- [WARN] UPC: placeholder. Получи реальный UPC через DistroKid/Amuse/Tunecore.
