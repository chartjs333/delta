[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "status", "smoke", "stop")]
    [string]$Action = "status",

    [string]$Config,
    [string]$DataDir,
    [switch]$AllowDirty,
    [switch]$SkipInstall,
    [int]$ReadyTimeoutSeconds = 90,
    [int]$ShutdownTimeoutSeconds = 75
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.."))
if ([string]::IsNullOrWhiteSpace($Config)) {
    $Config = Join-Path $RepositoryRoot "configs/working-version/local.json"
}
$ConfigPath = [IO.Path]::GetFullPath($Config)

if ([string]::IsNullOrWhiteSpace($DataDir)) {
    $LocalDataRoot = if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        [IO.Path]::GetTempPath()
    }
    else {
        $env:LOCALAPPDATA
    }
    $DataDir = Join-Path $LocalDataRoot "DeltaReduce/working-version"
}
$ResolvedDataDir = [IO.Path]::GetFullPath($DataDir)

if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "Deployment descriptor does not exist: $ConfigPath"
}

$Descriptor = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
if ($Descriptor.profile -ne "LOCAL_LOOPBACK") {
    throw "delta-local.ps1 starts only the LOCAL_LOOPBACK profile"
}
if ($Descriptor.bindings.host -ne "127.0.0.1") {
    throw "LOCAL_LOOPBACK must bind exactly 127.0.0.1"
}

$BindAddress = [string]$Descriptor.bindings.host
$ServicePort = [int]$Descriptor.bindings.port
$BaseUrl = "http://${BindAddress}:$ServicePort"
$AllowedOrigins = @($Descriptor.bindings.allowed_origins)
if ($AllowedOrigins.Count -ne 1 -or [string]$AllowedOrigins[0] -cne $BaseUrl) {
    throw "Deployment descriptor must allow only its exact local origin $BaseUrl"
}
$MinimumShutdownTimeoutSeconds = (
    [int][Math]::Ceiling([double]$Descriptor.limits.request_timeout_seconds) +
    [int][Math]::Ceiling([double]$Descriptor.limits.shutdown_grace_seconds) +
    10
)
if ($ShutdownTimeoutSeconds -lt $MinimumShutdownTimeoutSeconds) {
    throw (
        "ShutdownTimeoutSeconds must be at least $MinimumShutdownTimeoutSeconds seconds " +
        "for the configured request and Worker drain bounds"
    )
}

$PidPath = Join-Path $ResolvedDataDir "working-version.pid"
$StatePath = Join-Path $ResolvedDataDir "working-version-state.json"
$RuntimePath = Join-Path $ResolvedDataDir "runtime.json"
$StdoutPath = Join-Path $ResolvedDataDir "working-version.stdout.log"
$StderrPath = Join-Path $ResolvedDataDir "working-version.stderr.log"
$AdminUiDirectory = Join-Path $RepositoryRoot "tools/admin-ui"
$LiveUiDirectory = Join-Path $AdminUiDirectory "dist-live"
$SmokeClient = Join-Path $PSScriptRoot "smoke-working-version.py"

function Write-Result([hashtable]$Value) {
    $Value | ConvertTo-Json -Depth 8
}

function Invoke-Checked(
    [string]$Executable,
    [string[]]$ArgumentValues,
    [string]$WorkingDirectory
) {
    Push-Location $WorkingDirectory
    try {
        & $Executable @ArgumentValues
        if ($LASTEXITCODE -ne 0) {
            throw "$Executable exited with code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Get-LauncherState {
    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        return $null
    }
    try {
        return Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Test-CanonicalInstanceId([object]$Value) {
    if ($null -eq $Value) {
        return $false
    }
    $InstanceIdText = [string]$Value
    $ParsedInstanceId = [Guid]::Empty
    return (
        [Guid]::TryParseExact($InstanceIdText, "D", [ref]$ParsedInstanceId) -and
        $ParsedInstanceId.ToString("D") -ceq $InstanceIdText
    )
}

function Get-ProcessStartIdentity([Diagnostics.Process]$Process) {
    try {
        return $Process.StartTime.ToUniversalTime().ToString(
            "O",
            [Globalization.CultureInfo]::InvariantCulture
        )
    }
    catch {
        return $null
    }
}

function Get-NormalizedStartIdentity([object]$Value) {
    if ($null -eq $Value) {
        return $null
    }
    if ($Value -is [DateTime]) {
        return ([DateTime]$Value).ToUniversalTime().ToString(
            "O",
            [Globalization.CultureInfo]::InvariantCulture
        )
    }
    $Parsed = [DateTimeOffset]::MinValue
    if (
        -not [DateTimeOffset]::TryParseExact(
            [string]$Value,
            "O",
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind,
            [ref]$Parsed
        )
    ) {
        return $null
    }
    return $Parsed.UtcDateTime.ToString("O", [Globalization.CultureInfo]::InvariantCulture)
}

function Get-LaunchScopedPathFromState(
    [object]$State,
    [string]$PropertyName,
    [string]$FileNamePrefix,
    [string]$FileNameSuffix
) {
    if ($null -eq $State) {
        return $null
    }
    $InstanceIdProperty = $State.PSObject.Properties["instance_id"]
    if ($null -eq $InstanceIdProperty -or -not (Test-CanonicalInstanceId $InstanceIdProperty.Value)) {
        return $null
    }
    $PathProperty = $State.PSObject.Properties[$PropertyName]
    if ($null -eq $PathProperty -or [string]::IsNullOrWhiteSpace([string]$PathProperty.Value)) {
        return $null
    }
    try {
        $Candidate = [IO.Path]::GetFullPath([string]$PathProperty.Value)
        $Expected = [IO.Path]::GetFullPath(
            (
                Join-Path $ResolvedDataDir (
                    "$FileNamePrefix$([string]$InstanceIdProperty.Value)$FileNameSuffix"
                )
            )
        )
    }
    catch {
        return $null
    }
    $Comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if (-not [string]::Equals($Candidate, $Expected, $Comparison)) {
        return $null
    }
    return $Candidate
}

function Get-ShutdownPathFromState([object]$State) {
    return Get-LaunchScopedPathFromState `
        $State `
        "shutdown_request_path" `
        "shutdown-" `
        ".request"
}

function Get-ServiceRecord {
    $State = Get-LauncherState
    if ($null -eq $State) {
        return $null
    }
    $ProcessIdProperty = $State.PSObject.Properties["process_id"]
    $StartTimeProperty = $State.PSObject.Properties["process_start_time_utc"]
    if ($null -eq $ProcessIdProperty -or $null -eq $StartTimeProperty) {
        return $null
    }
    $ServiceProcessId = 0
    if (
        -not [int]::TryParse([string]$ProcessIdProperty.Value, [ref]$ServiceProcessId) -or
        $ServiceProcessId -lt 1
    ) {
        return $null
    }
    $ServiceProcess = Get-Process -Id $ServiceProcessId -ErrorAction SilentlyContinue
    if ($null -eq $ServiceProcess) {
        return $null
    }
    $ActualStartTime = Get-ProcessStartIdentity $ServiceProcess
    $ExpectedStartTime = Get-NormalizedStartIdentity $StartTimeProperty.Value
    if (
        $null -eq $ActualStartTime -or
        $null -eq $ExpectedStartTime -or
        $ActualStartTime -cne $ExpectedStartTime
    ) {
        return $null
    }
    $ShutdownPath = Get-ShutdownPathFromState $State
    $ExitCodePath = Get-LaunchScopedPathFromState $State "exit_code_path" "exit-" ".code"
    $SupervisorPath = Get-LaunchScopedPathFromState `
        $State `
        "supervisor_script_path" `
        "supervisor-" `
        ".ps1"
    $SupervisorSpecPath = Get-LaunchScopedPathFromState `
        $State `
        "supervisor_spec_path" `
        "supervisor-" `
        ".json"
    if (
        $null -eq $ShutdownPath -or
        $null -eq $ExitCodePath -or
        $null -eq $SupervisorPath -or
        $null -eq $SupervisorSpecPath
    ) {
        return $null
    }
    return [PSCustomObject]@{
        Process = $ServiceProcess
        State = $State
        ShutdownPath = $ShutdownPath
        ExitCodePath = $ExitCodePath
        SupervisorPath = $SupervisorPath
        SupervisorSpecPath = $SupervisorSpecPath
    }
}

function Test-ReadinessDocument(
    [object]$Document,
    [string]$ExpectedBuildId,
    [string]$ExpectedInstanceId
) {
    if (
        $null -eq $Document -or
        $ExpectedBuildId -notmatch "^[0-9a-f]{40}$" -or
        -not (Test-CanonicalInstanceId $ExpectedInstanceId)
    ) {
        return $false
    }
    $ExpectedFields = @{
        status = "READY"
        build_id = $ExpectedBuildId
        protocol_id = [string]$Descriptor.protocol_id
        contract_schema_version = [string]$Descriptor.contract_schema_version
        formal_semantics_id = [string]$Descriptor.formal_semantics_id
        instance_id = $ExpectedInstanceId
    }
    foreach ($FieldName in $ExpectedFields.Keys) {
        $Property = $Document.PSObject.Properties[$FieldName]
        if ($null -eq $Property -or [string]$Property.Value -cne $ExpectedFields[$FieldName]) {
            return $false
        }
    }
    return $true
}

function Get-Readiness([string]$ExpectedBuildId, [string]$ExpectedInstanceId) {
    try {
        $Document = Invoke-RestMethod `
            -Method Get `
            -Uri "$BaseUrl/readyz" `
            -Headers @{ Origin = $BaseUrl; "X-Delta-Request" = "1" } `
            -TimeoutSec 2
        if (Test-ReadinessDocument $Document $ExpectedBuildId $ExpectedInstanceId) {
            return $Document
        }
        return $null
    }
    catch {
        return $null
    }
}

function Test-RuntimeDocument(
    [string]$ExpectedBuildId,
    [string]$ExpectedInstanceId
) {
    if (-not (Test-Path -LiteralPath $RuntimePath -PathType Leaf)) {
        return $false
    }
    try {
        $Document = Get-Content -Raw -LiteralPath $RuntimePath | ConvertFrom-Json
        $ExpectedFields = @{
            schema_version = "1.0.0"
            status = "RUNNING"
            build_id = $ExpectedBuildId
            protocol_id = [string]$Descriptor.protocol_id
            contract_schema_version = [string]$Descriptor.contract_schema_version
            formal_semantics_id = [string]$Descriptor.formal_semantics_id
            instance_id = $ExpectedInstanceId
            base_url = $BaseUrl
        }
        foreach ($FieldName in $ExpectedFields.Keys) {
            $Property = $Document.PSObject.Properties[$FieldName]
            if ($null -eq $Property -or [string]$Property.Value -cne $ExpectedFields[$FieldName]) {
                return $false
            }
        }
        return $true
    }
    catch {
        return $false
    }
}

function Write-LauncherState([hashtable]$Value) {
    $TemporaryStatePath = "$StatePath.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        $Value | ConvertTo-Json | Set-Content -LiteralPath $TemporaryStatePath -Encoding utf8
        Move-Item -LiteralPath $TemporaryStatePath -Destination $StatePath -Force
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryStatePath) {
            Remove-Item -LiteralPath $TemporaryStatePath -Force
        }
    }
}

function Assert-Command([string]$Name) {
    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required executable is not available on PATH: $Name"
    }
}

switch ($Action) {
    "start" {
        Assert-Command "git"
        Assert-Command "uv"
        Assert-Command "npm"
        Assert-Command "pwsh"

        $ExistingRecord = Get-ServiceRecord
        if ($null -ne $ExistingRecord) {
            throw "Working version is already running as PID $($ExistingRecord.Process.Id)"
        }

        Push-Location $RepositoryRoot
        try {
            $BuildId = (& git rev-parse HEAD).Trim()
            if ($LASTEXITCODE -ne 0 -or $BuildId -notmatch "^[0-9a-f]{40}$") {
                throw "Cannot resolve exact Git HEAD"
            }
            $DirtyPaths = @(& git status --porcelain)
            if ($LASTEXITCODE -ne 0) {
                throw "Cannot inspect repository status"
            }
            if (-not $AllowDirty -and $DirtyPaths.Count -gt 0) {
                throw (
                    "Working tree is not clean. Commit/review the release or use -AllowDirty " +
                    "for development-only verification."
                )
            }
        }
        finally {
            Pop-Location
        }

        if (-not $SkipInstall) {
            Invoke-Checked "uv" @("sync", "--frozen") $RepositoryRoot
            Invoke-Checked "npm" @("ci", "--ignore-scripts") $AdminUiDirectory
            Invoke-Checked "npm" @("run", "build:live") $AdminUiDirectory
        }
        if (-not (Test-Path -LiteralPath $LiveUiDirectory -PathType Container)) {
            throw "Live Admin UI artifact is absent: $LiveUiDirectory"
        }

        New-Item -ItemType Directory -Force -Path $ResolvedDataDir | Out-Null
        $DataDirectoryItem = Get-Item -LiteralPath $ResolvedDataDir
        if (($DataDirectoryItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing a reparse-point data directory: $ResolvedDataDir"
        }
        $StaleState = Get-LauncherState
        $StaleShutdownPath = Get-ShutdownPathFromState $StaleState
        $StaleExitCodePath = Get-LaunchScopedPathFromState `
            $StaleState `
            "exit_code_path" `
            "exit-" `
            ".code"
        $StaleSupervisorPath = Get-LaunchScopedPathFromState `
            $StaleState `
            "supervisor_script_path" `
            "supervisor-" `
            ".ps1"
        $StaleSupervisorSpecPath = Get-LaunchScopedPathFromState `
            $StaleState `
            "supervisor_spec_path" `
            "supervisor-" `
            ".json"
        $StalePaths = @($PidPath, $StatePath, $RuntimePath)
        foreach (
            $ScopedStalePath in @(
                $StaleShutdownPath,
                $StaleExitCodePath,
                $StaleSupervisorPath,
                $StaleSupervisorSpecPath
            )
        ) {
            if ($null -ne $ScopedStalePath) {
                $StalePaths += $ScopedStalePath
            }
        }
        foreach ($StalePath in $StalePaths) {
            if (Test-Path -LiteralPath $StalePath) {
                Remove-Item -LiteralPath $StalePath -Force
            }
        }

        $InstanceId = [Guid]::NewGuid().ToString("D")
        $ShutdownPath = Join-Path $ResolvedDataDir "shutdown-$InstanceId.request"
        $ExitCodePath = Join-Path $ResolvedDataDir "exit-$InstanceId.code"
        $SupervisorPath = Join-Path $ResolvedDataDir "supervisor-$InstanceId.ps1"
        $SupervisorSpecPath = Join-Path $ResolvedDataDir "supervisor-$InstanceId.json"
        foreach (
            $NewScopedPath in @(
                $ShutdownPath,
                $ExitCodePath,
                $SupervisorPath,
                $SupervisorSpecPath
            )
        ) {
            if (Test-Path -LiteralPath $NewScopedPath) {
                throw "Launch-scoped path already exists: $NewScopedPath"
            }
        }
        $UvExecutable = (Get-Command "uv").Source
        $HostArguments = @(
            "run",
            "delta-working-version",
            "--config=$ConfigPath",
            "--data-dir=$ResolvedDataDir",
            "--ui-dir=$LiveUiDirectory",
            "--build-id=$BuildId",
            "--instance-id=$InstanceId",
            "--bootstrap-local-identity",
            "--shutdown-file=$ShutdownPath"
        )
        $SupervisorSource = @'
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SpecificationPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$SupervisorExitCode = 1
$Specification = Get-Content -Raw -LiteralPath $SpecificationPath | ConvertFrom-Json
try {
    Push-Location ([string]$Specification.working_directory)
    try {
        & ([string]$Specification.executable) @([string[]]$Specification.arguments)
        $SupervisorExitCode = if ($null -eq $LASTEXITCODE) { 1 } else { [int]$LASTEXITCODE }
    }
    finally {
        Pop-Location
    }
}
catch {
    [Console]::Error.WriteLine("Supervisor failed: $($_.Exception.Message)")
    $SupervisorExitCode = 1
}
finally {
    try {
        $ExitCodePath = [string]$Specification.exit_code_path
        $TemporaryPath = "$ExitCodePath.$([Guid]::NewGuid().ToString('N')).tmp"
        [IO.File]::WriteAllText(
            $TemporaryPath,
            [string]$SupervisorExitCode,
            [Text.UTF8Encoding]::new($false)
        )
        Move-Item -LiteralPath $TemporaryPath -Destination $ExitCodePath -Force
    }
    catch {
        [Console]::Error.WriteLine("Cannot persist supervised exit code: $($_.Exception.Message)")
        $SupervisorExitCode = 1
    }
}
exit $SupervisorExitCode
'@
        Set-Content -LiteralPath $SupervisorPath -Value $SupervisorSource -Encoding utf8
        @{
            schema_version = "1.0.0"
            executable = $UvExecutable
            arguments = $HostArguments
            working_directory = $RepositoryRoot
            exit_code_path = $ExitCodePath
        } | ConvertTo-Json -Depth 4 | Set-Content `
            -LiteralPath $SupervisorSpecPath `
            -Encoding utf8

        $PowerShellExecutable = (Get-Command "pwsh").Source
        $StartParameters = @{
            FilePath = $PowerShellExecutable
            ArgumentList = @(
                "-NoLogo",
                "-NoProfile",
                "-File",
                "`"$SupervisorPath`"",
                "-SpecificationPath",
                "`"$SupervisorSpecPath`""
            )
            WorkingDirectory = $RepositoryRoot
            RedirectStandardOutput = $StdoutPath
            RedirectStandardError = $StderrPath
            PassThru = $true
        }
        if ($IsWindows) {
            $StartParameters.WindowStyle = "Hidden"
        }
        $StartedProcess = $null
        try {
            $StartedProcess = Start-Process @StartParameters
            $StartedProcess.Refresh()
            $ProcessStartTime = Get-ProcessStartIdentity $StartedProcess
            if ($null -eq $ProcessStartTime) {
                throw "Cannot read the exact start time for PID $($StartedProcess.Id)"
            }
            Write-LauncherState @{
                schema_version = "1.0.0"
                process_id = $StartedProcess.Id
                process_start_time_utc = $ProcessStartTime
                instance_id = $InstanceId
                shutdown_request_path = $ShutdownPath
                exit_code_path = $ExitCodePath
                supervisor_script_path = $SupervisorPath
                supervisor_spec_path = $SupervisorSpecPath
                build_id = $BuildId
                base_url = $BaseUrl
                config = $ConfigPath
                data_dir = $ResolvedDataDir
                started_at = [DateTimeOffset]::UtcNow.ToString("O")
            }
            Set-Content -LiteralPath $PidPath -Value $StartedProcess.Id -NoNewline -Encoding utf8

            $ReadyDeadline = [DateTimeOffset]::UtcNow.AddSeconds($ReadyTimeoutSeconds)
            $Readiness = $null
            while ([DateTimeOffset]::UtcNow -lt $ReadyDeadline) {
                $StartedProcess.Refresh()
                if ($StartedProcess.HasExited) {
                    $ErrorTail = if (Test-Path -LiteralPath $StderrPath) {
                        (Get-Content -LiteralPath $StderrPath -Tail 40) -join [Environment]::NewLine
                    }
                    else {
                        "no stderr log"
                    }
                    throw "Working-version host exited before readiness. $ErrorTail"
                }
                $ReadinessCandidate = Get-Readiness $BuildId $InstanceId
                if (
                    $null -ne $ReadinessCandidate -and
                    (Test-RuntimeDocument $BuildId $InstanceId)
                ) {
                    $Readiness = $ReadinessCandidate
                    break
                }
                Start-Sleep -Milliseconds 200
            }
            if ($null -eq $Readiness) {
                throw "Working-version host did not become ready within $ReadyTimeoutSeconds seconds"
            }

            # Bind the readiness response to this exact launcher child.  A
            # foreign listener can imitate the public document, but it cannot
            # make this child retain the recorded PID/start-time identity and
            # publish the matching data-dir runtime document.
            Start-Sleep -Milliseconds 250
            $StartedProcess.Refresh()
            if (
                $StartedProcess.HasExited -or
                (Get-ProcessStartIdentity $StartedProcess) -cne $ProcessStartTime
            ) {
                throw "Working-version host exited after the initial readiness response"
            }
            $ConfirmedReadiness = Get-Readiness $BuildId $InstanceId
            if (
                $null -eq $ConfirmedReadiness -or
                -not (Test-RuntimeDocument $BuildId $InstanceId)
            ) {
                throw "Working-version readiness identity was not stable after startup"
            }
            $StartedProcess.Refresh()
            if (
                $StartedProcess.HasExited -or
                (Get-ProcessStartIdentity $StartedProcess) -cne $ProcessStartTime
            ) {
                throw "Working-version host exited during readiness confirmation"
            }
            $Readiness = $ConfirmedReadiness
        }
        catch {
            $StartFailure = $_
            $RollbackComplete = $null -eq $StartedProcess
            if ($null -ne $StartedProcess) {
                try {
                    @{
                        schema_version = "1.0.0"
                        instance_id = $InstanceId
                        requested_at = [DateTimeOffset]::UtcNow.ToString("O")
                        requested_by = "delta-local.ps1-startup-rollback"
                    } | ConvertTo-Json | Set-Content -LiteralPath $ShutdownPath -Encoding utf8
                    $RollbackDeadline = [DateTimeOffset]::UtcNow.AddSeconds(10)
                    while ([DateTimeOffset]::UtcNow -lt $RollbackDeadline) {
                        $StartedProcess.Refresh()
                        if ($StartedProcess.HasExited) {
                            break
                        }
                        Start-Sleep -Milliseconds 250
                    }
                    $StartedProcess.Refresh()
                    if (-not $StartedProcess.HasExited) {
                        # The supervisor owns uv -> Controller descendants. A
                        # forced kill of only the supervisor can orphan that
                        # process tree while falsely making rollback look
                        # complete. Keep exact lifecycle metadata instead; the
                        # operator can retry the launch-scoped graceful stop.
                        $RollbackComplete = $false
                    }
                    else {
                        $RollbackComplete = $true
                    }
                }
                catch {
                    # Preserve the original startup failure; the exact child PID
                    # remains recorded if rollback itself cannot complete.
                    $RollbackComplete = $false
                }
            }
            if ($RollbackComplete) {
                foreach (
                    $RollbackPath in @(
                        $PidPath,
                        $StatePath,
                        $ShutdownPath,
                        $ExitCodePath,
                        $SupervisorPath,
                        $SupervisorSpecPath,
                        $RuntimePath
                    )
                ) {
                    if (Test-Path -LiteralPath $RollbackPath) {
                        Remove-Item -LiteralPath $RollbackPath -Force
                    }
                }
            }
            throw $StartFailure
        }

        Write-Result @{
            status = "RUNNING"
            process_id = $StartedProcess.Id
            build_id = $BuildId
            instance_id = $InstanceId
            base_url = $BaseUrl
            data_dir = $ResolvedDataDir
            shutdown_request_path = $ShutdownPath
            exit_code_path = $ExitCodePath
            readiness = $Readiness
        }
        break
    }

    "status" {
        $ServiceRecord = Get-ServiceRecord
        if ($null -eq $ServiceRecord) {
            $HasStateMetadata = Test-Path -LiteralPath $StatePath -PathType Leaf
            Write-Result @{
                status = if ($HasStateMetadata) { "STALE_METADATA" } else { "STOPPED" }
                base_url = $BaseUrl
                data_dir = $ResolvedDataDir
                metadata_retained = $HasStateMetadata
            }
            exit 3
        }
        $ServiceProcess = $ServiceRecord.Process
        $State = $ServiceRecord.State
        $Readiness = Get-Readiness ([string]$State.build_id) ([string]$State.instance_id)
        if (-not (Test-RuntimeDocument ([string]$State.build_id) ([string]$State.instance_id))) {
            $Readiness = $null
        }
        Write-Result @{
            status = if ($null -ne $Readiness) { "READY" } else { "RUNNING_NOT_READY" }
            process_id = $ServiceProcess.Id
            instance_id = [string]$State.instance_id
            base_url = $BaseUrl
            data_dir = $ResolvedDataDir
            readiness = $Readiness
        }
        if ($null -eq $Readiness) {
            exit 2
        }
        break
    }

    "smoke" {
        Assert-Command "uv"
        $ServiceRecord = Get-ServiceRecord
        if ($null -eq $ServiceRecord) {
            throw "Working version is not ready; run the start action first"
        }
        $State = $ServiceRecord.State
        if (
            $null -eq (Get-Readiness ([string]$State.build_id) ([string]$State.instance_id)) -or
            -not (Test-RuntimeDocument ([string]$State.build_id) ([string]$State.instance_id))
        ) {
            throw "Working version is not ready; run the start action first"
        }
        Invoke-Checked "uv" @(
            "run",
            "python",
            $SmokeClient,
            "--base-url",
            $BaseUrl,
            "--origin",
            $BaseUrl
        ) $RepositoryRoot
        break
    }

    "stop" {
        $ServiceRecord = Get-ServiceRecord
        if ($null -eq $ServiceRecord) {
            if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
                throw (
                    "Cannot verify the recorded PID/start-time identity; " +
                    "launcher metadata and diagnostics were retained"
                )
            }
            Write-Result @{
                status = "ALREADY_STOPPED"
                base_url = $BaseUrl
                data_dir = $ResolvedDataDir
            }
            break
        }
        $ServiceProcess = $ServiceRecord.Process
        $State = $ServiceRecord.State
        $ShutdownPath = $ServiceRecord.ShutdownPath
        $ExitCodePath = $ServiceRecord.ExitCodePath

        New-Item -ItemType Directory -Force -Path $ResolvedDataDir | Out-Null
        @{
            schema_version = "1.0.0"
            instance_id = [string]$State.instance_id
            requested_at = [DateTimeOffset]::UtcNow.ToString("O")
            requested_by = "delta-local.ps1"
        } | ConvertTo-Json | Set-Content -LiteralPath $ShutdownPath -Encoding utf8

        $ShutdownDeadline = [DateTimeOffset]::UtcNow.AddSeconds($ShutdownTimeoutSeconds)
        while ([DateTimeOffset]::UtcNow -lt $ShutdownDeadline) {
            $ServiceProcess.Refresh()
            if ($ServiceProcess.HasExited) {
                break
            }
            Start-Sleep -Milliseconds 200
        }
        $ServiceProcess.Refresh()
        if (-not $ServiceProcess.HasExited) {
            throw (
                "Working-version host did not stop gracefully within " +
                "$ShutdownTimeoutSeconds seconds; it was not force-killed"
            )
        }
        $ServiceProcess.WaitForExit()
        if (-not (Test-Path -LiteralPath $ExitCodePath -PathType Leaf)) {
            throw (
                "Working-version supervisor did not persist an exit code; " +
                "launcher metadata and diagnostics were retained"
            )
        }
        $ExitCodeText = (Get-Content -Raw -LiteralPath $ExitCodePath).Trim()
        $ExitCode = 0
        if (-not [int]::TryParse($ExitCodeText, [ref]$ExitCode)) {
            throw (
                "Working-version supervisor persisted an invalid exit code; " +
                "launcher metadata and diagnostics were retained"
            )
        }
        if ($ExitCode -ne 0) {
            $ErrorTail = if (Test-Path -LiteralPath $StderrPath) {
                (Get-Content -LiteralPath $StderrPath -Tail 40) -join [Environment]::NewLine
            }
            else {
                "no stderr log"
            }
            throw (
                "Working-version process exited with code $ExitCode; " +
                "launcher metadata and diagnostics were retained. $ErrorTail"
            )
        }
        foreach (
            $StoppedStatePath in @(
                $PidPath,
                $StatePath,
                $ShutdownPath,
                $ExitCodePath,
                $ServiceRecord.SupervisorPath,
                $ServiceRecord.SupervisorSpecPath
            )
        ) {
            if (Test-Path -LiteralPath $StoppedStatePath) {
                Remove-Item -LiteralPath $StoppedStatePath -Force
            }
        }
        Write-Result @{
            status = "STOPPED"
            process_id = $ServiceProcess.Id
            instance_id = [string]$State.instance_id
            exit_code = $ExitCode
            base_url = $BaseUrl
            data_dir = $ResolvedDataDir
            graceful = $true
        }
        break
    }
}
