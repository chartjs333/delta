# Original APC coefficients and complete Q bytes in Lean

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-available-q-lean.json`.

`NativePlanQCorpus.bind` calls the actual original policy/state/APC coefficient
loader. For every derived eligible term, in its complete original order, it
calls `NativeAccumulatorBinding.bindCorpus` on the supplied original schema,
scale, shard plan, manifest, profile, configuration, proof and every DRQ1 block.
Neither a decoded corpus, expected translated row nor an approval Boolean is an
input. The zip rejects either unmatched tail and retains zero-weight rows.
General source and position lemmas retain exact original inputs, terms and
complete raw block lists. Rejected EC members remain in the original decoded
certificate source; this is not a reconstruction of the complete frozen ledger.

The manifest ticket/domain, native commitment/AC triple, schema, actual APC
proof ID and configuration must match the original coefficient row. Both loaders
use the same raw digest adapter and same configuration/proof/profile bytes.
`sharedDecodedProof` derives equality of the decoded accumulator from the actual
loader equations and checked proof ID; it does not assume equality of supplied
decoded snapshots or bodies. Hash correctness and provenance remain unverified.

`NativeAvailableQ` checks the exact native first-insert availability primitives:
permitted ticket membership, matching proof/commitment ticket and ID, ordered
unique nonempty required/covered leaf sets, their exact equality, permitted
distinct attesters and a positive matching uint32 threshold. The canonical
required leaf list must be a permutation of the entire manifest leaf list,
preserving exact multiplicity. Manifest range order remains unchanged; availability
content-ID order is separately checked. Equal incomplete caller-supplied required
and covered sets fail this stronger complete-manifest relation.

General proofs retain actual original frame encodings and derive every Q value's
range from signed16 payload decoding, including rejection of -32768. The public
`boundProductFits` and `boundDomainPrefixFits` compose successful source loading
with computed APC coefficients and decoded accumulator widths. Their statements
require actual coordinate lookup equations, not a caller-assumed Q range.
Every selected-domain subset/prefix of positions is bounded, including zero
terms. Coordinate selectors may choose different coordinates per ticket, so this
is an arithmetic bound, not yet equality to one aligned vector reduction.
No second EC gamma multiplication or substitution of a minimal LCM occurs.

## Explicit scope limits

Permission and observation inputs are typed **UNAUTHENTICATED_COMPONENT_INPUT**.
This module does not decode the separately versioned JSON observation envelope
or authenticate its root. Original InputLedger has no manifest field or serialized
commitment preimage: native commitment ID, manifest content ID, Merkle root and
AC ID remain different identities. There is no invented equality between them.
Consistently changing opaque commitment/AC IDs passes the primitive/content
checks; the APC-composed checker additionally binds the original ISC triple,
but cannot authenticate an entirely replaced synthetic history.

Configured tickets, attesters, thresholds, EC-seed data, certificate finality,
source selection and signatures still require independently anchored provenance.
Typed checks neither prove physical/network availability nor execute the native
InputLedger replay/late/conflict/WAL machine. ASCII/255-byte/4096-item constraints
are a stronger proposal profile, not every native parser behavior or error order.
Existing per-document/block resource checks are retained; no new aggregate
allocation/time/native resource-equivalence bound is claimed.

The join shares actual proof/config/schema, but cross-ticket parent checkpoint,
scale/plan/range/quantum compatibility and full original-to-draft vector
`LoadedRow`/`RowsBound`/`DerivedParameter` composition remain the next stage.
No original current/model/optimizer/APPLY source authority follows from these
inputs. The original008 missing proof stays missing; no original capture or
sequence5/6/8 is rewritten. Full public/native phase/send/delivery/QC/current/
crash/unknown/torn/repair recovery, verified codecs/hash/exporter/physical WAL,
arbitrary snapshots, contract freeze, clean offline reproduction and independent
review remain open. The native certificate -00/-01 compatibility failure remains.
No helper discharges `nativeArithmeticRecoveryRefines`, changes the runtime guard,
issues local PASS/GO or constitutes independent attestation.

## Kernel evidence and reproduction

Twenty typed primitive/coverage pairs include all17 retained unchanged native
InputLedger component observations and three extra whole-set mutations. Each
predicate is checked separately, so rejected primitives do not disguise missing
source coverage. Opaque-ID positive counterchecks expose the provenance gap.
Five original block range theorems reuse the prior kernel-checked whole manifest,
not new copies of its bytes; one product example combines an original payload
with the separately synthetic coefficient4. Other cases reject absent block/
coordinate/input tails and cover signed endpoints. There are55 named component
theorems; no new combined whole-policy/manifest/proof execution or native run.

```text
python formal/scripts/generate_native_available_q_lean.py
python -m unittest discover -s formal/tests -p test_native_available_q_lean.py -v
```

From `formal/proofs`, using the pinned Lean toolchain:

```text
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeAvailableQ.lean
lake --no-cache env lean DeltaReduce/NativePlanQCorpus.lean
lake --no-cache env lean DeltaReduce/NativeAvailableQVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Only final stable-source checks are retained. Draft membership proofs initially
reduced entire block structures unnecessarily; direct positional membership
witnesses reuse checked components instead. No expanded fixture corpus is needed.
