param([Parameter(Mandatory=$true)][string]$Installer, [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:LOCALAPPDATA ('ZSMM-install-check-' + [guid]::NewGuid().ToString('N'))
$workspace = Join-Path $env:RUNNER_TEMP ('ZSMM-user-data-' + [guid]::NewGuid().ToString('N'))
$result = @{ ok=$false; scope='clean-current-user-NSIS-bundled-core-no-models'; install=$target; acl=@(); checks=@() }
function Wait-Checked($p, $label) {
    if (-not $p.WaitForExit(300000)) { $p.Kill(); throw "$label timed out" }
    if ($p.ExitCode -ne 0) { throw "$label exit $($p.ExitCode)" }
}
try {
    if (Test-Path $target) { throw 'Install destination is not clean' }
    New-Item -ItemType Directory -Path $workspace | Out-Null
    $sentinel = Join-Path $workspace 'preserve-user-song.txt'
    Set-Content $sentinel 'user song must survive uninstall'
    # NSIS /D must be last and unquoted; our generated target contains no spaces.
    if ($target.Contains(' ')) { throw 'NSIS check requires a space-free generated target' }
    $p = Start-Process -FilePath (Resolve-Path $Installer) -ArgumentList @('/S', '/currentuser', "/D=$target") -PassThru
    Wait-Checked $p 'install'
    $exe = Join-Path $target 'ZS Music Maker.exe'
    if (-not (Test-Path $exe)) { throw 'Installed executable missing' }
    $result.checks += 'clean-silent-install'
    $broad = @('S-1-1-0', 'S-1-5-11', 'S-1-5-32-545')
    foreach ($path in @($target, $exe, (Join-Path $target 'resources'))) {
        $acl = Get-Acl $path
        $result.acl += @{ path=$path; sddl=$acl.Sddl }
        foreach ($rule in $acl.Access) {
            $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
            $danger = [System.Security.AccessControl.FileSystemRights]::Write -bor [System.Security.AccessControl.FileSystemRights]::Delete -bor [System.Security.AccessControl.FileSystemRights]::ChangePermissions -bor [System.Security.AccessControl.FileSystemRights]::TakeOwnership
            if ($sid -in $broad -and $rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $danger)) {
                throw "Broad writable install ACL: $sid on $path"
            }
        }
    }
    $result.checks += 'no-broad-install-write-acl'
    $env:ZSMM_WORKSPACE = $workspace
    $env:ZSMM_WINDOW_CHECK_OUT = Join-Path $workspace 'installed-window.json'
    $p = Start-Process -FilePath $exe -ArgumentList '--window-check' -PassThru
    Wait-Checked $p 'installed window'
    $window = Get-Content $env:ZSMM_WINDOW_CHECK_OUT -Raw | ConvertFrom-Json
    if (-not $window.ok) { throw 'Installed window failed' }
    $result.checks += 'installed-window'
    $project = Join-Path $target 'resources/project'
    $python = Join-Path $project '.python/python.exe'
    if (-not (Test-Path $python)) { throw 'Installed bundled Python missing' }
    $code = @'
import sys
sys.path.insert(0, sys.argv[1])
import cloudpickle, numpy, soundfile, scipy, requests
from app.ai.sequential_runner import SequentialAIRunner, AIStage
runner = SequentialAIRunner(vram_probe=lambda: 0)
runner.add(AIStage('installed', None, lambda h,c: {'ok': True}, timeout_sec=30))
report = runner.run()
assert report.stages[0].ok, report.to_dict()
assert runner.sink()['installed']['ok']
print('Installed bundled Python isolated stage PASS; no model inference claimed')
'@
    $originalAcl = Get-Acl $project
    $lockedAcl = Get-Acl $project
    $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $rule = [System.Security.AccessControl.FileSystemAccessRule]::new($sid, 'Write', 'ContainerInherit,ObjectInherit', 'None', 'Deny')
    $lockedAcl.AddAccessRule($rule)
    try {
        Set-Acl -Path $project -AclObject $lockedAcl
        $writeDenied = $false
        try { [System.IO.File]::WriteAllText((Join-Path $project 'forbidden-write-probe'), 'must fail') }
        catch { $writeDenied = ($_.Exception.InnerException -is [System.UnauthorizedAccessException]) -or ($_.Exception -is [System.UnauthorizedAccessException]) }
        if (-not $writeDenied) { throw 'Read-only install ACL was not enforced' }
        $pythonOutput = & $python -I -B -c $code $project 2>&1
        $pythonCode = $LASTEXITCODE
        $pythonOutput | Write-Output
        if ($pythonCode -ne 0) { throw ("Installed isolated stage failed under read-only install ACL: " + (($pythonOutput | Select-Object -Last 25) -join "`n")) }
        $result.checks += 'installed-relocated-python-isolated-stage-read-only-install'
    } finally {
        Set-Acl -Path $project -AclObject $originalAcl
    }
    $uninstaller = Get-ChildItem $target -Filter '*Uninstall*.exe' | Select-Object -First 1
    if (-not $uninstaller) { throw 'Uninstaller missing' }
    $p = Start-Process -FilePath $uninstaller.FullName -ArgumentList @('/S', "_?=$target") -PassThru
    Wait-Checked $p 'uninstall'
    if (Test-Path $exe) { throw 'Application executable survived uninstall' }
    if ((Get-Content $sentinel -Raw).Trim() -ne 'user song must survive uninstall') { throw 'User data lost' }
    $result.checks += 'uninstall-preserves-external-workspace'
    $result.ok = $true
} catch {
    $result.error = $_.Exception.Message
    $detail = $result.error.Replace('%','%25').Replace("`r",'%0D').Replace("`n",'%0A')
    Write-Output "::error title=Clean NSIS failure::$detail"
    throw
} finally {
    $result | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $Report
    Remove-Item Env:ZSMM_WORKSPACE -ErrorAction SilentlyContinue
}
