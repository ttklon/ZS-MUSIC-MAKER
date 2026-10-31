# -*- coding: utf-8 -*-
"""
modules/hit_scorer — HIT POTENTIAL SCORER.

Оценивает «хитовость» финального master.wav по 12 метрикам, скоррелированным
с реальными чартовыми характеристиками (Spotify Viral 50 / TikTok Sounds /
Apple Music Top 100). Идеологически — расширение auto_qa, но фокус смещён с
«живости звука» на «шансы попасть в чарт / зайти на TikTok».

Метрики (0..100 каждая, weighted sum → HitScore 0..100):
  1. hook_energy          — пик громкости в припеве vs куплете
  2. hook_repeatability   — сколько раз повторяется главный мотив
  3. chorus_catchiness    — гармоническая яркость + ритмическая простота припева
  4. drop_impact          — контраст drop/build (bass energy delta)
  5. tiktok_hookability   — есть ли 15-30 сек «вирусный кусок» с моментальным входом
  6. bpm_dance_fitness    — BPM в диапазоне 120-140 (dance) или 70-95 (trap)
  7. loudness_lufs        — интегральный LUFS близко к -8..-10 (стриминг-мастер)
  8. stereo_width         — стерео-разъезд (correlation < 0.85)
  9. low_end_power        — sub-bass (20-80 Hz) не рыхлый
 10. vocal_presence       — вокал в диапазоне 2-5 kHz читается
 11. structure_clarity    — узнаваемые границы intro/verse/chorus/outro
 12. novelty              — не «формульный» — уникальные звуковые события

Публичный API — `score_track(master_wav, out_json=None, sr=22050)`.

Раскладка пакета:
  * `audio`        — опциональные зависимости и декодирование/кэш;
  * `hook_metrics` — метрики хука, дропа, TikTok-среза и BPM;
  * `mix_metrics`  — громкость/LUFS, стерео, низ, вокал, форма, новизна;
  * `scoring`      — веса, вердикт, рекомендации, `score_track`.

Без внешних сервисов. librosa/numpy — опциональны: при их отсутствии метрики
деградируют до RMS-оценок и честно помечают provenance.
"""

from __future__ import annotations

from modules.hit_scorer.scoring import WEIGHTS, score_track  # noqa: F401

__all__ = ["WEIGHTS", "score_track"]
