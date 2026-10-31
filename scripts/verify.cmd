@echo off
REM ZS Music Maker - full local verification: tests + smoke + honesty audit
setlocal
cd /d "%~dp0.."
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
%PY% -m compileall -q app agents modules tools updater ui config main.py install.py || exit /b 1
%PY% -m pytest tests/ -q || exit /b 1
%PY% tools\smoke_audio.py || exit /b 1
%PY% tools\smoke_god.py || exit /b 1
%PY% tools\fallback_audit.py || exit /b 1
%PY% main.py --version
echo [verify] ALL GREEN
