"""Public entrypoint policy. Legacy routes remain callable only by explicit choice."""
from __future__ import annotations

PRIMARY = "Electron → Создание трека"
LEGACY_NOTICE = "LEGACY: этот вход не поддерживается как основной продукт. Откройте установленный ZS Music Maker → Создание трека."

ENTRYPOINTS = (
    {"id": "electron", "path": "desktop/electron/main.js", "command": "ZS Music Maker.exe", "policy": "primary_development"},
    {"id": "python_default", "path": "main.py", "command": "python main.py", "policy": "redirect_instructions_only"},
    {"id": "python_cli", "path": "app/cli", "command": "python main.py --help", "policy": "engineering_not_product_acceptance"},
    {"id": "installed_cli", "path": "pyproject.toml", "command": "zs-music-maker --help", "policy": "engineering_not_product_acceptance"},
    {"id": "pyside", "path": "app/gui", "command": "python main.py --desktop", "policy": "legacy_not_supported_as_product"},
    {"id": "gradio", "path": "app/cli/gui.py", "command": "python main.py --gradio", "policy": "legacy_not_supported_as_product"},
    {"id": "console", "path": "app/cli/commands.py", "command": "python main.py --console", "policy": "legacy_not_supported_as_product"},
    {"id": "hitmaker", "path": "hitmaker.py", "command": "python hitmaker.py", "policy": "experimental_not_supported_as_product"},
    {"id": "karaoke", "path": "ui/karaoke_recorder.py", "command": "python -m ui.karaoke_recorder", "policy": "engineering_diagnostic_not_product"},
    {"id": "pyside_onboarding_demo", "path": "app/gui/onboarding.py", "command": "python -m app.gui.onboarding", "policy": "developer_demo_not_product"},
    {"id": "pyside_theme_demo", "path": "app/gui/theme.py", "command": "python -m app.gui.theme", "policy": "developer_demo_not_product"},
    {"id": "preview", "path": "desktop/scripts/preview-server.js", "command": "npm run preview", "policy": "developer_mock_bridge_only"},
    {"id": "cmd_launchers", "path": "scripts", "command": "scripts/run.cmd; scripts/run_silent.cmd", "policy": "legacy_not_supported_as_product"},
)


def default_instructions() -> str:
    return ("Основной продукт: " + PRIMARY + ".\n"
            "Установщик: https://github.com/ttklon/ZS-MUSIC-MAKER/releases/latest\n"
            "Этот Python-вход не запускает старые GUI автоматически.\n"
            "Для инженерных команд: python main.py --help. Модели не скачиваются этим сообщением.")
