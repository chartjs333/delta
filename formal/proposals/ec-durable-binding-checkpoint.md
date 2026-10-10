# EC companion: scope 18 implementation checkpoint

T047/T053 / ISC-S16-D01. 10 October 2026. **R2.3 OPEN; Formal NO_GO.**
Assignment `b04b6d00-763e-4db0-a5c0-5adc39638af1`, formal-linkage role 2753,
branch `agent/isc-s16-formal-linkage`.

The operator's edited decision
`scope-decision-351641e848148e36894d472a92df4424` permits this isolated
formal/reference implementation and qualification. Its explicit delegation
supersedes the original request's specification-only STOP for this class.
The effective scope 18 core and persisted exact ACK are retained in
`evidence/profile-ec-durability/authorization.json`. These are workflow
authorization, never a premise authenticating a protocol snapshot.

The selected contract is the exact copy in `ec-durable-binding-contract.md`,
from commit `6ef27068b88c712245febb5584ebbf7763c3a66e`. Its coordinator result
and both ordinary process reviews were accepted before implementation. Those
reviews were performed by the same sequential executor and are not independent
Formal GO attestations. They did not review this implementation or close R2.3.

## What this closes inside the existing residual

The missing EC storage-association conjunct now has a concrete implementation:
the separate Profile T companion preserves original EC/seed bytes, the exact
original source cut, complete P0/P1/S0, preceding companion bytes and every
original source occurrence. It does not consume a native WAL slot or vote rank.

`ProfileEcDurability.checkStorage` composes the existing native EC computation,
whole original event/input/dependency binding, the complete preceding companion
chain and its retained cut with the exact new frame. `storageAndNativeJoined`
derives these conjuncts; neither successful public projection nor an imported
`durable=true` flag is an input. `chainSound`, `chainComplete`,
`chainNoRecordErasure` and `wholeJournalChecked` cover arbitrary finite journals
in this component's existing bounds, not only the example record.

The reference `bind_profile` resolves the independent bootstrap, retained
pre-event source index and original own companion journal through checked
Profile metadata. It verifies the exact occurrence and predecessor prefix;
it cannot use a later self-referencing index or replace missing history by
an empty journal. The original admitted rows, clock and prerequisite origins
remain inputs to be derived by the complete producing fold. Metadata integrity
does not silently certify those inputs.

The one-transaction crash machine proves that commit and exposure require a
successful barrier after the latest crash. Complete unacknowledged bytes must
be independently reverified and pass a new barrier. Torn/unknown bytes remain
retained and blocked. Native WAL bytes and logical committed/exposed history
remain unchanged by crash/recovery; repeated exposure uses the same original E.
These are statements under the approved Profile T primitive, not production
filesystem code or an independently attested observation of a barrier.
The machine models the companion byte stream. Wiring the barrier to every
required source artifact and its persistent namespace remains part of the
complete source/storage fold; a frame-only run does not establish that join.

## Qualification and precise limits

Run `formal/proposals/b-family-transfer/check_ec_durability.py` with the pinned
Lean and strict Ed25519 backend. Its receipt binds the fresh dependency closure,
all declaration axiom results, exact cross-language encoding/crash cases and
reference regressions. Sources are checked for changes during qualification.
Generated examples are explicitly synthetic, including placeholder initial
metadata in the indexed reference case; they are not lawful full source captures.
Finite SHA256 tables qualify exact preimages, not collision resistance.

This component does **not** close any of the three complete R2.3 obligations:

1. The full source/configuration/aliases/units must be derived from the
   independent genesis and producing prefix. In particular, P0, body/seed/norm,
   admitted inventory, phase/clock and prerequisite positions are not made
   lawful by their inclusion in the EC record.
2. That complete source must yield the complete collections/current/environment
   public family relation, with the existing bounds and all original identities.
3. Initial/incomplete snapshots and sufficient ABORT projection must preserve
   all existing lineage. The one-transaction machine here does not replace the
   existing full-current EC replay or prove arbitrary later ABORT recovery.

This is the same finite residual, not a new proof-layer requirement. The
scope-17 storage-contract STOP is superseded for this delegated component.
Continuing the full origin join found the separate seed-evidence boundary in
`seed-source-boundary.md`; no seed authority/algorithm was selected implicitly.
The named recovery
theorem must follow substantive reviewed R2.3 closure. No full R3, production
integration, concrete semantics ID, legacy migration or guard removal is claimed.
The fresh mandatory recipes pass phase0, contracts, pinned toolchain, TLA
parsing, safety and liveness. Lake builds successfully; the proof evidence gate
fails because `DeltaReduce.nativeArithmeticRecoveryRefines` and its axiom result
are absent. Mutants, refinement and report are not reached after that failed
prerequisite. Exact logs/hashes are in `evidence/profile-ec-durability/mandatory-gates.json`.
The first Windows-default-codepage failure and the unchanged-source UTF-8 retry
are retained separately in that directory. Component success does not upgrade
Formal NO_GO or waive the missing named theorem.
