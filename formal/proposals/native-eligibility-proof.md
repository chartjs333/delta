# Complete native EC membership and original parent edges

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO** remains.
Runtime, native arithmetic guard, demos and closed CONFIG/proposed-ISC
admission/replay modes are unchanged.

NativeEligibility reads the complete original certificate (16 JSON fields) and
proposed body, with all five entry fields. It retains the original context,
ordered entries, ISC/norm/profile IDs, configured quorum and signers. Gamma is
an actual signed int64 numerator transported as uint64 bits, unlike the norm
decimal string. Nonnegative gamma requires the lower half of those bits,
positive u64 denominator and gcd=1. JSON emits the integer's decimal value.
This does not repair or normalize the separate native norm spelling defect.

Certificate membership compares the complete ordered (ticket,domain) list
against the actual checked ISC tuple list. General helpers derive exact count,
positions, original typed source and bounded reencoding. Missing, duplicated or
substituted members cannot pass through count alone. All entry order/label/bounds,
context, parent IDs and configured signer/quorum guards are checked. The reused
ISC signer view supplies only threshold/signers; its dummy body is never admitted
or hashed. Gamma, accepted/reason and robust profile remain primitive: a well-shaped
rejected entry with reason ACCEPTED still passes shape, matching this source layer.

The EC QC ID hashes native canonical JSON. Its seed transcript is not a JSON
field. Proposed-body identity separately hashes context, u64 entry count, one-byte
Boolean, exact integer gamma bits, texts and separate seed-transcript ID using the
native vote-body domain. Policy wire has its own u32 vector counts. These byte
representations and identities are kept distinct.

NativeEligibilityLineage resolves original checked ISC, norm and seed records
by exact IDs, then checks finalized ISC membership, complete EC membership and
the native parent rules. Proposed EC uses the actual configured signer list and
quorum as its synthetic validation certificate, without treating that list as
an observed finalized QC or signature proof. Finalized EC preserves its actual
signer set and separate seed metadata.

Read-only pinned source reveals a deliberate distinction in this model:
the proposed loop requires both norm.isc and seed.isc equal EC.isc; the finalized
loop repeats seed.isc but does not repeat norm.isc equality. The latter norm was
already validated against some finalized ISC in the preceding norm section.
The model preserves these exact guards. A small countercheck shows the guard
difference only; it does NOT demonstrate a complete accepted mixed-parent native
snapshot, conflicting finalization or runtime exploit. Such claims require
checking producers, admission and the rest of the graph.

NativeEligibilitySection actually executes the finalized-ISC/norm section,
checks the whole seed vector, and checks both complete original EC lists plus
strict identity ordering and finalized-QC subset. Induction retains all original
lists and counts. Every admitted edge has actual checked original parent witnesses.
No supplied state equality, whole-body translation or approval table is used.
The section does not validate later APC/parameter/root/apply sections or widen
the existing closed runtime admission/replay modes.

The generator first validates the original pinned native certificate observation
and exact codec-EC/codec-APC policy sections. Original EC JSON, proposed/finalized
wire and voted-body hash match those retained observations. Six finite SHA samples
compose original ISC QC/body, norm, seed transcript, EC QC and EC body. The kernel
examples reuse actual checked original parents. They are component compositions,
not a new whole-policy/native execution or physical recovery run. Separate cases
exercise integer bounds/gcd, Boolean/labels, membership substitutions, quorum,
wrong context, absent finalization and the proposed/finalized parent distinction.
No new TLC or production-mutant suite is claimed.

Remaining: Q/norm/robust-selection derivation, APC accepted-ticket/weights/buckets
and accumulator chain, complete shared admission/replay, authenticated committee/
signatures/finalization/randomness/exporter, general C++ parser/JSON/SHA equivalence
and locale behavior, native decimal compatibility repair, DRS1 decoding/physical
scans/failures, full public64-state/native relation and nativeArithmeticRecoveryRefines.
The initial arbitrary snapshots and failed/unknown outcomes still need substantive
checked relations. Contract freeze, offline reproduction, independent review and
exact merged formal authority remain mandatory. No original or local GO.

Reproduce from repository root:

```text
python -X utf8 formal/scripts/generate_native_eligibility.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_eligibility.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeEligibility.lean
lake --no-cache env lean DeltaReduce/NativeEligibilityLineage.lean
lake --no-cache env lean DeltaReduce/NativeEligibilitySection.lean
lake --no-cache env lean DeltaReduce/NativeEligibilityVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Final source/check hashes and limits: evidence/native-eligibility.json.
