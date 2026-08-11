@echo off
REM ZS Music Maker — Windows launcher (AUDIT-FIX)
REM Раньше вызывал main_v8.py, которого НЕТ в репозитории — заменён
REM на единый main.py (консолидированная точка входа).
chcp 65001 >nul
setlocal ENABLEEXTENSIONS
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        set "PY=python"
    ) else (
        echo Python не найден. Установите Python 3.10+.
        pause & exit /b 1
    )
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo ============================================
echo   ZS Music Maker — Unified Launcher
echo ============================================

%PY% main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ошибка запуска. Логи: logs\session.log
    pause
)
endlocal
