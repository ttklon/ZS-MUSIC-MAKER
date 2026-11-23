# Повторный проход T0021–T0030 — работа продолжается

Код: c5117db3d4398fd7597c5f0abb210b4bb32b73f4.
Windows inference: https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45141041526
(запущен; результат при создании записи ещё не получен).

- T0021: контракт ресурсов и границ доказательств описан в docs/HARDWARE.md.
- T0022: воспроизводимые негативные случаи: NaN/Infinity/отрицательная оценка,
  bool/строка, нулевая свободная VRAM при нулевой оценке.
- T0023: fail-closed проверки, фактическая свободная VRAM плюс резерв; отдельно
  инвентарь, разрешение ресурсов и измеренный inference.
- T0024: checked_gib, HardwareBudget validation, RAM guards и VRAM reserve.
- T0025: проверки подключены к существующим ModelRegistry и ASR/LLM guards.
- T0026–T0028: локальный набор hardware/registry/Silero/benchmark/length:
  74 passed. Это контрактные тесты, не inference и не тесты всех GPU.
- T0029–T0030: полная приёмка НЕ заявлена. Запущен новый настоящий Windows
  Silero CPU benchmark; CUDA/AMD inference этим запуском не проверяются.

Дополнительно upstream Silero loader закреплён commit SHA; модельный пакет
хешируется в benchmark, но его digest ещё не является allowlist доверенных весов.
Python socket guard не заменяет независимый OS-level сетевой аудит.
Пакет из десяти пунктов остаётся активным, счётчик принятых не увеличен.
