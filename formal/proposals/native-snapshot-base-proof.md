# Shared native snapshot base and proposed ISC certificate expansion

T044/T048/T049/T053/T057/T060; amendment0001; Feature000 proposal only.
The source is the unmodified native implementation at
`60c692f6e391f839829dfc64e93380db54cd507b`. No runtime guard is changed.

`NativeProposedIsc` parses each original proposed input-set body, validates its
complete context, root and ordered tuples, and computes its binary body ID.
It derives the certificate view using **every configured validator** and the
actual `2*((n-1)/3)+1` threshold. It validates the full certificate, serializes
the canonical JSON and checks the inclusive 4 MiB contract bound before its
separate domain hash. It never accepts an externally supplied complete
certificate translation or approval bit. List lemmas retain every original
source and exact count/position; membership implies the actual body and bounded
certificate checks. Closed IDs refer to the binary vote body, not the JSON QC.

`NativeSnapshotBase` checks the original configuration sets, optional
accumulator proof identifier, header, complete expected constructor context,
proposed ISC bodies and exact closed-body membership/order. `bindSnapshot`
actually composes this base with `NativeFailureSection.bindSection` on the same
original policy/state, preserving the entire earlier finalized ISC/seed/norm/
EC/APC/PARAMETER/ROOT/APPLY/failure section chain and its size checks. It neither
empties a graph nor replaces the candidate list. `prepare` decodes the original
bounded policy and state; its theorem reuses the policy decoder's role, action,
candidate order/count and global context-uniqueness checks. Candidate body/
parent/live admission remains separate; a nonempty list of valid action numbers
does not prove those candidates authorized.

## Identifier correction and constructor distinction

Read-only `vote_admission.cpp::validate_policy_impl` checks configured validator
IDs with `require_sorted_ids(..., false)`: each is nonempty. The
`ChainVerifier` constructor checks nonempty 3f+1, order and threshold, without
requiring every configured validator to satisfy certificate `Label` syntax.
`contracts.cpp::validate_signers` requires that syntax on **actual signers**.
`NativeIscCertificate.CommitteeValid` is corrected at this exact boundary;
`SignersValid` retains the actual signer Label check. The policy wire still
separately checks printable ASCII and length4096. The pure committee predicate
alone does not certify that an arbitrary list came from the wire decoder.

A finalized three-signer certificate can therefore omit a fourth configured
non-Label identifier. A proposed certificate expands all four and must reject
that same identifier. Kernel cases demonstrate both. This is correction of an
overrestricted formal projection, not a new native runtime defect or repair.
The older closed `NativeProposalAdmission.GraphChecks` restrictions remain
explicitly separate; no completeness claim is inferred for that API.

The round ID **must still be a Label**, even for an empty certificate graph:
the ChainVerifier constructor unconditionally calls `validate_context`, which
calls `validate_context_values` and `require_label(round_id)`. Header round
checks are therefore retained. The previous timeout/request WireId correction
does not relax this independent constructor condition.

## Evidence and reproduction

`generate_native_snapshot_base.py` pins the complete original policy observation
`d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea`,
reencodes the original `codec-ISC` policy and checks its exact original body
against the separately pinned ISC certificate. It derives the four-signer
JSON SHA sample; this newly computed sample is not a fresh native observation.
The kernel examples execute the original proposed-body and `checkBase`
components. They do not claim a new complete `bindSnapshot`/`prepare` fixture,
native execution, signer authentication or exporter provenance. Generic
composition theorems use actual executable subresults, not an assumed recovered
state equality. The expanded JSON length and hash, two distinct identities,
configuration/accumulator/closed/order/context/committee negatives are checked.
The large size counterexample is mathematical and explicitly not an admissible
native policy. Exact generic overlimit rejection covers all payload lengths.

Run with the pinned local toolchain:

```text
python formal/scripts/generate_native_snapshot_base.py
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
python -m unittest discover -s formal/tests -p test_native_snapshot_base.py -v
python formal/scripts/check_lean_evidence.py
```

Lake runs from `formal/proofs`. The final command intentionally reports the
still-missing mandatory `nativeArithmeticRecoveryRefines`: 44/45, NO_GO.
Machine results and source hashes are in `evidence/native-snapshot-base.json`.

## Remaining scope

This closes the previously omitted configuration/accumulator/proposed ISC base
checks in an executable composition with the existing typed snapshot sections.
It does not establish general native acceptance/error-order/allocation
equivalence, full all-candidate admission, native arithmetic input execution,
CurrentPointerCommand or historical retry classification. Original byte/hash
functions, source configuration and runtime facts remain explicit boundaries.
The known native `-00`/`-01` decimal canonicality defect is not repaired.

Complete public64-variable/native journal correspondence, global send/delivery/
QC/current, unknown/crash/repair, physical WAL and scan completeness, SHA/exporter
authentication, contract freeze, offline reproduction and independent review
remain open. No new TLC run, production mutant, native execution, local PASS,
BenchmarkResultQC, independent attestation or merged formal GO is claimed.
