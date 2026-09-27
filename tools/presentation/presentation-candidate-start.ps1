[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'status', 'stop')]
    [string]$Action = 'start',
    [string]$ControllerRepo = 'D:\delta-main-demo',
    [string]$DataRoot = 'D:\delta-data\presentation-candidate-20260927',
    [string]$FormalReport = 'C:\Users\madoev\.codex\worktrees\feature000-binding-candidate\delta\formal\reports\formal-verification-report.json',
    [int]$ControllerPort = 8865,
    [int]$Port = 8890,
    [int]$NodePort = 8892
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ControllerRepo = [IO.Path]::GetFullPath($ControllerRepo)
$DataRoot = [IO.Path]::GetFullPath($DataRoot)
$PanelData = Join-Path $DataRoot 'panel'
$ControllerData = Join-Path $DataRoot 'controller'
$MetadataPath = Join-Path $PanelData 'candidate-process.json'
$Url = "http://127.0.0.1:$Port"
$Python = Join-Path $ControllerRepo '.venv/Scripts/python.exe'
$NodeData = Join-Path $DataRoot 'node-training'
$NodeMetadataPath = Join-Path $NodeData 'process.json'

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
        return $null
    }
    return $Candidate
}

function Assert-Identity($Health, $Metadata) {
    if ($null -eq $Health -or $null -eq $Metadata -or
        $Health.service -cne 'delta-presentation' -or
        $Health.instance_id -cne $Metadata.instance_id -or
        $Metadata.url -cne $Url -or $null -eq (Get-OwnedProcess $Metadata)) {
        throw 'Candidate presentation instance ownership could not be verified.'
    }
}

if ($Action -eq 'status') {
    $Health = Read-Health
    if ($null -eq $Health) {
        Write-Output "Candidate presentation ($Url): STOPPED"
        exit 1
    }
    Assert-Identity $Health (Read-Metadata)
    $Health | ConvertTo-Json
    Write-Output "Candidate presentation: READY ($Url)"
    exit 0
}

if ($Action -eq 'stop') {
    $Metadata = Read-Metadata
    $Health = Read-Health
    if ($null -ne $Health) {
        Assert-Identity $Health $Metadata
        if ($null -ne $Health.active_job) { throw 'A job is active. Wait for completion before stopping.' }
        $OwnedProcess = Get-OwnedProcess $Metadata
        try {
            Invoke-RestMethod "$Url/api/shutdown" -Method Post -ContentType 'application/json' `
                -Headers @{Origin = $Url; 'X-Delta-Presentation' = '1'} -Body '{}' -TimeoutSec 5 | Out-Null
        } catch { }
        if (-not $OwnedProcess.WaitForExit(10000)) {
            Stop-Process -Id $OwnedProcess.Id -Force
        }
    }
    # Stop node-training if owned by this candidate instance
    if (Test-Path -LiteralPath $NodeMetadataPath) {
        try {
            $NodeMeta = Get-Content -LiteralPath $NodeMetadataPath -Raw | ConvertFrom-Json
            $NodeProc = Get-Process -Id $NodeMeta.pid -ErrorAction SilentlyContinue
            if ($null -ne $NodeProc -and $NodeProc.StartTime.ToUniversalTime().Ticks -eq [long]$NodeMeta.start_ticks) {
                Stop-Process -Id $NodeProc.Id -Force -ErrorAction SilentlyContinue
            }
        } catch { }
    }
    Write-Output "Candidate presentation ($Url) stopped. Frozen demo stack on port 8870 was NOT touched."
    exit 0
}

# Start flow
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python executable missing: $Python"
}

# Launch candidate node-training on $NodePort
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'node-training-start.ps1') start -DataRoot $DataRoot -Port $NodePort
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Candidate node training example on port $NodePort could not be started; continuing presentation launch."
}

New-Item -ItemType Directory -Path $PanelData -Force | Out-Null

$Health = Read-Health
if ($null -ne $Health) {
    Assert-Identity $Health (Read-Metadata)
    Write-Output "Candidate presentation already running: $Url"
    exit 0
}

if ($null -ne (Get-OwnedProcess (Read-Metadata))) {
    throw 'Candidate presentation is starting or unresponsive; inspect logs in panel directory.'
}

# Ensure port is free
$Probe = [Net.Sockets.TcpClient]::new()
try {
    try { $Probe.Connect('127.0.0.1', $Port) } catch [Net.Sockets.SocketException] { }
    if ($Probe.Connected) { throw "Port $Port belongs to another listener; nothing was stopped." }
} finally { $Probe.Dispose() }

$InstanceId = [Guid]::NewGuid().ToString('N')
$Arguments = @((Join-Path $PSScriptRoot 'server.py'), '--data-dir', $PanelData,
    '--controller-port', [string]$ControllerPort, '--port', [string]$Port,
    '--node-port', [string]$NodePort,
    '--instance-id', $InstanceId)
if (Test-Path -LiteralPath $FormalReport) { $Arguments += @('--formal-report', $FormalReport) }

$QuotedArguments = foreach ($Argument in $Arguments) {
    if ($Argument.Contains('"')) { throw 'An argument contains an unsupported quote.' }
    '"' + $Argument.TrimEnd('\') + '"'
}

$Process = Start-Process -FilePath $Python -ArgumentList ($QuotedArguments -join ' ') `
    -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $PanelData 'candidate-server.stdout.txt') `
    -RedirectStandardError (Join-Path $PanelData 'candidate-server.stderr.txt')

@{pid = $Process.Id; start_ticks = $Process.StartTime.ToUniversalTime().Ticks;
    instance_id = $InstanceId; url = $Url; source = $PSScriptRoot;
    port = $Port; node_port = $NodePort} |
    ConvertTo-Json | Set-Content -LiteralPath $MetadataPath -Encoding utf8

for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
    $Health = Read-Health
    if ($null -ne $Health) {
        Assert-Identity $Health (Read-Metadata)
        Write-Output "Candidate presentation READY: $Url (Node Training: http://127.0.0.1:$NodePort/node-training/)"
        exit 0
    }
    if ($Process.HasExited) { throw "Candidate presentation exited unexpectedly. Inspect $PanelData\candidate-server.stderr.txt." }
    Start-Sleep -Milliseconds 300
}

throw 'Candidate readiness timed out. Inspect candidate-server.stderr.txt for diagnosis.'
