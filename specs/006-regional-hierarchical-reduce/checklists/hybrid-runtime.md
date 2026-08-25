# Checklist: 006 Hierarchical Runtime

- [x] C++ owns topology validation, integer math and QCs.
- [x] Java owns routing only and cannot drop/reweight regions.
- [x] Concrete PO-H1/PO-H2 preconditions are required.
- [x] Hierarchy equals flat bit-for-bit.
- [x] Missing quorum/artifacts cause repair or abort, not partial fallback.
- [x] Intermediate partials remain outside P2P.
