param(
    [switch]$Offline,
    [int]$Port = 0,
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$cacheDir = Join-Path $repoRoot "artifacts/local/mnist-cache"
$outputRoot = Join-Path $repoRoot "artifacts/local/mnist-demo"
$arguments = @(
    "run",
    "--offline",
    "delta-mnist-demo",
    "serve",
    "--cache-dir", $cacheDir,
    "--output-root", $outputRoot,
    "--repository-root", $repoRoot,
    "--port", "$Port"
)
if ($Offline) {
    $arguments += "--offline"
}
if (-not $NoBrowser) {
    $arguments += "--open-browser"
}

Push-Location $repoRoot
try {
    & uv @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "DeltaReduce MNIST demo failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
