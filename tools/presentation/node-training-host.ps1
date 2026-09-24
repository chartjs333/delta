param([string]$Source, [string]$Data, [string]$Instance)
$ErrorActionPreference = 'Stop'
& {
    try {
        # Reuse the demo's locked toolchain preparation and its environment bindings.
        & (Join-Path $Source 'tools/run-mnist-demo.ps1') -PrepareOnly -Offline
        & (Join-Path $Source '.venv/Scripts/python.exe') -u (Join-Path $PSScriptRoot 'node_training_host.py') `
            --source $Source --data $Data --instance $Instance
        if ($LASTEXITCODE -ne 0) { throw "Node training host exited: $LASTEXITCODE" }
    } catch { Write-Error $_; exit 1 }
} *> (Join-Path $Data 'host.log')
