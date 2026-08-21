# PLAN_v39 — ШАГ 065: performance cache

В `modules.hit_scorer` добавлен bounded LRU cache на 8 entries для наиболее повторяемой non-AI операции: decode/resample WAV. Ключ включает resolved path, sample rate и `st_mtime_ns`, поэтому повторный scoring неизменённого файла переиспользует decoded audio, а изменение файла автоматически инвалидирует entry.

Regression с patched loader подтверждает один decode для одинакового key и второй decode после изменения mtime. Это точечная оптимизация repeat scoring; она не затрагивает inference, не делает заявлений о 20% ускорении полного классического pipeline и не кэширует результаты после модификации файла.

На момент приёмки: cache regression — **1 passed**; полный `pytest tests/ -q` — **135 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
