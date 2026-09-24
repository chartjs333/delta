# Arithmetic binding candidate: no formal authority

These files make amendment `0001-arithmetic-input-binding.md` reviewable through
concrete arithmetic, canonical draft byte graphs and negative design vectors.
They are not a production artifact parser, completed refinement proof, runtime
implementation or new FormalVerificationReport. `DRAFT_NOT_AUTHORITY` and
`formal_go=false` remain explicit in generated evidence.

```text
python -m unittest discover -s formal/proposals -v
python formal/proposals/arithmetic_binding.py
python formal/proposals/check_cross_language.py --help
lean formal/proposals/ArithmeticBinding.lean
```

`arithmetic_binding.py` covers half ties, weighted accumulation, conversion
quantum, checked prefixes, model/optimizer state and domain-separated value bytes.
`native_binding.py` adds an exact content-addressed graph rooted in a separately
supplied native anchor. Its fixture has two domains, two shards, positive/negative
half ties and yields `model=[19,-21]`, `optimizer=[2,0]`.

Draft graph bytes are bounded ASCII canonical JSON with the domain separator
`deltareduce.000.arithmetic-binding.draft1` followed by NUL. Exact type, length,
hash, schema coverage, q-shard commitments, context and result checks are required.
ISC/EC/APC/Aggregate projections assume independently verified certificates.
This assumption is not a signature verifier or a production certificate codec.

The native authority arguments must ultimately be resolved from native durable
state. Passing both a candidate and its claimed authority from one untrusted
command would not establish binding. This proposal does not implement that
resolver, a WAL, a durable receipt or a QC.

The independent C++ arithmetic oracle matched Python on 1,012 cases under GCC
and UBSan. This checks arithmetic rather than complete runtime/canonical graph
conformance. The standalone Lean file has 15 checked helper statements with only
declared standard axioms; it does not discharge the complete binding obligation.

Production TLA+ modules in this candidate now compute bounded PARAMETER/APPLY
results from native input constants instead of expected-result constants. Their
current scope is one coordinate per shard with uniform q/weights. All 20 safety
and 7 liveness configurations and 14 production-source mutants passed, but the
public trace witness, arbitrary-vector proof and lifecycle binding remain open.

Self-review found two material migration issues:

- Per-domain rounding before mixture differs from mixing exact rationals first.
  For `1/2` and `-1/2` with equal weights, the candidate's result is 1 rather than 0.
  The selected operation order requires new formal authority.
- The candidate explicitly selects `FULL_SIGNED_INT64`, including exact
  `INT64_MIN / 1`. The existing native helper rejects that case by bounding an
  unsigned quotient by `INT64_MAX`. This is a migration issue, not permission to
  change runtime under the old report.

The source semantics have changed. The old `cc98f15a...` GO is historical evidence
for its own merged source only; it cannot authorize this candidate. No independent
reviewer attestations were fabricated. See `docs/feature010-progress.md` for the
executed checks and remaining obligations. PR50's PARAMETER/APPLY guard remains
until complete, reviewed and merged new formal authority exists.

## September 24: ordered arithmetic kernel (T044, T048, T049)

`formal/proofs/DeltaReduce/ArithmeticKernel.lean` is now imported by the mandatory
project and registered as PO-A4 with 13 axiom-audited conjuncts. Unlike the earlier
standalone helpers, the checked fold proves acceptance/rejection for arbitrary
ordered lists, products and every prefix, with independent signed intervals.
Quantum conversion checks the specified product order and a separate output
interval. Concrete theorems include INT64_MIN and positive/negative half ties.

The scoped offline runner compiles this exact module using Lean/Std, audits each
theorem, then removes five guards/rounding rules from the same source. Original
proofs reject every mutation; separately compiled concrete witness theorems show
the resulting incorrect acceptance or rounding. Evidence is retained in
`formal/proposals/evidence/arithmetic-kernel.json`.

```powershell
python formal/scripts/check_arithmetic_kernel.py `
  --lean D:/delta/formal/toolchain/windows/lean-4.32.1-windows/bin/lean.exe `
  --archive D:/delta/formal/toolchain/cache/lean-4.32.1-windows.zip `
  --platform windows --output formal/proposals/evidence/arithmetic-kernel.json
```

This is not a successful full Lake/mathlib build. PO-AB1 remains open, including
coefficient derivation and connection from authenticated bytes to this operation
graph. TLA still has its documented uniform-input finite scope. No runtime guard,
native decoder, certificate authority or benchmark qualification changed.
