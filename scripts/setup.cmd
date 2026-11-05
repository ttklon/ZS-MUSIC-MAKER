@echo off
REM ZS Music Maker - одноразовая подготовка окружения (Windows 11)
REM Проверяет Python, создаёт .venv, ставит зависимости и делает health-check.
setlocal EnableDelayedExpansion
cd /d "%~dp0.."

set "PYTHON_OK="
for %%P in (py python) do (
    if not defined PYTHON_OK (
        %%P -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "PYTHON_OK=%%P"
        )
    )
)
if not defined PYTHON_OK (
    echo [setup] Нужен Python 3.11 или новее.
    echo [setup] Скачай с https://www.python.org/downloads/ и отметь "Add python.exe to PATH".
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [setup] создаю окружение .venv ...
    %PYTHON_OK% -m venv .venv || goto :fail
)

set "VPY=.venv\Scripts\python.exe"
echo [setup] обновляю pip ...
"%VPY%" -m pip install --upgrade pip --quiet

echo [setup] ставлю зависимости (это может занять несколько минут) ...
"%VPY%" -m pip install -r requirements.txt || goto :fail

echo [setup] проверяю совместимость зависимостей ...
"%VPY%" -m pip check || goto :fail

echo [setup] проверяю окружение ...
"%VPY%" main.py --health
if errorlevel 1 (
    echo [setup] health-check вернул предупреждения - программа всё равно запустится.
)

echo.
echo [setup] ГОТОВО. Запуск: scripts\run.cmd   (или scripts\run_silent.cmd без консоли)
exit /b 0

:fail
echo [setup] УСТАНОВКА НЕ УДАЛАСЬ (код !ERRORLEVEL!)
exit /b 1
