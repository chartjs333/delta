# Native immutable admission snapshot boundary (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

This stage executes the unchanged PR50 native policy/admission implementation at
60c692f6e391f839829dfc64e93380db54cd507b. Eight complete translation units are
compiled, including protocol, certificate verifier, admission and the original
test fixture. No mutant macro or arithmetic-guard override is enabled.
The fixtures supply synthetic authority; this is component execution, not an
authenticated exporter, reactor/WAL run, full public refinement or acceptance.

## Exact identities and observations

RoundState and Vote use the native binary DRC1 envelope. They are not the
canonical JSON used for full native certificate contracts, nor the proposal's
tagged complete public states, nor legacy diagnostic snapshot JSON.
The harness retains exact DRC1 hex bytes, original fields and native responses.
The proposal decoder accepts only the exact flat RoundState/Vote field sets
with checked headers, lengths, tag types, field order, numeric spelling,
source semantics and count ordering. Its 16 KiB/4096-text limits are diagnostic
tooling restrictions, not a proof of the general production decoder's bounds.

snapshot.state_id is independently recomputed as SHA-256 of
deltareduce:003:round-state:v1, NUL and the entire native DRC1 state envelope.
The eleven native state fields are available_ticket_count,
committed_ticket_count, config_id, durable_sequence, height,
parent_checkpoint_id, phase, round_id, state_root, ticket_count and view;
the envelope also carries type/schema/formal-semantics identity.
The old native semantics remains cc98f15a..., not candidate GO authority.

The emitted input body includes every native context field, input_root and
ordered tuple (ticket, domain, commitment ID, AC ID). Its voted-body ID is
recomputed through the preceding checked binary ISC codec. No commitment ID
is relabeled a content ID, and no voted-body ID is relabeled a QC ID.
The diagnostic retains selected snapshot fields only; it is not a serialized
complete policy or private runtime snapshot.

## Native checks exercised

Sixty-six cases separately record policy validation and vote admission.
Seven original non-arithmetic action fixtures accept: CONFIG, ISC, EC, APC,
ROOT, VIEW and ABORT. All four PARAMETER/APPLY live/recovery cases pass policy
validation and then reject at the actual authoritative-arithmetic-input guard.

Eleven stale-state cases reject snapshot identity (the committed-count case
also lowers available count to retain native count-shape validity). Cases
reject missing/foreign/duplicate closed membership, missing typed body,
unrebound root/commitment/AC/domain/ticket changes, context/config/epoch/profile/
schema/candidate substitutions and noncanonical committees.
The native vote path additionally rejects changed actor, body, context,
coordinates, expected or supplied sequence, parent, not-ready live state,
invalidated authority, deadline and abort request.

Recovery mode permits recovery_ready=false as the existing replay contract
requires, but still rejects invalidated authority. The test does not call this
successful recovery: it only executes the admission predicate.
Rejected calls produce no VoteAdmission result; accepted calls preserve the
formal action/context. Neither outcome is an effect, receipt or network send.

## Confirmed scope counterchecks

Rebinding a changed inner state_root or ticket count to a new exact state_id
passes this component. The hash proves byte identity, not a preimage relation
from state_root to all 64 public variables.

Changing the proposed ISC root, commitment or AC and recomputing its body ID,
closed-set entry and vote body also passes at the same native state_id.
Removing the finalized-config assertion from the synthetic ISC snapshot passes.
These are explicit trust-boundary counterchecks: the component consumes an
already-prepared immutable authority snapshot and does not construct CloseInput
or prove its producer. They are not demonstrated attacks on the complete
production runtime, and must not be summarized as full-pipeline vulnerabilities.

Read-only caller inspection shows Runtime validates the supplied policy against
its initial state, retains vote_policy_identity, rechecks admission during replay
and invalidates authority after a state command. vote_codec serializes snapshot
fields including closed IDs and typed bodies. Those separate policy identity/
origin and WAL bindings have not been executed or proved by this harness.

The complete public pre-state still needs an independently bound producer,
configuration and action position. Its proposals/finalized certificates,
closedInputBodies, commitment/content/AC/root preimages, live per-shard
availability, clock, actor recovery and complete durable/received/sent sets
cannot be supplied merely as native summary counts or rehashed opaque IDs.
No full-public-state-to-native adapter is falsely marked complete in this stage.

## Verification and next stage

Ten tooling tests check the 66 actual results, both guarded actions/modes,
all source/harness pins and exact byte reproduction. They reject every truncated
prefix of a retained native state, bad header/type/count/tag/order/number/identity,
diagnostic omission/reordering and changed state/body/context evidence.
No new Lean/TLC result or production mutant is claimed. The mandatory audit
remains 44/45; nativeArithmeticRecoveryRefines is missing.

Run python formal/scripts/generate_native_admission_vectors.py; add --vcvars
with the VS2019 vcvars64.bat path for the native compile/run. Run unittest
discovery with -s formal/tests -p test_native_admission_snapshot.py.
Evidence is formal/proposals/evidence/native-admission-snapshot.json and its
sibling directory. Discarded harness drafts do not count as passing evidence.

Next inspect and bind the complete native policy identity/serialization at the
actual runtime-open and replay boundary, and identify its authoritative producer.
An exact policy hash still cannot replace provenance or the complete public
CloseInput/configuration relation. Construct that relation from actual source
artifacts; leave unavailable root/content/availability metadata unresolved.
Do not enable the mixed non-arithmetic PublicDurablePrefix branch from these
synthetic component results. Phase/send/delivery/QC/current/crash/unknown and
the general recovery theorem remain open, as do native adapter/WAL completeness,
arbitrary failures/snapshots/repair, contract freeze, offline reproduction and
independent reviews. No original GO or SIMULATED_LOCAL PASS is issued.
