# Specification Quality Checklist: 006 Hierarchical BFT Integer Reduce

**Reviewed**: 2026-08-23  
**Status**: Specification reconciled — implementation blocked until exact preflight

- [x] Regional/global committees replace central routing authority.
- [x] Regional outputs are integer sums, not floating averages.
- [x] Hierarchical output must equal flat reference bit-for-bit.
- [x] Topology covers each ticket and parameter element exactly once.
- [x] QCs bind topology, input, domain, profile, proof and shard context.
- [x] Missing quorum/region aborts instead of post-freeze exclusion.
- [x] Accumulator proof composes regional and global bounds.
- [x] Intermediate partials are prohibited from P2P distribution.
- [x] Failure/restart/equivocation and WAN behavior are independently testable.
- [x] No unresolved clarification remains; failed exact-equivalence/safety gate blocks feature 007.
