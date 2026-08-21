# PLAN_v39 — ШАГ 075: единый CLI-стиль tools

Проведён bounded audit всех 19 executable scripts в `tools/`. До исправления часть `--help` запускала smoke/E2E/audit workload, часть завершалась ошибкой, `ab_compare` требовал optional `pyloudnorm` ещё до parser-а, а `validate_final_track --help` пытался открыть файл `--help`.

Добавлен `tools/cli_contract.py`: no-option maintenance tools используют safe argparse guard в executable `__main__` block, поэтому help завершается до workload, а неизвестные flags получают стандартный parser error. `readiness.py` не использует generic guard: у него реализован собственный argparse parser для существующего `--inventory-markdown`. `p0_truth_test.py` переведён из import-time workload в `main() -> int` с honest non-zero outcome. `ab_compare` переносит отсутствие optional `pyloudnorm` на execution path после parser-а; `validate_final_track` получил optional positional argument через argparse и сохранил latest-master fallback.

Приёмка: реальный `python tools/<script> --help` выполнен для **19/19** executable tools с exit 0 и `usage:` output, без timeout. Новый `tests/test_tools_cli.py` закрепляет этот contract. Первичный audit непреднамеренно создал deep-audit reports и `data/health_v12.json`; они были изолированно удалены/восстановлены, а последующий `audit_data_inventory.py` вернул **73 managed, 0 unknown, 0 invalid**.

Финальная проверка: полный `pytest tests/ -q` — **167 passed**; `compileall` успешно; AST-аудит — **0 dead imports**.
