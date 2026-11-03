@echo off
REM ZS Music Maker - запуск мастера с консолью (видно прогресс и ошибки)
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
    echo [run] окружение не найдено - запускаю setup ...
    call "%~dp0setup.cmd" || exit /b 1
)
".venv\Scripts\python.exe" main.py %*
exit /b %ERRORLEVEL%
