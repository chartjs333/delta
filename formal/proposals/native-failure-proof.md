# Original native timeout, view and abort snapshot tail

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO remains.**

This stage extends the typed native snapshot subrelation after NativeApplySection.
Source: consensus.cpp, vote_admission.cpp and vote_codec.cpp at pinned native
commit60c692f6e391f839829dfc64e93380db54cd507b. Runtime files are unchanged.

NativeFailurePayload retains complete original timeout observations, VIEW bodies,
abort requests and fourteen-field ABORT bodies. Readers reconstruct the exact
original typed trees. Executable row checks use the actual native policy schema
encoder, retain exact wire bytes, and compute body IDs from source-derived binary
preimages. These hashes use uint64 big-endian text lengths and list counts;
the policy wire format uses its own uint32 lengths. They are not interchangeable.
VIEW retains round/height/fromView/toView/softDeadline. ABORT retains round/epoch/
height/view/hardDeadline/parent/reason and all seven ordered finalized-ID lists.
Domain-separated SHA remains an explicit function premise. This source binary
hash helper has no certificate-JSON4MiB guard; none is invented. Original policy
wire bounds and per-field encoding checks remain. No general SHA implementation,
allocation/error-order equivalence or native authentication is proved.

NativeFailureSection reads every original snapshot list, requires canonical
strict timeout tuple order (round,height,view), strict request order (round,reason),
strict computed VIEW/ABORT body-ID order, request reasons exactly INCOMPLETE_INPUT
or UNSAFE_COEFFICIENTS, and the original wire count/width bounds. Every ABORT body
must match all fourteen actual policy/state/lineage fields, including the entire
seven finalized lists, not counts or aliases. Successful execution reconstructs
original lists and proves every body passed its actual reader/encoder/hash and
exact-lineage checks. bindSection actually calls NativeApplySection.bindSection;
prepare uses original bounded policy/state decoders. No approval Boolean or
caller-supplied whole-body translation is used. The generic helper is instantiated
with fixed source readers and hash functions in the concrete entry points.

The source snapshot checks deliberately do not impose VIEW candidate freshness,
current coordinates or increment/deadline guards on every stored VIEW body.
Likewise a snapshot ABORT body can carry a matching nonempty finalizedApply list;
selected ABORT admission later requires that list empty. Kernel counterchecks
show these limits of TailChecks/AbortExact only: they do not claim accepted whole
policy/runtime execution. Missing source/hash checks are not inferred from a
standalone TailChecks result. The new complete checkTail examples use all checks.

Examples reuse original codec-VIEW_CHANGE and codec-ABORT policy observations,
first verifying the complete pinned observation SHA
 d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea.
Python reproduces both original whole policy wires and independently computes
binary body preimages matching original candidate body IDs. Lean proves component
wire encoding/decoding, two original body IDs under two finite SHA samples, exact
original policy extraction and two complete checkTail results against the reused
original CONFIG fixture state. The state fixture has the same original round,
height, view and parent. These are mathematical component compositions, not fresh
native execution or exporter provenance. No full bindSection native execution
example is claimed. Requests/negative cases are synthetic mathematical tests.

Checks cover every ABORT field substitution, all seven list positions/order/
multiplicity, timeout/request duplicate and reverse order, tuple precedence,
request vocabulary, out-of-width integers, malformed trees, absent SHA output,
and duplicate body IDs. Original bytes/sequences and prior witness files remain.
All new named definitions and theorems are axiom-audited; no sorry/native_decide/new axioms.

Open next: original VIEW/ABORT candidate parents/context/body/timeout matching,
no-overflow view increment, selected ABORT empty finalizedApply and request-or-
deadline enabling; complete shared admission/replay/phase/readiness/sequence and
CurrentPointerCommand. Actual native arithmetic/source joins, canonical decimal
compatibility, proposedISC size path, complete64-variable public/native recovery,
physical WAL/unknown scan/repair, authentication, contract freeze, clean offline
reproduction and independent review remain required. nativeArithmeticRecoveryRefines
is still missing. This does not widen closed CONFIG/ISC admission modes or discharge
the mandatory conjunct. No runtime guard change, local PASS, original GO or new QC.

Reproduction: generate_native_failure.py; lake build DeltaReduce;
lake env lean DeltaReduce/AxiomAudit.lean; test_native_failure.py;
check-refinement.py --all-fixtures. Final stable-source logs/counts/hashes are in
formal/proposals/evidence/native-failure.json and its sibling directory. Retained
TLA/mutant/native observations keep earlier finite scope; no fresh native/TLC run
or new production mutant. make formal-check is not claimed when make is absent.
