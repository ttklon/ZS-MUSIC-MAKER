@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  ZS Music Maker v9 — Chart Killer Edition
echo ========================================
echo.

REM ---- поиск python
if exist "venv\Scripts\python.exe" (
    set PY=venv\Scripts\python.exe
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
) else (
    set PY=python
)

REM ---- запуск v9
%PY% main_v9.py
if errorlevel 1 (
    echo.
    echo [v9] запуск завершился с ошибкой. Попробую main_v8...
    %PY% main_v8.py
    if errorlevel 1 (
        echo [v9] main_v8 тоже упал. Смотри logs\app.log
        pause
    )
)
endlocal
