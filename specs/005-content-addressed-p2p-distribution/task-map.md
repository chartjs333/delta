# Normative Task Map: Feature 005

This map reconciles semantic tasks `T000–T032` with hybrid-runtime obligations
`HR005-001–HR005-013`. Both sets are mandatory. Java transport success cannot substitute for
native certification acceptance, and authenticated peers cannot substitute for feature-008
consensus/certificate transport.

| Semantic tasks | Runtime obligations | Binding outcome |
| --- | --- | --- |
| T000–T004 | HR005-003, HR005-012 | Exact feature-004/Formal predecessor, zero authority/plane violations and passing preflight |
| T005–T010 | HR005-002, HR005-010, HR005-012 | Frozen bounded runtime-neutral schemas, identities, policy registry and fixtures |
| T011–T015 | HR005-001, HR005-003–HR005-006, HR005-010, HR005-012 | Pinned tools, native verifier, C ABI/FFM parity, mutants and refinement traces |
| T016–T019 | HR005-003, HR005-008 | Java CAS/publication only after native acceptance, atomicity and idempotence |
| T020–T024 | HR005-002, HR005-004–HR005-007, HR005-009–HR005-010 | Bounded peer plane, discovery, direct/copy lifetime, leak and event-loop gates |
| T025–T028 | HR005-008, HR005-011 | Resumable journal/download/materialization and complete/incomplete seed-loss matrix |
| T029–T032 | HR005-013 | Service/telemetry/docs, content-addressed execution evidence and final compatibility |

## Closure rules

1. `tasks.md` is the semantic ledger; `runtime-tasks.md` contains mandatory runtime outcomes.
2. A task closes only after every mapped runtime outcome and test/evidence gate passes.
3. `aggregated-transition-qc-v1` permits publication only as an immutable aggregate artifact.
   `apply-qc-v1` remains inactive until feature 008 and cannot make a checkpoint current here.
4. Worker q shards, commitments, AC fragments, input candidates, regional partials and parameter
   partials are forbidden even when the caller is authenticated.
5. A Java-side policy shortcut, weaker-policy fallback, alternate content identity, new terminal
   outcome or current-state transition is `SEMANTIC`: stop and amend feature 000 first.
6. Public DHT, WAN claims, hierarchy and complete certificate transport cannot close feature-005
   tasks.
