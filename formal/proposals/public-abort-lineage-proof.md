# Conditional native ABORT lineage and partial public ancestors

Feature000 candidate only (T044/T048/T053/T054/T056/T057). This does not
discharge nativeArithmeticRecoveryRefines or authorize runtime work.

NativeFinalizedLookup resolves each original ID to exactly one complete typed
object. Missing or ambiguous matches fail. General proofs retain exact query
order, positions, length, membership, unique identity and full payloads.
Unreferenced available objects are allowed; duplicate query IDs are preserved
by this generic resolver, not silently removed. Native snapshot strict finalized
list checks are the separate source of native duplicate-query rejection.

NativeAbortLineage starts with an actual NativeEarlySource.Loaded and an actual
selected NativeFailureSource.Abort. All seven lists come from that original
ABORT and equal the original policy snapshot's finalized lists. CONFIG is a
native ID list, not a full certificate payload collection; every listed config
is proved to equal the original configured native ID. ISC/EC/APC/PARAMETER/ROOT/
APPLY IDs resolve to complete typed objects from the checked snapshot sections.
The source-bound native certificate checks are retained for every ISC/EC/APC/
PARAMETER/ROOT object. Accepted ABORT implies APPLY absence; the resolved APPLY
list is therefore proved empty, rather than being supplied as an assumption.
Lookup uses finalized certificates, never a fabricated proposed ROOT vote or
current first-vote freshness for those certificates.

PublicAbortAncestors constructs CONFIG aliases and complete ISC/EC/APC ancestor
values with the existing source-derived loaders. Each public list preserves
the original finalized ID position and count and is paired with the full native
object. It retains full ISC tuples, EC seed/norm/member data and APC parents/
weights/coefficient keys. Inner and outer duplicate public values reject through
separation checks; set sorting preserves every value. Canonicality is checked
against the supplied model namespace. Primitive metadata and the namespace
still require independently authenticated live configuration; fixtures use
explicitly synthetic metadata. SamePlanParents remains a stronger projection
restriction, not a claim of native admission equivalence.

This is deliberately a PARTIAL public ABORT projection. The complete native
PARAMETER and ROOT objects and original IDs remain in the returned image, with
general retention proofs. They are not replaced by empty public sets. No full
ABORT body/vote constructor is exposed by this module; the existing complete
PublicFailureBody API still rejects nonempty downstream lineage. Numerical
PARAMETER/finalized ROOT public construction and full ABORT envelope/history
composition remain next work. The selected action-6 ROOT loader is not called
on an action-9 ABORT. NativeCertifiedCorpus can resolve finalized ROOTs once the
actual NativeVectorContext and required artifacts are source-bound.

Examples reuse original individual ISC/EC/APC/PARAMETER lookup components and
separate synthetic public ancestor components. Small general lookup/collection
cases cover missing, conflicting/identical duplicate, substituted, reordered,
extra and omitted values, missing primitive metadata and changed APC parents.
They do not instantiate a joined nonempty original ABORT snapshot/vector corpus,
and are not new native executions, captures, TLC runs or production mutants.

All-kind/all-actor exact prior public durable correspondence, independent raw
observation/alias/configuration authentication, actual phase/send/delivery/QC/
current/crash/unknown composition and general recovery remain open. Original
008 proof/base/current capture limitations and scalar/ordinal/decimal projection
restrictions remain. Runtime/native guard unchanged; no local PASS, GO,
BenchmarkResultQC or independent attestation is claimed.
