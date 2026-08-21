# DEAD_IMPORT — Мёртвый импорт (не используется в файле)

**Severity:** 🟡 MEDIUM
**Всего:** 111
**Как чинить:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

## Все вхождения

### `agents/sample_hunter.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import json
  ```

### `agents/sample_hunter_v9.py` — 1 шт.
- **строка 26** — import 'annotations' не используется в теле файла
  ```
         24 | """
         25 | 
  >>>    26 | from __future__ import annotations
         27 | 
         28 | import json
  ```

### `agents/trend_scout_v3.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```

### `app/ai/__init__.py` — 3 шт.
- **строка 4** — import 'MODEL_REGISTRY' не используется в теле файла
  ```
          2 | """ZS Music Maker - app/ai package (v38 AI CORE)
          3 | Единый AI-слой: все модули идут через registry + SequentialAIRunner."""
  >>>     4 | from app.ai.registry import registry, MODEL_REGISTRY, HardwareBudget  # noqa: F401
          5 | from app.ai.sequential_runner import SequentialAIRunner, AIStage  # noqa: F401
  ```
- **строка 4** — import 'HardwareBudget' не используется в теле файла
  ```
          2 | """ZS Music Maker - app/ai package (v38 AI CORE)
          3 | Единый AI-слой: все модули идут через registry + SequentialAIRunner."""
  >>>     4 | from app.ai.registry import registry, MODEL_REGISTRY, HardwareBudget  # noqa: F401
          5 | from app.ai.sequential_runner import SequentialAIRunner, AIStage  # noqa: F401
  ```
- **строка 5** — import 'AIStage' не используется в теле файла
  ```
          3 | Единый AI-слой: все модули идут через registry + SequentialAIRunner."""
          4 | from app.ai.registry import registry, MODEL_REGISTRY, HardwareBudget  # noqa: F401
  >>>     5 | from app.ai.sequential_runner import SequentialAIRunner, AIStage  # noqa: F401
  ```

### `app/ai/llm_service.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - app/ai/llm_service.py (v38): обёртка над llama-cpp."""
  >>>     3 | from __future__ import annotations
          4 | import json
          5 | from typing import Any, Optional
  ```

### `app/ai/prompts.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - app/ai/prompts.py (v38): промпты для локальных LLM."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | SYSTEM_LYRICS = """Ты - русскоязычный автор-хитмейкер (рэп/трэп/фонк/поп-рэп/шансон). Правила:
  ```

### `app/ai/quality.py` — 1 шт.
- **строка 9** — import 'annotations' не используется в теле файла
  ```
          7 | fallback до сохранения артефакта на диск.
          8 | """
  >>>     9 | from __future__ import annotations
         10 | 
         11 | import re
  ```

### `app/ai/registry.py` — 2 шт.
- **строка 5** — import 'annotations' не используется в теле файла
  ```
          3 | Реестр локальных AI-моделей. Одна тяжёлая модель в VRAM за раз.
          4 | Бюджет: VRAM<=12GB, RAM<=32GB, CPU 2xXeon(40 threads). Только серьёзные модели (>=8B)."""
  >>>     5 | from __future__ import annotations
          6 | import gc, os, time, threading
          7 | from dataclasses import dataclass
  ```
- **строка 238** — import 'torch_directml' не используется в теле файла
  ```
        236 |             pass
        237 |         try:
  >>>   238 |             import torch_directml  # noqa
        239 |             if pref in ("dml", "auto") and need <= self.hw.vram_gb:
        240 |                 return "dml"
  ```

### `app/ai/sequential_runner.py` — 1 шт.
- **строка 4** — import 'annotations' не используется в теле файла
  ```
          2 | """ZS Music Maker - app/ai/sequential_runner.py (v38)
          3 | Последовательный раннер: одна тяжёлая модель в VRAM за раз."""
  >>>     4 | from __future__ import annotations
          5 | import gc, time, logging
          6 | from dataclasses import dataclass, field
  ```

### `app/core/cover_gen.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | """v6 Cover — minimal-art обложка через Pillow. Никаких сетевых зависимостей."""
          2 | 
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import random
  ```

### `app/core/font_utils.py` — 1 шт.
- **строка 13** — import 'annotations' не используется в теле файла
  ```
         11 | C:\\ и /home/ubuntu в production-коде.
         12 | """
  >>>    13 | from __future__ import annotations
         14 | 
         15 | import os
  ```

### `app/core/hw_autodetect.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```

### `app/core/isrc.py` — 1 шт.
- **строка 20** — import 'annotations' не используется в теле файла
  ```
         18 | пометку UNREGISTERED (никогда не фейковый placeholder).
         19 | """
  >>>    20 | from __future__ import annotations
         21 | 
         22 | import hashlib
  ```

### `app/core/license_manager.py` — 1 шт.
- **строка 7** — import 'annotations' не используется в теле файла
  ```
          5 | """
          6 | 
  >>>     7 | from __future__ import annotations
          8 | 
          9 | from dataclasses import dataclass
  ```

### `app/core/musicgen_texture.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import hashlib
  ```

### `app/core/orchestrator.py` — 1 шт.
- **строка 19** — import 'annotations' не используется в теле файла
  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import json
  ```

### `app/core/orchestrator_ai.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - app/core/orchestrator_ai.py (v38 GOD MODE 4.0 AI)"""
  >>>     3 | from __future__ import annotations
          4 | import json, math, shutil
          5 | from pathlib import Path
  ```

### `app/core/orchestrator_v10_patch.py` — 1 шт.
- **строка 10** — import 'annotations' не используется в теле файла
  ```
          8 | """
          9 | 
  >>>    10 | from __future__ import annotations
         11 | 
         12 | import json
  ```

### `app/core/orchestrator_v11_patch.py` — 1 шт.
- **строка 8** — import 'annotations' не используется в теле файла
  ```
          6 | """
          7 | 
  >>>     8 | from __future__ import annotations
          9 | 
         10 | import json
  ```

### `app/core/orchestrator_v12_patch.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import sys
  ```

### `app/core/orchestrator_v8_patch.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import traceback
  ```

### `app/core/orchestrator_v9_patch.py` — 1 шт.
- **строка 22** — import 'annotations' не используется в теле файла
  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import json
  ```

### `app/gui/onboarding.py` — 1 шт.
- **строка 9** — import 'annotations' не используется в теле файла
  ```
          7 | """
          8 | 
  >>>     9 | from __future__ import annotations
         10 | 
         11 | from PySide6.QtWidgets import (
  ```

### `app/gui/theme_v12.py` — 1 шт.
- **строка 20** — import 'annotations' не используется в теле файла
  ```
         18 | """
         19 | 
  >>>    20 | from __future__ import annotations
         21 | 
         22 | # Токены дизайн-системы v12 (RGB, без градиентов).
  ```

### `app/gui/wizard.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import os
  ```

### `app/gui/wizard_v8_extensions.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | try:
  ```

### `app/hw_probe.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | """Автодетект железа: CUDA / DirectML / CPU + VRAM + режим full/fallback."""
          2 | 
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import json
  ```

### `app/runtime_orchestrator.py` — 1 шт.
- **строка 1** — import 'annotations' не используется в теле файла
  ```
  >>>     1 | from __future__ import annotations
          2 | 
          3 | import threading
  ```

### `config/settings.py` — 1 шт.
- **строка 15** — import 'annotations' не используется в теле файла
  ```
         13 | (комментарии # и кавычки поддерживаются). .env.example остаётся шаблоном.
         14 | """
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import os
  ```

### `main.py` — 1 шт.
- **строка 20** — import 'annotations' не используется в теле файла
  ```
         18 | """
         19 | 
  >>>    20 | from __future__ import annotations
         21 | 
         22 | import io
  ```

### `modules/ai_detector_pro.py` — 1 шт.
- **строка 12** — import 'annotations' не используется в теле файла
  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import os
  ```

### `modules/anti_ai_polish.py` — 1 шт.
- **строка 23** — import 'annotations' не используется в теле файла
  ```
         21 | """
         22 | 
  >>>    23 | from __future__ import annotations
         24 | 
         25 | import math
  ```

### `modules/anti_neuro_v10.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import json
  ```

### `modules/arrangement_engine.py` — 1 шт.
- **строка 23** — import 'annotations' не используется в теле файла
  ```
         21 | """
         22 | 
  >>>    23 | from __future__ import annotations
         24 | 
         25 | import json
  ```

### `modules/artist_dossier/__init__.py` — 1 шт.
- **строка 4** — import 'DossierManager' не используется в теле файла
  ```
          2 | """ZS Music Maker - modules/artist_dossier (v38)
          3 | Досье на артистов и треки: demucs -> whisper -> librosa/CLAP -> analysis_llm."""
  >>>     4 | from modules.artist_dossier.manager import DossierManager  # noqa: F401
  ```

### `modules/artist_dossier/collectors.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/artist_dossier/collectors.py (v38)"""
  >>>     3 | from __future__ import annotations
          4 | import os, re
          5 | from pathlib import Path
  ```

### `modules/artist_dossier/manager.py` — 1 шт.
- **строка 4** — import 'annotations' не используется в теле файла
  ```
          2 | """ZS Music Maker - modules/artist_dossier/manager.py (v38)
          3 | Последовательный AI-пайплайн на трек: demucs -> whisper -> librosa -> CLAP -> LLM."""
  >>>     4 | from __future__ import annotations
          5 | import json, re, time, hashlib, shutil
          6 | from dataclasses import dataclass, field, asdict
  ```

### `modules/author_ref_lyrics.py` — 1 шт.
- **строка 21** — import 'annotations' не используется в теле файла
  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import hashlib
  ```

### `modules/auto_qa.py` — 1 шт.
- **строка 21** — import 'annotations' не используется в теле файла
  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import json
  ```

### `modules/beat_gen.py` — 1 шт.
- **строка 25** — import 'torch_directml' не используется в теле файла
  ```
         23 |             return "cuda"
         24 |         try:
  >>>    25 |             import torch_directml  # noqa
         26 | 
         27 |             return "dml"
  ```

### `modules/beat_gen_ai.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/beat_gen_ai.py (v38, MusicGen-large, чанки 20с)."""
  >>>     3 | from __future__ import annotations
          4 | import math
          5 | from pathlib import Path
  ```

### `modules/cover_art_ai.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/cover_art_ai.py (v38, SDXL Base 1.0 fp16)."""
  >>>     3 | from __future__ import annotations
          4 | from pathlib import Path
          5 | from typing import Any, Dict
  ```

### `modules/cover_art_gen.py` — 2 шт.
- **строка 12** — import 'annotations' не используется в теле файла
  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import hashlib
  ```
- **строка 20** — import 'ImageFont' не используется в теле файла
  ```
         18 | 
         19 | try:
  >>>    20 |     from PIL import Image, ImageDraw, ImageFilter, ImageFont
         21 | 
         22 |     PIL_OK = True
  ```

### `modules/distribution_export_v11.py` — 1 шт.
- **строка 9** — import 'annotations' не используется в теле файла
  ```
          7 | """
          8 | 
  >>>     9 | from __future__ import annotations
         10 | 
         11 | import csv
  ```

### `modules/essentia_analyzer.py` — 1 шт.
- **строка 20** — import 'annotations' не используется в теле файла
  ```
         18 | """
         19 | 
  >>>    20 | from __future__ import annotations
         21 | 
         22 | import json
  ```

### `modules/expert_mode_v11.py` — 1 шт.
- **строка 8** — import 'annotations' не используется в теле файла
  ```
          6 | """
          7 | 
  >>>     8 | from __future__ import annotations
          9 | 
         10 | import json
  ```

### `modules/female_backing.py` — 1 шт.
- **строка 15** — import 'annotations' не используется в теле файла
  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | from pathlib import Path
  ```

### `modules/freesound_client.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import hashlib
  ```

### `modules/health_v12.py` — 1 шт.
- **строка 24** — import 'annotations' не используется в теле файла
  ```
         22 | """
         23 | 
  >>>    24 | from __future__ import annotations
         25 | 
         26 | import importlib
  ```

### `modules/hit_kpi_monitor_v11.py` — 1 шт.
- **строка 12** — import 'annotations' не используется в теле файла
  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import fnmatch
  ```

### `modules/hit_scorer.py` — 1 шт.
- **строка 36** — import 'annotations' не используется в теле файла
  ```
         34 | """
         35 | 
  >>>    36 | from __future__ import annotations
         37 | 
         38 | import json
  ```

### `modules/hw_directml.py` — 1 шт.
- **строка 11** — import 'annotations' не используется в теле файла
  ```
          9 | """
         10 | 
  >>>    11 | from __future__ import annotations
         12 | 
         13 | import json
  ```

### `modules/karaoke_engine.py` — 1 шт.
- **строка 14** — import 'annotations' не используется в теле файла
  ```
         12 | """
         13 | 
  >>>    14 | from __future__ import annotations
         15 | 
         16 | import json
  ```

### `modules/kpi_dashboard_v12.py` — 1 шт.
- **строка 18** — import 'annotations' не используется в теле файла
  ```
         16 | """
         17 | 
  >>>    18 | from __future__ import annotations
         19 | 
         20 | import json
  ```

### `modules/llm_clients_v15.py` — 1 шт.
- **строка 19** — import 'annotations' не используется в теле файла
  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import base64
  ```

### `modules/lyric_vault_v10.py` — 1 шт.
- **строка 15** — import 'annotations' не используется в теле файла
  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import hashlib
  ```

### `modules/lyrics_gen.py` — 1 шт.
- **строка 15** — import 'annotations' не используется в теле файла
  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import json
  ```

### `modules/lyrics_gen_ai.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/lyrics_gen_ai.py (v38 AI-first)"""
  >>>     3 | from __future__ import annotations
          4 | import json, re, time
          5 | from pathlib import Path
  ```

### `modules/lyrics_gen_v8.py` — 1 шт.
- **строка 19** — import 'annotations' не используется в теле файла
  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import random
  ```

### `modules/master_pipeline_v12.py` — 1 шт.
- **строка 37** — import 'annotations' не используется в теле файла
  ```
         35 | """
         36 | 
  >>>    37 | from __future__ import annotations
         38 | 
         39 | import json
  ```

### `modules/mastering.py` — 1 шт.
- **строка 25** — import 'annotations' не используется в теле файла
  ```
         23 | """
         24 | 
  >>>    25 | from __future__ import annotations
         26 | 
         27 | import os
  ```

### `modules/mastering_ai.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/mastering_ai.py (v38): matchering -> mastering_pro."""
  >>>     3 | from __future__ import annotations
          4 | from pathlib import Path
          5 | from typing import Any, Dict, Optional
  ```

### `modules/mastering_v9.py` — 1 шт.
- **строка 18** — import 'annotations' не используется в теле файла
  ```
         16 | """
         17 | 
  >>>    18 | from __future__ import annotations
         19 | 
         20 | import json
  ```

### `modules/matchering_master.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import logging
  ```

### `modules/onboarding_tour.py` — 1 шт.
- **строка 10** — import 'annotations' не используется в теле файла
  ```
          8 | """
          9 | 
  >>>    10 | from __future__ import annotations
         11 | 
         12 | import json
  ```

### `modules/phoneme_coverage.py` — 1 шт.
- **строка 14** — import 'annotations' не используется в теле файла
  ```
         12 | """
         13 | 
  >>>    14 | from __future__ import annotations
         15 | 
         16 | import json
  ```

### `modules/reference_ingest.py` — 1 шт.
- **строка 22** — import 'annotations' не используется в теле файла
  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import hashlib
  ```

### `modules/release_pack_full.py` — 1 шт.
- **строка 50** — import 'annotations' не используется в теле файла
  ```
         48 | """
         49 | 
  >>>    50 | from __future__ import annotations
         51 | 
         52 | import json
  ```

### `modules/release_pack_v9.py` — 1 шт.
- **строка 22** — import 'annotations' не используется в теле файла
  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import json
  ```

### `modules/render_queue.py` — 1 шт.
- **строка 11** — import 'annotations' не используется в теле файла
  ```
          9 | """
         10 | 
  >>>    11 | from __future__ import annotations
         12 | 
         13 | import json
  ```

### `modules/rvc_manager.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import json
  ```

### `modules/rvc_trainer_v9.py` — 1 шт.
- **строка 18** — import 'annotations' не используется в теле файла
  ```
         16 | """
         17 | 
  >>>    18 | from __future__ import annotations
         19 | 
         20 | import json
  ```

### `modules/self_diag_v13.py` — 1 шт.
- **строка 29** — import 'annotations' не используется в теле файла
  ```
         27 | """
         28 | 
  >>>    29 | from __future__ import annotations
         30 | 
         31 | import json
  ```

### `modules/sidechain.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```

### `modules/tiktok_edit_v9.py` — 1 шт.
- **строка 19** — import 'annotations' не используется в теле файла
  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import json
  ```

### `modules/track_templates.py` — 1 шт.
- **строка 10** — import 'annotations' не используется в теле файла
  ```
          8 | """
          9 | 
  >>>    10 | from __future__ import annotations
         11 | 
         12 | import json
  ```

### `modules/video_edit_v11.py` — 1 шт.
- **строка 15** — import 'annotations' не используется в теле файла
  ```
         13 | """
         14 | 
  >>>    15 | from __future__ import annotations
         16 | 
         17 | import json
  ```

### `modules/vocal_fx.py` — 1 шт.
- **строка 24** — import 'annotations' не используется в теле файла
  ```
         22 | """
         23 | 
  >>>    24 | from __future__ import annotations
         25 | 
         26 | import json
  ```

### `modules/voice_onboarding.py` — 1 шт.
- **строка 21** — import 'annotations' не используется в теле файла
  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import json
  ```

### `modules/voice_recording.py` — 1 шт.
- **строка 19** — import 'annotations' не используется в теле файла
  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import json
  ```

### `modules/voice_synth_ai.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker - modules/voice_synth_ai.py (v38): XTTS-v2 -> RVC."""
  >>>     3 | from __future__ import annotations
          4 | from pathlib import Path
          5 | from typing import Any, Dict, Optional
  ```

### `modules/voice_vault_v9.py` — 1 шт.
- **строка 21** — import 'annotations' не используется в теле файла
  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import hashlib
  ```

### `modules/wizard_v12_integration.py` — 1 шт.
- **строка 21** — import 'annotations' не используется в теле файла
  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import json
  ```

### `tests/test_ai_layer.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — smoke-тесты AI-слоя и архитектурные инварианты импортов."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import ast
  ```

### `tests/test_ai_quality.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """Качественные контракты outputs LLM и генерации аудио."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import json
  ```

### `tests/test_ast_dead_imports.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — AST dead-imports аудит (ШАГ 010)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import sys
  ```

### `tests/test_data_inventory.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """Регрессии для versioned-каталога data и его статического аудита."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | from tools.audit_data_inventory import scan_data
  ```

### `tests/test_font_utils.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — tests for app/core/font_utils (ШАГ 002)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | from app.core import font_utils as F
  ```

### `tests/test_isrc.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — tests for app/core/isrc (ШАГ 003)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | from app.core import isrc as I
  ```

### `tests/test_settings.py` — 3 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — tests for config/settings (ШАГ 007)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import os
  ```
- **строка 5** — import 'os' не используется в теле файла
  ```
          3 | from __future__ import annotations
          4 | 
  >>>     5 | import os
          6 | from pathlib import Path
          7 | 
  ```
- **строка 6** — import 'Path' не используется в теле файла
  ```
          4 | 
          5 | import os
  >>>     6 | from pathlib import Path
          7 | 
          8 | import pytest
  ```

### `tests/test_version_consistency.py` — 1 шт.
- **строка 3** — import 'annotations' не используется в теле файла
  ```
          1 | # -*- coding: utf-8 -*-
          2 | """ZS Music Maker — единый источник версии (ШАГ 009)."""
  >>>     3 | from __future__ import annotations
          4 | 
          5 | import json
  ```

### `tools/ab_compare.py` — 1 шт.
- **строка 17** — import 'annotations' не используется в теле файла
  ```
         15 | """
         16 | 
  >>>    17 | from __future__ import annotations
         18 | 
         19 | import argparse
  ```

### `tools/ast_dead_imports.py` — 1 шт.
- **строка 22** — import 'annotations' не используется в теле файла
  ```
         20 | Exit code: 0 если чисто, 1 если есть кандидаты.
         21 | """
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import ast
  ```

### `tools/audit_data_inventory.py` — 1 шт.
- **строка 12** — import 'annotations' не используется в теле файла
  ```
         10 |     python tools/audit_data_inventory.py --json
         11 | """
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import argparse
  ```

### `tools/deep_audit_v40.py` — 1 шт.
- **строка 22** — import 'annotations' не используется в теле файла
  ```
         20 |   • отсутствие явных таймаутов у HTTP-запросов
         21 | """
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import ast
  ```

### `tools/fallback_audit.py` — 1 шт.
- **строка 11** — import 'annotations' не используется в теле файла
  ```
          9 | """
         10 | 
  >>>    11 | from __future__ import annotations
         12 | 
         13 | import json
  ```

### `tools/pull_ai_models.py` — 1 шт.
- **строка 5** — import 'annotations' не используется в теле файла
  ```
          3 |   python tools/pull_ai_models.py --list | --all | --model <role>
          4 | """
  >>>     5 | from __future__ import annotations
          6 | import argparse, sys
          7 | from pathlib import Path
  ```

### `tools/readiness.py` — 1 шт.
- **строка 7** — import 'annotations' не используется в теле файла
  ```
          5 | """
          6 | 
  >>>     7 | from __future__ import annotations
          8 | 
          9 | import json
  ```

### `tools/real_e2e_v14.py` — 1 шт.
- **строка 13** — import 'annotations' не используется в теле файла
  ```
         11 | """
         12 | 
  >>>    13 | from __future__ import annotations
         14 | 
         15 | import json
  ```

### `tools/smoke_v26.py` — 1 шт.
- **строка 19** — import 'annotations' не используется в теле файла
  ```
         17 | """
         18 | 
  >>>    19 | from __future__ import annotations
         20 | 
         21 | import shutil
  ```

### `tools/smoke_v29.py` — 1 шт.
- **строка 16** — import 'annotations' не используется в теле файла
  ```
         14 | """
         15 | 
  >>>    16 | from __future__ import annotations
         17 | 
         18 | import json
  ```

### `ui/__init__.py` — 2 шт.
- **строка 2** — import 'karaoke_recorder' не используется в теле файла
  ```
          1 | # ZS Music Maker v3 — ui package
  >>>     2 | from . import karaoke_recorder, tutorial
  ```
- **строка 2** — import 'tutorial' не используется в теле файла
  ```
          1 | # ZS Music Maker v3 — ui package
  >>>     2 | from . import karaoke_recorder, tutorial
  ```

### `ui/karaoke_recorder.py` — 1 шт.
- **строка 12** — import 'annotations' не используется в теле файла
  ```
         10 | """
         11 | 
  >>>    12 | from __future__ import annotations
         13 | 
         14 | import json
  ```

### `updater/updater.py` — 1 шт.
- **строка 22** — import 'annotations' не используется в теле файла
  ```
         20 | """
         21 | 
  >>>    22 | from __future__ import annotations
         23 | 
         24 | import hashlib
  ```
