# Whole original policy/state to APC members and arithmetic refusal

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-plan-source.json`.

The attempted successful whole-source vector example exposed a source mismatch:
the original008 policy requires the `sha256:ffff...ffff` accumulator proof. The
available original004 proof has a different content ID. Previous vector examples
combine original004 Q components with explicitly constructed membership metadata;
they do not instantiate a successful original008 raw-source join.

`NativePlanSourceVectors` now composes the exact retained5849-byte
`codec-PARAMETER` policy with the674-byte retained state matching its snapshot ID.
The complete policy is decoded and re-encoded, including the unused later
PARAMETER candidate/body. All ISC, norm, seed, EC and APC sections are checked in
the same source, with exact lists, identities, finalized-set membership and parent
relationships. `rawMembersPrepared` executes the actual `NativePlanMembers.prepare`
entry over these bytes and derives the original eligible ticket, final APC alpha
and bucket. It does not assume that a supplied whole snapshot was already loaded.

Small reused encoding and certificate lemmas compose the source. A finite SHA
registry reuses the original certificate samples and adds the exact state and
original004 proof preimages/digests. Python independently computes the latter
digest; the Lean kernel checks its use and spelling. This remains a synthetic
hash adapter, not SHA correctness, authenticated snapshot export or signer custody.
The state comes from a retained component observation with the same exact state ID;
this is not a new execution, a reachable full native history or a native WAL run.

`NativeSourceRefusal` proves that a supplied proof with a different computed ID
cannot load for the required authority, irrespective of the supplied config and
profile. A failed arithmetic source load propagates through the complete Q corpus,
aligned vector context and `NativeVectorJoin.run`, for arbitrary permissions, Q
inputs and even an independently valid draft Binding. The concrete kernel case
rejects substituting the original004 proof for the original008 required proof.
No successful vector join is claimed and no absent preimage is invented.

The plan parser checks only the stated certificate sections. It does not validate
the later PARAMETER body, phase/time, candidate freshness, actual signatures,
availability, input-ledger provenance or all production admission guards. Original
base-config/current/model/optimizer/APPLY captures and the required008 proof remain
missing. Synthetic wrappers can be constructed separately but must receive new
source identities and may not overwrite retained captures.

The full original-to-draft positive example, full configuration/context/current/
APPLY relation, general codecs/hash/exporter, arbitrary snapshots, full-batch
resources, phase/QC/send/delivery/journal/crash/unknown/torn/repair/WAL composition,
native decimal compatibility, amendment freeze, offline reproduction and independent
review remain open. `nativeArithmeticRecoveryRefines` is not discharged. No runtime
guard change, qualifying GO, local acceptance PASS or independent attestation.
