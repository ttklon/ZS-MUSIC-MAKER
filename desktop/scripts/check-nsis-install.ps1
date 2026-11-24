param([Parameter(Mandatory=$true)][string]$Installer, [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:LOCALAPPDATA ('ZSMM-install-check-' + [guid]::NewGuid().ToString('N'))
$workspace = Join-Path $env:RUNNER_TEMP ('ZSMM-user-data-' + [guid]::NewGuid().ToString('N'))
$result = @{ ok=$false; scope='clean-current-user-NSIS-installed-agent-preflight-no-models'; install=$target; installerSha256=(Get-FileHash -Algorithm SHA256 $Installer).Hash; acl=@(); checks=@() }
$windowReportFile = $null
$originalWindowReport = $env:ZSMM_WINDOW_CHECK_OUT
$originalAppData = $env:APPDATA
$originalPath = [Environment]::GetEnvironmentVariable('PATH', 'Process')
$originalPythonPath = [Environment]::GetEnvironmentVariable('PYTHONPATH', 'Process')
$originalPythonHome = [Environment]::GetEnvironmentVariable('PYTHONHOME', 'Process')
$originalAgentScenario = [Environment]::GetEnvironmentVariable('ZSMM_AGENT_TEST_SCENARIO', 'Process')
$runtimeOverrideNames = @('ZSMM_WORKSPACE', 'ZSMM_PYTHON', 'ZSMM_PIPELINE_ROOT', 'ZSMM_ROOT')
$originalRuntimeOverrides = @{}
foreach ($name in $runtimeOverrideNames) { $originalRuntimeOverrides[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
function Wait-Checked($p, $label, $timeoutMs = 300000) {
    if (-not $p.WaitForExit($timeoutMs)) { $p.Kill(); throw "$label timed out" }
    if ($p.ExitCode -ne 0) { throw "$label exit $($p.ExitCode)" }
}
function Is-UnderPath($candidate, $root) {
    if ([string]::IsNullOrWhiteSpace($candidate) -or [string]::IsNullOrWhiteSpace($root)) { return $false }
    try {
        $fullCandidate = [System.IO.Path]::GetFullPath($candidate).TrimEnd([char[]]@('\\', '/'))
        $fullRoot = [System.IO.Path]::GetFullPath($root).TrimEnd([char[]]@('\\', '/'))
        return [string]::Equals($fullCandidate, $fullRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
            $fullCandidate.StartsWith($fullRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
    } catch { return $false }
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
    $project = Join-Path $target 'resources/project'
    $python = Join-Path $project '.python/python.exe'
    if (-not (Test-Path $python)) { throw 'Installed bundled Python missing' }
    $result.installedExeSha256 = (Get-FileHash -Algorithm SHA256 $exe).Hash
    $result.installedPythonSha256 = (Get-FileHash -Algorithm SHA256 $python).Hash
    $result.installedVersion = (Get-Content (Join-Path $project 'version.json') -Raw | ConvertFrom-Json).version
    $result.installedMainSha256 = (Get-FileHash -Algorithm SHA256 (Join-Path $project 'main.py')).Hash
    $isolatedAppData = Join-Path $workspace 'AppData/Roaming'
    New-Item -ItemType Directory -Path $isolatedAppData -Force | Out-Null
    $env:APPDATA = $isolatedAppData
    foreach ($name in $runtimeOverrideNames) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
    $checkoutRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
    $pathEntries = @($env:PATH -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $removedCheckoutPathEntries = @($pathEntries | Where-Object { Is-UnderPath $_ $checkoutRoot })
    $env:PATH = (@($pathEntries | Where-Object { -not (Is-UnderPath $_ $checkoutRoot) }) -join ';')
    Remove-Item Env:PYTHONPATH, Env:PYTHONHOME, Env:ZSMM_AGENT_TEST_SCENARIO -ErrorAction SilentlyContinue
    $result.runtimeIsolation = @{ checkoutRoot=$checkoutRoot; removedCheckoutPathEntries=$removedCheckoutPathEntries; noCheckoutPath=(@($env:PATH -split ';' | Where-Object { Is-UnderPath $_ $checkoutRoot }).Count -eq 0); pythonPathCleared=($null -eq [Environment]::GetEnvironmentVariable('PYTHONPATH', 'Process')); pythonHomeCleared=($null -eq [Environment]::GetEnvironmentVariable('PYTHONHOME', 'Process')) }
    $windowReportFile = Join-Path $workspace 'installed-window.json'
    $env:ZSMM_WINDOW_CHECK_OUT = $windowReportFile
    $env:ZSMM_AGENT_PREFLIGHT_CHECK = '1'
    $env:ZSMM_ONLINE = '0'
    $env:ZSMM_PROBE_LOCAL_SERVICES = '0'
    $p = Start-Process -FilePath $exe -ArgumentList '--window-check' -PassThru
    if (-not $p.WaitForExit(720000)) { $p.Kill(); throw 'Installed window with agent preflight/retry timed out' }
    if (-not (Test-Path $env:ZSMM_WINDOW_CHECK_OUT)) { throw "Installed window report missing (exit $($p.ExitCode))" }
    $window = Get-Content $env:ZSMM_WINDOW_CHECK_OUT -Raw | ConvertFrom-Json
    $result.windowCheck = $window
    if ($p.ExitCode -ne 0) { throw "Installed window with agent preflight/retry exit $($p.ExitCode)" }
    if (-not $window.ok) { throw 'Installed window/agent preflight check failed' }
    if (-not $window.agentPreflight.ok) { throw 'Installed agent preflight denial or recovery failed' }
    $result.agentPreflight = $window.agentPreflight
    foreach ($acceptanceId in @('A0003', 'A0004')) {
        $record = $result.agentPreflight.acceptanceRecords.$acceptanceId
        if ($record -and $record.artifactHashes) { $record.artifactHashes.installerSha256 = $result.installerSha256 }
    }
    $result.checks += 'installed-window'
    $result.checks += 'installed-agent-ui-unknown-and-unbudgeted-denial-plus-measured-retry'
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
    if ($windowReportFile -and (Test-Path $windowReportFile)) {
        try {
            $result.windowCheck = Get-Content $windowReportFile -Raw | ConvertFrom-Json
            if ($result.windowCheck.agentPreflight) {
                $result.agentPreflight = $result.windowCheck.agentPreflight
                foreach ($acceptanceId in @('A0003', 'A0004')) {
                    $record = $result.agentPreflight.acceptanceRecords.$acceptanceId
                    if ($record -and $record.artifactHashes) { $record.artifactHashes.installerSha256 = $result.installerSha256 }
                }
            }
        } catch { $result.windowReportReadError = $_.Exception.Message }
    }
    $detail = $result.error.Replace('%','%25').Replace("`r",'%0D').Replace("`n",'%0A')
    Write-Output "::error title=Clean NSIS failure::$detail"
    throw
} finally {
    $json = $result | ConvertTo-Json -Depth 14 -Compress
    $json | Set-Content -Encoding utf8 $Report
    $window = $result.windowCheck
    $agent = $result.agentPreflight
    $agentFailures = @()
    $runtime = $null
    $retry = $null
    if ($agent -and $agent.checks) {
        $runtime = $agent.checks.canonicalRuntimePath
        foreach ($name in @('creationPreparationGate','unknownRamDenial','insufficientRamDenial','unknownDiskDenial','insufficientDiskDenial','unknownVramDenial','insufficientVramDenial','unbudgetedHeavyEngineDenial','measuredRetry')) {
            $check = $agent.checks.$name
            if ($check -and $check.ok -ne $true) {
                $status = [string]$check.uiStatus
                if ($status.Length -gt 300) { $status = $status.Substring(0, 300) }
                $errors = @{}
                foreach ($field in @('error','runError','taskError','reportError','protocolError')) {
                    $value = [string]$check.$field
                    if ($value.Length -gt 300) { $value = $value.Substring(0, 300) }
                    if ($value) { $errors[$field] = $value }
                }
                $agentFailures += @{ name=$name; reasons=@($check.reasons | Select-Object -First 2); errors=$errors; reportKeys=$check.reportKeys; taskDone=$check.taskDone; taskOk=$check.taskOk; syntheticSetupOnly=$check.syntheticSetupOnly; realSetupAcceptance=$check.realSetupAcceptance; uiStatus=$status; backend=$check.selectedBackend; filesUnchanged=$check.filesUnchanged; noHeavyStages=$check.noHeavyStages }
            }
        }
        $retry = $agent.checks.measuredRetry
    }
    $agentFailureNames = @($agentFailures | ForEach-Object { $_.name })
    $firstAgentFailure = $agentFailures | Select-Object -First 1
    $contractFailures = @()
    if ($window.resultContract.checks) {
        $contractFailures = @($window.resultContract.checks | Where-Object { $_.ok -ne $true } | ForEach-Object { $_.name })
    }
    $summary = @{
        ok=$result.ok; error=$result.error; installerSha256=$result.installerSha256
        installedVersion=$result.installedVersion; installedExeSha256=$result.installedExeSha256
        installedPythonSha256=$result.installedPythonSha256; installedMainSha256=$result.installedMainSha256
        runtimeIsolation=$result.runtimeIsolation
        windowOk=$window.ok; windowError=$window.error; resultContractOk=$window.resultContractVerified
        resultContractFailures=$contractFailures; agentPreflightOk=$agent.ok; agentPreflightError=$agent.error
        agentPreflightFailedChecks=$agentFailureNames; firstAgentPreflightFailure=$firstAgentFailure; canonicalRuntimePath=$runtime
        retry=$(if ($retry) { @{ ok=$retry.ok; taskDone=$retry.taskDone; taskOk=$retry.taskOk; taskError=$retry.taskError; protocolError=$retry.protocolError; runError=$retry.runError; reportError=$retry.reportError; reportKeys=$retry.reportKeys; resultStatus=$retry.resultStatus; backend=$retry.backend; preflightStatus=$retry.preflightStatus; preflightDecision=$retry.preflightDecision; previousFilesPreserved=$retry.previousFilesPreserved; masterSha256=$retry.masterSha256; uiStatus=$retry.uiStatus } } else { $null })
    }
    $summaryJson = $summary | ConvertTo-Json -Depth 8 -Compress
    $annotation = $summaryJson.Replace('%','%25').Replace("`r",'%0D').Replace("`n",'%0A')
    Write-Output "::notice title=NSIS installed-check summary::$annotation"
    if ($env:GITHUB_STEP_SUMMARY) {
        @('### NSIS installed-check report','```json',$json,'```') | Add-Content -Encoding utf8 $env:GITHUB_STEP_SUMMARY
    }
    Remove-Item Env:ZSMM_AGENT_PREFLIGHT_CHECK, Env:ZSMM_ONLINE, Env:ZSMM_PROBE_LOCAL_SERVICES, Env:ZSMM_WINDOW_CHECK_OUT, Env:PYTHONPATH, Env:PYTHONHOME, Env:ZSMM_AGENT_TEST_SCENARIO -ErrorAction SilentlyContinue
    if ($null -ne $originalWindowReport) { [Environment]::SetEnvironmentVariable('ZSMM_WINDOW_CHECK_OUT', $originalWindowReport, 'Process') }
    if ($null -eq $originalPath) { Remove-Item Env:PATH -ErrorAction SilentlyContinue }
    else { [Environment]::SetEnvironmentVariable('PATH', $originalPath, 'Process') }
    if ($null -ne $originalPythonPath) { [Environment]::SetEnvironmentVariable('PYTHONPATH', $originalPythonPath, 'Process') }
    if ($null -ne $originalPythonHome) { [Environment]::SetEnvironmentVariable('PYTHONHOME', $originalPythonHome, 'Process') }
    if ($null -ne $originalAgentScenario) { [Environment]::SetEnvironmentVariable('ZSMM_AGENT_TEST_SCENARIO', $originalAgentScenario, 'Process') }
    foreach ($name in $runtimeOverrideNames) {
        if ($null -eq $originalRuntimeOverrides[$name]) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
        else { [Environment]::SetEnvironmentVariable($name, $originalRuntimeOverrides[$name], 'Process') }
    }
    if ($null -eq $originalAppData) { Remove-Item Env:APPDATA -ErrorAction SilentlyContinue }
    else { $env:APPDATA = $originalAppData }
}
