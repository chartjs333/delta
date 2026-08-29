# Feature 007 semantic/runtime task map

This map reconciles semantic tasks `T000–T033` with hybrid-runtime obligations
`HR007-001–HR007-012`. Both sets are mandatory. Transport success cannot substitute for native
lease/commit safety, and deterministic unit fixtures cannot substitute for formal refinement or
durable recovery evidence.

| Semantic tasks | Runtime obligations | Mandatory evidence boundary |
| --- | --- | --- |
| T000–T004 | HR007-007, HR007-011, HR007-012 | Exact merged feature 006, inherited Formal GO, zero new semantics/forbidden authority and passing preflight |
| T005–T010 | HR007-001, HR007-005, HR007-007, HR007-012 | Frozen canonical schemas, IDs, valid/invalid cross-language fixtures and deterministic contract evidence |
| T011–T014 | HR007-002, HR007-007, HR007-008, HR007-010 | Native exact ticket/data/quota/feasibility planner, 50-worker permutations and production mutants |
| T015–T018 | HR007-003, HR007-007, HR007-008, HR007-010 | Native capability policy, math-neutral initial leases, speed-independence and infeasibility matrix |
| T019–T023 | HR007-004, HR007-005, HR007-009, HR007-010 | Native durable timers/lease epochs/reassignment, commit ordering and crash/race/terminal matrix |
| T024–T026 | HR007-005, HR007-006, HR007-007 | Bounded C ABI parity and Java authenticated transport/admission/timer adapter with zero decision authority |
| T027–T028 | HR007-007, HR007-009, HR007-011 | Accepted legal native traces and rejected illegal traces/production mutants |
| T029–T033 | HR007-008, HR007-012 | Measured determinism, exact-source compiler/JDK/sanitizer CI and content-addressed final evidence |

## Authority rule

C++ alone creates canonical tickets, decides eligibility/feasibility, advances lease epochs, validates
timer tokens and orders commitment versus expiry. Java authenticates and transports canonical bytes,
returns opaque timer tokens and records operations telemetry. Python trains against an already
finalized ticket. Neither Java nor Python may repair, override or infer native scheduling state.

## Formal boundary

Feature 007 refines existing lease, logical deadline, reassignment, commitment and recovery actions.
It does not introduce new certificate types, ISC/seed behavior, ApplyQC/current transitions or a
wall-clock fallback. Discovery of such behavior is `SEMANTIC` and returns the branch to feature 000.
