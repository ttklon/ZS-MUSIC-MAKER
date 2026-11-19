# Run after actions/setup-python (3.11 x64), before electron-builder.
# Copy a regular CPython installation, not a non-relocatable virtualenv.
$ErrorActionPreference = 'Stop'
$source = $env:pythonLocation
if (-not $source -or -not (Test-Path "$source/python.exe")) { throw 'setup-python runtime missing' }
$target = Join-Path $PSScriptRoot '../python-runtime'
if (Test-Path $target) { Remove-Item $target -Recurse -Force }
New-Item $target -ItemType Directory -Force | Out-Null
& "$source/python.exe" -m pip install -r "$PSScriptRoot/../../requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'Core dependencies installation failed' }
Copy-Item "$source/*" $target -Recurse -Force
# Verify relocation rather than merely checking that python.exe exists.
& "$target/python.exe" -I -c "import sys, pip, numpy, soundfile, scipy, requests; assert sys.version_info[:2] == (3, 11); print(sys.executable)"
if ($LASTEXITCODE -ne 0) { throw 'Relocated Python failed its import smoke test' }
"ZSMM_BUNDLE_PYTHON=1" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8
