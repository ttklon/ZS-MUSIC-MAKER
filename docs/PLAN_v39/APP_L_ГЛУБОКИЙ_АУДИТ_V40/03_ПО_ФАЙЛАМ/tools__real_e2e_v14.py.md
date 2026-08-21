# АУДИТ ФАЙЛА: `tools/real_e2e_v14.py`

**LOC:** 186  |  **Размер:** 6420 байт  |  **Проблем:** 17  |  **Risk score:** 1

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 13 | `__future__.annotations` | from |
| 15 | `json` | import |
| 16 | `sys` | import |
| 17 | `time` | import |
| 18 | `pathlib.Path` | from |
| 31 | `numpy` | import |
| 32 | `soundfile` | import |
| 97 | `app.core.orchestrator.run_full_pipeline` | from |
| 134 | `tools.fallback_audit` | from |
| 134 | `tools.readiness` | from |
| 67 | `soundfile` | import |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 28 | `_synthesize_reference` | 34 | 3 | ❌ |
| 65 | `_check_wav` | 14 | 1 | ❌ |
| 82 | `main` | 100 | 9 | ❌ |

## Классы

_классов нет_

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 15 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 83** — print() вместо logger

  ```
         81 | 
         82 | def main() -> int:
  >>>    83 |     print("=" * 64)
         84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
         85 |     print("=" * 64)
  ```

- **строка 84** — print() вместо logger

  ```
         82 | def main() -> int:
         83 |     print("=" * 64)
  >>>    84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
         85 |     print("=" * 64)
         86 | 
  ```

- **строка 85** — print() вместо logger

  ```
         83 |     print("=" * 64)
         84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
  >>>    85 |     print("=" * 64)
         86 | 
         87 |     ts = int(time.time())
  ```

- **строка 93** — print() вместо logger

  ```
         91 |     ref_path = workdir / "reference.wav"
         92 |     ref_meta = _synthesize_reference(ref_path, duration=15.0, bpm=140)
  >>>    93 |     print(
         94 |         f"[e2e] synthetic reference: {ref_path}  (sr={ref_meta['sr']}, dur={ref_meta['duration']}s)"
         95 |     )
  ```

- **строка 165** — print() вместо logger

  ```
        163 |     )
        164 | 
  >>>   165 |     print()
        166 |     print("─" * 64)
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
  ```

- **строка 166** — print() вместо logger

  ```
        164 | 
        165 |     print()
  >>>   166 |     print("─" * 64)
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
  ```

- **строка 167** — print() вместо logger

  ```
        165 |     print()
        166 |     print("─" * 64)
  >>>   167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
  ```

- **строка 168** — print() вместо logger

  ```
        166 |     print("─" * 64)
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
  >>>   168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
  ```

- **строка 169** — print() вместо logger

  ```
        167 |     print(f"Verdict:            {summary['pipeline_verdict']}")
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
  >>>   169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
        171 |     print(f"Release files:      {len(release_check)}")
  ```

- **строка 170** — print() вместо logger

  ```
        168 |     print(f"Stages ok/total:    {summary['stages_ok']}/{summary['pipeline_stages']}")
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
  >>>   170 |     print(f"Masters generated:  {len(stands_check)}/8")
        171 |     print(f"Release files:      {len(release_check)}")
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
  ```

- **строка 171** — print() вместо logger

  ```
        169 |     print(f"Fallback stages:    {summary['stages_fallback']}")
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
  >>>   171 |     print(f"Release files:      {len(release_check)}")
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
  ```

- **строка 172** — print() вместо logger

  ```
        170 |     print(f"Masters generated:  {len(stands_check)}/8")
        171 |     print(f"Release files:      {len(release_check)}")
  >>>   172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
        174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
  ```

- **строка 173** — print() вместо logger

  ```
        171 |     print(f"Release files:      {len(release_check)}")
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
  >>>   173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
        174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
        175 |     print()
  ```

- **строка 174** — print() вместо logger

  ```
        172 |     print(f"Readiness (formula):{summary['readiness_percent']}%")
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
  >>>   174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
        175 |     print()
        176 | 
  ```

- **строка 175** — print() вместо logger

  ```
        173 |     print(f"Red flags:          {summary['fallback_red_flags_count']}")
        174 |     print(f"Full JSON:          {workdir / 'e2e_summary.json'}")
  >>>   175 |     print()
        176 | 
        177 |     if (
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 13** — import 'annotations' не используется в теле файла

  ```
         11 | """
         12 | 
  >>>    13 | from __future__ import annotations
         14 | 
         15 | import json
  ```

### MISSING_DOCSTRING — 1 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 82** — public function 'main' без docstring

  ```
         80 | 
         81 | 
  >>>    82 | def main() -> int:
         83 |     print("=" * 64)
         84 |     print("ZS Music Maker v14 — real_e2e_v14 (non-dry pipeline)")
  ```
