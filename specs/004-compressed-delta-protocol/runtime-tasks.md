# Hybrid Runtime Tasks: 004 Fixed-Point Delta Protocol

- [x] **HR004-001** Bind exact merged feature-003 evidence, the accepted formal semantics ID and
  PO-A1/PO-A2 plus the rational-coefficient-only PO-A3 boundary before production source.
- [x] **HR004-002** Freeze `int16-fixed-v1` scale/rounding/endian/range profile in `delta-protocol`.
- [x] **HR004-003** Implement portable C++ reference encoder and checked accumulator helpers.
- [x] **HR004-004** Implement deterministic shard plan/envelope writer and bounded streaming reader.
- [x] **HR004-005** Generate concrete theorem-precondition evidence for maximum-safe and first-unsafe profiles.
- [x] **HR004-006** Add Python independent fixture generation from feature-002 normalized inputs.
- [x] **HR004-007** Add Java FFM/direct/copy byte-preservation and malformed-envelope conformance tests.
- [x] **HR004-008** Add GCC/Clang, x86_64/aarch64 where available, endian and signed-boundary golden vectors.
- [x] **HR004-009** Add ASan/UBSan, parser libFuzzer and allocation-limit corpus.
- [x] **HR004-010** Add architecture test rejecting FP contribution formats, per-worker scales and q-to-float consensus conversion.
- [x] **HR004-011** Rerun feature-003 bit-identity/refinement traces through direct q streaming.
- [ ] **HR004-012** Publish profile, proof-instance, compiler, parser and cross-language evidence.

## STOP rule

Any new consensus rounding rule, accepted floating contribution path, worker-selected lattice,
silent saturation, unmodeled durability outcome or residual transaction semantics is `SEMANTIC`:
stop, amend feature 000 and obtain a compatible Formal GO before implementation.
