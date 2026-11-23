# -*- coding: utf-8 -*-
"""
modules.agent_guide — ИИ-агентик-проводник: 4 вопроса → готовый хит.

Зачем отдельный пакет: диалог («настроение / артист / референсы / голос») —
это не UI и не пайплайн, а связка между ними. Раньше её не было: окно
собирало бит на JS, а `hit_factory` жил своей жизнью, поэтому «Сделать хит»
и «все ИИ-агенты автономно» были двумя разными кнопками.

Что внутри:

  * `questions`   — канонические 4 вопроса и разбор ответов (`parse_answers`);
  * `plan`        — `build_plan`: настроение/артист/референсы/голос → wizard_state;
  * `make_one`    — `run_conversation_hit`: trend_scout → досье → текст → голос →
                    бит → микш/мастер через `HitFactory` (единственный прогон);
  * `narration`   — человеческий текст прогресса и честный вердикт.

Правило честности: где движка нет (Ollama, MusicGen, RVC), отчёт говорит
`BLOCKED` и причину. Ни одна ступень не подменяется шаблоном молча.
"""

from __future__ import annotations

# `# noqa: F401` — это публичный API пакета (реэкспорт), а не мёртвый импорт:
# аудит `tools/ast_dead_imports.py` иначе считает его неиспользованным.
from modules.agent_guide.narration import narrate, verdict  # noqa: F401
from modules.agent_guide.questions import QUESTIONS, answer_summary, parse_answers  # noqa: F401
from modules.agent_guide.runner import build_plan, run_conversation_hit  # noqa: F401

__all__ = [
    "QUESTIONS",
    "answer_summary",
    "build_plan",
    "narrate",
    "parse_answers",
    "run_conversation_hit",
    "verdict",
]
