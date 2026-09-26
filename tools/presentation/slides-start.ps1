[CmdletBinding()]
param([Parameter(Position=0)][ValidateSet('start','status','stop')][string]$Action='start')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Data = 'D:/delta-data/presentation-20260924/slides-tunnel'
$Slides = 'D:/delta-presentation/slides'
$Python = 'D:/delta-main-demo/.venv/Scripts/python.exe'
$Cloudflared = 'C:/Program Files (x86)/cloudflared/cloudflared.exe'
$MetaPath = Join-Path $Data 'process.json'
$ControlPath = Join-Path $Data 'control.json'
$Local = 'http://127.0.0.1:8874'

function Health($Control) {
    if ($null -eq $Control) { return $null }
    try { return Invoke-RestMethod "$Local/_tunnel/health" -Headers @{'X-Delta-Tunnel-Control'=$Control.control} -TimeoutSec 3 }
    catch { return $null }
}
function Publish($H) {
    if ($H.url -cnotmatch '^https://[a-z0-9-]+\.trycloudflare\.com$') { throw 'Invalid public URL.' }
    $PublicHost = ([Uri]$H.url).DnsSafeHost
    $Published = @(Resolve-DnsName $PublicHost -Server 1.1.1.1 -Type A -DnsOnly -QuickTimeout | Where-Object { $_.Type -eq 'A' })
    if ($Published.Count -eq 0) { throw 'Slides public DNS is not ready yet.' }
    $Response = Invoke-WebRequest ($H.url + '/?lang=ru') -TimeoutSec 12
    if ($Response.StatusCode -ne 200 -or $Response.Content -notmatch 'name="code"') { throw 'Public access not verified.' }
    [IO.File]::WriteAllText((Join-Path $Data 'current-url.txt'), $H.url + "`n")
    [IO.File]::WriteAllText('D:/delta-presentation/SLIDES-URL.txt', $H.url + "`n")
    # Existing live panel serves this asset dynamically; no panel restart needed.
    $Origin = $H.url | ConvertTo-Json -Compress
    $Js = @"
(() => {
  const origin = $Origin;
  const nav = document.querySelector('.sidebar nav');
  if (!nav || document.getElementById('slides-ru')) return;
  for (const [lang, label] of [['ru', 'Презентация RU'], ['en', 'Presentation EN']]) {
    const a = document.createElement('a');
    a.id = 'slides-' + lang; a.className = 'nav'; a.href = origin + '/?lang=' + lang;
    a.target = '_blank'; a.rel = 'noopener';
    const icon = document.createElement('span'); icon.textContent = '▣';
    const text = document.createElement('span'); text.className = 'nav-text'; text.textContent = label;
    a.append(icon, text); nav.append(a);
  }
})();
"@
    $Asset = 'D:/delta-main-demo/tools/admin-ui/dist-live/assets/presentation-slides-links.js'
    $Temp = $Asset + '.next'
    [IO.File]::WriteAllText($Temp, $Js, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $Temp -Destination $Asset -Force
    Write-Output "Presentation RU: $($H.url)/?lang=ru"
    Write-Output "Presentation EN: $($H.url)/?lang=en"
    Write-Output 'Use the existing demo access code. Compute services were not restarted.'
}

$Mutex = [Threading.Mutex]::new($false,'Local\DeltaPresentationSlides-8874')
$Held = $false
try {
    try { $Held = $Mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $Held = $true }
    if (-not $Held) { throw 'Another slides launcher is active.' }
    $Control = if (Test-Path $ControlPath) { Get-Content $ControlPath -Raw | ConvertFrom-Json } else { $null }
    $Meta = if (Test-Path $MetaPath) { Get-Content $MetaPath -Raw | ConvertFrom-Json } else { $null }
    $Owned = $null
    if ($null -ne $Meta) {
        $Candidate = Get-Process -Id $Meta.pid -ErrorAction SilentlyContinue
        if ($null -ne $Candidate -and $Candidate.StartTime.ToUniversalTime().Ticks -eq [long]$Meta.start_ticks) { $Owned = $Candidate }
    }
    $H = Health $Control
    if ($null -ne $H -and ($null -eq $Owned -or $H.instance_id -cne $Meta.instance_id -or $H.instance_id -cne $Control.instance_id)) { throw 'Slides ownership mismatch.' }
    if ($Action -eq 'stop') {
        if ($null -ne $H) {
            Invoke-RestMethod "$Local/_tunnel/stop" -Method Post -Body '{}' -ContentType 'application/json' -Headers @{'X-Delta-Tunnel-Control'=$Control.control} | Out-Null
            if (-not $Owned.WaitForExit(20000)) { throw 'Slides graceful stop timed out.' }
        } elseif ($null -ne $Owned) { throw 'Slides process is unresponsive; nothing killed.' }
        Write-Output 'Slides stopped; compute demo remains running.'
        exit 0
    }
    if ($null -ne $H -and $H.status -ceq 'READY') { Publish $H; exit 0 }
    if ($null -ne $Owned) { throw 'Slides still starting or unresponsive; no duplicate started.' }
    if ($Action -eq 'status') { Write-Output 'Slides are stopped.'; exit 1 }
    foreach ($Port in @(8873,8874)) {
        if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { throw "Port $Port is occupied." }
    }
    New-Item -ItemType Directory -Path $Data -Force | Out-Null
    Copy-Item -LiteralPath 'D:/delta-data/presentation-20260924/tunnel/access-code.txt' -Destination (Join-Path $Data 'access-code.txt') -Force
    $Control = @{instance_id=[Guid]::NewGuid().ToString('N');control=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))}
    $Control | ConvertTo-Json | Set-Content -LiteralPath $ControlPath -Encoding utf8
    $Arguments = @((Join-Path $PSScriptRoot 'slides_host.py'),'--slides',$Slides,'--data-dir',$Data,'--cloudflared',$Cloudflared) | ForEach-Object { '"' + $_ + '"' }
    $Process = Start-Process -FilePath $Python -ArgumentList ($Arguments -join ' ') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $Data 'stdout.txt') -RedirectStandardError (Join-Path $Data 'stderr.txt')
    @{pid=$Process.Id;start_ticks=$Process.StartTime.ToUniversalTime().Ticks;instance_id=$Control.instance_id} | ConvertTo-Json | Set-Content -LiteralPath $MetaPath -Encoding utf8
    for ($Try=0; $Try -lt 90; $Try++) {
        if ($Process.HasExited) { throw 'Slides process exited; inspect slides-tunnel/stderr.txt.' }
        $H = Health $Control
        if ($null -ne $H -and $H.status -ceq 'READY') {
            try { Publish $H; exit 0 } catch { if ($Try -gt 75) { throw } }
        }
        Start-Sleep -Seconds 1
    }
    throw 'Slides public URL not ready.'
} finally { if ($Held) { $Mutex.ReleaseMutex() }; $Mutex.Dispose() }
