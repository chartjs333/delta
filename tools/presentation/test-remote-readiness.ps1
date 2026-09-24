# Isolated launcher checks. Uses no live tunnel, browser, credentials or network.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Tokens = $null
$ParseErrors = $null
$Ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $PSScriptRoot 'START-REMOTE.ps1'), [ref]$Tokens, [ref]$ParseErrors)
if ($ParseErrors.Count) { throw 'Launcher parse failed.' }
$Function = $Ast.Find({param($Node)
    $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $Node.Name -eq 'Show-Address'
}, $true)
. ([scriptblock]::Create($Function.Extent.Text))

$TestData = Join-Path ([IO.Path]::GetTempPath()) ('delta-dns-test-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $TestData | Out-Null
$UrlPath = Join-Path $TestData 'current-url.txt'
$CodePath = Join-Path $TestData 'access-code.txt'
$ReachabilityPath = Join-Path $TestData 'reachability.json'
[IO.File]::WriteAllText($CodePath, 'test-only-not-a-real-code')
$Health = @{status='READY'; url='https://test-only.trycloudflare.com'; instance_id='test-instance'}
$script:Calls = [Collections.Generic.List[string]]::new()
$script:Scenario = ''
$script:LASTEXITCODE = 0

function Assert-Test($Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Resolve-DnsName {
    param($Name, $Server, $Type, [switch]$DnsOnly, [switch]$QuickTimeout)
    $script:Calls.Add('public-dns')
    Assert-Test ($Server -eq '1.1.1.1') 'Unexpected resolver.'
    if ($script:Scenario -eq 'unpublished') { throw 'Test NXDOMAIN' }
    [pscustomobject]@{Type='A'; IPAddress='192.0.2.1'}
}
function Invoke-WebRequest {
    param($Uri, $TimeoutSec)
    $script:Calls.Add('system-https')
    if ($script:Scenario -in @('pending', 'edge-failed')) { throw 'Test DNS failure' }
    [pscustomobject]@{StatusCode=200; Content='<h1>DeltaReduce</h1><input name="code">'}
}
function curl.exe {
    $script:Calls.Add('resolved-https')
    Assert-Test ($args -contains '--resolve') 'Expected explicit IP for fallback only.'
    Assert-Test (-not ($args -contains '--insecure' -or $args -contains '-k')) 'TLS validation disabled.'
    $script:LASTEXITCODE = if ($script:Scenario -eq 'edge-failed') {22} else {0}
    '<h1>DeltaReduce</h1><input name="code">'
}

try {
    $script:Scenario = 'unpublished'
    $Failed = $false
    try { Show-Address $Health | Out-Null } catch { $Failed = $true }
    Assert-Test $Failed 'Unpublished hostname was accepted.'
    Assert-Test ($script:Calls -notcontains 'system-https') 'System DNS queried before publication.'
    Assert-Test (-not (Test-Path $ReachabilityPath)) 'Success metadata was written for failed readiness.'

    $script:Scenario = 'pending'
    $script:Calls.Clear()
    $Output = Show-Address $Health | Out-String
    $Status = Get-Content $ReachabilityPath -Raw | ConvertFrom-Json
    Assert-Test ($Output.IndexOf('DNS_PENDING') -lt $Output.IndexOf('Presentation EN:')) 'DNS warning is not prominent.'
    Assert-Test ($Status.status -eq 'DNS_PENDING' -and -not $Status.system_dns_https) 'Fallback reported as normal readiness.'
    Assert-Test (-not $Status.browser_verified) 'Launcher claimed a browser test.'
    Assert-Test ($script:Calls[0] -eq 'public-dns') 'Fresh hostname was not checked publicly first.'

    $script:Scenario = 'system-ready'
    $script:Calls.Clear()
    $Output = Show-Address $Health | Out-String
    $Status = Get-Content $ReachabilityPath -Raw | ConvertFrom-Json
    Assert-Test ($Status.status -eq 'SYSTEM_DNS_HTTPS_OK' -and $Status.system_dns_https) 'Normal HTTPS success not recorded.'
    Assert-Test (-not $Status.browser_verified -and -not $Status.public_dns_fallback_used) 'Readiness overclaimed.'
    Assert-Test ($script:Calls.Count -eq 1 -and $script:Calls[0] -eq 'system-https') 'Existing URL was rotated or unnecessarily resolved publicly.'

    $script:Scenario = 'edge-failed'
    $Failed = $false
    try { Show-Address $Health | Out-Null } catch { $Failed = $true }
    Assert-Test $Failed 'Unreachable HTTPS edge was accepted.'
    Write-Output 'PASS: unpublished DNS, DNS_PENDING, normal DNS/HTTPS, failed edge, TLS and browser-claim boundary.'
} finally {
    # Remove only the three files created by this test, then the empty directory.
    foreach ($File in @($CodePath, $UrlPath, $ReachabilityPath)) {
        if (Test-Path -LiteralPath $File) { Remove-Item -LiteralPath $File }
    }
    Remove-Item -LiteralPath $TestData
}
