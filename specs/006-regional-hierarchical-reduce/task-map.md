# Feature 006 semantic/runtime task map

This map reconciles semantic tasks `T000–T030` with hybrid-runtime obligations
`HR006-001–HR006-011`. Both sets are mandatory; transport success cannot substitute for native
integer/topology correctness, and theorem success cannot substitute for failure/interleaving tests.

| Semantic tasks | Runtime obligations | Mandatory evidence boundary |
| --- | --- | --- |
| T000–T004 | HR006-001, HR006-008 | Exact merged feature 005, Formal GO/proofs, zero forbidden paths and passing preflight |
| T005–T010 | HR006-001, HR006-005, HR006-010 | Frozen topology/result/QC schemas, theorem instance, fixtures, IDs and denylist |
| T011–T014 | HR006-002, HR006-005, HR006-008 | Native exact topology/coverage/bound verifier, fuzz and production mutants |
| T015–T018 | HR006-003, HR006-008, HR006-009 | Native regional integer result/QC durability and failure/recovery matrix |
| T019–T022 | HR006-004, HR006-008, HR006-009 | Native exact global required-set combine, QC body and failure/recovery matrix |
| T023–T025 | HR006-005, HR006-007, HR006-008 | Complete canonical coverage, exact flat equivalence and refinement/mutant gate |
| T026–T028 | HR006-006, HR006-007, HR006-009 | Bounded C ABI, Java routing-only orchestration, lifetime/order/recovery parity |
| T029–T030 | HR006-010, HR006-011 | Partial-media rejection, measured fan-in and content-addressed final evidence |

## Authority rule

C++ alone validates topology, theorem preconditions, integer arithmetic and committee-result/QC
bodies. Java transports canonical bytes and executes native effects; it cannot exclude regions,
average partials, choose coefficients, decide quorum sufficiency or authorize P2P publication.

## Certificate boundary

Feature 006 basic regional/global committee quorum envelopes are refinement artifacts only.
ISC/EC/APC, full ParameterShardQC/AggregateRootQC lineage, ApplyQC and current-pointer completion
remain feature-008 obligations.
