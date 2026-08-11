@echo off
REM ================================================================
REM  autodetect_python.bat — ищет Python если PATH сломан
REM  Используется windows_build.bat как fallback
REM ================================================================
setlocal

set "FOUND="

REM 1. python в PATH
where python >nul 2>nul
if not errorlevel 1 (
  set "FOUND=python"
  goto :done
)

REM 2. py launcher
where py >nul 2>nul
if not errorlevel 1 (
  py -3.11 --version >nul 2>nul && set "FOUND=py -3.11"
  if defined FOUND goto :done
  py -3 --version >nul 2>nul && set "FOUND=py -3"
  if defined FOUND goto :done
)

REM 3. Стандартные пути установки
for %%D in (
  "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
  "C:\Python311\python.exe"
  "C:\Python312\python.exe"
  "C:\Python310\python.exe"
  "%ProgramFiles%\Python311\python.exe"
  "%ProgramFiles%\Python312\python.exe"
) do (
  if exist %%D (
    set "FOUND=%%~D"
    goto :done
  )
)

:done
if defined FOUND (
  echo %FOUND%
  endlocal & exit /b 0
)
echo NOT_FOUND
endlocal & exit /b 1
