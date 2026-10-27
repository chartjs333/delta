# Seed source association — selected reference binding

T047/T053; standing scope 3, assignment
`dbaba853-6cc2-4f10-b707-ef79155613a8`, 27 October 2026.
This is the original seed-source obligation inside R2.3, not another DoD layer.
R2.3 OPEN / Formal NO_GO. Existing producer, agreement, generation and Profile T
contracts remain authoritative. The approved component receipts and both reviews
at `4e0dcb51`, `575fca3c`, `aef46c21` precede this composition.

## Selected association

Use the existing materialized Profile SOURCE_INDEX, independent bootstrap and
original own-journal custody. Do not import an accepted Machine/Replay cache.
Replay the local seed companion from empty across the full original ordered
event prefix; preserve all other actions verbatim for their enclosing handlers.
The outer source fold establishes the original finalized ISC and its complete
context; this binding cannot infer that fact from a seed signature or EC.

One canonical reference invocation descriptor identifies a seed producer action:
`type_name="SEED_SOURCE_STEP"`, `schema_version="1"`, the existing `profile_id`,
`bootstrap_id`, `instance_id`, `operation`, `intent_ordinal`, and `commit_ids`.
All fields are required, closed and encoded by existing Profile canonical JSON.
Actor and source position remain solely on the original Event descriptor.
The action ID is `ACT-SEED-PRODUCER`; operations are RECEIVE, INTENT, SIGN,
SIGNED, BARRIER, COMMIT, EXPOSE, CRASH and RECOVER. These are isolated reference
invocations, not new production protocol transitions, native WAL kinds or ABI.

RECEIVE/INTENT/SIGN/SIGNED/CRASH take exactly one original byte input: respectively
received envelope, unsigned body, original signed output, original signed output,
or surviving companion bytes. Other operations have no inputs. INTENT alone may
carry original COMMIT witness IDs; SIGN/SIGNED/EXPOSE alone carry a positive
intent ordinal. All other ordinal/witness fields are zero/empty. Dependencies
remain complete, strictly backward source positions; they do not authorize
substitution of a later input. Every retry and rejected invocation remains a
distinct occurrence even when its machine effect is empty.

SIGN validates the exact signature output against the already committed own
INTENT, original enrolled key and complete earlier knowledge. Its independently
retained original invocation associates that artifact with the own signing
step; a RECEIVE or a merely valid signature cannot supply this association.
This public check does **not** prove private HMAC derivation. Honest private
DEAL/OPEN generation remains the explicitly selected algorithm and existing
honest-validator/unforgeability/PRF assumptions. `durability.sign` is its private
executable reference; no key, private seed, `coins_valid` flag or success callback
is added to a public snapshot/source index. Faulty remote contributions may use
other polynomials; the public PVSS verifier must not exclude them. This binding
must never be reported as an unconditional cryptographic generation proof.

For each seed occurrence, independently decode its complete original descriptor,
recheck raw hashes/lengths/order and exact inputs, run the selected primitive
transition, and retain success or rejection with its exact position and before/
after state. A rejected invocation is a no-op, not an omitted source occurrence.
Unknown operation/dispatch or malformed descriptor is unresolved and prevents
claiming coverage; invalid protocol payloads are retained rejected invocations.
SIGN's signed-output assertion and CRASH's surviving-image assertion are facts
of those original steps, not arbitrary network commands. If either contradicts
its producer/T rule, mark the source unresolved; never reinterpret that claimed
physical/output event as a harmless rejected command. No later event repairs its
coverage, though the original suffix remains retained for diagnostics.
An unrelated original action is retained for its own handler, not declared legal
by this seed facet. A seed action for another actor is also retained unchanged.

At requested prefix cuts compare the computed surviving companion bytes with
the independently retained original journal for the exact actor/instance.
Its Profile journal ID is `PROFILE-SEED-PRODUCER-V1:` followed by the existing
domain-separated `instance_id` (including its `sha256:` prefix).
Missing journal is not empty; original descriptor identity/count and byte tip
must agree. Torn/BLOCKED/incomplete states remain representable, retain all
bytes, and cannot expose a seed. Original native WAL bytes are retained without
rewriting slots or public vote ordinals. Complete global native WAL association
and ISC/clock legality are still the enclosing source fold, not this facet.
Before any accepted invocation creates/uses an instance, an absent companion is
represented as **absent**, not synthesized as an owned empty journal. The empty
fold used to diagnose rejected attempts does not create an instance. After an
accepted invocation, a missing own companion is unresolved even if its durable
prefix happens to be empty. Initial/no-seed snapshots therefore need no invented
per-instance protocol object or journal.

## Alternatives and compatibility

Reject importing a prevalidated Machine, a `durable`/`legal` boolean or a signed
artifact as a surrogate signing event: these assume the missing provenance.
Reject copying private seeds into evidence or requiring every faulty dealer to
use the honest KDF: these disclose keys or narrow the lawful Byzantine domain.
The selected minimal invocation descriptor reuses original Profile event/input
references and the existing primitive machine, with no parallel authority.
Historical source events are not relabelled as these future reference actions.
No old signed bytes, QC, WAL, production Init/Next or semantics ID changes.

## Qualification and remaining composition

Check complete original descriptor/input association; duplicate/invalid events;
omitted, reordered and future inputs; signing/exposure without each barrier;
same-command retries; all original crash regions and repeated unresolved crash;
original journal mismatch/missing journal; unrelated source-event preservation;
context/actor/instance substitution. Derive exact-prefix and occurrence retention
lemmas from the fold, not a supplied public acceptance premise. Compose local
intent/knowledge rules with the cross-view factor and original ISC/timeout/
configuration/native-state joins before claiming the complete seed edge or R2.3.
Qualification records must keep these claims distinct. The whole three R2.3
obligations remain OPEN until their substantive composition and reviews pass.
