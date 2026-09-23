[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ContainerName,
    [Parameter(Mandatory = $true)][string]$DiagnosticCampaignId,
    [Parameter(Mandatory = $true)][string]$ReceiptNonce,
    [Parameter(Mandatory = $true)][string]$ExpectedCollectorSha256,
    [Parameter(Mandatory = $true)][string]$AttemptSealPath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [Parameter(Mandatory = $true)][string]$LanesCompletePath,
    [Parameter(Mandatory = $true)][string]$TelemetryPath,
    [ValidateRange(1, 7200)][int]$WaitSeconds = 900
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$SchemaVersion = "1.1.0"

function Get-ContentId([byte[]]$Bytes) {
    $digest = [System.Security.Cryptography.SHA256]::HashData($Bytes)
    return "sha256:" + [Convert]::ToHexString($digest).ToLowerInvariant()
}

function Get-FileContentId([string]$Path) {
    return Get-ContentId ([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Path)))
}

function Write-ExclusiveJson([string]$Path, [object]$Value) {
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw "The preregistered host-exchange directory does not exist: $parent"
    }
    $json = $Value | ConvertTo-Json -Depth 20 -Compress
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($json + "`n")
    $stream = [IO.File]::Open(
        $Path,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write,
        [IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
}

function Invoke-Docker([string[]]$Arguments) {
    $output = & docker @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($Arguments -join ' ') failed: $output"
    }
    return ($output -join "`n").Trim()
}

function ConvertTo-UnixNanoseconds([DateTime]$Value) {
    $utc = $Value.ToUniversalTime()
    return [long](($utc.Ticks - [DateTime]::UnixEpoch.Ticks) * 100)
}

function Read-EventFamily([string[]]$Providers, [DateTime]$Start, [DateTime]$End) {
    $events = [Collections.Generic.List[object]]::new()
    $successfulQueries = 0
    $errors = [Collections.Generic.List[string]]::new()
    foreach ($provider in $Providers) {
        try {
            Get-WinEvent -ListProvider $provider -ErrorAction Stop | Out-Null
            $records = Get-WinEvent -FilterHashtable @{
                ProviderName = $provider
                StartTime = $Start
                EndTime = $End
            } -ErrorAction Stop
            $successfulQueries += 1
            foreach ($record in $records) {
                $instant = ConvertTo-UnixNanoseconds $record.TimeCreated
                $detail = [Text.UTF8Encoding]::new($false).GetBytes($record.ToXml())
                $events.Add([ordered]@{
                    category = $provider
                    detail_sha256 = Get-ContentId $detail
                    end_wall_time_ns = $instant
                    event_id = [string]$record.Id
                    provider = [string]$record.ProviderName
                    start_wall_time_ns = $instant
                })
            }
        }
        catch {
            if ($_.FullyQualifiedErrorId -like "NoMatchingEventsFound*") {
                $successfulQueries += 1
            }
            else {
                $errors.Add("$provider`: $($_.Exception.GetType().Name)")
            }
        }
    }
    if ($successfulQueries -ne $Providers.Count) {
        return [ordered]@{
            reason = "Not every requested Windows event provider was queryable ($successfulQueries/$($Providers.Count)): $($errors -join '; ')"
            status = "NOT_AVAILABLE"
        }
    }
    $ordered = @($events | Sort-Object start_wall_time_ns, provider, event_id)
    return [ordered]@{ status = "AVAILABLE"; value = $ordered }
}

$collectorSha256 = Get-FileContentId $PSCommandPath
if ($collectorSha256 -ne $ExpectedCollectorSha256) {
    throw "Host collector hash mismatch: expected $ExpectedCollectorSha256, got $collectorSha256"
}
if (Test-Path -LiteralPath $ReceiptPath) {
    throw "Host receipt already exists; this campaign cannot be retried: $ReceiptPath"
}
if (Test-Path -LiteralPath $TelemetryPath) {
    throw "Host telemetry already exists; this campaign cannot be retried: $TelemetryPath"
}
if (Test-Path -LiteralPath $LanesCompletePath) {
    throw "Lanes-complete handshake already exists; this campaign cannot be retried: $LanesCompletePath"
}
if (-not (Test-Path -LiteralPath $AttemptSealPath -PathType Leaf)) {
    throw "The runner has not published its durable attempt seal: $AttemptSealPath"
}
$attempt = Get-Content -LiteralPath $AttemptSealPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (
    [string]$attempt.schema_version -ne $SchemaVersion -or
    [string]$attempt.type_name -ne "FEATURE010_SIDECAR_DIAGNOSTIC_ATTEMPT_SEAL" -or
    [string]$attempt.state -ne "ARMED_ONE_SHOT_NO_RERUN" -or
    [string]$attempt.authority -ne "DIAGNOSTIC_ONLY" -or
    [string]$attempt.diagnostic_campaign_id -ne $DiagnosticCampaignId
) {
    throw "The durable attempt seal does not authorize this exact diagnostic campaign"
}

$captureStart = [DateTime]::UtcNow
$inspect = (Invoke-Docker @("inspect", $ContainerName) | ConvertFrom-Json)[0]
$runtimeVersion = Invoke-Docker @("version", "--format", "{{.Server.Version}}")
$cgroupVersion = Invoke-Docker @("info", "--format", "{{.CgroupVersion}}")
$period = [long]$inspect.HostConfig.CpuPeriod
if ($period -le 0) { $period = 100000 }
$quota = [long]$inspect.HostConfig.CpuQuota
if ($quota -le 0 -and [long]$inspect.HostConfig.NanoCpus -gt 0) {
    $quota = [long](([decimal]$inspect.HostConfig.NanoCpus * $period) / 1000000000)
}
$cpuMax = if ($quota -gt 0) { "$quota $period" } else { "max $period" }
$memoryMax = if ([long]$inspect.HostConfig.Memory -gt 0) {
    [string][long]$inspect.HostConfig.Memory
} else {
    "max"
}
$cpuset = [string]$inspect.HostConfig.CpusetCpus
if ([string]::IsNullOrWhiteSpace($cpuset)) {
    throw "The container has no explicit HostConfig.CpusetCpus allocation"
}
$machineMaterial = "$env:COMPUTERNAME|$((Get-CimInstance Win32_ComputerSystemProduct).UUID)"
$machineSha256 = Get-ContentId ([Text.UTF8Encoding]::new($false).GetBytes($machineMaterial))

$receipt = [ordered]@{
    collected_at_utc = [DateTime]::UtcNow.ToString("o")
    collector_sha256 = $collectorSha256
    container = [ordered]@{
        container_id = ([string]$inspect.Id).ToLowerInvariant()
        image_digest = ([string]$inspect.Image).ToLowerInvariant()
        runtime = "docker"
        runtime_version = $runtimeVersion
    }
    diagnostic_campaign_id = $DiagnosticCampaignId
    host = [ordered]@{
        machine_id_sha256 = $machineSha256
        operating_system = [Environment]::OSVersion.VersionString
    }
    receipt_nonce = $ReceiptNonce
    resources = [ordered]@{
        cgroup_mode = "V$([string]$cgroupVersion)"
        cpu_max = $cpuMax
        cpuset_cpus_effective = $cpuset
        memory_max = $memoryMax
    }
    schema_version = $SchemaVersion
    type_name = "FEATURE010_SIDECAR_DIAGNOSTIC_HOST_RECEIPT"
}
Write-ExclusiveJson $ReceiptPath $receipt

$deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
while (-not (Test-Path -LiteralPath $LanesCompletePath -PathType Leaf)) {
    if ([DateTime]::UtcNow -ge $deadline) {
        throw "Timed out waiting for lanes-complete handshake: $LanesCompletePath"
    }
    Start-Sleep -Milliseconds 100
}
$lanesCompleteSha256 = Get-FileContentId $LanesCompletePath
$captureEnd = [DateTime]::UtcNow
$dockerProviders = @(
    "Docker Desktop",
    "Microsoft-Windows-Lxss-Manager",
    "Microsoft-Windows-Hyper-V-Compute"
)
$hardwareProviders = @(
    "Microsoft-Windows-WHEA-Logger",
    "disk",
    "stornvme",
    "storport",
    "Microsoft-Windows-Kernel-Power",
    "Microsoft-Windows-Kernel-Processor-Power"
)
$telemetry = [ordered]@{
    capture_ended_at_utc = $captureEnd.ToString("o")
    capture_started_at_utc = $captureStart.ToString("o")
    collector_sha256 = $collectorSha256
    diagnostic_campaign_id = $DiagnosticCampaignId
    docker_wsl_events = Read-EventFamily $dockerProviders $captureStart $captureEnd
    lanes_complete_sha256 = $lanesCompleteSha256
    receipt_nonce = $ReceiptNonce
    schema_version = $SchemaVersion
    type_name = "FEATURE010_SIDECAR_DIAGNOSTIC_HOST_TELEMETRY"
    windows_hardware_events = Read-EventFamily $hardwareProviders $captureStart $captureEnd
}
Write-ExclusiveJson $TelemetryPath $telemetry
