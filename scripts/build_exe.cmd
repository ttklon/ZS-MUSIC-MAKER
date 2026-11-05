@echo off
REM ZS Music Maker - сборка exe для Windows 11 (PyInstaller, onedir)
REM Результат: dist\ZS Music Maker\ZS Music Maker.exe
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo [build] нет .venv - запускаю setup.cmd
    call "%~dp0setup.cmd" || goto :fail
)

set PY=.venv\Scripts\python.exe
echo [build] проверяю PyInstaller...
%PY% -c "import PyInstaller" 2>nul || %PY% -m pip install "pyinstaller>=6.6" || goto :fail

echo [build] чищу прошлые артефакты...
if exist build\zsmm rmdir /s /q build\zsmm
if exist "dist\ZS Music Maker" rmdir /s /q "dist\ZS Music Maker"

echo [build] собираю...
%PY% -m PyInstaller packaging\zsmm.spec --noconfirm --clean --distpath dist --workpath build\zsmm || goto :fail

echo [build] smoke-тест собранного exe...
"dist\ZS Music Maker\ZS Music Maker.exe" --version || goto :fail

echo [build] ГОТОВО: dist\ZS Music Maker\
exit /b 0

:fail
echo [build] СБОРКА НЕ УДАЛАСЬ
exit /b 1
