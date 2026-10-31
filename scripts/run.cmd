@echo off
REM ZS Music Maker - launch desktop wizard (visible console for progress)
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
    echo [run] no .venv found, running setup first...
    call "%~dp0setup.cmd" || exit /b 1
)
".venv\Scripts\python.exe" main.py %*
exit /b %ERRORLEVEL%
