# PLAN_v39 — ШАГ 057: remix и separation workflow

Добавлен `modules.remix.render_remix()`: он смешивает **новый beat** и vocal stem только при явном `source_authorized=True`. Это делает ownership/permission requirement частью технического контракта, а не примечанием в интерфейсе. Renderer не loop-ит source vocal: он использует только пересечение длин vocal/beat, ресемплирует vocal при необходимости, обеспечивает stereo и применяет 0.98 peak ceiling.

Существующий Demucs workflow остаётся аналитическим; persisted dossier `stems.vocals` может быть source только для треков, на которые пользователь имеет права. Добавлены WAV tests authorization refusal и authorised stereo mix с проверкой использованных vocal frames, sample rate и peak.

На момент приёмки: `pytest tests/test_remix.py -q` — **2 passed**; полный `pytest tests/ -q` — **125 passed**; `compileall` — успешно; AST-аудит — **0 dead imports**.
