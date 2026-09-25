[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'status', 'stop')]
    [string]$Action = 'start',
    [string]$ControllerRepo = 'D:\delta-main-demo',
    [string]$DataRoot = 'D:\delta-data\presentation-20260924',
    [string]$FormalReport = 'C:\Users\madoev\.codex\worktrees\feature000-binding-candidate\delta\formal\reports\formal-verification-report.json',
    [int]$ControllerPort = 8865,
    [int]$Port = 8870,
    [switch]$KeepController
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ControllerRepo = [IO.Path]::GetFullPath($ControllerRepo)
$DataRoot = [IO.Path]::GetFullPath($DataRoot)
$PanelData = Join-Path $DataRoot 'panel'
$ControllerData = Join-Path $DataRoot 'controller'
$Config = Join-Path $DataRoot "local-$ControllerPort.json"
$MetadataPath = Join-Path $PanelData 'presentation-process.json'
$Url = "http://127.0.0.1:$Port"
$ControllerLauncher = Join-Path $ControllerRepo 'tools/working-version/delta-local.ps1'
$Python = Join-Path $ControllerRepo '.venv/Scripts/python.exe'
$ExpectedControllerCommit = 'c8aea64972f741060d1e527ebbb6f9a5a168a075'

function Read-Health {
    try { return Invoke-RestMethod "$Url/api/health" -TimeoutSec 3 -ErrorAction Stop }
    catch { return $null }
}

function Read-Metadata {
    if (Test-Path -LiteralPath $MetadataPath) {
        return Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
    }
    return $null
}

function Get-OwnedProcess($Metadata) {
    if ($null -eq $Metadata) { return $null }
    $Candidate = Get-Process -Id $Metadata.pid -ErrorAction SilentlyContinue
    if ($null -eq $Candidate) { return $null }
    if ($Candidate.StartTime.ToUniversalTime().Ticks -ne [long]$Metadata.start_ticks) {
        # After reboot Windows may reuse a saved PID. It no longer identifies
        # our process; never stop it. Health identity and the port probe below
        # still prevent taking over an unrelated listener.
        return $null
    }
    return $Candidate
}

function Assert-Identity($Health, $Metadata) {
    if ($null -eq $Health -or $null -eq $Metadata -or
        $Health.service -cne 'delta-presentation' -or
        $Health.instance_id -cne $Metadata.instance_id -or
        $Metadata.url -cne $Url -or $null -eq (Get-OwnedProcess $Metadata)) {
        throw 'Presentation instance ownership could not be verified.'
    }
}

function Invoke-Controller([string]$Command) {
    & pwsh -NoProfile -File $ControllerLauncher $Command -SkipInstall -Config $Config -DataDir $ControllerData
    if ($LASTEXITCODE -ne 0) { throw "Controller $Command failed with exit code $LASTEXITCODE" }
}

function Ensure-Controller {
    $StatusOutput = & pwsh -NoProfile -File $ControllerLauncher status -Config $Config -DataDir $ControllerData
    $StatusCode = $LASTEXITCODE
    $ControllerStatus = ($StatusOutput -join [Environment]::NewLine) | ConvertFrom-Json
    if ($StatusCode -eq 0 -and $ControllerStatus.status -ceq 'READY') { return }
    if ($StatusCode -eq 3 -and $ControllerStatus.status -in @('STOPPED', 'STALE_METADATA')) {
        Invoke-Controller 'start'
        return
    }
    throw 'Controller exists but is not ready; inspect its logs before restarting.'
}

if ($Action -eq 'status') {
    $Health = Read-Health
    if ($null -eq $Health) { Write-Output 'Presentation: STOPPED'; exit 1 }
    Assert-Identity $Health (Read-Metadata)
    $Health | ConvertTo-Json
    Write-Output "Open: $Url"
    exit 0
}

if ($Action -eq 'stop') {
    $Metadata = Read-Metadata
    $Health = Read-Health
    if ($null -ne $Health) {
        Assert-Identity $Health $Metadata
        if ($null -ne $Health.active_job) { throw 'A job is active. Wait for completion before stopping.' }
        $OwnedProcess = Get-OwnedProcess $Metadata
        Invoke-RestMethod "$Url/api/shutdown" -Method Post -ContentType 'application/json' `
            -Headers @{Origin = $Url; 'X-Delta-Presentation' = '1'} -Body '{}' -TimeoutSec 5 | Out-Null
        if (-not $OwnedProcess.WaitForExit(10000)) { throw 'Graceful stop timed out; process was not killed.' }
    }
    elseif ($null -ne (Get-OwnedProcess $Metadata)) {
        throw 'Owned process is unresponsive. It was not killed; inspect server.stderr.txt.'
    }
    if (-not $KeepController -and (Test-Path -LiteralPath $Config)) { Invoke-Controller 'stop' }
    Write-Output 'Presentation stopped. Saved runs were retained.'
    exit 0
}

if (-not (Test-Path -LiteralPath $Python) -or -not (Test-Path -LiteralPath $ControllerLauncher)) {
    throw 'Prepared baseline Controller environment is missing. See tools/presentation/README.md.'
}
$ActualCommit = (& git -C $ControllerRepo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $ActualCommit -cne $ExpectedControllerCommit) {
    throw 'Controller source differs from the reviewed presentation baseline.'
}
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'node-training-start.ps1') start -DataRoot $DataRoot
if ($LASTEXITCODE -ne 0) {
    Write-Warning 'MNIST example is unavailable; inspect node-training/host.log. Main application startup continues.'
}
New-Item -ItemType Directory -Path $PanelData -Force | Out-Null
if (-not (Test-Path -LiteralPath $Config)) {
    $Descriptor = Get-Content (Join-Path $ControllerRepo 'configs/working-version/local.json') -Raw | ConvertFrom-Json
    $Descriptor.bindings.port = $ControllerPort
    $Descriptor.bindings.allowed_origins = @("http://127.0.0.1:$ControllerPort")
    $Descriptor | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Config -Encoding utf8
}
$ExistingConfig = Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
if ($ExistingConfig.bindings.port -ne $ControllerPort) { throw 'Stored Controller port does not match.' }

$Health = Read-Health
if ($null -ne $Health) {
    Assert-Identity $Health (Read-Metadata)
    Ensure-Controller
    Write-Output "Already running: $Url"
    exit 0
}
if ($null -ne (Get-OwnedProcess (Read-Metadata))) { throw 'Presentation is starting or unresponsive; inspect logs.' }
# Refuse an unrelated listener, including one that does not speak this API.
$Probe = [Net.Sockets.TcpClient]::new()
try {
    try { $Probe.Connect('127.0.0.1', $Port) } catch [Net.Sockets.SocketException] { }
    if ($Probe.Connected) { throw "Port $Port belongs to another listener; nothing was stopped." }
}
finally { $Probe.Dispose() }

Ensure-Controller
$InstanceId = [Guid]::NewGuid().ToString('N')
$Arguments = @((Join-Path $PSScriptRoot 'server.py'), '--data-dir', $PanelData,
    '--controller-port', [string]$ControllerPort, '--port', [string]$Port,
    '--instance-id', $InstanceId)
if (Test-Path -LiteralPath $FormalReport) { $Arguments += @('--formal-report', $FormalReport) }
# Start-Process uses a command-line string. Quote each path and reject embedded quotes.
$QuotedArguments = foreach ($Argument in $Arguments) {
    if ($Argument.Contains('"')) { throw 'An argument contains an unsupported quote.' }
    '"' + $Argument.TrimEnd('\') + '"'
}
$Process = Start-Process -FilePath $Python -ArgumentList ($QuotedArguments -join ' ') `
    -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $PanelData 'server.stdout.txt') `
    -RedirectStandardError (Join-Path $PanelData 'server.stderr.txt')
@{pid = $Process.Id; start_ticks = $Process.StartTime.ToUniversalTime().Ticks;
    instance_id = $InstanceId; url = $Url; source = $PSScriptRoot} |
    ConvertTo-Json | Set-Content -LiteralPath $MetadataPath -Encoding utf8
for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
    $Health = Read-Health
    if ($null -ne $Health) {
        Assert-Identity $Health (Read-Metadata)
        Write-Output "Ready: $Url"
        exit 0
    }
    if ($Process.HasExited) { throw 'Presentation exited. Inspect panel/server.stderr.txt.' }
    Start-Sleep -Milliseconds 300
}
throw 'Readiness timed out. Processes and logs were retained for diagnosis.'
