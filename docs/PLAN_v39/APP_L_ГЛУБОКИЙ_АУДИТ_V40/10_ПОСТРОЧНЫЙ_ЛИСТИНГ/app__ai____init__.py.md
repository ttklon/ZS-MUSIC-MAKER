# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/ai/__init__.py`

**Всего строк:** 5

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| docstring | 2 | 40.0 |
| import | 2 | 40.0 |
| comment | 1 | 20.0 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - app/ai package (v38 AI CORE)
    3 [docstring ] Единый AI-слой: все модули идут через registry + SequentialAIRunner."""
    4 [import    ] from app.ai.registry import registry, MODEL_REGISTRY, HardwareBudget  # noqa: F401
    5 [import    ] from app.ai.sequential_runner import SequentialAIRunner, AIStage  # noqa: F401
```