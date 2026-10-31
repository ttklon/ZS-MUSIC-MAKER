@echo off
REM ZS Music Maker - one-time environment setup (Windows 11)
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
    echo [setup] creating venv...
    python -m venv .venv || goto :fail
)
echo [setup] installing core dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fail
echo [setup] ready. Launch: scripts\run.cmd
exit /b 0
:fail
echo [setup] FAILED
exit /b 1
