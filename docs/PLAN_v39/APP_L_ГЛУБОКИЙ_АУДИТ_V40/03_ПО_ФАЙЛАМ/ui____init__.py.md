# АУДИТ ФАЙЛА: `ui/__init__.py`

**LOC:** 2  |  **Размер:** 76 байт  |  **Проблем:** 2  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 2 | `.karaoke_recorder` | from |
| 2 | `.tutorial` | from |

## Функции

_функций нет_

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### DEAD_IMPORT — 2 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

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
