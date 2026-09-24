# DNS readiness correction [T051, HR010-001]

Before: configured resolver NXDOMAIN and browser ERR_NAME_NOT_RESOLVED, while
authoritative and public resolvers returned A records. Negative SOA TTL counted
down to approximately 06:59:33 UTC. Windows cache flush did not clear the upstream
entry. After expiry, ordinary DNS and HTTPS succeeded at 06:59:59 UTC without
IP overrides. The exact external URL was then opened in the actual in-app browser;
the English access-code form was visible. This is a LOGIN PAGE browser check,
not a claim that an authenticated browser training run was performed.

The tunnel URL was preserved. No system DNS/hosts/security settings were changed.
Launcher status now distinguishes DNS_PENDING from SYSTEM_DNS_HTTPS_OK and never
claims browser verification. New hostnames are checked for public DNS publication
before the system resolver is queried. Isolated PowerShell readiness tests passed.

Explanation: https://developers.cloudflare.com/dns/troubleshooting/dns-issues/#newly-created-record-still-does-not-resolve

Local presentation evidence only; no Feature010 GO or independent attestation.
