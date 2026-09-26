# Complete native APC coverage and original parent section

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO** remains.
Runtime, native arithmetic guard, demos and closed CONFIG/proposed-ISC
admission/replay modes are unchanged.

NativePlan represents every original APC field and both complete ordered arrays.
Its canonical JSON has 20 fields. Bucket assignments retain bucket/ticket; weights
retain the signed-int64 numerator transported as uint64 bits, positive u64
denominator and ticket. Nonnegative reduced alpha is checked, including zero's
unique denominator. Both arrays must be nonempty, bounded and strictly ticket
ordered. Iterations are positive uint32. Exact context, primitive content IDs,
configured quorum and signer membership are checked. The reused signer predicate
does not admit or hash its dummy ISC body.

The native body hash is separate from certificate JSON and policy wire: body
iteration count is u64, whereas the policy codec field is uint32. Body counts and
texts use the native u64 format; policy vectors use u32 counts. Neither source
bytes nor identities are silently interchanged. Proposed validation injects the
configured all-validator signer list solely as the original synthetic certificate
view; finalized certificates retain their actual original signers.

Coverage filters the original EC entries in order by accepted, then compares
the complete list with sorted assignment tickets and original weight tickets.
General proofs derive exact positions and counts; the checked nonempty guard
makes all-rejected EC coverage impossible. Sorting the assignments in the coverage
helper does not allow reversed source assignments: the independent original order
guard rejects them. The model uses byte lexicographic insertion sort in this helper;
general C++ library/locale/JSON equivalence is not established by examples.

NativePlanLineage resolves actual ISC, EC and seed records by their exact IDs,
checks ISC/EC finalized membership, the EC's separate seed-transcript identity,
the configured required accumulator and whole accepted-ticket coverage. Original
typed trees and bounded reencoding are retained. NativePlanSection actually runs
the preceding EC/ISC/norm/seed section, both complete original APC lists, strict
computed body/QC identity ordering and the finalized-APC subset. The accumulator
syntax check is conditional on at least one nonempty plan list, as in the source.
General helpers derive original lists/counts and executable parent witnesses.

Read-only source60c692f6e391f839829dfc64e93380db54cd507b does not explicitly repeat
EC.isc=plan.isc or seed.isc=plan.isc in its APC verifier. The EC section separately
checks EC/seed lineage. This model preserves the observed guards. An isolated
countercheck substitutes a caller-provided ISC checked record and demonstrates
that this predicate alone does not demand cross-ISC equality. That record is not
proved to result from a real ISC check. This is **not** an accepted complete native
mixed-parent snapshot or exploit; producers, finalization and whole admission
must be examined before such a claim.

The generator independently pins original native observations and codec-APC /
codec-PARAMETER policy sections before extracting any bytes. Original APC JSON,
body and policy bytes are preserved. Two additional finite SHA samples extend
the existing six ISC/norm/seed/EC samples. Checked component lemmas compose the
original parent records with both APC modes; no whole policy/native execution,
new TLC or production-mutant suite is claimed. Separate mathematical multi-ticket
examples cover filtering, missing/extra/reordered records, all-rejected input,
integer bounds/gcd, absent finalization, changed accumulator and distinct IDs.

Alpha, bucket allocation, iterations, transcript and accumulator preimages are
not recomputed from Q/robust aggregation. A changed bucket/alpha still passes
shape, explicitly retaining that limitation. Signer lists do not authenticate
signatures. General SHA, native exporter, configuration/finalization provenance
and native decimal compatibility remain open. The prior -00/-01 spelling defect
is neither normalized nor repaired here.

Next: complete native PARAMETER body/QC and exact original leaf/denominator/
decimal-result/parent checks; then aggregate/APPLY/current and joined admission/
replay. Arbitrary snapshots, physical WAL/scan failures and unknown outcomes,
full public64-state/native recovery, nativeArithmeticRecoveryRefines, contract
freeze, offline reproduction and independent review remain mandatory. Only exact
merged formal authority permits runtime work. No original or local GO.

Reproduce from repository root:

```text
python -X utf8 formal/scripts/generate_native_plan.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_plan.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativePlan.lean
lake --no-cache env lean DeltaReduce/NativePlanLineage.lean
lake --no-cache env lean DeltaReduce/NativePlanSection.lean
lake --no-cache env lean DeltaReduce/NativePlanVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Final source/check hashes and limits: evidence/native-plan.json.
