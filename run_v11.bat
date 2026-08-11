@echo off
REM ZS Music Maker v11 «Hit Locked» — Windows launcher
REM UTF-8 в коде, CP866 в консоли (ТЗ 6)

chcp 866 >nul 2>&1
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
    echo [run_v11] Python не найден. Запусти windows_build.bat один раз.
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo ====================================================
echo   ZS Music Maker v11 «Hit Locked»
echo   Python: %PYEXE%
echo ====================================================

"%PYEXE%" main_v11.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo [run_v11] v11 exit code=%RC%. Fallback to v10...
    if exist run_v10.bat (
        call run_v10.bat
    ) else if exist main_v10.py (
        "%PYEXE%" main_v10.py
    ) else if exist run_v9.bat (
        call run_v9.bat
    ) else (
        "%PYEXE%" main.py
    )
)

endlocal
