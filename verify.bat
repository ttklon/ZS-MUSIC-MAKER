@echo off
REM ================================================================
REM  ZS Music Maker — verify.bat (быстрая проверка установки)
REM  v30 FIX (P1): раньше скрипт вызывал НЕсуществующие корневые
REM  smoke_test.py и bootstrap_e2e_test.py (удалены много версий
REM  назад) — проверка всегда падала на первом же шаге. Теперь
REM  используем реально существующие pytest-набор и smoke_v26/v29.
REM ================================================================
setlocal
title ZS Music Maker — Verify
cd /d "%~dp0"
chcp 65001 >nul

echo.
echo ============================================================
echo   ZS MUSIC MAKER — VERIFY (быстрая проверка)
echo ============================================================
echo.

if exist venv\Scripts\activate.bat (
  echo [+] Активирую venv...
  call venv\Scripts\activate.bat
) else (
  echo [!] venv не найден. Использую системный Python.
  echo [!] Если импорты падают — выполни: python install.py
)

where python >nul 2>nul
if errorlevel 1 (
  echo [!!] Python не найден в PATH. Выполни: python install.py
  pause & exit /b 1
)

echo.
echo ============================================================
echo   [1/3] PYTEST SUITE (tests/)
echo ============================================================
python -m pytest tests/ -q
set TEST_CODE=%errorlevel%

echo.
echo ============================================================
echo   [2/3] SMOKE v26 (аудио-качество)
echo ============================================================
python tools\smoke_v26.py
set SMOKE26_CODE=%errorlevel%

echo.
echo ============================================================
echo   [3/3] SMOKE v29 (God Mode E2E)
echo ============================================================
python tools\smoke_v29.py
set SMOKE29_CODE=%errorlevel%

echo.
echo ============================================================
if %TEST_CODE% EQU 0 (
  if %SMOKE26_CODE% EQU 0 (
    if %SMOKE29_CODE% EQU 0 (
      echo   [OK] ВСЁ ЗЕЛЁНОЕ! Приложение готово.
      echo   Запускай run.bat или: python main.py --god
      goto :done
    )
  )
)
echo   [!] Есть падения. Смотри вывод выше и logs\
:done
echo ============================================================
pause
