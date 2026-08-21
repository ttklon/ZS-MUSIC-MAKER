# АУДИТ ФАЙЛА: `app/ai/__init__.py`

**LOC:** 5  |  **Размер:** 335 байт  |  **Проблем:** 3  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 4 | `app.ai.registry.registry` | from |
| 4 | `app.ai.registry.MODEL_REGISTRY` | from |
| 4 | `app.ai.registry.HardwareBudget` | from |
| 5 | `app.ai.sequential_runner.SequentialAIRunner` | from |
| 5 | `app.ai.sequential_runner.AIStage` | from |

## Функции

_функций нет_

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 3 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

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
