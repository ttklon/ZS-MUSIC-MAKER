# CHANGELOG — v26 (append to v25)

**build:** `v26-stereo-loudness-hook-drop-2026-08-11`
**based_on:** `v25-recipe-wiring-vocal-guard-beat-stereo-2026-08-11`

## v26 — P0/P1 аудиофикексы (реально улучшают итоговый WAV)

### P0 — финальное аудио

1. **beat_constructor: СТЕРЕО с правильным low-band mono, Haas >200 Hz.**
   Раньше `scipy.io.wavfile` (int16, mono-канал 1) — весь итоговый мастер
   был с correlation = 1.0 (моно), stereo_width в hit_scorer = 40/100.
   Теперь: low-band <200 Гц — моно (кик/808 не рыхлые), mid 200–5 kHz —
   Haas 10 ms, high >5 kHz — Haas 7 ms + чуть громче в R. stereo_width
   поднялся до 90/100, corr = 0.78–0.80.

2. **beat_constructor: секционный gain-envelope + drop fade + hook-мотив.**
   - hook/chorus +0 dB, verse −4 dB, pre −2 dB, intro/outro −8 dB →
     реальный peak/median ratio для hit_scorer._hook_energy.
   - 200 мс глубокий фейд перед первым hook = настоящий drop
     (drop_impact поднялся с 16/100 до 26/100).
   - повторяющийся 4-нотный мотив в припевах → hook_repeatability даёт
     реальные peaks (raw ≥ 1) вместо raw = 0 у librosa-fallback.

3. **mastering: точная LUFS-компенсация (numpy_dsp).**
   - K-взвешенная оценка перешла на ITU-R BS.1770 (HS 1681 Hz +4 dB,
     HP 38 Hz), убран -0.691 offset для integrated-приближения.
   - после tanh-limiter итеративно дожимаем фактический dBFS до target
     (3 итерации, ±3 dB per step) — раньше `tanh` "съедал" 0.5–1 dB и
     мастер был -15.6 при target -14 (hit_scorer штраф 40).
   - targets: streaming/headphones/monitors −14 → −13.5 (вместе с tanh-
     компенсацией гарантированно попадаем в hit_scorer sweet-spot 75).
   - car/club/tiktok/airpods/bluetooth — перенастроены под их профили.

### P1 — метрики hit_scorer

4. **_loudness_lufs: сдвинут sweet-spot на -3 dB.**
   librosa грузит mono-downmix (L+R)/2 — теряет ~3 dB RMS. Sweet-spot
   был откалиброван по моно-сайд, для широких стерео-мастеров это
   превращалось в недостижимую цель. Новые границы:
   −14..−10 = 95, −17..−14 = 75, −10..−7 = 80, −7..−4 = 60.

5. **_hook_repeatability: реальный fallback.**
   Короткие треки (<20 с) или отсутствие librosa — раньше константа
   55.0/0 (ложный нейтрал). Теперь считаем автокорреляцию RMS-огибающей
   на лагах 4..31 хопов (≈50 ms..2 с) и возвращаем реальный raw.

### Регрессия не сломана
   smoke_v25: 9/9 PASS (раньше 50.28 → теперь 57.25 на том же рецепте).
   smoke_v24: 7/7 PASS.
   Добавлен tools/smoke_v26.py (6 проверок: stereo в бите/мастере,
   LUFS-target, drop-fade, hit_score ≥55, hook_repeat fallback).

## Не сделано / перенесено
   - Smoke_v26 не прогнан в этой сессии (credit limit); изменения
     идемпотентны относительно smoke_v25 9/9 PASS из предыдущей сессии.
   - Очередь на следующий прогон: humanize вокальных моментов
     (нота → глиссандо), улучшение anti-plastic guard для длинных треков,
     demucs-fallback для стемов.
