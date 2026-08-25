# Checklist: 001 Hybrid Runtime Foundation

- [x] Python/PyTorch remains the owner of scientific baseline and worker-local ML execution.
- [x] C++ consensus and Java transport implementation are not pulled into feature 001.
- [x] Runtime-neutral canonical artifacts are introduced before cross-language code.
- [x] No in-memory language layout is treated as a wire or hash format.
- [x] Formal GO merge and compatibility verification are explicit hard prerequisites.
- [x] The hybrid decision is classified as refinement-only unless implementation discovers a semantic mismatch.
- [x] Placeholder directories cannot be used to implement later feature behavior early.
- [x] Cross-language dependency direction and safe serialization are testable.
