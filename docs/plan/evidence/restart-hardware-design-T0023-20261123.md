# T0023 — решение по аппаратной интеграции и откату

Дата: 2026-11-23. Область: установленный agent-hit/current creation путь и
аппаратная граница; решение не объявляет весь набор AI entrypoints принятым.

## Решение

Для канонического agent-hit использовать одну read-only inventory snapshot и
передавать её неизменённой между preflight и backend-specific checks:

1. `app.ai.profiles.measure_profile(output_volume)` собирает inventory. Его тип
   остаётся `inventory_only`; наличие адаптера/объём памяти не означает запуск
   или поддержку модели.
2. `app.ai.agent_preflight.preflight_agent_hardware()` валидирует схему,
   измеренные CPU/RAM/disk и согласованность с `system` snapshot. Operational
   stop floors 2 GiB RAM и 1 GiB disk — только ранний отказ, не бюджеты моделей.
   Невалидная/неполная inventory блокирует выбор тяжёлого backend.
3. Тот же snapshot поступает в adaptive routing и RVC preflight. MusicGen/ACE-Step
   блокируются без собственного проверенного бюджета; MusicGen texture выключена
   в этом agent-пути. RVC использует общий
   `modules.rvc_manager.infer.preflight_rvc_inference()` до работы.
4. Проверка конкретного model backend выполняется отдельным строгим runner:
   `tools.local_model_benchmark.py` принимает точный backend и локальный package
   с SHA, запрещает неявное переключение CUDA/ROCm → CPU, проверяет устройство
   результата и сохраняет время/RSS/VRAM. Такой benchmark подтверждает только
   зафиксированный inference, не качество песни.

Предел архитектурного решения: generic `app.ai.registry.ModelRegistry` имеет
собственную `device_pref`/`cpu_fallback` семантику. Её нельзя считать эквивалентом
строгого explicit-backend benchmark или автоматически распространять на agent
flow. Перед общей поддержкой всех AI entrypoints нужно отдельно свести фактически
выбранное устройство, модель fallback и результат для каждого engine.

## Рассмотренные альтернативы

| Альтернатива | Решение | Причина |
|---|---|---|
| Дублировать RAM/VRAM проверки отдельно в UI, CLI и renderer | Отклонена для canonical agent path | Разные snapshots и несовпадающие правила; общая проверка должна быть до тяжёлых стадий. |
| Считать имя GPU, WMI/DXGI adapter или VRAM estimate доказательством backend | Отклонена | Инвентарь не подтверждает PyTorch/CTranslate2/DirectML совместимость или inference. |
| Автоматически заменять выбранный CUDA/ROCm на CPU и сохранять прежний GPU-статус | Отклонена для строгого профиля и RVC refusal | Это меняет backend результата и создаёт ложный PASS; CPU rerun должен быть явным. |
| Принять общие пороги памяти как модели-бюджеты | Отклонена | 2 GiB/1 GiB agent floors только отсекают заведомо малый host; per-engine budgets ещё не измерены. |
| Продолжать MusicGen/ACE-Step/texture в canonical agent без бюджета, полагаясь на адаптивную эвристику | Отклонена | Сценарий может загрузить тяжёлую модель без профиля; текущий путь блокирует эти engine и сохраняет DSP как unverified, а не model inference. |

## План отката / безопасное восстановление

- Если inventory отсутствует, повреждена или не проходит safety floor — остановить
  запрос **до** backend selection и до создания output directory. Сохранить прежние
  файлы и показать причину; не обходить проверку ради успешного завершения.
- Если budget/VRAM выбранной модели неизвестен или недостаточен — заблокировать
  именно этот запрос. Предложить отдельный явный CPU-запуск, только если для CPU
  есть собственная проверка; не записывать результат CPU как CUDA/ROCm.
- Если optional MusicGen texture/ACE-Step/RVC ломает безопасный agent путь,
  восстановиться на inventory-only/процедурной ветви при достаточном базовом
  inventory, `use_texture=false`, `inference_verified=false` и
  `product_profile_accepted=false`. Это ограниченный деградированный путь, не
  приёмка песни.
- При регрессии интеграции откатывать только конкретное изменение entrypoint и
  оставлять отказ неизвестных/недостаточных ресурсов. Не удалять model-specific
  guard в RVC или backend checks, не удалять предыдущие результаты и не превращать
  тестовые doubles в успешный продуктовый результат.

## Совместимость и открытые проверки

- PyTorch ROCm виден через CUDA API и различается по `torch.version.hip`; это само
  по себе не доказывает поддержку CUDA-only engines (например CTranslate2).
- DirectML inventory и адаптер AMD не являются результатом strict benchmark.
- Успешный Windows run 45166373798 подтверждает только Silero v3_1_ru CPU draft
  speech на source commit `6d452ce…`; полный render, MusicGen/RVC, singing,
  CUDA и AMD GPU не испытаны.
- Текущий workspace контрактный regression: 120 passed; тесты используют
  fixtures/fake backends и не заменяют inference.
- Не закрыты совместимость всех legacy registry entrypoints, измеренные per-engine
  budgets, полный поддерживаемый CPU profile, NVIDIA CUDA и AMD ROCm profiles.
  Их нельзя объявить поддержанными по этому техническому решению.

## Статус T0023

Технический выбор, альтернативы и безопасный rollback задокументированы. Строгая
предметная приёмка остаётся `in_progress` / `acceptance_met=false`, потому что
общий критерий пакета требует реальные протоколы каждого заявляемого CPU/CUDA/AMD
профиля. Это решение закрывает дизайн-вопрос T0023, но не подменяет измерения
T0021/T0024/T0029 и не разрешает закрывать T0030.
