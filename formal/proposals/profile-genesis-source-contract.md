# Profile genesis values — selected source binding

T047/T053; standing scope 3, worker assignment
`2fd81f70-bb27-4872-a09c-8a712c0e2311`, 28 October 2026.
This is the initial source/configuration/units part of the existing R2.3 residual.
No production protocol, snapshot activation, trust root, concrete semantics ID,
QC/WAL identity, R3 or new independently required proof layer is introduced.

## Existing authority and selected bytes

The independently provisioned BOOTSTRAP already pins both `genesis_ref` and
`initial_config_ref`. ProfileOrigin/metadata resolution alone authenticated
their exact references; it did not parse their initial arithmetic meaning.
For the isolated future reference generation, select one closed genesis-value
artifact at that existing `genesis_ref`. Do not reinterpret historical bytes.
Its complete canonical ASCII JSON contains exactly these fields, in ASCII order:

`formal_semantics_id`, `height`, `model_values`, `optimizer_values`, `origin_id`,
`schema_version`, `type_name`, `validator_epoch_id`.

`schema_version="1.0.0"`; `type_name="PROFILE_GENESIS_VALUES"`. Semantics,
origin and epoch equal the independent bootstrap values. Semantics must be the
separately selected future generation, never a legacy fallback. `height` is the
existing canonical U64 decimal string, without imposing a new genesis-height
constant. Values are ordered arrays of canonical signed INT64 decimal strings;
`-0`, leading zeros, positive signs and alternate spellings are rejected.
Model length is 1..100000 and optimizer length is identical, reusing the native
current-value contract. No zero-initialization or special vector length is
assumed. Every original coordinate, including repeated values, is retained.

Canonical encoding reuses storage-source JSON (closed fields, duplicate member
rejection, exact reconstruction, no numbers/null/floats). This artifact is not
one of Profile's four 4 MiB control documents: only the existing complete source
budget applies in addition to native value bounds. Applying a 4 MiB control cap
here would exclude existing 100000-coordinate model/optimizer pairs and is not
authorized. The artifact keeps the existing raw-content reference identity;
there is no new genesis certificate or signer population.

Derive checkpoint/optimizer IDs using the unchanged native preimages:
`ASCII("deltareduce.008.model.v1") || 00 || concat(ASCII(value) || ";")`, and
the corresponding `optimizer` domain. The initial native pointer has those IDs,
the original height and empty QC, as permitted by `NativeCurrentPointer.StateValid`.
This is the base before certificate-producing history, not an imported current
with an invented certificate. All finalized/candidate/history collections start
empty according to existing Init; no supplied nonempty collection is erased or
accepted as genesis. Such collections must be derived from subsequent original
events. The bootstrap `initial_anchor` is a separate trusted floor: it still
requires its existing valid ApplyQC and complete producing prefix. Genesis
values, their hashes and this binding never replace that check or authorize READY.

The initial configuration remains complete original bytes selected by its
bootstrap reference. Extract the already selected `arithmetic_units` member,
validate exact INITIAL_ARITHMETIC_UNITS bytes, parameter schema and positive
reduced quantum. No default quantum, candidate-selected units or replacement
configuration is permitted. Other initial configuration fields remain retained
and require their existing source validators; this join does not bless them.

## Executable boundary and qualification

The reference entry point takes independent PrimitiveTrust plus original
manifest/index/artifact bytes. It reruns metadata/floor/custody checks and source
materialization before resolving genesis and initial configuration. It accepts
neither a supplied Metadata/Prefix cache nor a boolean asserting legal origin.
Kernel binding composes existing Origin.bind with complete genesis bytes,
native decimal/hash/value rules and exact initial configuration member bytes.
Prove original-byte, coordinate/count, INT64-bound and existing hash-preimage
preservation, and completeness for this selected grammar. No successful public
state/refinement result occurs in its premises.

Qualify duplicate/unknown fields, alternate decimal/JSON encodings, context and
reference substitution, whole-config/quantum substitution, full native endpoint
values and a valid artifact larger than 4 MiB. Synthetic fixtures are codec/source
examples, not complete lawful snapshots or production provisioning evidence.

## Alternatives, compatibility and residual

The base configuration join uses the independently selected schema-3 decoder
and the existing ConfigurationUnits admission checks. It resolves validator and
storage enrollment through the SAME raw bootstrap/initial configuration; checks
the whole retained configuration and declaration; derives the full parent tuple
from original genesis values; and requires original parent, increasing height,
schema and both units. The legacy schema-2 decoder is unchanged and is never a
fallback for this route. No configuration field, vote/QC ID or admission rule is
added. The kernel composition retains its explicit independent Enrollment
premise; Python resolves that premise from raw Profile inputs. This is the base
case to be used by the enclosing producer, not permission to reset later current
state to genesis, infer proposal/finalization from a valid body, or erase history.

Do not accept an opaque genesis merely because its hash is pinned; that leaves
the initial arithmetic source uninterpreted. Do not synthesize an ApplyCandidate
or ApplyQC to reuse its value decoder; that invents protocol identities. Reuse
the existing value decoder/hash rules directly. Do not select initial values or
units from the imported current, successful EC/APPLY, or public projection.

The change adds only an isolated reference artifact grammar beneath an existing
bootstrap reference. Previously qualified historical objects are not migrated,
relabelled, resigned or newly declared conforming. The new artifact/producer
grammar requires its own future-generation pins and affected qualification.
R1/R2.1/R2.2 remain closed for their original domains. R2.3 remains OPEN: complete
native producing history, original ISC/clock/seed joins, all full public-state
constraints and initial/incomplete/ABORT composition still require completion
and review. This source binding alone establishes neither their legality nor
the named recovery theorem nor Formal GO.
