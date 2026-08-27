# Normative Task Map: Feature 003

This map reconciles semantic tasks `T000–T052` with hybrid-runtime obligations `HR003-001–HR003-024`. Both task sets are mandatory. A semantic task closes only when the mapped native implementation and its declared evidence pass; a Python fixture/evidence helper cannot substitute for C++ core/runtime, C ABI or Java FFM work.

| Semantic tasks | Runtime obligations | Binding outcome |
| --- | --- | --- |
| T000–T003 | HR003-001–HR003-003 | Exact predecessors, Formal GO/artifacts, architecture scan and formal-impact preflight |
| T004–T010 | HR003-004, HR003-007–HR003-008 | Frozen canonical schemas, encoders, fixtures and golden hashes |
| T011–T015 | HR003-002–HR003-003 | Pinned toolchains, build targets, CI matrix and pure-core boundary gates |
| T016–T017 | HR003-004 | Explicit native types, canonical encoders and fail-closed parsers |
| T018–T019 | HR003-005 | Checked fixed-width arithmetic and safe prepared-integer bounds |
| T020–T024 | HR003-006–HR003-008 | Pure transition, canonical state/effect/WAL bytes and portable golden results |
| T025 | HR003-009 | Single-writer reactor and bounded submission |
| T026 | HR003-010 | Canonical WAL, sequencing and durability barrier |
| T027–T031 | HR003-011–HR003-013 | Snapshot/journal recovery, persist-before-expose and crash matrix |
| T032–T034 | HR003-014–HR003-015, HR003-019 | Versioned C ABI, exception containment, ownership and sizing |
| T035–T039 | HR003-016–HR003-019 | JDK FFM lanes, direct/copy identity and boundary mismatch/lifetime tests |
| T040–T042 | HR003-022–HR003-023 | Formal trace projection/refinement and real production-path mutations |
| T043–T044 | HR003-020 | Four-native-runtime 100-ticket identity and restart equivalence |
| T045–T047 | HR003-021 | ASan/UBSan, separate TSan and bounded fuzz evidence |
| T048–T052 | HR003-003, HR003-024 | Final architecture, documentation, content-addressed evidence and phase gate |

## Closure rules

1. `tasks.md` is the execution ledger; `runtime-tasks.md` states non-negotiable runtime outcomes.
2. When one `T` maps to multiple `HR` obligations, every mapped obligation must pass.
3. When one `HR` obligation spans multiple `T` tasks, it remains open until all those tasks pass.
4. Any new transition, precondition, deadline, durability outcome or failure terminal is `SEMANTIC`: stop, amend feature 000 and obtain a new Formal GO.
5. Production quantization/codecs (`004`) and protobuf/gRPC/Netty/TLS/P2P transport (`005/008`) cannot be used to close a feature-003 task.
