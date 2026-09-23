[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [Parameter(Mandatory = $true)][string]$ManifestCheckout,
    [Parameter(Mandatory = $true)][string]$SourceCheckout,
    [Parameter(Mandatory = $true)][string]$AllocationRoot,
    [Parameter(Mandatory = $true)][string]$AllocationManifestPath,
    [Parameter(Mandatory = $true)][string]$EvidenceParent,
    [Parameter(Mandatory = $true)][string]$LedgerDirectory,
    [Parameter(Mandatory = $true)][string]$HostExchangeDirectory,
    [Parameter(Mandatory = $true)][string]$ContainerSourcePath,
    [Parameter(Mandatory = $true)][string]$ContainerManifestCheckoutPath,
    [Parameter(Mandatory = $true)][string]$CollectorScript,
    [string]$ContainerName = "delta-pr50-sidecar-diagnostic"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Existing([string]$Path, [string]$Kind) {
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    if ($Kind -eq "Directory" -and -not (Test-Path -LiteralPath $resolved -PathType Container)) {
        throw "Expected a directory: $Path"
    }
    if ($Kind -eq "File" -and -not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "Expected a file: $Path"
    }
    return $resolved
}

function Get-PosixParent([string]$Path) {
    $index = $Path.LastIndexOf("/")
    if ($index -le 0) { throw "Expected an absolute non-root POSIX path: $Path" }
    return $Path.Substring(0, $index)
}

function Get-PosixLeaf([string]$Path) {
    $index = $Path.LastIndexOf("/")
    if ($index -lt 0 -or $index -eq $Path.Length - 1) {
        throw "Expected a POSIX path with a final component: $Path"
    }
    return $Path.Substring($index + 1)
}

function Join-Posix([string]$Parent, [string]$Child) {
    return $Parent.TrimEnd("/") + "/" + $Child.TrimStart("/")
}

function Invoke-Docker([string[]]$Arguments, [switch]$AllowFailure) {
    $output = & docker @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "docker $($Arguments -join ' ') failed: $output"
    }
    return [ordered]@{ exit_code = $exitCode; output = ($output -join "`n").Trim() }
}

$manifestHost = Resolve-Existing $ManifestPath "File"
$manifestCheckoutHost = Resolve-Existing $ManifestCheckout "Directory"
$sourceHost = Resolve-Existing $SourceCheckout "Directory"
$allocationHost = Resolve-Existing $AllocationRoot "Directory"
$allocationManifestHost = Resolve-Existing $AllocationManifestPath "File"
$evidenceParentHost = Resolve-Existing $EvidenceParent "Directory"
$ledgerHost = Resolve-Existing $LedgerDirectory "Directory"
$exchangeHost = Resolve-Existing $HostExchangeDirectory "Directory"
$collectorHost = Resolve-Existing $CollectorScript "File"
$manifest = Get-Content -LiteralPath $manifestHost -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.manifest_state -ne "FROZEN_EXECUTABLE") {
    throw "The manifest is not FROZEN_EXECUTABLE"
}

$collectorHash = "sha256:" + (Get-FileHash -LiteralPath $collectorHost -Algorithm SHA256).Hash.ToLowerInvariant()
if ($collectorHash -ne [string]$manifest.environment.host_collector_sha256) {
    throw "Collector hash does not match the frozen manifest"
}
$runtimeVersion = (Invoke-Docker @("version", "--format", "{{.Server.Version}}")).output
if ($runtimeVersion -ne [string]$manifest.environment.container_runtime.version) {
    throw "Docker runtime version does not match the frozen manifest"
}

$campaignId = [string]$manifest.diagnostic_campaign_id
$evidenceLeaf = Get-PosixLeaf ([string]$manifest.evidence_directory)
$evidenceHost = Join-Path $evidenceParentHost $evidenceLeaf
$terminalHost = Join-Path $ledgerHost "$campaignId.terminal.json"
$completedHost = Join-Path $ledgerHost "$campaignId.completed.json"
$failedHost = Join-Path $ledgerHost "$campaignId.failed.json"
$recoverTerminalOnly = (
    (Test-Path -LiteralPath $terminalHost -PathType Leaf) -and
    -not (Test-Path -LiteralPath $completedHost) -and
    -not (Test-Path -LiteralPath $failedHost)
)
if (-not $recoverTerminalOnly) {
    if (Test-Path -LiteralPath $evidenceHost) {
        throw "Evidence directory already exists; the one-shot campaign cannot run: $evidenceHost"
    }
    foreach ($suffix in @("attempt", "started", "terminal", "completed", "failed")) {
        $record = Join-Path $ledgerHost "$campaignId.$suffix.json"
        if (Test-Path -LiteralPath $record) {
            throw "Campaign ledger record already exists; the campaign cannot be retried: $record"
        }
    }
}
$attemptHost = Join-Path $ledgerHost "$campaignId.attempt.json"

$manifestRelative = [IO.Path]::GetRelativePath($manifestCheckoutHost, $manifestHost)
if ($manifestRelative.StartsWith("..")) {
    throw "ManifestPath must be inside ManifestCheckout"
}
$manifestRelative = $manifestRelative.Replace("\", "/")
$containerManifest = Join-Posix $ContainerManifestCheckoutPath $manifestRelative
$containerAllocationRoot = [string]$manifest.environment.allocation_root
$containerAllocationManifest = [string]$manifest.environment.allocation_manifest.path
$containerAllocationManifestParent = Get-PosixParent $containerAllocationManifest
$containerEvidenceParent = Get-PosixParent ([string]$manifest.evidence_directory)
$containerLedger = [string]$manifest.environment.campaign_ledger_directory
$containerExchange = Get-PosixParent ([string]$manifest.environment.host_receipt_path)
if ((Get-PosixParent ([string]$manifest.environment.host_telemetry_path)) -ne $containerExchange) {
    throw "The host receipt and telemetry paths must share one mounted exchange directory"
}
$receiptHost = Join-Path $exchangeHost (Get-PosixLeaf ([string]$manifest.environment.host_receipt_path))
$telemetryHost = Join-Path $exchangeHost (Get-PosixLeaf ([string]$manifest.environment.host_telemetry_path))
$lanesCompleteHost = Join-Path $evidenceHost "lanes-complete.json"
if (-not $recoverTerminalOnly) {
    foreach ($freshPath in @($receiptHost, $telemetryHost, $lanesCompleteHost)) {
        if (Test-Path -LiteralPath $freshPath) {
            throw "Preregistered campaign artifact already exists; no stale receipt may be reset: $freshPath"
        }
    }
}

$allocation = Get-Content -LiteralPath $allocationManifestHost -Raw -Encoding UTF8 | ConvertFrom-Json
$cpuParts = ([string]$allocation.resources.cpu_max).Split(" ")
if ($cpuParts.Length -ne 2 -or $cpuParts[0] -eq "max") {
    throw "The wrapper requires a finite preregistered CPU quota and period"
}
$memory = [string]$allocation.resources.memory_max
if ($memory -eq "max") { throw "The wrapper requires a finite preregistered memory limit" }

$mounts = @(
    "type=bind,src=$sourceHost,dst=$ContainerSourcePath,readonly",
    "type=bind,src=$manifestCheckoutHost,dst=$ContainerManifestCheckoutPath,readonly",
    "type=bind,src=$allocationHost,dst=$containerAllocationRoot,readonly",
    "type=bind,src=$evidenceParentHost,dst=$containerEvidenceParent",
    "type=bind,src=$ledgerHost,dst=$containerLedger",
    "type=bind,src=$exchangeHost,dst=$containerExchange,readonly"
)
if (
    (Split-Path -Parent $allocationManifestHost) -ne $allocationHost -or
    $containerAllocationManifestParent -ne $containerAllocationRoot
) {
    $mounts += "type=bind,src=$(Split-Path -Parent $allocationManifestHost),dst=$containerAllocationManifestParent,readonly"
}
$runArguments = @(
    "run", "--rm", "--detach", "--name", $ContainerName,
    "--network", "none",
    "--cpuset-cpus", [string]$allocation.resources.cpuset_cpus_effective,
    "--cpu-quota", $cpuParts[0],
    "--cpu-period", $cpuParts[1],
    "--memory", $memory
)
foreach ($mount in $mounts) { $runArguments += @("--mount", $mount) }
$runArguments += @([string]$manifest.environment.container_image_digest, "sleep", "infinity")

$started = $false
$armedByThisInvocation = $false
$collectorJob = $null
try {
    Invoke-Docker $runArguments | Out-Null
    $started = $true
    $runnerPath = Join-Posix $ContainerSourcePath "specs/010-wan-benchmark-and-quality/scripts/run_sidecar_diagnostic.py"
    if ($recoverTerminalOnly) {
        $recoveryArguments = @(
            "exec", "--workdir", $ContainerSourcePath, $ContainerName,
            "uv", "run", "python", $runnerPath,
            "--manifest", $containerManifest,
            "--recover-terminal"
        )
        $recovery = Invoke-Docker $recoveryArguments -AllowFailure
        if ($recovery.exit_code -ne 0) {
            throw "Terminal-only recovery failed with exit $($recovery.exit_code): $($recovery.output)"
        }
        $recovery.output
        return
    }
    $preflightReceipt = "/tmp/$campaignId.sidecar-diagnostic-preflight.json"
    $preflightArguments = @(
        "exec", "--workdir", $ContainerSourcePath, $ContainerName,
        "uv", "run", "python", $runnerPath,
        "--manifest", $containerManifest,
        "--manifest-checkout", $ContainerManifestCheckoutPath,
        "--source-checkout", $ContainerSourcePath,
        "--preflight-receipt", $preflightReceipt,
        "--preflight-only"
    )
    $preflight = Invoke-Docker $preflightArguments -AllowFailure
    if ($preflight.exit_code -ne 0) {
        throw "The non-consuming diagnostic preflight failed with exit $($preflight.exit_code): $($preflight.output)"
    }
    $armArguments = @(
        "exec", "--workdir", $ContainerSourcePath, $ContainerName,
        "uv", "run", "python", $runnerPath,
        "--manifest", $containerManifest,
        "--manifest-checkout", $ContainerManifestCheckoutPath,
        "--source-checkout", $ContainerSourcePath,
        "--preflight-receipt", $preflightReceipt,
        "--arm-only"
    )
    $arm = Invoke-Docker $armArguments -AllowFailure
    if ($arm.exit_code -ne 0) {
        throw "The consuming diagnostic arm failed with exit $($arm.exit_code): $($arm.output)"
    }
    $armedByThisInvocation = $true
    if (-not (Test-Path -LiteralPath $attemptHost -PathType Leaf)) {
        throw "The runner reported ready without publishing its durable attempt seal"
    }
    $collectorArguments = @(
        $ContainerName,
        $campaignId,
        [string]$manifest.environment.host_receipt_nonce,
        $collectorHash,
        $attemptHost,
        $receiptHost,
        $lanesCompleteHost,
        $telemetryHost,
        ([int]$manifest.environment.host_telemetry_wait_seconds + 300)
    )
    $collectorJob = Start-Job -FilePath $collectorHost -ArgumentList $collectorArguments
    $receiptDeadline = [DateTime]::UtcNow.AddSeconds(60)
    while (-not (Test-Path -LiteralPath $receiptHost -PathType Leaf)) {
        if ($collectorJob.State -in @("Failed", "Stopped", "Completed")) {
            Receive-Job $collectorJob
            throw "Host collector ended before producing its receipt"
        }
        if ([DateTime]::UtcNow -ge $receiptDeadline) {
            throw "Timed out waiting for the host receipt"
        }
        Start-Sleep -Milliseconds 100
    }
    $execArguments = @(
        "exec", "--workdir", $ContainerSourcePath, $ContainerName,
        "uv", "run", "python", $runnerPath,
        "--manifest", $containerManifest,
        "--manifest-checkout", $ContainerManifestCheckoutPath,
        "--source-checkout", $ContainerSourcePath,
        "--preflight-receipt", $preflightReceipt,
        "--output-directory", [string]$manifest.evidence_directory
    )
    $runner = Invoke-Docker $execArguments -AllowFailure
    if ($runner.exit_code -ne 0) {
        Stop-Job $collectorJob -ErrorAction SilentlyContinue
        Receive-Job $collectorJob -ErrorAction SilentlyContinue
        throw "The diagnostic runner failed with exit $($runner.exit_code): $($runner.output)"
    }
    Wait-Job $collectorJob -Timeout ([int]$manifest.environment.host_telemetry_wait_seconds + 300) | Out-Null
    if ($collectorJob.State -ne "Completed") {
        throw "The host collector did not complete after the lanes-complete handshake"
    }
    Receive-Job $collectorJob
    $runner.output
}
catch {
    $originalError = $_
    if ($armedByThisInvocation -and (Test-Path -LiteralPath $attemptHost -PathType Leaf)) {
        $failureArguments = @(
            "exec", "--workdir", $ContainerSourcePath, $ContainerName,
            "uv", "run", "python", $runnerPath,
            "--manifest", $containerManifest,
            "--manifest-checkout", $ContainerManifestCheckoutPath,
            "--source-checkout", $ContainerSourcePath,
            "--preflight-receipt", $preflightReceipt,
            "--fail-armed",
            "--failure-message", ([string]$originalError.Exception.Message)
        )
        $terminal = Invoke-Docker $failureArguments -AllowFailure
        if ($terminal.exit_code -ne 0) {
            throw "Campaign failed after its durable arm and terminal failure sealing also failed: $($terminal.output). Original failure: $($originalError.Exception.Message)"
        }
    }
    throw $originalError
}
finally {
    if ($null -ne $collectorJob) { Remove-Job $collectorJob -Force -ErrorAction SilentlyContinue }
    if ($started) { Invoke-Docker @("stop", $ContainerName) -AllowFailure | Out-Null }
}
