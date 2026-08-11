@echo off
chcp 866 >nul 2>&1
setlocal
set "PYEXE=python.exe"
where py.exe >nul 2>&1 && set "PYEXE=py.exe"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
echo ============ SMOKE v9 ============
"%PYEXE%" smoke_v9.py
echo.
echo ============ SMOKE v10 ============
"%PYEXE%" smoke_v10.py
echo.
echo ============ SMOKE v11 ============
"%PYEXE%" smoke_v11.py
echo.
echo ============ SMOKE v17 (orchestrator P0) ============
"%PYEXE%" tools\smoke_v17.py
echo.
echo ============ SMOKE v18 (vocal_fx + sidechain + audit) ============
"%PYEXE%" tools\smoke_v18.py
echo.
pause
endlocal
