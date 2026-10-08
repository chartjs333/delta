# Storage source binding — approved O generation

T047/T053; scope 11, human decision
`scope-decision-e5c12ebc8342d99630d5fcf28a9c6753`. **R2.3 OPEN / Formal NO_GO.**
Exact assigned worker ACK: `scope-ack-a07a96b9126f50c24a663f2b99658f95`.

`codec.py` implements the already approved ADR0016 A/Ms/SAG1/D/ac/Rs/Ks
contract at `1438fa3d78ec99291475cf4660fd8c190ac01bb3`, under ADR0018's
authenticated-statement claim at `90561a97de7f41f409bf22065ad6cdc9b3932458`.
These pins are immutable despite their historical PROPOSED headings; their
later human approvals, not those headings, supply this reference-work authority.
No legacy object is converted, no concrete successor semantics ID is selected.

The independent primitive bootstrap produces the exact storage registry/key
table. Imported Rs/Ks can only match it. A and D bind their complete original
context, leaf and full envelope length. Authentication uses the existing pinned
strict libsodium 1.0.22 primitive and its actual Ed25519 computation; no boolean
or opaque verification callback is accepted. Each leaf's original signer subset
must independently reach the configured storage threshold. The decoder rejects
duplicate JSON names before typed parsing, unknown/missing members, noncanonical
bytes, wrong roles/keys/domains/context and witness reordering/inflation.

The return value retains the exact D, every original input-inventory occurrence
(including unused, duplicate and invalid deliveries), and the actual witness.
Resolving repeated identical bytes to one content ID does not remove an event.
Different witnesses remain different ac artifacts. This function neither elects
the first accepted certificate nor replaces one with a later witness.

`Context` is explicitly a **component input**, not an origin credential. The next
composition must derive it from the independently checked configuration,
ticket/commitment and manifest preimages and restrict witness resolution to the
actual original prefix. Calling this function with a supplied Context or any
list of messages does not prove that prefix existed. Likewise, no physical disk
presence or successful data use follows from the authenticated witness.

The storage codec does not import ISC's unrelated 4 MiB message cap. Scalar
grammars and SAG1 U32 framing are enforced; enclosing full-source and W1 budgets
remain separate mandatory checks. A maximal legal A fits the existing strict
primitive's message bound without changing it. This is a component compatibility
check, not qualification of the complete approved source domain.

Run `formal/proposals/isc-source-generation/check_storage.py` with the existing
`ISC_SODIUM_DLL` pin. Its synthetic byte/signature fixtures are conformance
evidence only, never a captured production history or full R2 result. The original
scope-11 component changed no TLA/Lean or production artifacts.

## Scope 13: exact original retention declaration

Human decision `scope-decision-ccba23f3167be9feed1dd79a49db09b0` approved the
exact binding at
`12326b892690705b7141fcd32bf3f32cf07d092e:formal/proposals/retention-policy-source-binding-v1.md`.
Role 2753 ACK `scope-ack-a30732f8d640518596da678cfa2e63c3` is GET-confirmed.
`retention.py` and `retention-source.schema.json` implement the closed future R
and required storage_binding. Schema validation follows strict original-byte
decoding; a post-parse schema alone cannot detect duplicate JSON member names.

Resolution requires the entire original E and checks its positive U64 length,
raw digest and contextual epoch. E is never normalized, interpreted, executed
or fetched. The derived r is a source identity, not a certificate. The S
composition verifies actual signatures and preserves the original AC and every
delivery occurrence. A bare epoch, digest-only inventory, missing R or different
declaration cannot substitute for the original bytes. The returned component
does not certify the enclosing RoundConfig or its original producing prefix.

`RetentionSource.lean` proves canonical codec inversion/injectivity and exact
resolution for arbitrary admitted R/E, without a policy-validity or collision
axiom. Two differing E accepted for the same R necessarily exhibit an equal
digest representation. The hash primitive remains explicitly parameterized;
this is not a proof of SHA-256 collision resistance. Shared synthetic vectors
check Python/Lean byte agreement, including binary E and maximum epoch length.

Run `formal/proposals/isc-source-generation/check_retention.py` with the same
`ISC_SODIUM_DLL`. It rebuilds the Lean closure, audits axioms and records a
separate `formal/proposals/evidence/retention-source-v1/` receipt. Scope-11
evidence is historical and is not overwritten or relabeled as scope-13 proof.

Still OPEN: derive the exact enclosing configuration and original event
association from independently anchored history; compose the full O source and
public state, budgets and affected model/refinement/mutant/review gates. This
component adds no trusted boolean, production policy value, temporal retention
evaluator, source cap or physical truth assumption. R2.3 is not CLOSED. No
production code, guard, old identities, named recovery theorem or full R3 changes.
