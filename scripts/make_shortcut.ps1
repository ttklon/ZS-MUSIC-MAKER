# Creates a Desktop shortcut for ZS Music Maker (Windows 11)
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root "scripts\run.cmd"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) "ZS Music Maker.lnk"))
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,138"
$shortcut.Save()
Write-Host "Shortcut created on Desktop."
