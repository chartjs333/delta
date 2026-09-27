# Computed authority root, recursive closure and conditional Binding

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-binding-construction.json`.

NativeGraphClosure executes loadPayload against the actual store at every
referenced node, checks ID/length bounds and recursively visits every decoded
child in original field/list order. A successful finite-depth check constructs
the inductive Complete relation; completeness is no longer a caller premise in
this API. Shared DAG references are allowed. Missing nodes, invalid bytes/types,
bad child types and exhausted depth reject. This is graph completeness, not
arithmetic/phase validity or certificate authentication. Depth bounds path length,
not total repeated traversal work, branching or concrete decoder/hash resources.

NativeAuthorityProjection computes the full AUTHORITY payload from the preceding
checked native preparation context and all eight computed artifact references:
SCHEMA, PROFILE, PLAN, MODEL, OPTIMIZER, ISC, EC, APC. Context strings must retain
the original round/epoch/parent bytes and pass identifier checks. The full JSON
encoding includes the complete parents object; no caller-translated authority is
accepted. Actual canonical bytes/hash/length/decoded payload are checked and the
whole recursively referenced store must pass closure. The raw run API first
executes NativeStateProjection.run, retaining original preparation and history.

NativeBindingConstruction derives the pre-aggregate Anchor and constructs an
actual Binding from those successful executions. Model/optimizer/profile paths
are built at their exact authority edge positions; all original current values,
artifact bytes, common schema and quantum are retained. Current hash identity is
derived from original pointer history under the same named HashAdapter, now a
mandatory argument to every Binding construction entry point. No
supplied whole-state equality or already translated graph-completeness proof is
used. The PARAMETER wrapper calls the existing original/draft arithmetic verifier
on this constructed Binding and retains its numerical and full-leaf checks.

This Anchor is computed, NOT independently authenticated by its computation.
The separate Premises fields require native anchor/recovery and ISC/EC/APC
certificate authentication from Trust. There is deliberately no implementation
or synthetic instance of these premises. UnitSource provenance and independently
configured profile selection are still open. A closed self-consistent store does
not establish either, and cannot supply the Premises when anchor authentication
is false. No phase/role/deadline or native admission assertion follows.

Aggregate is explicitly absent in the constructed Anchor. This stage covers the
graph before aggregate certification and the conditional PARAMETER composition;
it does not construct an APPLY aggregate certificate, full original/draft Inputs
instance, actual native execution or nativeArithmeticRecoveryRefines.

Small kernel cases use a synthetic one-byte codec and repeated-byte IDs to test
the general traversal, including shared Q/schema paths, missing leaves/parents,
changed bytes/length/kind, noncanonical input and insufficient depth. That codec
is neither canonical JSON nor cryptography. Separate component encoding proofs
compose the complete AUTHORITY bytes, checked independently with Python canonical
JSON. They do not instantiate full original policy/state/history or authentication.

All prior restrictions remain: unknown or empty current history cannot invent
values; quantum is unresolved primitive metadata; native/draft hash domains are
distinct; source schema/current-height checks, layout4096 and artifact4MiB are
projection restrictions. Native -00/-01 compatibility, original008 captures,
initial snapshot authority, arbitrary phase/QC/send/delivery/journal/current and
crash/unknown/torn/repair/physical WAL, bounded concrete codecs/hash/exporter,
contract freeze, clean offline reproduction and independent review remain open.
Runtime guards and existing demos are unchanged. No local PASS or formal GO.
