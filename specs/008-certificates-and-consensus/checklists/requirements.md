# Specification Quality Checklist: 008 Certificates and Consensus

**Reviewed**: 2026-08-23  
**Status**: Specification reconciled — exact predecessor/formal preflight PASS

## Source fidelity

- [x] ISC freezes exact `{T_j,C_j,AC_j}` before randomness.
- [x] EC binds norms, clipping limits and accepted workers/tickets.
- [x] APC binds post-ISC bucketing, iterative centered clipping and scalar weights.
- [x] AggregateRootQC atomically ties every ParameterShardQC.
- [x] ApplyQC certifies domain mixture, momentum and next checkpoint.
- [x] Mandatory Frankenstein mixed-view rejection exit gate is explicit.

## Deterministic arithmetic

- [x] Norm, trimming, clipping, weights, shard sums and apply are integer/rational fixed-point.
- [x] Exact formulas/profiles, iteration count, tie order and rounding are versioned.
- [x] APC/apply coefficients trigger renewed overflow proofs.
- [x] Tolerance-based equality and float fallback are forbidden.

## BFT safety and lineage

- [x] Every certificate has explicit parent roots and `2f+1` signatures.
- [x] Persist-before-sign, epoch/role/signer and replay rules are requirements.
- [x] `SeedAfterInputFreeze`, `ViewAtomicity`, `ApplyUniqueness` and `DomainMixturePreservation` are testable.
- [x] Current checkpoint advances only through ApplyQC.
- [x] Distribution policy strength is explicit.

## Readiness decision

- [x] Independent scenarios cover full chain, robust plan, aggregate, apply and malicious view.
- [x] Limitations of robust filtering are not overstated.
- [x] No unresolved clarification remains; any chain/arithmetic/Frankenstein/ApplyQC failure blocks feature 009.
- [x] Constitution 2.1.0, exact merged feature-007 predecessor and formal semantics ID are explicit.
- [x] C++ is certificate/robust/apply authority; Java is transport/timer/artifact adapter and Python is worker-local.
- [x] Semantic tasks and HR008 obligations have a complete normative task map.
