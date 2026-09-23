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
