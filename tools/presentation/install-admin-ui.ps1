[CmdletBinding()]
param(
    [string]$ControllerRepo = 'D:\delta-main-demo',
    [string]$DataRoot = 'D:\delta-data\presentation-20260924',
    [string]$PresentationUrl = 'http://127.0.0.1:8870/'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$SourceRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$BuildRoot = Join-Path $SourceRepo 'tools/admin-ui/dist-live'
$TargetRoot = Join-Path ([IO.Path]::GetFullPath($ControllerRepo)) 'tools/admin-ui/dist-live'
$EvidenceRoot = Join-Path ([IO.Path]::GetFullPath($DataRoot)) 'admin-ui'
$ExpectedController = 'c8aea64972f741060d1e527ebbb6f9a5a168a075'
$ControllerCommit = (& git -C $ControllerRepo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $ControllerCommit -cne $ExpectedController) {
    throw 'Controller source is not the reviewed presentation baseline.'
}
$SourceCommit = (& git -C $SourceRepo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot identify Admin UI source.' }
if (@(& git -C $SourceRepo status --porcelain).Count -ne 0) {
    throw 'Commit reviewed source and build it before installing Admin UI.'
}
$PreviousPresentationUrl = $env:VITE_PRESENTATION_URL
try {
    $env:VITE_PRESENTATION_URL = $PresentationUrl
    & npm --prefix (Join-Path $SourceRepo 'tools/admin-ui') run build:live
    if ($LASTEXITCODE -ne 0) { throw 'Admin UI build failed; installed UI is unchanged.' }
    & npm --prefix (Join-Path $SourceRepo 'tools/admin-ui') run audit:live
    if ($LASTEXITCODE -ne 0) { throw 'Admin UI audit failed; installed UI is unchanged.' }
}
finally { $env:VITE_PRESENTATION_URL = $PreviousPresentationUrl }
if (@(& git -C $SourceRepo status --porcelain).Count -ne 0 -or
    (& git -C $SourceRepo rev-parse HEAD).Trim() -cne $SourceCommit) {
    throw 'Source changed while building; installed UI is unchanged.'
}
$Files = @(Get-ChildItem -LiteralPath $BuildRoot -File -Recurse)
$ManifestFiles = foreach ($File in $Files) {
    $Relative = [IO.Path]::GetRelativePath($BuildRoot, $File.FullName).Replace('\', '/')
    if ($Relative -cne 'live.html' -and $Relative -cnotmatch '^assets/[A-Za-z0-9_.-]+\.(js|css)$') {
        throw "Unexpected build file: $Relative"
    }
    if ($File.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Build links are not supported.' }
    @{path = $Relative; sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $TargetRoot 'assets') -Force | Out-Null
$LiveHtml = Join-Path $TargetRoot 'live.html'
if (Test-Path -LiteralPath $LiveHtml) {
    $OldHash = (Get-FileHash -LiteralPath $LiveHtml -Algorithm SHA256).Hash.ToLowerInvariant()
    $Backup = Join-Path $EvidenceRoot "live-$OldHash.html"
    if (-not (Test-Path -LiteralPath $Backup)) { Copy-Item -LiteralPath $LiveHtml -Destination $Backup }
}
# Keep every previous hashed asset so existing open tabs continue to work.
foreach ($Entry in $ManifestFiles | Where-Object { $_.path -cne 'live.html' }) {
    $Destination = Join-Path $TargetRoot $Entry.path
    if (Test-Path -LiteralPath $Destination) {
        if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Entry.sha256) {
            throw "Existing asset has different bytes: $($Entry.path)"
        }
    }
    else { Copy-Item -LiteralPath (Join-Path $BuildRoot $Entry.path) -Destination $Destination }
}
$TemporaryHtml = Join-Path $TargetRoot ("live-" + [Guid]::NewGuid().ToString('N') + '.next.html')
Copy-Item -LiteralPath (Join-Path $BuildRoot 'live.html') -Destination $TemporaryHtml
Move-Item -LiteralPath $TemporaryHtml -Destination $LiveHtml -Force
foreach ($Entry in $ManifestFiles) {
    if ((Get-FileHash -LiteralPath (Join-Path $TargetRoot $Entry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Entry.sha256) {
        throw "Installed bytes differ: $($Entry.path)"
    }
}
$Manifest = @{schema_version = '1.0.0'; mode = 'PRESENTATION_UI_ONLY';
    controller_source_commit = $ControllerCommit; admin_ui_source_commit = $SourceCommit;
    files = $ManifestFiles; installed_at = [DateTime]::UtcNow.ToString('o');
    protocol_semantics_changed = $false; qualifying_evidence = $false}
$Manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $EvidenceRoot 'installed.json') -Encoding utf8
Write-Output 'Admin UI installed. Refresh the browser; Controller was not restarted.'
