# ISC S16 continuous lane tasks

## Global boundary

- Preserve all historical objects, signatures, QC, WAL and evidence.
- Reference targets remain quarantined and are not production integration.
- No native guard removal, sigma assignment, R2.3 or R3.
- Every branch includes the sprint directory and reads `continuity-agent.md`.
- Ordinary ambiguities are resolved in-place using the minimal fail-closed rule.
- `NEED_DECISION`/`STOP` is reserved for frozen-authority or cross-owner issues.

## ISC-S16-CONTINUITY

Verify the historical A01 result and handoff, the corrected current sprint checksums,
and the latest project-state transition context. For the initial run create
`handoffs/ISC-S16-CONTINUITY-RECOVERY.json` and choose `START_W1`.

For later runs:

1. identify the exact source node, assignment, branch, from/final commits and feedback;
2. reproduce the blocker from repository evidence;
3. resolve it within delegated authority or define a bounded fail-closed remediation;
4. commit a decision/handoff on the canonical coordinator branch;
5. choose the correct `RESUME_*` outcome.

Do not claim independent review or Formal GO.

## ISC-S16-B01 — W1 reference engine

Implement only an isolated, clearly marked reference W1 codec/file harness and tests.
No production runtime/ABI/Java integration, no quorum/source/signature authority.
Required checks include exact framing, checked lengths, checksum, boundaries,
mixed kinds, replay and fault cuts. `DONE`, `NEED_DECISION`, or `STOP`.

## ISC-S16-C01 — crypto reference

Implement only quarantined canonical K/E/R/V/M/G encoders, exact signable preimage,
detached Ed25519 conformance and public synthetic vectors. No production key custody,
consensus invocation, WAL integration or new trust authority. `DONE`,
`NEED_DECISION`, or `STOP`.

## ISC-S16-D01 — formal linkage

Work only on frozen TLA+/Lean integration points: explicit parent, budgets,
identity separation, V→G, original physical slot and mixed-WAL mapping. No production
code, R2.3/R3 or invariant weakening. Return `GO`, `NO_GO`, `NEED_DECISION`, or `STOP`.

## ISC-S16-Q01 — formal qualification

Join exact accepted commits and review decisions. Re-run source-bound compatibility,
model, proof, mutant and evidence gates for this limited scope. Return `GO` only for
the exact qualified scope. `NO_GO`, `NEED_DECISION`, or `STOP` routes to Coordinator
for remediation rather than terminating the sprint.
