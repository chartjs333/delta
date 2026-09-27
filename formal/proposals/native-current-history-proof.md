# Original pointer history and canonical current value preimages

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-current-history.json`.

`NativeCurrentValues` parses every original finalized candidate model/optimizer
decimal through the existing native decimal model, then requires exact computed
signed-decimal spelling. It retains original bytes, order, coordinate count and
signed64 bounds. It computes the existing native model/optimizer hash preimages,
including their different domains, NUL separator and trailing semicolons, and
compares both complete content IDs. Empty models, unequal vector lengths,
oversized vectors and non-32-byte digests reject. SHA remains a supplied function,
not a verified implementation or authenticated content service.

This spelling requirement is a stronger projection restriction. The existing
native parser still accepts -00/-01; the new checker rejects them without changing
the raw input. It does not fix native decimal compatibility or native admission.

`NativeCurrentHistory` takes an observed original pointer-WAL and exactly one
original policy/state byte pair per complete record. For every record it executes
the existing complete policy and state decoders, APPLY section checker and
finalized-QC lookup. The command is constructed from that selected certificate,
not supplied as a whole translated object. Original candidate/certificate content
IDs, parent/ROOT/profile relations, threshold checks and 4 MiB guards are retained.
The entire computed pointer record must equal the observed record. Its candidate
parent model and optimizer must match the previous pointer state; its next
model/optimizer IDs must match the original canonical value preimages.

The checker recursively consumes every record and evidence pair in order. It
proves exact ordered record/input retention, linked adjacent states, increasing
heights, individual checked source records, and final state computed from the
whole sequence. Equality of that result with the original WAL decoder's result
is derived by induction over their executions. It is not an assumed equality
between caller-supplied state snapshots. Missing or extra evidence rejects.

The `current` API obtains vectors only from the last checked finalized candidate
and proves their hashes equal the recovered pointer. Known empty or torn-only
history cannot supply initial vectors and returns no current value result.
Unknown observations remain unknown. Existing checksum, duplicate-height,
parent-link and malformed-line rejection is preserved. An unterminated suffix
is retained in the original recovery result; physical truncation, exact storage
presence/absence and provenance of the whole observation remain unproved.

This is a stronger formal candidate checker, not equivalence to current native
recovery. Existing native pointer recovery accepts structurally valid rehashed
IDs without loading their certificates. The prior counterexample remains valid
for that API and is rejected here when historical evidence is absent. The new
parent-optimizer and canonical-value checks are also additional restrictions.
No runtime code or guard is changed.

Source policy/state bytes are fully checked structurally, but their independent
authority and reachability are not established by the caller providing them.
Signatures, configuration custody, initial pointer provenance, historical APPLY
arithmetic correctness and actual persist/flush/repair ordering still need the
general relation. Complete observed records are not proof that the physical
observation is complete. Existing permissive SHA/codec/trust premises are not
replaced with a finite approval table or claimed to be cryptographic authority.

Small kernel cases reuse the prior separately synthetic computed candidate and
finite SHA samples, plus existing synthetic pointer-WAL cases. Placeholder hashes
in the original golden candidate are deliberately rejected. No new positive
full policy/state/WAL-history example, original native capture, full original/
draft Binding or joined execution is instantiated. Current checkpoint IDs use
native value-hash domains, not the draft MODEL/OPTIMIZER artifact hash domains.
Schema, quantum, round configuration and APPLY-profile provenance must still be
derived before constructing that artifact relation; no fixture values fill it.

Full arbitrary-snapshot phase/QC/send/delivery/journal/current/crash/unknown/torn/
repair/WAL refinement, bounded hash/codec/exporter/resources, contract freeze,
clean offline reproduction and independent review remain mandatory.
`nativeArithmeticRecoveryRefines` is missing. No local PASS, qualifying GO,
BenchmarkResultQC or independent attestation follows.
