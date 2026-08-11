# Production notes — лето, тачки, drift_phonk, время идёт

- Genre: **drift_phonk**
- BPM: **130**
- Key: **?**
- Language: **ru**
- Duration: **180s**

## Pipeline

- _stage_analyze: ok=True 0.007s
- _stage_groove: ok=True 0.002s
- _stage_arrangement: ok=True 0.003s
- _stage_beat: ok=True 2.504s
- _stage_texture: ok=True [fallback,BLOCKED,synthetic] 0.034s
- _stage_lyrics: ok=True [fallback] 0.001s
- _stage_voice_synth: ok=True [fallback,BLOCKED,synthetic] 0.363s
- _stage_rvc: ok=True [BLOCKED] 0.0s
- _stage_vocal_fx: ok=True 0.1s
- _stage_mix_and_sidechain: ok=True 1.555s
- _stage_mastering: ok=True 6.689s
- _stage_polish: ok=True 1.611s
- _stage_stems: ok=True [BLOCKED] 0.0s
- _stage_hit_score: ok=True 28.857s

## Hit metrics
- hit_score: 73.68
- verdict: solid
- metrics: {'hook_energy': {'score': 53.47, 'raw': 1.2673523592812912, 'hint': 'loud-quiet dynamic between chorus and verse'}, 'hook_repeatability': {'score': 100.0, 'raw': 118, 'hint': 'how many times main motif repeats'}, 'chorus_catchiness': {'score': 79.81, 'raw': {'tempo': 129.19921875, 'peaks': 92, 'chroma_var': 0.1081693172454834}, 'hint': 'harmonic simplicity + rhythmic regularity'}, 'drop_impact': {'score': 27.45, 'raw': 2.28791345145359, 'hint': 'biggest RMS jump = drop'}, 'tiktok_hookability': {'score': 68.41, 'raw': {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}, 'hint': 'instant-hook 25 sec slice for TikTok'}, 'bpm_dance_fitness': {'score': 100.0, 'raw': 129.19921875, 'hint': 'BPM in dance/trap sweet spot'}, 'loudness_lufs': {'score': 95.0, 'raw': -12.562373559843707, 'hint': 'integrated dBFS ≈ LUFS streaming target'}, 'stereo_width': {'score': 40.0, 'raw': 0.9514525846899267, 'hint': 'channel correlation 0.6-0.85'}, 'low_end_power': {'score': 70.0, 'raw': 4.4311304533646805, 'hint': '20-80 Hz vs 200-2000 Hz ratio'}, 'vocal_presence': {'score': 90.4, 'raw': 0.7266338591164134, 'hint': '2-5 kHz vocal readability'}, 'structure_clarity': {'score': 70.0, 'raw': 42, 'hint': 'distinct intro/verse/chorus/outro'}, 'novelty': {'score': 100.0, 'raw': 26.127883911132812, 'hint': 'non-formulaic spectral variety'}}
- tiktok_slice: {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}
- actions: ['Припев тише куплета — подними RMS припева на +2 dB или сделай drop громче', 'Добавь build-up (риз) перед drop и полусекунду тишины перед first-beat drop', 'Стерео-картинка слишком узкая или слишком широкая. Целься в correlation 0.6-0.85']
- engine: hit_scorer.score_track

## Legal / distribution
- Все использованные сэмплы: CC0 / CC-BY.
- Голос: собственный (RVC от пользователя) или TTS fallback.
- [WARN] ISRC: placeholder (`XX-XXX-00-00000`). Замени на реальный код перед дистрибуцией.
- [WARN] UPC: placeholder. Получи реальный UPC через DistroKid/Amuse/Tunecore.
