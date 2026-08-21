# GLOBAL_STATEMENT — global — обычно антипаттерн

**Severity:** 🟡 MEDIUM
**Всего:** 3
**Как чинить:** Инкапсулировать в класс или get_*().

## Все вхождения

### `config/settings.py` — 2 шт.
- **строка 149** — global — антипаттерн
  ```
        147 | 
        148 | def get_settings() -> Settings:
  >>>   149 |     global _settings
        150 |     if _settings is None:
        151 |         _settings = Settings.load()
  ```
- **строка 157** — global — антипаттерн
  ```
        155 | def reset_settings() -> None:
        156 |     """Сбрасывает кэш настроек (используется тестами)."""
  >>>   157 |     global _settings
        158 |     _settings = None
  ```

### `modules/mastering_pro.py` — 1 шт.
- **строка 72** — global — антипаттерн
  ```
         70 |     v29: добавлен true-peak ceiling (-1 dBTP) и honest output-метрики.
         71 |     """
  >>>    72 |     global HAS_PEDALBOARD, HAS_PYLOUDNORM
         73 |     if not os.path.exists(input_wav):
         74 |         raise FileNotFoundError(f"Input wav not found: {input_wav}")
  ```
