# Checked scalar/vector correspondence and partial numeric join

T044/T048/T049/T053/T057/T060, amendment 0001. **Not native authority.**

The production TLA arithmetic model stores one scalar per shard. Native
arithmetic stores vectors and schema offsets/lengths. Their representations
cannot be identified by selecting the first coordinate or by renaming hashes.
This stage makes that boundary explicit before a complete action/refinement
relation can be claimed.

## Lossless projection

`NativeScalarProjection.lean` loads a layout from the resolved native schema.
It checks positive width, distinct shard names, one coordinate per shard,
offset bounds and exact coverage of every coordinate. Each output cell reads
the native vector at the schema offset; order never substitutes for offset.
Missing coordinates and extra vector elements reject, without truncation or
zero padding. General proofs retain every native coordinate and prove
injectivity: equal projected cells under the same layout imply equal original
vectors. Reordered offsets still read the correct coordinates.

The PARAMETER projection consumes an actual `DerivedParameter`, retaining its
canonical numerator and original denominator/leaf IDs. Its scalar is proved to
equal the checked accumulation of the independently loaded native rows. No
expected scalar is supplied. The APPLY projection consumes an actual
`NativeApply`; both output vectors use the same bound schema. It retains the
native model/optimizer value-hash relationships. Structured model values are
not asserted to be cryptographic hash bytes.

Multi-coordinate native shards deliberately have no projection to this scalar
model. This restriction is a limitation of the model correspondence, **not a
new native arithmetic admission precondition**. It is not installed in the
runtime, and must not be used to reject valid vector work at native admission.
No theorem here equates TLC's finite limit 127 with native INT64/INT128 bounds.

## Numeric part of the public-state relation

`PublicScalarNumbers.lean` uses independently configured shard-name aliases to
compare complete abstract numeric tables with these computed native cells.
Missing or duplicate aliases, missing/extra/duplicate table entries, wrong
number tags, substituted values, wrong model/optimizer kind and wrong schema
symbol reject. The MODEL/OPTIMIZER record has exactly its three fields. Alias
resolution supplies names only, never arithmetic outputs. The enclosing public
observation loader remains responsible for canonical ordering and full preimage
validation; table matching alone is not a byte-decoding proof.

The executable partial join composes `PublicVoteEffects` with the actual
`PublicJournal` native slot checker, independent `NativeReplay` graph/metadata,
frame identity/clock checks, original all-vote sequence and numerical results.
General theorems extract the original native preparation and preserve all 64
public after-state effects. A known-cut execution composes with the existing
reachable journal machine. An unknown append cannot enter this complete-state
API: it remains the previous incomplete-observation/recovery relation, with no
inferred absence or manufactured after-state.

This partial join does **not** check the whole public arithmetic body. It still
needs the complete authority/input/denominator/quantum/parent/QC correspondence,
domain/shard identity, public/native durable-prefix correspondence beyond the
checked count, phase/committee guards, global delivery/QC/current transitions,
root/exporter authentication and the general crash/recovery composition. The
alias and schema symbols are not independently authenticated by this module.
The name `VoteNumbers` intentionally does not assert full vote admission.

## Kernel examples and verification scope

`NativeScalarProjectionVectors` reuses the pinned native fixture: schema load,
both derived PARAMETER scalars (1 and -2, denominator 1), and derived APPLY
model [19,-19]/optimizer [2,-2]. It also checks offset permutation, signed
endpoints, shape/coverage/name failures and unrepresentable vector shards.
The finite codec, synthetic trust and original artifact byte strings remain
exactly the earlier fixture scope, not native C++ execution.

`PublicScalarNumbersExamples` checks small typed tables and three-field records.
Its explicit countercheck demonstrates that correct numerical records can
coexist with a body lacking authority and parent fields. Such a body is **not**
validated by this numeric layer. This guards against accidentally claiming the
remaining full-body obligation has been proved.

The generic native/public join and reachability-composition theorems compile,
but no new full-state/native execution example is claimed at this stage. Draft
combined examples caused excessive definitional reduction and were not retained
as evidence. Existing full-state examples, original sequences 5/6/8 and
native journal fixtures are unchanged. The retained examples are the successful
small component/kernel cases only; no draft timeout is counted as a pass.

All new definitions and theorems are included in the mandatory project's axiom
audit. A complete build is not full formal verification: mandatory coverage
remains 44/45, and `nativeArithmeticRecoveryRefines` is still missing.
No new TLC run, production mutant, authenticated exporter or physical WAL test
is claimed. The native arithmetic guard and frozen demonstrations stay intact.

From `formal/proofs`, reproduce the mandatory project with `lake --no-cache build
DeltaReduce`, then run `lake --no-cache env lean DeltaReduce/AxiomAudit.lean`.
Fresh generic kernel checks use `lake --no-cache env lean
DeltaReduce/NativeScalarProjection.lean` and `lake --no-cache env lean
DeltaReduce/PublicScalarNumbers.lean`. From the repository root, run
`python formal/scripts/check_lean_evidence.py`; its expected current result is
FAIL specifically for the missing recovery conjunct, not a claim of GO.
Tooling/oracle commands and complete outputs are retained under
`formal/proposals/evidence/native-scalar-projection/`.

Next: derive complete public body/authority/parent projections from the bound
native graph and configured identity relation, including the denominator and
quantum inputs. Match the entire prior durable vote set to the reachable native
all-vote journal, rather than only its size. Compose actual phase/send/delivery/
QC/current and crash/unknown transitions. Native adapters, admission completeness,
arbitrary snapshots/availability/failures/repair, contract freeze, clean offline
reproduction and independent review remain required before authority.
