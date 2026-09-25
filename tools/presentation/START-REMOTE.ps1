[CmdletBinding()]
param(
    [Parameter(Position = 0)][ValidateSet('start', 'status', 'stop', 'restart')][string]$Action = 'start',
    [string]$DataRoot = 'D:\delta-data\presentation-20260924',
    [string]$ControllerRepo = 'D:\delta-main-demo',
    [string]$Cloudflared = 'C:\Program Files (x86)\cloudflared\cloudflared.exe',
    [int]$Port = 8871,
    [int]$PresentationPort = 8870
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RemoteData = Join-Path ([IO.Path]::GetFullPath($DataRoot)) 'tunnel'
$MetadataPath = Join-Path $RemoteData 'process.json'
$ControlPath = Join-Path $RemoteData 'control.json'
$CodePath = Join-Path $RemoteData 'access-code.txt'
$UrlPath = Join-Path $RemoteData 'current-url.txt'
$ReachabilityPath = Join-Path $RemoteData 'reachability.json'
$LocalUrl = "http://127.0.0.1:$Port"
$Python = Join-Path $ControllerRepo '.venv/Scripts/python.exe'

function Read-Saved([string]$Path) {
    if (Test-Path -LiteralPath $Path) { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
    return $null
}
function Read-Health($Control) {
    if ($null -eq $Control) { return $null }
    try {
        return Invoke-RestMethod "$LocalUrl/_tunnel/health" -Headers @{'X-Delta-Tunnel-Control' = $Control.control} -TimeoutSec 3
    } catch { return $null }
}
function Owned-Process($Metadata) {
    if ($null -eq $Metadata) { return $null }
    $Candidate = Get-Process -Id $Metadata.pid -ErrorAction SilentlyContinue
    if ($null -eq $Candidate) { return $null }
    if ($Candidate.StartTime.ToUniversalTime().Ticks -ne [long]$Metadata.start_ticks) {
        # Stale metadata after reboot/PID reuse is not ownership of the new process.
        # The caller still checks the authenticated listener and port before starting.
        return $null
    }
    return $Candidate
}
function Assert-Identity($Health, $Metadata, $Control) {
    if ($null -eq $Health -or $null -eq $Metadata -or $null -eq $Control -or
        $Health.service -cne 'delta-remote-gateway' -or $Health.instance_id -cne $Control.instance_id -or
        $Metadata.instance_id -cne $Control.instance_id -or
        $Metadata.local_url -cne $LocalUrl -or $null -eq (Owned-Process $Metadata)) {
        throw 'Tunnel process ownership could not be verified.'
    }
    # A Windows venv Python launcher remains the parent of the actual interpreter.
    if ($Health.pid -ne $Metadata.pid) {
        $Interpreter = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$Health.pid)"
        if ($null -eq $Interpreter -or $Interpreter.ParentProcessId -ne $Metadata.pid) {
            throw 'Gateway interpreter is not the child of the owned Python launcher.'
        }
    }
}
function Show-Address($Health) {
    if ($Health.status -cne 'READY' -or $Health.url -cnotmatch '^https://[a-z0-9]+(-[a-z0-9]+)*\.trycloudflare\.com$') {
        throw 'Tunnel is not connected yet. No old URL will be displayed.'
    }
    # Verify the public edge, not just a line in cloudflared's startup log.
    # On a newly allocated hostname, first let public DNS see the record. An
    # immediate system-resolver lookup can cache NXDOMAIN upstream for 30 minutes.
    $PublicHost = ([Uri]$Health.url).DnsSafeHost
    $PreviousUrl = if (Test-Path -LiteralPath $UrlPath) {
        (Get-Content -LiteralPath $UrlPath -Raw).Trim()
    } else { '' }
    if (-not $PreviousUrl.StartsWith($Health.url + '/', [StringComparison]::Ordinal)) {
        $Published = @(Resolve-DnsName $PublicHost -Server 1.1.1.1 -Type A -DnsOnly -QuickTimeout |
            Where-Object { $_.Type -eq 'A' })
        if ($Published.Count -eq 0) { throw 'Public DNS has not published the new hostname yet.' }
    }
    $PublicDnsFallback = $false
    try {
        $Page = Invoke-WebRequest "$($Health.url)/_access/login?lang=en" -TimeoutSec 10
        if ($Page.StatusCode -ne 200) { throw 'Public login is unavailable.' }
        $PageText = $Page.Content
    } catch {
        # Some ISP resolvers retain NXDOMAIN for a newly allocated Quick Tunnel.
        # Resolve this one hostname via Cloudflare DNS and verify normal HTTPS
        # with the same hostname/SNI/certificate. Never disable TLS checks or
        # change the computer's DNS settings/hosts file.
        $Addresses = @(Resolve-DnsName $PublicHost -Server 1.1.1.1 -Type A -DnsOnly -QuickTimeout |
            Where-Object { $_.Type -eq 'A' } | Select-Object -ExpandProperty IPAddress)
        if ($Addresses.Count -eq 0) { throw 'The new public hostname is not resolvable yet. Run status shortly.' }
        $Resolved = $PublicHost + ':443:' + $Addresses[0]
        $PageText = (& curl.exe --fail --silent --show-error --connect-timeout 5 --max-time 15 `
            --resolve $Resolved "$($Health.url)/_access/login?lang=en") -join "`n"
        if ($LASTEXITCODE -ne 0) { throw 'The public HTTPS login is not reachable yet. Inspect cloudflared.log.' }
        $PublicDnsFallback = $true
    }
    if (-not $PageText.Contains('DeltaReduce') -or
        -not $PageText.Contains('name="code"')) { throw 'Public login page did not pass verification.' }
    [IO.File]::WriteAllText($UrlPath, "$($Health.url)/?lang=en" + [Environment]::NewLine)
    $Reachability = @{
        checked_at = [DateTime]::UtcNow.ToString('o')
        instance_id = $Health.instance_id
        public_url = $Health.url
        status = $(if ($PublicDnsFallback) { 'DNS_PENDING' } else { 'SYSTEM_DNS_HTTPS_OK' })
        system_dns_https = -not $PublicDnsFallback
        public_dns_fallback_used = $PublicDnsFallback
        tls_certificate_validation = $true
        browser_verified = $false
    }
    $Reachability | ConvertTo-Json | Set-Content -LiteralPath $ReachabilityPath -Encoding utf8
    Write-Output ''
    if ($PublicDnsFallback) {
        Write-Output 'DNS_PENDING: this host cannot open the URL using its normal resolver.'
        Write-Output 'DNS_PENDING: браузер на этом компьютере может не открыть ссылку. Проверка HTTPS через публичный DNS прошла, но обычный DNS сети ещё не работает.'
        Write-Output 'Keep this tunnel running and retry status after the network DNS cache expires. Restarting creates a new hostname and can prolong the wait.'
    } else {
        Write-Output 'SYSTEM_DNS_HTTPS_OK: ordinary HTTPS works on this host; browser interaction is not tested by this script.'
        Write-Output 'Обычный HTTPS работает на этом компьютере. Скрипт не проверяет вход и действия в браузере.'
    }
    Write-Output "Presentation EN: $($Health.url)/?lang=en"
    Write-Output "Presentation RU: $($Health.url)/?lang=ru"
    Write-Output "Verification EN: $($Health.url)/verification/?lang=en"
    Write-Output "Verification RU: $($Health.url)/verification/?lang=ru"
    Write-Output "Admin UI EN:     $($Health.url)/admin/?lang=en#/live-execution"
    Write-Output "Admin UI RU:     $($Health.url)/admin/?lang=ru#/live-execution"
    Write-Output "SDK:             $($Health.url)/admin/?lang=en#/sdk"
    Write-Output "Node training EN: $($Health.url)/node-training/?lang=en"
    Write-Output "Node training RU: $($Health.url)/node-training/?lang=ru"
    Write-Output "Visual guide EN: $($Health.url)/admin/?lang=en#/guide"
    Write-Output "Visual guide RU: $($Health.url)/admin/?lang=ru#/guide"
    Write-Output "Access code:     $((Get-Content -LiteralPath $CodePath -Raw).Trim())"
    Write-Output "Current URL file: $UrlPath"
    Write-Output "Reachability:     $ReachabilityPath"
    Write-Output 'Keep this host powered on and connected. Share the URL and code only with your audience.'
    Write-Output 'After a reboot, run START-REMOTE.ps1 again to obtain the new URL.'
    if ($PublicDnsFallback) {
        Write-Output 'DNS note: no system DNS or hosts changes were made; check access from the presentation computer before the show.'
    }
}
function Protect-Directory {
    New-Item -ItemType Directory -Path $RemoteData -Force | Out-Null
    # Build only a DACL, without copying owner/SACL fields from Get-Acl.
    # This also works on repeat starts without SeSecurityPrivilege elevation.
    $Acl = [Security.AccessControl.DirectorySecurity]::new()
    $Acl.SetAccessRuleProtection($true, $false)
    foreach ($Sid in @([Security.Principal.WindowsIdentity]::GetCurrent().User,
            [Security.Principal.SecurityIdentifier]::new('S-1-5-18'),
            [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) {
        $Rule = [Security.AccessControl.FileSystemAccessRule]::new($Sid, 'FullControl',
            'ContainerInherit,ObjectInherit', 'None', 'Allow')
        $Acl.AddAccessRule($Rule)
    }
    [IO.FileSystemAclExtensions]::SetAccessControl([IO.DirectoryInfo]::new($RemoteData), $Acl)
}

$Mutex = [Threading.Mutex]::new($false, "Local\DeltaPresentationQuickTunnel-$Port")
$Held = $false
try {
    try { $Held = $Mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $Held = $true }
    if (-not $Held) { throw 'Another tunnel launcher is running. Wait for it to finish.' }
    $Metadata = Read-Saved $MetadataPath
    $Control = Read-Saved $ControlPath
    $Health = Read-Health $Control
    $Owned = Owned-Process $Metadata
    if ($Action -in @('stop', 'restart')) {
        if ($null -ne $Health) {
            Assert-Identity $Health $Metadata $Control
            Invoke-RestMethod "$LocalUrl/_tunnel/stop" -Method Post -Body '{}' -ContentType 'application/json' `
                -Headers @{'X-Delta-Tunnel-Control' = $Control.control} -TimeoutSec 5 | Out-Null
            if (-not $Owned.WaitForExit(20000)) { throw 'Graceful tunnel stop timed out. Inspect gateway.stderr.txt.' }
        } elseif ($null -ne $Owned) { throw 'Owned gateway is unresponsive. Nothing was killed.' }
        if (Test-Path -LiteralPath $UrlPath) { [IO.File]::WriteAllText($UrlPath, 'STOPPED - run START-REMOTE.ps1 to obtain a new URL.') }
        Write-Output 'Remote access stopped. Local Presentation and Controller remain running.'
        if ($Action -eq 'stop') { exit 0 }
        # Continue under the same launcher mutex. Only the verified gateway was
        # stopped; startup below reuses the existing local application and code.
        $Metadata = $null
        $Control = $null
        $Health = $null
        $Owned = $null
    }
    if ($null -ne $Health) {
        Assert-Identity $Health $Metadata $Control
        if ($Action -eq 'start') {
            & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'presentation-start.ps1') start `
                -DataRoot $DataRoot -ControllerRepo $ControllerRepo -Port $PresentationPort
            if ($LASTEXITCODE -ne 0) { throw 'Local application recovery failed; tunnel URL was not rotated.' }
        }
        try { Show-Address $Health }
        catch {
            [IO.File]::WriteAllText($UrlPath, 'UNVERIFIED - public access failed; run START-REMOTE.ps1 status or restart.')
            throw "Public access could not be verified. Check the connection; if the Quick Tunnel address has expired, run START-REMOTE.ps1 restart to obtain a new URL. / Адрес не подтверждён: проверьте сеть; для нового адреса выполните START-REMOTE.ps1 restart. Details: $($_.Exception.Message)"
        }
        exit 0
    }
    if ($null -ne $Owned) { throw 'Gateway is starting or unresponsive. Inspect gateway.stderr.txt; no duplicate was started.' }
    if (Test-Path -LiteralPath $UrlPath) { [IO.File]::WriteAllText($UrlPath, 'NOT CONNECTED - no current verified URL.') }
    if ($Action -eq 'status') { Write-Output 'Tunnel: STOPPED. Run START-REMOTE.ps1 start.'; exit 1 }
    if (-not (Test-Path -LiteralPath $Cloudflared)) {
        $Found = Get-Command cloudflared -ErrorAction SilentlyContinue
        if ($null -eq $Found) { throw 'cloudflared is missing. Install Cloudflare cloudflared and run again.' }
        $Cloudflared = $Found.Source
    }
    foreach ($ConfigName in @('config.yml', 'config.yaml')) {
        if (Test-Path -LiteralPath (Join-Path $env:USERPROFILE ".cloudflared/$ConfigName")) {
            throw 'An existing cloudflared config may disable Quick Tunnels. Use a separate prepared account or temporarily move that config yourself.'
        }
    }
    $Probe = [Net.Sockets.TcpClient]::new()
    try {
        try { $Probe.Connect('127.0.0.1', $Port) } catch [Net.Sockets.SocketException] { }
        if ($Probe.Connected) { throw "Port $Port is occupied by an unverified service; nothing was stopped." }
    } finally { $Probe.Dispose() }
    & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'presentation-start.ps1') start `
        -DataRoot $DataRoot -ControllerRepo $ControllerRepo -Port $PresentationPort
    if ($LASTEXITCODE -ne 0) { throw 'Local application startup failed; tunnel was not started.' }
    Protect-Directory
    if (-not (Test-Path -LiteralPath $CodePath)) {
        $Bytes = [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
        [IO.File]::WriteAllText($CodePath, [Convert]::ToHexString($Bytes).ToLowerInvariant())
    }
    $Control = @{instance_id = [Guid]::NewGuid().ToString('N');
        control = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))}
    $Control | ConvertTo-Json | Set-Content -LiteralPath $ControlPath -Encoding utf8
    $Arguments = @((Join-Path $PSScriptRoot 'tunnel_gateway.py'), '--data-dir', $RemoteData,
        '--cloudflared', $Cloudflared, '--port', [string]$Port, '--upstream', [string]$PresentationPort)
    $Quoted = $Arguments | ForEach-Object {
        if ($_.Contains('"')) { throw 'Embedded quotes in paths are not supported.' }
        '"' + $_ + '"'
    }
    $Process = Start-Process -FilePath $Python -ArgumentList ($Quoted -join ' ') -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $RemoteData 'gateway.stdout.txt') `
        -RedirectStandardError (Join-Path $RemoteData 'gateway.stderr.txt')
    $Metadata = @{pid = $Process.Id; start_ticks = $Process.StartTime.ToUniversalTime().Ticks;
        instance_id = $Control.instance_id; local_url = $LocalUrl}
    $Metadata | ConvertTo-Json | Set-Content -LiteralPath $MetadataPath -Encoding utf8
    Write-Output 'Connecting to Cloudflare; waiting for the current public URL...'
    for ($Attempt = 0; $Attempt -lt 90; $Attempt++) {
        if ($Process.HasExited) { throw "Tunnel exited. Inspect $RemoteData/gateway.stderr.txt and cloudflared.log." }
        $Health = Read-Health $Control
        if ($null -ne $Health -and $Health.status -ceq 'READY') {
            Assert-Identity $Health $Metadata $Control
            try { Show-Address $Health; exit 0 } catch {
                if ($Attempt -gt 75) { throw }
            }
        }
        Start-Sleep -Seconds 1
    }
    throw "Tunnel did not become reachable. Inspect $RemoteData/cloudflared.log; then use status or stop."
} finally {
    if ($Held) { $Mutex.ReleaseMutex() }
    $Mutex.Dispose()
}
