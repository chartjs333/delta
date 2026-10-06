# Delta R2.3 — exact storage contract awaiting decision

6 October 2026. T047/T053. Existing sprint; **R2.3 OPEN / Formal NO_GO**.

Scope6 human decision `scope-decision-344bf1b51a2dd860e4fd57e20f3a9b84`
approved the earlier request to write one storage source specification.
Official whoami returned coordinator2750, assignment
`6a4e2acb-444f-45dd-aa08-8b4c4741a39c`, branch
`agent/isc-s16-continuous-sprint`. Fresh effective source/core hashes and
precedence were checked. Exact ACK `scope-ack-cc85140300f70cddfca87cc7527e9807`
persisted and was GET-confirmed after the HTTP client timed out; it was not
blindly resubmitted.

The allowed document is complete at
`1438fa3d78ec99291475cf4660fd8c190ac01bb3`:
`docs/adr/0016-storage-availability-source-binding-v1.md`.
Its adjacent `docs/adr/evidence/0016-storage-availability-source-binding-v1-audit.json`
pins inspected original sources. Staged/committed bytes and source digests were
checked; no canonical/signature vectors, native tests or formal gate result is
claimed for this specification. Production, schemas, Lean/TLA/proofs and legacy
objects remain unchanged. Commit was pushed and remote branch equality checked.

The new semantic decision is exact approval/rejection/edit of ADR0016 §§3–7:
existing independent deployment provisioning -> pinned initial configuration's
proposed storage binding -> original storage identities and their own keys;
exact attestation/signature/AC bytes; per-leaf quorum and original witness/cut.
The config-to-storage-key binding is explicitly **new and unapproved**, not an
already existing fact. No new trust root or stronger storage honesty assumption
is silently selected. The proposal preserves close/repair/deadline policy and
all original history. Signatures authenticate statements; availability and lawful
producing history still require the original independent source evidence.

Structured request source:
`scope-requests/ISC-S16-R23-STORAGE-CONTRACT-APPROVAL.json`.
Register it through the actual-role scope-request API with fresh CAS context;
the server creates the Pending decision, not a raw amendment or fabricated
operator approval. The adjacent checkpoint records the resulting request/receipt.

**STOP after document as required by scope6.** Do not send coordinator RESUME
to escape this waiting point; no result, review or graph transition is fabricated.
Ordinary process reviewer gates still apply to the next submitted result. The
two earlier same-executor reviews belong to worker `e766ef98`, not this document,
and are not independent Formal GO attestations.

After an actual new applied human decision, fetch official identity and fresh
effective scope; verify exact source/core/precedence, ACK and GET-confirm. Follow
only that actual scope. If approved as requested, resume the existing reviewed
formal/reference workflow, preserving legacy Init/Next, identities, original
source rules and full lineage. Missing original producer/evidence, incompatible
bounds, or a need for new trust/protocol semantics is a new concrete STOP.

No general R2.3 reauthorization is needed. R1/R2.1/R2.2 remain CLOSED for their
original domain; recovery theorem only follows reviewed substantive R2.3 closure;
full R3, production integration, concrete sigma and guard removal remain excluded.
Keep the automation ACTIVE, with quiet read-only polling while this exact
decision is pending. Never recreate a rejected request as if it were new consent.
