@echo off
REM ================================================================
REM  ZS Music Maker — run.bat (главный запуск, Windows)
REM  v30 FIX (P0): этого файла НЕ БЫЛО в репозитории, хотя на него
REM  ссылались README.md ("run.bat :: главный запуск"), INSTALL.md,
REM  create_desktop_shortcut.ps1 и verify.bat. Двойной клик по
REM  ярлыку/инструкциям вёл в никуда. Восстановлен как тонкая
REM  обёртка над единой точкой входа main.py.
REM ================================================================
chcp 65001 >nul 2>&1
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Ищем Python: сначала venv проекта, потом системный
set "PYEXE="
if exist "venv\Scripts\python.exe" (
    set "PYEXE=venv\Scripts\python.exe"
) else (
    for %%P in (py.exe python.exe python3.exe) do (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            set "PYEXE=%%P"
            goto :got_python
        )
    )
)
:got_python
if "%PYEXE%"=="" (
    echo [run] Python не найден. Установите Python 3.10+ и добавьте в PATH.
    echo [run] Затем выполните: python install.py
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo ====================================================
echo   ZS Music Maker — Unified Launcher
echo   Python: %PYEXE%
echo   Режимы: --god ^| --desktop ^| --gradio ^| --console
echo ====================================================

"%PYEXE%" main.py %*
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo [run] exit code=%RC%. Логи: logs\
    pause
)

endlocal
