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

## Продолжение: измерения и Windows-регрессия

- 45141041526: весь workflow failed. Есть notice успешных аудиопроверок,
  но это не равнозначно успешному job. Прямая загрузка логов недоступна в
  sandbox. Публикация JSON сделана ASCII-safe; регрессия воспроизводит
  печать русских полей через строгую cp1252 без исключения.
- 45142874352: **real-silero job 137584922710 success**, source
  57907020318c2ed7d8bc95f898d77df90df3cbbf. Отчёт из GitHub annotations
  сохранён в `restart-hardware-silero-45142874352.json`.
  Online: аудио 3.875 s, wall 12.5343 s, sampled RSS 773193728 bytes.
  Offline: аудио 4.6875 s, wall 8.9905 s, sampled RSS 990769152 bytes,
  RTF 1.918, Python network attempts 0. Torch 2.5.1+cpu, RAM 15.99 GiB.
  Это реальная черновая речь, не музыкальный inference/пение.
- Workflow 45142874352 всё ещё failed из-за PowerShell: ожидаемый отказ pip
  оставлял LASTEXITCODE=1. Добавлен exit 0 **только после проверки** точного
  конфликта AudioCraft/Torch. Не маскируются произвольные ошибки сети/pip.
  Установка AudioCraft этим тестом не подтверждается.
- Инвентарь профиля теперь использует detect_system: адаптеры, PyTorch device,
  DirectML отдельно; mock AMD/DirectML остаётся явно непроверенным inference.
- 45143253532: Windows-контракт обнаружил зависимость теста от заранее
  установленной librosa (1 failed, 73 passed). Тест import-контракта исправлен:
  проверяет как подставленный модуль, так и отсутствие модуля. Продуктовая
  проверка зависимости не ослаблена.
- Добавлены retry после отказа RAM без изменения прежнего файла и совместимость
  задания только CPU_THREADS (автоматически ограничивает detected CPU_CORES).
- Финальный локальный набор: **115 passed** (hardware/registry/offline/benchmark,
  bootstrap/dependencies, plan/product, function budget).
- Финальный Windows-прогон **45143489947**, source
  201d933d39a6703fe8932af9a6da6cbf1914c6c7: **SUCCESS, оба job**.
  Hardware/offline/registry contracts: **76 passed on Windows**.
  Реальный offline Silero: 4.6875 s аудио / 6.2315 s wall, RTF 1.3294,
  sampled RSS 1049825280 bytes; Python network attempts 0.
  RAM 15.99 GiB, 4 потока/2 ядра; PyTorch GPU отсутствует.
  Полный JSON: `restart-hardware-windows-45143489947.json`.
  Зелёный resolver job означает проверку ожидаемого отказа несовместимых
  зависимостей и bootstrap guard, НЕ успешную установку AudioCraft.

Открытая предметная работа: реальные полные продуктовые сценарии, CUDA и AMD
на физически доступном оборудовании. Hosted CPU runner не подменяет их.
