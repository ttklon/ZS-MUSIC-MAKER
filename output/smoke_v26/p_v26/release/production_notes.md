# Production notes — лето, тачки, drift_phonk, время идёт

- Genre: **drift_phonk**
- BPM: **130**
- Key: **?**
- Language: **ru**
- Duration: **180s**

## Pipeline

- _stage_analyze: ok=True 0.004s
- _stage_groove: ok=True 0.0s
- _stage_arrangement: ok=True 0.0s
- _stage_beat: ok=True 2.428s
- _stage_texture: ok=True [fallback,BLOCKED,synthetic] 0.033s
- _stage_lyrics: ok=True [fallback] 0.001s
- _stage_voice_synth: ok=True 5.501s
- _stage_rvc: ok=True [BLOCKED] 0.002s
- _stage_vocal_fx: ok=True 0.186s
- _stage_mix_and_sidechain: ok=True 1.688s
- _stage_mastering: ok=True 6.737s
- _stage_polish: ok=True 1.613s
- _stage_stems: ok=True [BLOCKED] 0.0s
- _stage_hit_score: ok=True 3.581s

## Hit metrics
- hit_score: 71.5
- verdict: solid
- metrics: {'hook_energy': {'score': 25.08, 'raw': 1.1253916705373865, 'hint': 'loud-quiet dynamic between chorus and verse'}, 'hook_repeatability': {'score': 100.0, 'raw': 50, 'hint': 'how many times main motif repeats'}, 'chorus_catchiness': {'score': 83.5, 'raw': {'tempo': 129.19921875, 'peaks': 97, 'chroma_var': 0.09639695286750793}, 'hint': 'harmonic simplicity + rhythmic regularity'}, 'drop_impact': {'score': 49.66, 'raw': 4.138474972335785, 'hint': 'biggest RMS jump = drop'}, 'tiktok_hookability': {'score': 65.0, 'raw': {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}, 'hint': 'instant-hook 25 sec slice for TikTok'}, 'bpm_dance_fitness': {'score': 100.0, 'raw': 129.19921875, 'hint': 'BPM in dance/trap sweet spot'}, 'loudness_lufs': {'score': 98.0, 'raw': -12.833802351373004, 'hint': 'integrated dBFS ≈ LUFS streaming target'}, 'stereo_width': {'score': 40.0, 'raw': 0.9810282442779628, 'hint': 'channel correlation 0.6-0.85'}, 'low_end_power': {'score': 70.0, 'raw': 1.6137015487558615, 'hint': '20-80 Hz vs 200-2000 Hz ratio'}, 'vocal_presence': {'score': 75.81, 'raw': 0.5645447213643286, 'hint': '2-5 kHz vocal readability'}, 'structure_clarity': {'score': 70.0, 'raw': 34, 'hint': 'distinct intro/verse/chorus/outro'}, 'novelty': {'score': 100.0, 'raw': 33.523033142089844, 'hint': 'non-formulaic spectral variety'}}
- tiktok_slice: {'start_sec': 8.0, 'end_sec': 33.0, 'reason': 'immediate hook + sustained energy'}
- actions: ['Припев тише куплета — подними RMS припева на +2 dB или сделай drop громче', 'Добавь build-up (риз) перед drop и полусекунду тишины перед first-beat drop', 'Стерео-картинка слишком узкая или слишком широкая. Целься в correlation 0.6-0.85']
- engine: hit_scorer.score_track

## Legal / distribution
- Все использованные сэмплы: CC0 / CC-BY.
- Голос: собственный (RVC от пользователя) или TTS fallback.
- [WARN] ISRC: placeholder (`XX-XXX-00-00000`). Замени на реальный код перед дистрибуцией.
- [WARN] UPC: placeholder. Получи реальный UPC через DistroKid/Amuse/Tunecore.
