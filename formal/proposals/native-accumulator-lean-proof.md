# Original accumulator configuration and proof in Lean (candidate)

T044/T048/T053/T054/T056/T057. **NO_GO**, no runtime change.
Evidence: `formal/proposals/evidence/native-accumulator-lean.json`.

`NativeAccumulatorBytes` decodes all twelve original004 configuration fields and
all eighteen proof fields from canonical bytes. The exact ordered theorem-name
array is consumed as required literal metadata; the other fields remain in the
typed wire. General roundtrip, whole-preimage and uniqueness lemmas retain the
entire document. These are bounded ASCII/list parsers, not a native resource or
error-order equivalence proof. `PASS`, historical semantics, historical Lean ID
and matching names are checked metadata, never sufficient mathematical evidence.

`NativeAccumulatorBinding` parses canonical positive/nonnegative decimal values,
including the complete positive INT128 range. The old vote parser is uint64 and
cannot be reused for these bounds. Signs, non-digits, alternate zero/leading-zero
spellings and values beyond the field's precise limit reject. Product width and
accumulator width are checked independently; both accept only64/128.

From actual decoded coefficient bound A and count N it computes P=32767*A and
S=P*N, compares the declared product/prefix, bounds intermediate arithmetic and
requires S<=F<=selected accumulator maximum. General theorems compose these
computed inequalities with `FixedPoint` to prove every bounded signed product
and every subset/prefix sum fits. Actual coefficient/Q/count premises remain
explicit: one manifest is not evidence that a certified multi-ticket plan obeys
them. The exact positive uint64 denominator is retained, without inferred LCM,
quantum or divisibility claims.

F-S is the unique headroom compatible with the native validation equation.
Headroom is absent from the canonical proof: uniqueness does not authenticate a
native caller's observation. Zero and nonzero admissible headroom cases remain
distinct. Bounds for Q sums do not establish conversion/mixture/optimizer safety.

The loader decodes the original configuration/proof, compares all shared fields,
and requires the exact complete immutable004 worker-profile preimage. It hashes
each original domain+NUL+bytes under an explicit UNVERIFIED adapter. The worker
profile uses ties-to-even quantization; it is not the original008 APPLY profile.
`bindCorpus` executes the prior complete manifest/schema/scale/plan/raw-Q loader
and the new proof loader, uses the manifest's actual proof identity, and checks
all original configuration/schema/scale/plan/profile/semantics edges. It does not
take a preapproved corpus or a supplied whole-state translation. General source
and composition lemmas retain every original block and its position/count.

The original config/proof/profile bytes have kernel-checked component preimages,
parser and numeric results. Three exact-preimage hash examples agree with Python
SHA but are SYNTHETIC and not a SHA proof or exporter authentication. There is no
new combined whole-corpus example/native execution. BaseRoundConfig and parent
checkpoint preimages remain absent. Original008's missing accumulator edge is
unchanged. Original-to-draft `LoadedRow`/`RowsBound`/`DerivedParameter`, certified
weights/count/common-denominator conditions, current model/optimizer/APPLY and
general public/native phase/QC/journal/recovery remain open. The mandatory
`nativeArithmeticRecoveryRefines`, native certificate decimal failure, verified
hash/codec/exporter/WAL, contract freeze, clean offline reproduction and independent
reviews are not discharged. Neither local acceptance PASS nor GO is issued.

Reproduce with `python formal/scripts/generate_native_accumulator_lean.py` and
`python -m unittest discover -s formal/tests -p test_native_accumulator_lean.py -v`.
The mandatory `lake --no-cache build DeltaReduce` includes all three new modules;
fresh module compilation and `AxiomAudit.lean` remain required. Aggregate
`make formal-check` is not claimed when make is unavailable.
