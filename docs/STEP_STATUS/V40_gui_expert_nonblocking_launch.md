# APP_L v40 — nonblocking Gradio expert launch

`Wizard.launch_gradio_expert()` started the Gradio server on a background thread but then called `time.sleep(2)` in the Qt caller thread before opening the browser. This could freeze the desktop Wizard during server warm-up.

The fixed implementation keeps the two-second warm-up delay with `threading.Timer(2.0, webbrowser.open, ...)`, so the browser launch is scheduled asynchronously and the UI thread returns immediately. The old `time` import was removed after the full AST dead-import regression correctly detected it as obsolete.

A focused AST regression verifies that the method contains a `threading.Timer` call and no `time.sleep` call. It avoids importing PySide6 or starting Gradio.

Acceptance: focused nonblocking-launch test — **1 passed**. Full `pytest tests/ -q` — **252 passed**; `compileall` successful; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
