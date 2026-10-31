# -*- coding: utf-8 -*-
"""
app/ai/quality — единая точка входа для валидаторов артефактов AI-ролей.

Валидаторы не оценивают художественную ценность: они отсекают объективно
непригодные результаты (пустые, обрезанные, клиппинг, неполная схема), чтобы
честный fallback срабатывал ДО сохранения артефакта на диск.

Раскладка:
  * `lyrics`   — метрики и проверки текста;
  * `metadata` — контракт метаданных релиза;
  * `audio`    — измеримые проверки аудио и мастеринга;
  * `analysis` — DSP/CLAP/ASR/стемы/стерео/досье.
"""

from app.ai.quality.analysis import (  # noqa: F401
    validate_analysis_json,
    validate_audio_tags,
    validate_asr_transcript,
    validate_dsp_features,
    validate_stereo_texture,
    validate_stem_artifact,
)
from app.ai.quality.audio import (  # noqa: F401
    audio_metrics,
    master_audio_metrics,
    validate_audio_artifact,
    validate_cover_artifact,
    validate_master_artifact,
    validate_rvc_artifact,
    validate_vocal_artifact,
)
from app.ai.quality.lyrics import (  # noqa: F401
    lyrics_metrics,
    validate_lyrics,
    validate_song_lyrics,
)
from app.ai.quality.metadata import validate_metadata_json  # noqa: F401

__all__ = [
    "audio_metrics",
    "lyrics_metrics",
    "master_audio_metrics",
    "validate_analysis_json",
    "validate_audio_artifact",
    "validate_audio_tags",
    "validate_asr_transcript",
    "validate_cover_artifact",
    "validate_dsp_features",
    "validate_lyrics",
    "validate_master_artifact",
    "validate_metadata_json",
    "validate_rvc_artifact",
    "validate_song_lyrics",
    "validate_stem_artifact",
    "validate_stereo_texture",
    "validate_vocal_artifact",
]
