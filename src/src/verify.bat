@echo off
REM ================================================================
REM  ZS Music Maker v5 - Быстрая проверка (без переустановки)
REM  smoke_test.py (24 теста) + bootstrap_e2e_test.py (15 стадий)
REM ================================================================
setlocal
title ZS Music Maker v5 - Verify
cd /d "%~dp0"
chcp 65001 >nul

echo.
echo ============================================================
echo   ZS MUSIC MAKER v5 - VERIFY
echo   Быстрая проверка без переустановки зависимостей
echo ============================================================
echo.

if exist venv\Scripts\activate.bat (
  echo [+] Активирую venv...
  call venv\Scripts\activate.bat
) else (
  echo [!] venv не найден. Использую системный Python.
  echo [!] Если импорты падают - запусти windows_build.bat один раз.
)

where python >nul 2>nul
if errorlevel 1 (
  echo [!!] Python не найден в PATH. Запусти windows_build.bat.
  pause & exit /b 1
)

echo.
echo ============================================================
echo   [1/2] SMOKE-TEST (24 компонента)
echo ============================================================
python smoke_test.py
set SMOKE_CODE=%errorlevel%

echo.
echo ============================================================
echo   [2/2] E2E BOOTSTRAP TEST (15 стадий)
echo ============================================================
python bootstrap_e2e_test.py
set E2E_CODE=%errorlevel%

echo.
echo ============================================================
if %SMOKE_CODE% EQU 0 (
  if %E2E_CODE% EQU 0 (
    echo   [OK] ВСЁ ЗЕЛЁНОЕ! Приложение готово.
    echo   Запускай run.bat -^> http://127.0.0.1:7860
  ) else (
    echo   [!] smoke OK, но e2e упал. Смотри logs\e2e_report.json
  )
) else (
  echo   [!!] smoke упал. Запусти windows_build.bat переустановить.
)
echo ============================================================
pause
