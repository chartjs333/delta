param(
    [string]$OutputDir = "",
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputDir = Join-Path $repoRoot "artifacts/local/commission-demo/run-$runStamp"
}
elseif (-not [System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputDir = Join-Path $repoRoot $OutputDir
}

Push-Location $repoRoot
try {
    & uv run --offline delta-commission-demo --output-dir $OutputDir
    if ($LASTEXITCODE -ne 0) {
        throw "DeltaReduce commission demo failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

$reportHtml = Join-Path $OutputDir "commission-demo-report.html"
if (-not (Test-Path -LiteralPath $reportHtml -PathType Leaf)) {
    throw "Commission demo report was not created: $reportHtml"
}

Write-Host "DeltaReduce commission demo completed: DEMO_PASS"
Write-Host "Report: $reportHtml"
if (-not $NoBrowser) {
    Start-Process -FilePath $reportHtml
}
