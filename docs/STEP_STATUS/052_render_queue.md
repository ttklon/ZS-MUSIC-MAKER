# PLAN_v39 — ШАГ 052: render queue и отмена

`RenderQueue` подтверждён как FIFO worker с persisted JSON state и дополнен явным состоянием `cancelled`. Pending job отменяется до исполнения; для running job сохраняется `cancel_requested`, а cancellation применяется на следующей границе `stage_hook`. Это безопасно для тяжёлого sequential pipeline: активный нативный inference не принудительно убивается в середине вызова, но дальнейшие стадии не запускаются.

| Поведение | Результат |
|---|---|
| Batch FIFO | Один worker обрабатывает items последовательно. |
| UI responsiveness | Worker является daemon thread; enqueue/poll остаются неблокирующими. |
| Progress | Каждая stage callback обновляет stage/progress и persist state. |
| Restart | `running` task при restore возвращается к `pending`; состояния `done/error/cancelled` сохраняются. |
| Cancel | Pending сразу `cancelled`; running отменяется на следующем stage boundary. |

Добавлены isolated fake-orchestrator tests FIFO order, JSON restore, pending cancellation и running cancellation. На момент приёмки: `pytest tests/test_render_queue.py -q` — **2 passed**; полный `pytest tests/ -q` — **118 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
