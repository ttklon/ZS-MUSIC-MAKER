@echo off
REM ZS Music Maker - полная локальная проверка: компиляция, тесты, смоуки, аудиты
setlocal
cd /d "%~dp0.."
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

echo [verify] 1/7 компиляция ...
%PY% -m compileall -q app agents modules tools updater ui main.py install.py || goto :fail
echo [verify] 2/7 тесты ...
%PY% -m pytest tests/ -q -p no:cacheprovider || goto :fail
echo [verify] 3/7 smoke: аудио ...
%PY% tools\smoke_audio.py || goto :fail
echo [verify] 4/7 smoke: God Mode ...
%PY% tools\smoke_god.py || goto :fail
echo [verify] 5/7 аудит честности ...
%PY% -m tools.audit_honesty || goto :fail
echo [verify] 6/7 мёртвые импорты ...
%PY% tools\ast_dead_imports.py || goto :fail
echo [verify] 7/7 версия и готовность ...
%PY% main.py --version || goto :fail
%PY% main.py --readiness || goto :fail

echo.
echo [verify] ALL GREEN
exit /b 0

:fail
echo.
echo [verify] ПРОВЕРКА НЕ ПРОЙДЕНА
exit /b 1
