# ISC S16 sequential lane tasks

## Global boundary

- Canonical manifest: `agent/isc-s16-sequential-sprint:orchestration/sprints/isc-s16-sequential/sequential-sprint.json`
- Completed A01: `agent/isc-s16-contract-freeze@a579a5c66586ba3f8f1d7cc26c454aba5addbd8f`
- Source baseline: `ea5a70d8c5fd3516de243632f2c5681b0e5a6292`
- No production integration, sigma assignment, R2.3 or R3.
- Every nonterminal transition is independently reviewed twice.

## ISC-S16-A01-HANDOFF

Create only `orchestration/sprints/isc-s16-sequential/handoffs/ISC-S16-A01.json`.
Verify exact A01 branch/from/final commits, ancestry, diff and evidence. Record
`review_status=PENDING_GRAPH_REVIEW`. Do not modify A01.

## ISC-S16-B01

Quarantined W1 reference codec/storage harness under `formal/reference/isc_w1/**`:
DRW1 kind-3/sections, checked parser, append/barrier/reopen, fault injection,
mixed-WAL/replay tests. No production runtime, quorum, crypto, schemas or formal model.

## ISC-S16-C01

Quarantined canonical-byte/Ed25519 conformance under
`formal/reference/isc_crypto/**`: K/E/R/V/M/G bytes, domains, test vectors, negative
cases and available-library verification. No key custody, consensus invocation or WAL.

## ISC-S16-D01

Limited TLA+/Lean linkage: explicit parent, budgets, conditional liveness, exact
encodings/identities/size equations, V→G physical-slot relation and mutants.
Return GO/NO_GO/STOP. No production code or R2.3/R3.

## ISC-S16-Q01

Join exact accepted commits/outcomes from A/B/C/D and reviewer decisions. Compare
normative bytes, reference vectors, formal statements, ancestry and scope. Produce a
limited-scope source-bound GO/NO_GO report only. No production merge or sigma assignment.
