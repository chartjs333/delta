param(
    [string]$BaseUrl = "http://localhost:8025",
    [string]$ProjectPhone = "9008",
    [string]$RepositoryUrl = "https://github.com/chartjs333/delta.git",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sprintPath = Join-Path $scriptDir "sequential-sprint.json"

if (-not (Test-Path -LiteralPath $sprintPath)) {
    throw "Sprint JSON not found: $sprintPath"
}

# Refuse to replace a live assignment unless the operator explicitly requests it.
try {
    $state = Invoke-RestMethod `
        -Method Get `
        -Uri "$BaseUrl/api/v1/projects/$ProjectPhone/state.json"
    $execution = $state.execution
    if (
        -not $Force `
        -and $null -ne $execution `
        -and $execution.status -eq "active" `
        -and -not [string]::IsNullOrWhiteSpace([string]$execution.current_assignment_id)
    ) {
        throw (
            "Project $ProjectPhone has an active assignment " +
            "$($execution.current_assignment_id). Complete it or rerun with -Force."
        )
    }
}
catch {
    if ($_.Exception.Message -like "Project * has an active assignment *") {
        throw
    }
    Write-Host "State preflight unavailable; continuing with import: $($_.Exception.Message)"
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$sprintJson = Get-Content -LiteralPath $sprintPath -Raw -Encoding UTF8
$sprintBytes = $utf8NoBom.GetBytes($sprintJson)

Write-Host "Importing sequential sprint for project $ProjectPhone..."
$importResponse = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/v1/projects/$ProjectPhone/agents/import" `
    -ContentType "application/json; charset=utf-8" `
    -Body $sprintBytes

Write-Host "Sprint imported. Requesting current sequential identity..."
$identity = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/v1/agents/whoami"

if (
    $null -ne $identity.reply_url `
    -and -not [string]::IsNullOrWhiteSpace([string]$identity.reply_url)
) {
    $repoBody = @{
        git_address = $RepositoryUrl
    } | ConvertTo-Json -Compress
    $repoBytes = $utf8NoBom.GetBytes($repoBody)

    $identity = Invoke-RestMethod `
        -Method Post `
        -Uri ([string]$identity.reply_url) `
        -ContentType "application/json; charset=utf-8" `
        -Body $repoBytes
}

Write-Host "Current assignment:"
$identity | ConvertTo-Json -Depth 100
