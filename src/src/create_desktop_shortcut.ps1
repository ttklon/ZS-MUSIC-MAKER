# create_desktop_shortcut.ps1
# Создаёт ярлык "ZS Music Maker v7" на Рабочем столе.
$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\ZS Music Maker v7.lnk")
$AppDir  = (Get-Location).Path
$Shortcut.TargetPath       = "$AppDir\run.bat"
$Shortcut.WorkingDirectory = "$AppDir"
$Shortcut.IconLocation     = "$AppDir\run.bat,0"
$Shortcut.WindowStyle      = 7
$Shortcut.Description      = "ZS Music Maker v7 (MM ZS) — локальная студия хитов"
$Shortcut.Save()
Write-Host "Ярлык создан на Рабочем столе."
