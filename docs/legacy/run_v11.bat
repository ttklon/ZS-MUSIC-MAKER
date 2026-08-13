@echo off
REM ZS Music Maker — Windows launcher (AUDIT-FIX)
REM Раньше этот скрипт вызывал main_v11.py, которого НЕТ в репозитории
REM (файл был консолидирован в единый main.py). Запуск всегда падал
REM в fallback-цепочку из таких же несуществующих main_v*.py.

chcp 65001 >nul 2>&1
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYEXE="
for %%P in (py.exe python.exe python3.exe) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set "PYEXE=%%P"
        goto :got_python
    )
)
:got_python
if "%PYEXE%"=="" (
    echo [run] Python не найден. Установите Python 3.10+ и добавьте в PATH.
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo ====================================================
echo   ZS Music Maker — Unified Launcher
echo   Python: %PYEXE%
echo ====================================================

"%PYEXE%" main.py %*
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo [run] exit code=%RC%.
    pause
)

endlocal
