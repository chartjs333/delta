# DeltaReduce v1 formal-first hybrid-runtime roadmap

## Gate status

Feature `000-formal-tla-spec` has a deterministic `GO` for formal semantics:

`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

Features 000–005 are merged. Feature 003 merged as
`53da4d3c0b236726566fb242fdcae84032b42679` after its native core/runtime, ABI/FFM,
compiler/sanitizer, refinement and final `REFINEMENT_ONLY` gates passed. Its verified source is
`189e5f155b787c2d1d391630fc599b67ea366bba` and its evidence overlay is
`f4f2101969d14709834ab6b6d60e88755d710334`. Feature 004 merged as
`bd31efaa6d521bbfc3362ad9aac39455bd29a098`; its verified source is
`22dd996b5d169763bfde49f32c1b1b18f2656493` and evidence overlay is
`29fb4138499a348f90d6bbc44e77fe6d1914e25f`. Feature 005 merged as
`1e884b4122898a8e0ff17254bc42414a8773830c` with deterministic `REFINEMENT_ONLY` GO; its verified
source is `01f200b193733a1b474ad755c5c0c739b3189a96`, evidence overlay is
`be5d72305bfd883a5bd99607df6c2788014bfd0a`, and final report SHA-256 is
`7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6`. Feature 006 is restacked
on that merge and remains implementation-blocked until its exact predecessor/formal/hierarchy
preflight passes.

## Branch topology

| Order | Branch | Base | Primary exit gate | Runtime focus |
| ---: | --- | --- | --- | --- |
| 0 | `000-formal-tla-spec` | `main` | Formal GO | TLA+/Lean/refinement/evidence |
| 1 | `001-reproducible-training-baseline` | `000-formal-tla-spec` | merged Formal GO + deterministic baseline | Python worker + protocol foundation |
| 2 | `002-local-round-engine` | `001-reproducible-training-baseline` | fixed ticket reconstructs worker state | Python/PyTorch local engine |
| 3 | `003-bft-round-state-machine` | `002-local-round-engine` | C++ traces refine TLA+; four nodes agree exactly | C++ core/runtime/WAL, C ABI, Java FFM harness |
| 4 | `004-compressed-delta-protocol` | `003-bft-round-state-machine` | exact fixed-point bytes and proof instances | C++ codec/shards + cross-language fixtures |
| 5 | `005-content-addressed-p2p-distribution` | `004-compressed-delta-protocol` | certified object survives seed loss | Java Netty P2P, safe FFM ingress |
| 6 | `006-regional-hierarchical-reduce` | `005-content-addressed-p2p-distribution` | formal and empirical flat equality | C++ hierarchy + Java routing |
| 7 | `007-domain-pure-ticket-scheduling` | `006-regional-hierarchical-reduce` | deterministic quota/lease safety | C++ scheduler state + Java admission |
| 8 | `008-certificates-and-consensus` | `007-domain-pure-ticket-scheduling` | full chain, Frankenstein reject, ApplyQC unique | C++ certificates/apply + Java TLS/timers |
| 9 | `009-qlora-8gb-mode` | `008-certificates-and-consensus` | frozen base and certified adapter run | Python QLoRA + C++ adapter core + Java node |
| 10 | `010-wan-benchmark-and-quality` | `009-qlora-8gb-mode` | preregistered GO result | polyglot E2E/sanitizer/fuzz/WAN/quality |
| 11 | `011-multiregion-pilot` | `010-wan-benchmark-and-quality` | signed pilot decision | packaged native/JVM nodes + Python workers |

## Normative implementation artifacts

Every feature keeps original `spec.md`, `plan.md`, `tasks.md` and adds:

- `runtime-profile.md`: language/runtime ownership, boundary and formal-impact rules;
- `runtime-tasks.md`: supplemental mandatory implementation tasks;
- `checklists/hybrid-runtime.md`: readiness and boundary checklist.

The hybrid addenda may narrow implementation choices but cannot weaken the Constitution or formal semantics.

## Cross-feature runtime invariants

- C++ core does not perform network I/O or read wall-clock time.
- C++ native runtime owns single-writer state, WAL and durable recovery.
- Java owns transport, TLS, peers, backpressure, opaque timers and operations—not consensus decisions.
- Python owns worker-local ML and evaluation—not validator state.
- Cross-runtime communication uses canonical bytes and a versioned C ABI.
- Native effects become visible only after durable commit.
- Java-owned memory is borrowed synchronously and never retained by native code.
- Zero-copy is a fast path with mandatory bounded-copy fallback.
- Timer events use opaque tokens and stale-token rejection.
- Every runtime binds the same protocol/schema/formal semantics IDs.
- Embedded FFM and isolated sidecar profiles are tested and reported separately.

## Formal impact classes

- `NONE`: documentation/build change with no protocol-visible behavior.
- `REFINEMENT_ONLY`: implementation choice already representable by accepted formal actions; requires trace/refinement evidence.
- `SEMANTIC`: changes an external action/precondition/outcome/durability/failure rule; must return to 000 and obtain a new Formal GO before code.

ADR-0010 is initially classified `REFINEMENT_ONLY`. Discovery of a new action such as an unmodeled timeout fallback, partial durability outcome or alternate current-state transition automatically reclassifies it as `SEMANTIC` and stops implementation.

## Superseded refs

`003-central-round-coordinator`, `007-adaptive-heterogeneous-scheduling` and `008-permissioned-trust-and-resilience` remain historical only.

## Execution protocol

1. Merge and verify 000.
2. Implement one stacked branch at a time.
3. Read both original feature artifacts and hybrid addenda.
4. Run formal-impact analysis before code and after design changes.
5. Require exact cross-language fixtures before optimizing.
6. Treat unsafe native behavior, pointer lifetime ambiguity, WAL ordering ambiguity or event-loop blocking as STOP defects.
7. Promote only after feature, formal-refinement and runtime-boundary gates pass.
