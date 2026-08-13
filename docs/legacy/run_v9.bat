@echo off
REM ZS Music Maker — Windows launcher (AUDIT-FIX)
REM Раньше вызывал main_v9.py / main_v8.py, которых НЕТ в репозитории —
REM заменён на единый main.py (консолидированная точка входа).
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  ZS Music Maker — Unified Launcher
echo ========================================
echo.

if exist "venv\Scripts\python.exe" (
    set PY=venv\Scripts\python.exe
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
) else (
    set PY=python
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

%PY% main.py %*
if errorlevel 1 (
    echo.
    echo [run] Запуск завершился с ошибкой. Смотри logs\app.log
    pause
)
endlocal
