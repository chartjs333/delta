# Presentation progress — 2026-09-24

T051 / HR010-001 UI/tooling scope, formal impact NONE. Shared disk profile,
campaign/workload/run handoff, fixed same-origin gateway, linked Presentation
receipt checks, and EN/RU purpose/examples for form fields prepared and tested.
Source/runtime baseline stays c8aea649; no native arithmetic guard changed.
See tools/presentation/ADMIN-UX.md and README.md for architecture and checks.
Installation and browser evidence follow in the presentation-local evidence.

Separate formal candidate advanced to 8380dcf: production VoteParameter current
checkpoint precondition, 22 safety + 7 liveness checks, 18 detected mutants, 72
formal tooling tests, 9 legal + 31 illegal traces. Candidate semantics
sha256:f57b27a2feae0328e1ecf0c8d14b0a041eef260231a26958647af41303caedda,
report SHA-256 00c7bafdcfea3e08c6fec6bae51ae08021cb78b72548de87935e0b46d4a6b1b6,
verifier PASS but decision NO_GO. This bounded stage is self-reviewed and does
not replace missing full binding/proofs/independent attestations/merged authority.
Feature010 qualifying gates, ResultQC and GO checkpoint remain unfulfilled.


Presentation acceptance complete: installed source 91b51eb, 257 UI tests,
16 server tests, EN/RU browser checks, actual run and identical canonical receipt,
profile persistence across server restart. Evidence and limitations are recorded
in specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260924/admin-connected/.
Controller source and instance remain unchanged. Open the shared Admin workspace
at http://127.0.0.1:8870/admin/?lang=en#/campaigns for the morning walkthrough.

SDK / remote access follow-up (T051 / HR010-001): bilingual SDK contracts, complete
executable example and downloadable code; authenticated Cloudflare Quick Tunnel
gateway and START-REMOTE.ps1 with live URL verification, ownership checks and
restart support. Shared Admin links use the public origin, retaining local
legacy redirects. 262 UI tests / 44 files, 26 presentation tests, TypeScript,
offline build/audit passed during development. Live install and real external
browser/restart evidence follow under remote-sdk. Formal impact NONE; baseline
protocol sources unchanged; no qualifying WAN/GO claims.

SDK/remote acceptance recorded under remote-sdk: installed Admin bbd83b0, external
HTTPS execution 934a9d51-e5aa-46da-bbc3-963b9f409914 completed; receipt
ec715072b34d3add3e3cd7c191341e491e70866c40663752a91f7a5b6bf0230d equals local bytes.
Controller instance/source unchanged. Real tunnel restart changes hostname and
repeat start reuses the same PID/instance. D:/delta-presentation/START-REMOTE.ps1
prints current URL/code; start/status/stop are documented in REMOTE-ACCESS.md.
Gateway remains running on loopback 8871. Preserve it for the morning demo;
do not restart it needlessly because that invalidates the shared public URL.
Default host DNS returns NXDOMAIN for some new tunnel names; HTTPS acceptance
with public Cloudflare DNS passes while public browser on host remains explicitly
BLOCKED_HOST_DNS. The launcher reports this without changing Windows DNS/hosts/TLS.
Continue formal work in the separate candidate; this UI access is not Gate D.

Visual guide follow-up (T051 / HR010-001, formal impact NONE): one shared
How it works page links from Presentation and Admin. Seven original PNGs,
EN/RU captions, navigation/keyboard/fullscreen, URL-selected slide, visible
arithmetic corrections on slide 5. Static image allowlists retain fixed paths
and remote authentication. Source and deployment checks are recorded under
presentation-local/20260924/visual-guide; no qualifying claims are added.

Browser login follow-up: user reported ORIGIN_FORBIDDEN on access-code submission.
The no-referrer login policy causes real browser form POSTs to send Origin:null;
reproduced with the same gateway handler in an isolated loopback browser fixture.
The login document now uses same-origin referrer policy. Strict Origin checking,
code comparison, signed cookies and private control fencing remain in place.

Visual guide source 8447294 and login correction 00aa732 are deployed. Seven
public HTTPS PNG hashes match; 266 UI tests/45 files and 29 presentation tests
pass. Real browser EN/RU login/regression checks use an isolated instance of the
production handler; actual public browser remains blocked by this host's DNS.
See presentation-local/20260924/visual-guide for exact acceptance and limitations.

Operational recovery at 23:41Z: a managed execution-session interruption stopped
the local processes. Restored through an independent hidden Windows launcher
(Win32_Process.Create, ShowWindow=0), with data and installed UI retained.
Controller instance is now d7602a7b-f488-47eb-8ef3-220dea499291; source stays
c8aea649 and the previous exact canonical receipt remains available. Do not
restart the currently working gateway needlessly. Use START-REMOTE.ps1 status
for the current URL; old links from earlier in the conversation no longer work.

## 2026-09-24 morning tunnel recovery [T051, HR010-001]
Expired Quick Tunnel hostname replaced after authoritative NXDOMAIN. Public HTTPS login, EN/RU pages, slide bytes and exact persisted receipt verified; Controller instance unchanged. START-REMOTE now supports explicit restart; this branch is parsed/reviewed (live recovery used stop then start). status never silently rotates a URL. Evidence: specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260924/tunnel-recovery/http-acceptance.json. Non-qualifying local presentation only.


## 2026-09-24 node training example [T051, HR010-001]
Integrated the existing worktree-c2 MNIST UI through fixed /node-training/ routes: shared EN/RU navigation, app palette, original report validation, nonce/token and origin boundaries. Source demo worktree changes preserved. Local real run completed with four Python worker processes, 82.05% centralized/distributed accuracy, BYTE-EXACT and RECOVERED_AND_APPLIED. 266 Admin tests, build and boundary audits passed; 32 presentation/gateway tests passed. Original gateway stop test now waits for the asynchronous stopping event. UI/proxy integration only: no protocol changes or qualifying Feature010 claim. Deployment/public acceptance follows in its evidence commit.


Node demo deployed and public smoke PASS (2026-09-24 06:36 UTC). Fixed Cloudflare empty-POST framing with a strictly empty JSON envelope, translated to the original bodyless run command. Actual authenticated HTTPS run, origin/token/argument/concurrency rejection, exact original report equality, EN/RU browser navigation, recovery selector and saved-report restoration verified. Current URL comes from START-REMOTE.ps1 status; code unchanged. Preserve node backend 8872 and D:/delta-data/presentation-20260924/node-training as well as 8870/8865. Launcher start also restores the local host while preserving a working tunnel. Evidence: specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260924/node-training. Formal candidate/native closure remains outstanding; no Feature010 GO claimed.


## 2026-09-24 DNS readiness correction [T051, HR010-001]
At 06:44 UTC the normal resolver and browser returned NXDOMAIN/ERR_NAME_NOT_RESOLVED for the current tunnel. Authoritative Cloudflare DNS and 1.1.1.1/8.8.8.8 returned its A records; HTTPS with normal certificate validation plus explicit resolution passed. Configured resolver negative SOA TTL was approximately 872 seconds; clearing the Windows cache did not clear upstream cache. DO NOT rotate the connected tunnel while this expires. No system DNS/hosts/security settings changed. START-REMOTE now checks public DNS publication first for a new name, prints DNS_PENDING prominently for fallback verification, writes timestamped reachability.json, and never claims browser_verified. Isolated PowerShell cases PASS: unpublished DNS prevents premature system lookup, fallback vs system readiness, TLS failure, and no browser overclaim. Actual normal-browser retest is pending cache expiry, expected around 06:59 UTC.


DNS recovery completed: configured DNS and ordinary HTTPS (no IP override) passed at 06:59:59 UTC, following the observed negative-cache expiry. At approximately 07:00 UTC the exact external node-training URL opened in the actual in-app browser and displayed the English access-code form. Scope is LOGIN_PAGE_ONLY; do not report authenticated browser execution as tested. Same URL, no tunnel rotation, no system DNS/hosts/security reconfiguration. Evidence: specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260924/dns-readiness. The launcher distinguishes DNS_PENDING from SYSTEM_DNS_HTTPS_OK; neither implies browser interaction verification.

