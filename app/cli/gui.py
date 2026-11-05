# -*- coding: utf-8 -*-
"""
app/cli/gui.py — запуск графических интерфейсов из CLI.

Порядок предпочтений: нативный Desktop Wizard (PySide6) → веб-UI (Gradio) →
консольный REPL. Все импорты GUI ленивые: CLI обязан работать на машине без
PySide6 и без gradio.
"""

from __future__ import annotations

import sys
import traceback

from app.cli.env import safe_print


def try_launch_pyside() -> bool:
    """Поднять Desktop Wizard. True — окно открывалось (выход через SystemExit)."""
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as e:
        safe_print(
            f"[ERROR] PySide6 не найден. Для работы GUI установите: pip install PySide6. Ошибка: {e}"
        )
        return False
    try:
        from app.gui import theme
        from app.gui.wizard import Wizard
        from app.hw_probe import probe
        from app.core.logger import install_excepthook, setup_logger
        from app.runtime_orchestrator import RuntimeOrchestrator
    except Exception as e:
        safe_print(
            f"[ERROR] Не удалось загрузить модули GUI. Проверьте целостность папки app/gui. Ошибка: {e}"
        )
        traceback.print_exc()
        return False
    app = QApplication.instance() or QApplication(sys.argv)
    try:
        theme.apply(app)
    except Exception as exc:
        safe_print(f"[main] GUI theme fallback after apply failure: {exc}")
    try:
        log = setup_logger("zsmm")
        # крэш-репорт рядом с журналом: окно не должно закрываться «молча»
        install_excepthook(log, context="desktop-wizard")
        hw = probe()
        orch = RuntimeOrchestrator(log=log)
        w = Wizard(orch=orch, hw=hw, log=log)
        w.show()
        rc = app.exec()
        raise SystemExit(rc)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        return False


def try_launch_gradio() -> bool:
    """Поднять веб-UI на 127.0.0.1:7860 (локально, без share)."""
    try:
        import gradio  # noqa: F401
    except Exception as e:
        safe_print(f"[main] gradio недоступен: {e}")
        return False
    try:
        from app.core.orchestrator import build_gradio_ui

        demo = build_gradio_ui()
        demo.launch(
            server_name="127.0.0.1", server_port=7860, share=False, show_error=True
        )
        return True
    except Exception as e:
        safe_print(f"[main] gradio UI failed: {e}")
        traceback.print_exc()
        return False
