@echo off
rem ZS Music Maker — прогон всех smoke-тестов (Windows).
rem v33 FIX (P0): раньше этот файл вызывал ЧЕТЫРЕ несуществующих скрипта
rem (smoke_v9.py / smoke_v10.py / smoke_v11.py в корне и tools\smoke_v17.py,
rem tools\smoke_v18.py — перенесены в docs\legacy\ в v29). Linux-версия
rem run_all_smoke.sh была исправлена, Windows — оставлена битой.
rem Теперь: идём только по реально существующим tools\smoke_v*.py,
rem как это делает run_all_smoke.sh. Активные: smoke_v26 (audio quality),
rem smoke_v29 (God Mode E2E).
chcp 866 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PYEXE=python.exe"
where py.exe >nul 2>&1 && set "PYEXE=py.exe"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

set /a PASS=0
set /a FAIL=0

for %%f in (tools\smoke_v*.py) do (
    echo ============ %%f ============
    "%PYEXE%" "%%f"
    if errorlevel 1 (
        echo [FAIL] %%f
        set /a FAIL+=1
    ) else (
        set /a PASS+=1
    )
    echo.
)

echo ================================================
echo SMOKE SUMMARY: %PASS% passed, %FAIL% failed
pause
endlocal
exit /b %FAIL%
