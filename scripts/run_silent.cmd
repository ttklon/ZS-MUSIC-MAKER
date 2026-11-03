@echo off
REM ZS Music Maker - запуск без окна консоли (как обычное приложение).
REM Журнал и крэш-репорты: %LOCALAPPDATA%\ZS Music Maker\logs
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\pythonw.exe" (
    echo [run] окружение не найдено - запускаю setup ...
    call "%~dp0setup.cmd" || exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" main.py --desktop %*
exit /b 0
