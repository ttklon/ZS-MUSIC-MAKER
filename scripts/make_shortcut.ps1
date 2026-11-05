# Ярлык ZS Music Maker на рабочем столе (Windows 11).
#
# Если рядом со скриптом лежит собранная папка dist\ZS Music Maker, ярлык ведёт
# на exe (запуск без консоли и без Python). Иначе — на scripts\run_silent.cmd,
# то есть запуск из исходников тоже проходит без окна консоли.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root "dist\ZS Music Maker\ZS Music Maker.exe"
$fallback = Join-Path $root "scripts\run_silent.cmd"

if (Test-Path $exe) {
    $target = $exe
    Write-Host "[shortcut] цель: собранный exe"
} else {
    $target = $fallback
    Write-Host "[shortcut] цель: run_silent.cmd (exe не собран)"
}

if (-not (Test-Path $target)) {
    Write-Error "Не найдено: $target"
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) "ZS Music Maker.lnk"))
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $root
$shortcut.Description = "ZS Music Maker - локальная студия треков"
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,138"
$shortcut.Save()
Write-Host "[shortcut] готово: рабочий стол -> ZS Music Maker.lnk"
