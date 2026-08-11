@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS
cd /d "%~dp0"

REM ---- ZS Music Maker v8 launcher ----
echo ============================================
echo   ZS Music Maker v8 — Night Drive Edition
echo ============================================

REM 1) find python
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY=py -3.11"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        set "PY=python"
    ) else (
        echo Python не найден. Запусти windows_build.bat.
        pause & exit /b 1
    )
)

REM 2) HW detect print
%PY% -c "from app.core.hw_autodetect import detect, human_summary; print(human_summary(detect()))"

REM 3) launch main_v8
%PY% main_v8.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ошибка запуска. Логи: logs\session.log
    pause
)
endlocal
