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
