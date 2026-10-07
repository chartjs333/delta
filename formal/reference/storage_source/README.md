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
evidence only, never a captured production history or full R2 result. No TLA,
Lean, production runtime, schema, guard, old fixture or accepted result is
modified by this component.
