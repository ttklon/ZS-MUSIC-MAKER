# АУДИТ ФАЙЛА: `modules/voice_onboarding.py`

**LOC:** 274  |  **Размер:** 9850 байт  |  **Проблем:** 22  |  **Risk score:** 3

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 21 | `__future__.annotations` | from |
| 23 | `json` | import |
| 24 | `time` | import |
| 25 | `dataclasses.asdict` | from |
| 25 | `dataclasses.dataclass` | from |
| 25 | `dataclasses.field` | from |
| 26 | `pathlib.Path` | from |
| 27 | `typing.Any` | from |
| 185 | `modules.voice_recording` | from |
| 248 | `modules.voice_recording` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 113 | `build_plan` | 36 | 2 | ❌ |
| 152 | `compute_phoneme_coverage` | 15 | 3 | ❌ |
| 170 | `_load_manifest` | 6 | 2 | ❌ |
| 179 | `_save_manifest` | 1 | 0 | ❌ |
| 183 | `record_step` | 18 | 5 | ❌ |
| 204 | `compute_progress` | 24 | 4 | ❌ |
| 231 | `is_ready_for_rvc` | 3 | 0 | ❌ |
| 237 | `run_cli` | 33 | 4 | ❌ |
| 94 | `as_dict` | 1 | 0 | ❌ |
| 109 | `as_dict` | 1 | 0 | ❌ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 79 | `OnboardingStep` | ❌ |
| 99 | `OnboardingProgress` | ❌ |

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 12 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 238** — print() вместо logger

  ```
        236 | 
        237 | def run_cli() -> int:
  >>>   238 |     print("=" * 64)
        239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
        240 |     print("=" * 64)
  ```

- **строка 239** — print() вместо logger

  ```
        237 | def run_cli() -> int:
        238 |     print("=" * 64)
  >>>   239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
        240 |     print("=" * 64)
        241 |     plan = build_plan()
  ```

- **строка 240** — print() вместо logger

  ```
        238 |     print("=" * 64)
        239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
  >>>   240 |     print("=" * 64)
        241 |     plan = build_plan()
        242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
  ```

- **строка 242** — print() вместо logger

  ```
        240 |     print("=" * 64)
        241 |     plan = build_plan()
  >>>   242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
        243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
  ```

- **строка 243** — print() вместо logger

  ```
        241 |     plan = build_plan()
        242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
  >>>   243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
        245 |     print(f"  — караоке: {PLAN['karaoke']}s")
  ```

- **строка 244** — print() вместо logger

  ```
        242 |     print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
        243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
  >>>   244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
        245 |     print(f"  — караоке: {PLAN['karaoke']}s")
        246 |     print()
  ```

- **строка 245** — print() вместо logger

  ```
        243 |     print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
  >>>   245 |     print(f"  — караоке: {PLAN['karaoke']}s")
        246 |     print()
        247 |     try:
  ```

- **строка 246** — print() вместо logger

  ```
        244 |     print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
        245 |     print(f"  — караоке: {PLAN['karaoke']}s")
  >>>   246 |     print()
        247 |     try:
        248 |         from modules import voice_recording as vr
  ```

- **строка 253** — print() вместо logger

  ```
        251 |     except Exception as e:
        252 |         cap = {"real_recording_possible": False, "error": str(e)}
  >>>   253 |     print("[capability]", json.dumps(cap, ensure_ascii=False))
        254 |     mic_ok = bool(cap.get("real_recording_possible"))
        255 |     if not mic_ok:
  ```

- **строка 256** — print() вместо logger

  ```
        254 |     mic_ok = bool(cap.get("real_recording_possible"))
        255 |     if not mic_ok:
  >>>   256 |         print("⚠️  Микрофон недоступен. Реальная запись НЕВОЗМОЖНА в этой среде.")
        257 |     m = _load_manifest()
        258 |     m["started_at"] = m.get("started_at") or int(time.time())
  ```

- **строка 262** — print() вместо logger

  ```
        260 |     m["recording_capable"] = mic_ok
        261 |     _save_manifest(m)
  >>>   262 |     print(f"✓ manifest saved: {MANIFEST}")
        263 |     # v34 FIX (P3.16): раньше run_cli() ВСЕГДА возвращал 0 — даже когда
        264 |     # микрофон недоступен и onboarding по факту «только план, без записи».
  ```

- **строка 268** — print() вместо logger

  ```
        266 |     # Теперь: 0 = полная capability, 1 = план сохранён, но запись невозможна.
        267 |     if not mic_ok:
  >>>   268 |         print("[voice_onboarding] exit=1 (plan-only: mic unavailable)")
        269 |         return 1
        270 |     return 0
  ```

### MISSING_DOCSTRING — 5 шт. — 🟢 LOW
**Смысл:** Public-функция без docstring
**Fix:** Добавить """что делает, args, returns""" 3-5 строк.

- **строка 113** — public function 'build_plan' без docstring

  ```
        111 | 
        112 | 
  >>>   113 | def build_plan() -> list[OnboardingStep]:
        114 |     steps: list[OnboardingStep] = []
        115 |     per_phrase = int(PLAN["phoneme_text"] / len(PHONEME_SCRIPT))
  ```

- **строка 152** — public function 'compute_phoneme_coverage' без docstring

  ```
        150 | 
        151 | 
  >>>   152 | def compute_phoneme_coverage(texts: list[str]) -> dict[str, Any]:
        153 |     seen = set()
        154 |     for t in texts:
  ```

- **строка 183** — public function 'record_step' без docstring

  ```
        181 | 
        182 | 
  >>>   183 | def record_step(step: OnboardingStep, mode: str = "auto") -> OnboardingStep:
        184 |     try:
        185 |         from modules import voice_recording as vr
  ```

- **строка 204** — public function 'compute_progress' без docstring

  ```
        202 | 
        203 | 
  >>>   204 | def compute_progress(steps: list[OnboardingStep]) -> OnboardingProgress:
        205 |     total_rec = sum(s.duration_sec for s in steps)
        206 |     styles_done = sum(
  ```

- **строка 237** — public function 'run_cli' без docstring

  ```
        235 | 
        236 | 
  >>>   237 | def run_cli() -> int:
        238 |     print("=" * 64)
        239 |     print("ZS Music Maker — Voice Onboarding (5 минут)")
  ```

### MISSING_CLASS_DOCSTRING — 2 шт. — 🟢 LOW
**Смысл:** Public-класс без docstring
**Fix:** Добавить """назначение класса, публичные методы""".

- **строка 79** — public class 'OnboardingStep' без docstring

  ```
         77 | 
         78 | @dataclass
  >>>    79 | class OnboardingStep:
         80 |     step_id: str
         81 |     kind: str
  ```

- **строка 99** — public class 'OnboardingProgress' без docstring

  ```
         97 | 
         98 | @dataclass
  >>>    99 | class OnboardingProgress:
        100 |     total_target_sec: int = 300
        101 |     total_recorded_sec: float = 0.0
  ```

### DEAD_IMPORT — 1 шт. — 🟡 MEDIUM
**Смысл:** Мёртвый импорт (не используется в файле)
**Fix:** Удалить строку `import X`. Убедиться, что X не используется (grep -R).

- **строка 21** — import 'annotations' не используется в теле файла

  ```
         19 | """
         20 | 
  >>>    21 | from __future__ import annotations
         22 | 
         23 | import json
  ```

### SILENT_EXCEPT_PASS — 1 шт. — 🟡 MEDIUM
**Смысл:** 'except ...: pass' — тихое поглощение ошибок
**Fix:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

- **строка 174** — except: pass — тихое подавление ошибок

  ```
        172 |         try:
        173 |             return json.loads(MANIFEST.read_text(encoding="utf-8"))
  >>>   174 |         except Exception:
        175 |             pass
        176 |     return {"steps": [], "started_at": None, "completed_at": None}
  ```

### BLOCKING_SLEEP — 1 шт. — 🟢 LOW
**Смысл:** time.sleep() без комментария/аргументации
**Fix:** Комментарий или await asyncio.sleep().

- **строка 195** — time.sleep(...) без пояснения

  ```
        193 |         info = rec.start()
        194 |         if info.get("ok"):
  >>>   195 |             time.sleep(step.target_sec)
        196 |             out = rec.stop()
        197 |             if out.get("ok"):
  ```
