# Arithmetic binding candidate: no formal authority

These files make amendment `0001-arithmetic-input-binding.md` reviewable through
concrete arithmetic, canonical draft byte graphs and negative design vectors.
They are not a production artifact parser, completed refinement proof, runtime
implementation or new FormalVerificationReport. `DRAFT_NOT_AUTHORITY` and
`formal_go=false` remain explicit in generated evidence.

```text
python -m unittest discover -s formal/proposals -v
python formal/proposals/arithmetic_binding.py
python formal/proposals/check_cross_language.py --help
lean formal/proposals/ArithmeticBinding.lean
```

`arithmetic_binding.py` covers half ties, weighted accumulation, conversion
quantum, checked prefixes, model/optimizer state and domain-separated value bytes.
`native_binding.py` adds an exact content-addressed graph rooted in a separately
supplied native anchor. Its fixture has two domains, two shards, positive/negative
half ties and yields `model=[19,-21]`, `optimizer=[2,0]`.

Draft graph bytes are bounded ASCII canonical JSON with the domain separator
`deltareduce.000.arithmetic-binding.draft1` followed by NUL. Exact type, length,
hash, schema coverage, q-shard commitments, context and result checks are required.
ISC/EC/APC/Aggregate projections assume independently verified certificates.
This assumption is not a signature verifier or a production certificate codec.

The native authority arguments must ultimately be resolved from native durable
state. Passing both a candidate and its claimed authority from one untrusted
command would not establish binding. This proposal does not implement that
resolver, a WAL, a durable receipt or a QC.

The independent C++ arithmetic oracle matched Python on 1,012 cases under GCC
and UBSan. This checks arithmetic rather than complete runtime/canonical graph
conformance. The standalone Lean file has 15 checked helper statements with only
declared standard axioms; it does not discharge the complete binding obligation.

Production TLA+ modules in this candidate now compute bounded PARAMETER/APPLY
results from native input constants instead of expected-result constants. Their
current scope is one coordinate per shard with uniform q/weights. All 20 safety
and 7 liveness configurations and 14 production-source mutants passed, but the
public trace witness, arbitrary-vector proof and lifecycle binding remain open.

Self-review found two material migration issues:

- Per-domain rounding before mixture differs from mixing exact rationals first.
  For `1/2` and `-1/2` with equal weights, the candidate's result is 1 rather than 0.
  The selected operation order requires new formal authority.
- The candidate explicitly selects `FULL_SIGNED_INT64`, including exact
  `INT64_MIN / 1`. The existing native helper rejects that case by bounding an
  unsigned quotient by `INT64_MAX`. This is a migration issue, not permission to
  change runtime under the old report.

The source semantics have changed. The old `cc98f15a...` GO is historical evidence
for its own merged source only; it cannot authorize this candidate. No independent
reviewer attestations were fabricated. See `docs/feature010-progress.md` for the
executed checks and remaining obligations. PR50's PARAMETER/APPLY guard remains
until complete, reviewed and merged new formal authority exists.

## September 24: ordered arithmetic kernel (T044, T048, T049)

`formal/proofs/DeltaReduce/ArithmeticKernel.lean` is now imported by the mandatory
project and registered as PO-A4 with 13 axiom-audited conjuncts. Unlike the earlier
standalone helpers, the checked fold proves acceptance/rejection for arbitrary
ordered lists, products and every prefix, with independent signed intervals.
Quantum conversion checks the specified product order and a separate output
interval. Concrete theorems include INT64_MIN and positive/negative half ties.

The scoped offline runner compiles this exact module using Lean/Std, audits each
theorem, then removes five guards/rounding rules from the same source. Original
proofs reject every mutation; separately compiled concrete witness theorems show
the resulting incorrect acceptance or rounding. Evidence is retained in
`formal/proposals/evidence/arithmetic-kernel.json`.

```powershell
python formal/scripts/check_arithmetic_kernel.py `
  --lean D:/delta/formal/toolchain/windows/lean-4.32.1-windows/bin/lean.exe `
  --archive D:/delta/formal/toolchain/cache/lean-4.32.1-windows.zip `
  --platform windows --output formal/proposals/evidence/arithmetic-kernel.json
```

This is not a successful full Lake/mathlib build. PO-AB1 remains open, including
coefficient derivation and connection from authenticated bytes to this operation
graph. TLA still has its documented uniform-input finite scope. No runtime guard,
native decoder, certificate authority or benchmark qualification changed.


## September 24: heterogeneous finite arithmetic checkpoint (T029, T031, T050)

This supersedes the earlier uniform-input scope above. The production arithmetic
model now takes explicit ordered ticket/domain inputs, rational ticket weights,
per-domain/per-shard quanta, unequal domain mixture weights and distinct parent
model/optimizer coordinates. Four new finite configurations exercise positive
3-of-4 PARAMETER/root/APPLY quorums and replay, product overflow, prefix overflow
hidden by cancellation, and conversion overflow. Their expected results are
literal independent oracles, checked separately by `check_heterogeneous_fixture.py`.
Five additional production mutations detect removing these guards, ignoring
mixture weights and moving rounding across the domain boundary.

Parsing, 26 safety configurations and all 23 production mutants pass. The full
config-to-APPLIED liveness check regressed to a 600-second TLC timeout: this is
an unresolved evaluation/performance failure, not a successful liveness gate.
Six other liveness configurations pass, including the nonzero arithmetic
full chain (42 states). Fairness assumptions were not weakened. The gate now invalidates old logs
before a new batch and preserves failures so stale PASS evidence cannot survive.
The complete Lean project builds, but 4 of 45 mandatory conjuncts (PO-AB1) remain
missing. Formal authority remains NO_GO, with the old frozen baseline unchanged.

This remains one coordinate per shard and a serialized certified Phase6 suffix,
not arbitrary vector/byte decoding, public arithmetic witness refinement,
all interleavings/crash cuts, independent review or benchmark qualification.
Evidence: `formal/proposals/evidence/heterogeneous-arithmetic.json`.


## September 24: liveness evaluation regression resolved (T041, T059)

The earlier 600-second timeout is now closed. `ABApply` binds its computed
integer gradient through the identity `[v \in {g} |-> F(v)][g] = F(g)`.
`ABApplyChecked` binds the sole calculated result before checking every
intermediate. This avoids repeated evaluation during TLC's ENABLED expansion;
the arithmetic formula and all range checks are unchanged. The production
transition relation, fairness expression, temporal properties, configuration
bounds and 600-second limit were not edited.

All seven mandatory liveness configurations and the no-fairness countercheck
pass. `check_arithmetic_evaluation.py --base-source 9a45110 --output <path>`
compares full before/after finite state/transition dumps for both full-chain
profiles, including every state value; the bytes match exactly (42 states each).
That supplementary check removes temporal properties only from its diagnostic
copies and cannot qualify liveness. Mandatory temporal checks run separately
against the unmodified configurations.

The candidate remains NO_GO: PO-AB1, concrete byte/public witness refinement,
frozen contracts, clean offline reproduction and independent reviews remain
open. See `formal/proposals/evidence/liveness-recovery.json` and the progress log.

## September 24: public first-vote arithmetic witnesses (T053-T057)

The public trace schema and checker now require an arithmetic witness for every
accepted PARAMETER/APPLY first vote. A separate native evidence file and its
verifier-supplied SHA256 bind the recovered pre-state, authority graph and exact
command bytes. The existing draft byte oracle recomputes the full candidate.
Twenty-one new negative public traces cover missing/substituted/rehashed data,
current model/optimizer, role, sequence and result changes. A positive trace
executes crash/restart/recovery before arithmetic voting.

The synthetic fixture exporter is isolated from the verifier. Its manifest is
test input, never a native authenticity attestation. Certificate/projection
authentication remains a named external premise. The core arithmetic source is
still a candidate oracle: concrete schema-coordinate mapping, real native state
export, WAL/receipt/retry identity and all crash cuts remain open with PO-AB1.
This checkpoint does not promote the candidate into runtime authority.

Evidence: `formal/proposals/evidence/native-trace-witness.json`. TLA and Lean
sources are byte-identical to the retained liveness checkpoint; this stage runs
the affected public-schema/refinement/tooling checks, not new TLC/Lean executions.

## September 24: concrete coordinate projection (T053-T057)

The public contract now hashes the complete ordered coordinate list and explicit
per-obligation offsets/lengths. Every domain covers the same whole vector exactly
once, and each shard has one shared interval across domains. The checker derives
native SCHEMA bytes from this contract and compares the resolved authority graph's
SCHEMA bytes exactly; it never derives required coordinates from observed votes.

The positive public fixture uses three domains and shards of lengths 2 and 3.
Its five-coordinate expected model and optimizer vectors have a separate literal
arithmetic derivation. Eleven additional negative fixtures include fully rehashed
native graphs with recomputed candidates, aggregates and result hashes. Three
production Python guard-removal counterchecks demonstrate that only the explicit
schema-binding check prevents those self-consistent substitutions.

Validation: 11 legal / 63 illegal traces, 106 tooling tests, 38 oracle tests,
targeted Ruff and byte-exact fixture regeneration pass. Evidence is in
`formal/proposals/evidence/coordinate-binding.json`. This is a bounded flattened
vector projection (up to the existing 4096-item witness bound), not native tensor/
adapter/frozen-base decoding or an unbounded vector proof. TLA/Lean are unchanged
and were not rerun. Full WAL/receipt/retry refinement and all four PO-AB1 proofs
remain open; the candidate report remains NO_GO and no runtime guard changed.

### Draft durable journal/receipt projection

`native_durability_witness.py` checks separately pinned operation observations
against admitted arithmetic commands and the complete per-actor vote prefix.
Identical retries before/after current advance and recovery return exactly the
old diagnostic receipt/effect/sequence. Conflicting canonical requests stutter
without a new record or effect. All accepted vote kinds allocate consecutive
abstract sequences; a repeated envelope cannot consume another sequence.

The receipt/effect ASCII schema is explicitly a draft evidence projection, not
the production WAL or C ABI. Stages are claimed observations, whose native
provenance/authentication must still be established. This checkpoint covers
synthetic complete-journal traces, not torn writes, every crash cut, initial
snapshot import or failed first admission. Public TLA/Lean sources are unchanged.
All four PO-AB1 proofs and Formal GO remain open. Retained checks and limitations:
`formal/proposals/evidence/durable-retry.json`.


### Candidate persistence crash cuts (T015-T018, T042, T050-T052, T057-T061)

`DeltaReducePersistenceHarness.tla` calls the production PARAMETER/APPLY vote,
send, crash, restart and journal-recovery actions. Two registered mandatory
safety configurations explore the same eight cut selections: uninterrupted,
after validation, after append, after durability, after commit, after exposure,
a failed barrier and a corrupt/torn append. Unacknowledged append and failed
barrier each branch into absent and complete surviving records; neither can
expose a result before recovery. A surviving record reuses the original vote
and abstract receipt sequence. Corrupt recovery stays unready. Intentional
DONE/BLOCKED terminal stages explicitly stutter; other deadlocks fail TLC.

The module adds `PersistenceRecordSound` and `PersistenceRecoverySound` to the
existing safety invariants. Every scheduled action has mandatory positive
coverage. Four additional production-source mutations change sequence increment
or omit volatile restoration in `RecoverJournal`, for both arithmetic vote kinds.
`check_persistence_counterchecks.py --output <path>` separately tests early
exposure and corrupt READY promotion by mutating only the candidate harness.
Those supplementary counterchecks are explicitly not production-action mutants.

This is a one-validator, one-fault, one-coordinate/shard, serialized certified
suffix. It retains all existing protocol actions and introduces only internal
stuttering stages. Receipts are tuples, not production bytes. Concurrent current
changes, arbitrary initial journals, physical disk outcomes, native exporter
provenance and concrete trace refinement for these cuts remain obligations.
No fsync, native conformance, liveness or Formal GO is established by this model.
The four PO-AB1 statements still require substantive proofs. Lean sources are
unchanged; the previous proof audit remains scoped evidence, not a new execution.

### Persisted-but-unexposed public witnesses (T053-T057)

Native evidence container 1.2.0 distinguishes an internal durable vote from
exposure of its diagnostic receipt/effect. Eight synthetic legal traces cover
PARAMETER and APPLY cuts at durability, commit, a complete unacknowledged append
and a complete append surviving a failed barrier. All recover the original
journal and replay the original canonical bytes/sequence without another append.
Unacknowledged presence is retrospective: the trace must contain a later verified
recovery. A missing response alone cannot establish presence or absence.

An unexposed record has no signer power in the public quorum projection. Only
validated exact replay can expose the old vote. Nine negative fixtures reject
early output, invalid stage ordering, premature quorum use, replay before crash,
unverified presence, recovery truncation and rewritten replay receipts. Three
Python guard-removal counterchecks demonstrate their respective boundary checks;
they are not additional TLA production mutants or independent reviews.

Evidence: `formal/proposals/evidence/persisted-unexposed.json`. All 28 TLA/Lean
inputs match the prior checkpoint; no new TLC/Lean execution is claimed. The
public-schema semantics ID changes, and the new source-bound report remains
NO_GO. This is a bounded synthetic complete-record projection. Public binding
for absent/torn/unknown outcomes, first-admission rejection without append,
initial snapshots, native exporter provenance, physical WAL/fault execution and
the four PO-AB1 proofs remain open.
