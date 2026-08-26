# Syntactic Traceability and Constitution Vocabulary Check

Syntactic traceability result: **PASS**.

This tool checks identifier presence, registry/set equality, source anchors, fixture cardinality and Constitution vocabulary. It does **not** claim semantic completeness, liveness non-vacuity or proof-statement strength.

| Principle | Result | Evidence boundary |
| --- | --- | --- |
| formal-first | PASS | formal, tla+, theorem |
| replicated-state | PASS | 3f+1, 2f+1, quorum |
| fixed-work | PASS | workticket, immutable, domain |
| integer-arithmetic | PASS | fixed-point, overflow, integer |
| certificate-lineage | PASS | certificate, parent, applyqc |
| failure-semantics | PASS | partition, crash, abort |
| atomic-apply | PASS | current, applyqc, atomic |
| plane-separation | PASS | distribution, worker-local, certified |

Semantic evidence is established separately by executed TLC, Lean, production-mutation and refinement gates. Final Formal GO additionally requires clean offline reproduction and two independent human review records.
