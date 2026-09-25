# Exact actor-prefix checks with an explicit unsupported legacy boundary

T044/T048/T049/T053/T057/T060; candidate amendment 0001. This stage does not
complete nativeArithmeticRecoveryRefines or authorize native arithmetic.

PublicDurablePrefix rederives historical PARAMETER/APPLY bodies from the original
NativeReplay resolver and the complete PublicApplyJoin.SourceBody construction.
It compares the entire typed native envelope, canonical bytes, original context
key, sequence, command, effect and encoded receipt. Actor, kind, public context,
height, epoch and original parent are checked against separately bound metadata.
It does not reapply current-checkpoint freshness to a historical retry. Actual
original admission comes separately from the reachable journal theorem, not from
successful historical body decoding.

The prefix checker compares every original slot with one public vote. It checks
the original per-actor sequence starting at one, exact actor-filtered public-set
permutation, duplicate freedom and tip count. An ordered list is untrusted
matching evidence: all bodies are recomputed and the list must be exactly the
state's local vote set. Public set serialization order is not journal chronology.
General induction proves length, sequence position, both directions of coverage
and original record provenance. The known-cut wrapper first joins the complete
new body/effects, then checks the entire previous prefix, and only then calls
the existing persistence operation. UNKNOWN has no complete-state fallback.
Other actors' journals and arbitrary nonempty initial snapshots are not covered
by this per-actor empty-origin relation.

There is deliberately no accepting non-arithmetic projection branch. The prior
otherAuthorized callback cannot supply a missing canonical body or satisfy this
checker. All original eight-slot normal journals and the four-slot prefix before
the first PARAMETER fail this stronger gate. This is an explicit incomplete
bridge, not a successful full journal/native refinement or a new runtime guard.
The older scoped journal/number/body APIs remain unchanged and must not be
advertised as passing this new complete-prefix API.

The source inventory confirms why a total mapping cannot be inferred from these
legacy fixtures. ISC/EC/APC/ROOT vote body hashes are SHA-256 of the literal
labels normal-isc-body, normal-ec-body, normal-apc-body and normal-root-body.
Their vote envelopes also have empty parent arrays. Finalizer events separately
carry some parent links. The twelve-artifact arithmetic store contains different
minimal ISC_PROJECTION/EC_PROJECTION/APC_PROJECTION/AGGREGATE_PROJECTION objects,
not canonical native certificate bodies for those hashes. Existing native
certificate contracts contain additional context, parent, signer, quorum, root,
availability and other fields. CONFIG has a genuine canonical round-contract
projection preimage, but that is not an independently authenticated full native
RoundConfigQC. The audit distinguishes this case from the four label hashes.

The original arithmetic bodies at sequences 5/6/8 retain real canonical draft
preimages and independent fixture recomputation. No legacy hash, context, byte,
receipt or sequence is rewritten. Changing the non-arithmetic body IDs and
rehashing envelopes would create different receipts/roots, not authenticate the
old history. A new witness version needs actual typed artifact preimages and a
field-level relation to the public bodies, explicit primitive configuration and
certificate provenance, plus a separate registry/source/run identity. Model
labels and fixture membership cannot supply that relation. No cryptographic
collision or production C++ admission defect is inferred from this fixture gap.

The next bridge must also distinguish a voted body from a finalized certificate.
Read-only PR50 source 60c692f6e391f839829dfc64e93380db54cd507b already separates
VoteInputSetBody/vote_input_set_body_id from InputSetCertificate/content_id, and
does the same for eligibility and aggregation plans. A finalized QC's signer
list is not a substitute for the original pre-quorum voted body. Inspect those
exact types/encoders before specifying a new witness; do not add signer fields
or reuse a finalized-QC content ID merely because the legacy hash has no body.

The checked inventory is produced by audit_public_prefix_sources.py only after
independent public/native pins and the complete existing legacy checker pass.
It records all original eight per-actor slots and explicitly returns
MIXED_PREFIX_BODY_PROVENANCE_INCOMPLETE with full_prefix_bridge_pass=false.
This is evidence of scope, not a new gate success or production execution.

Two Lean modules contain sixteen general helpers/eight executable definitions,
nineteen component/composition examples and seven small definitions, all fifty
names axiom-audited. Examples distinguish set order from sequence, reject
same-count substitutions, missing/extra/duplicate votes and wrong tips, and
prove the original mixed prefix remains rejected even with otherAuthorized=true.
They retain original 5/6/8 and reject omitted/renumbered prefixes. The small
positive alignment cases are mathematical records, not authenticated bodies.
There is no new nonempty complete-prefix native execution example.

Configuration/alias authentication, canonical decoder/hash/exporter/WAL,
non-arithmetic body/phase/QC/send/delivery/current, complete recovery and arbitrary
snapshots/failures/repair remain open. Contract freeze, clean offline reproduction
and independent reviews are still required. Formal-first STOP, NO_GO and separate
SIMULATED_LOCAL scope remain unchanged. A missing response never proves absence;
unknown/incomplete/corrupt/ambiguous scans retain their existing fail-closed rules.

Reproduction: lake --no-cache build DeltaReduce; fresh lake --no-cache env lean
for PublicDurablePrefix, PublicDurablePrefixVectors and AxiomAudit; Python unittest
formal/tests and proposals, refinement, scoped Ruff/consistency and source-bound
fixture regeneration. Evidence: formal/proposals/evidence/public-durable-prefix.json.
