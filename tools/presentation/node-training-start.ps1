[CmdletBinding()]
param(
    [ValidateSet('start', 'status')][string]$Action = 'start',
    [string]$Source = 'D:/delta/worktree-c2',
    [string]$DataRoot = 'D:/delta-data/presentation-20260924'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Source = (& git -C $Source rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'The configured MNIST demo checkout is unavailable.' }
$Data = Join-Path ([IO.Path]::GetFullPath($DataRoot)) 'node-training'
$MetadataPath = Join-Path $Data 'process.json'
$Base = 'http://127.0.0.1:8872/node-training'
function Read-Health {
    try { Invoke-RestMethod "$Base/api/health" -TimeoutSec 2 } catch { $null }
}
function Assert-Owned($Health, $Metadata) {
    $Owned = Get-Process -Id $Metadata.pid -ErrorAction SilentlyContinue
    if ($null -eq $Owned -or $Health.service -cne 'delta-node-training-example' -or
        $Health.instance_id -cne $Metadata.instance_id -or $Health.pid -ne $Metadata.pid -or
        [IO.Path]::GetFullPath($Health.source) -ine [IO.Path]::GetFullPath($Source) -or
        $Owned.StartTime.ToUniversalTime().Ticks -ne [long]$Metadata.start_ticks) {
        throw 'The node training listener ownership could not be verified.'
    }
}
$Mutex = [Threading.Mutex]::new($false, 'Local\DeltaNodeTrainingExample-8872')
$Held = $false
try {
    try { $Held = $Mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $Held = $true }
    if (-not $Held) { throw 'Node training startup is already running.' }
    $Health = Read-Health
    if ($null -ne $Health) {
        if (-not (Test-Path -LiteralPath $MetadataPath)) { throw 'Unverified listener on 8872.' }
        Assert-Owned $Health (Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json)
        Write-Output "Node training example: READY ($Base/)"
        exit 0
    }
    if ($Action -eq 'status') { Write-Output 'Node training example: STOPPED'; exit 1 }
    $Probe = [Net.Sockets.TcpClient]::new()
    try {
        try { $Probe.Connect('127.0.0.1', 8872) } catch [Net.Sockets.SocketException] { }
        if ($Probe.Connected) { throw 'Port 8872 is occupied. No process was stopped.' }
    } finally { $Probe.Dispose() }
    New-Item -ItemType Directory -Path $Data -Force | Out-Null
    $Instance = [Guid]::NewGuid().ToString('N')
    $Arguments = @((Get-Command pwsh).Source, '-NoProfile', '-File',
        (Join-Path $PSScriptRoot 'node-training-host.ps1'), '-Source', $Source,
        '-Data', $Data, '-Instance', $Instance)
    $Quoted = $Arguments | ForEach-Object {
        if ($_.Contains('"')) { throw 'Embedded quotes are unsupported in launcher paths.' }
        '"' + $_ + '"'
    }
    # Independent hidden process: it must survive the calling terminal/task closing.
    $Startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0}
    $Started = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine=($Quoted -join ' '); CurrentDirectory=$PSScriptRoot; ProcessStartupInformation=$Startup
    }
    if ($Started.ReturnValue -ne 0) { throw "Node training launch failed: $($Started.ReturnValue)" }
    Write-Output 'Preparing the offline MNIST example; waiting for its local API...'
    for ($Attempt = 0; $Attempt -lt 180; $Attempt++) {
        $Health = Read-Health
        if ($null -ne $Health) {
            if ($Health.instance_id -cne $Instance) { throw 'An unexpected listener appeared on 8872.' }
            $Owned = Get-Process -Id $Health.pid -ErrorAction Stop
            $Metadata = @{pid=$Health.pid; start_ticks=$Owned.StartTime.ToUniversalTime().Ticks; instance_id=$Instance}
            Assert-Owned $Health $Metadata
            $Metadata | ConvertTo-Json | Set-Content -LiteralPath $MetadataPath -Encoding utf8
            Write-Output "Node training example: READY ($Base/)"
            exit 0
        }
        if ($null -eq (Get-Process -Id $Started.ProcessId -ErrorAction SilentlyContinue)) {
            throw "Node training preparation failed. See $Data/host.log"
        }
        Start-Sleep -Seconds 1
    }
    throw "Node training did not become ready. Inspect $Data/host.log before retrying."
} finally {
    if ($Held) { $Mutex.ReleaseMutex() }
    $Mutex.Dispose()
}
