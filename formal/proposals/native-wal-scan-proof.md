# Complete observed-byte WAL scan (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

NativeWalScan composes the exact DRW1 scanHead reader over the entire supplied
byte observation, from an empty prefix. It retains every original complete frame
and typed entry, in order, plus an explicit remaining tail and computed torn
flag. It returns no partial successful result when a complete corrupt frame is
encountered. A truncated header or incomplete declared body retains the exact
unresolved bytes. Nothing is written, truncated, sent or declared READY.

The recursion budget is input length plus one. General proofs show that every
accepted frame strictly decreases remaining byte length, execution derives an
actual checked trace, and every such trace executes with any budget greater than
input length. Sufficient budgets yield identical results; a failed complete scan
derives a reachable corrupt scan head rather than unexplained budget exhaustion.
The trace contains actual scanHead equalities, not assumed prefix/recovered-state
identity or supplied approval flags.

From successful scanning the proof derives the complete original byte partition,
exact consumed prefix and remaining suffix, each piece's decoded canonical bytes
and native size bounds, and the terminal complete/torn condition. Trace results
are unique for the same input and hash function. Complete means all supplied
bytes were consumed; it is not authentication of the supplied file or proof that
the physical WAL contains no further bytes.

Sequence checking remains a separate executable step, as in native Runtime.
It checks all entries from sequence 1, including state commands. Position and
sequence uniqueness follow from successful checks. Reordered, duplicated,
or gapped entries fail sequence validation even when their individual frames
pass structural scanning. Omitting a first/interior entry leaves such a gap;
omitting a complete suffix cannot be detected from the remaining bytes alone.
An apparently complete prefix therefore does not prove authenticated absence.
A typed result may retain a torn tail after
sequence validation; it still does not authorize readiness or truncation.

The general indexed receipt theorem composes a checked stream position with
the actual NativeWalBytes receipt/policy checker. It derives original canonical
receipt/frame/WAL bytes and the receipt's original all-entry sequence. Neither
an invented receipt nor a caller assertion of recovered-state equality supplies
the relation. Policy semantics/provenance and native vote admission remain
unproved; the checker only compares exact provided policy bytes through SHA.

Examples reuse the prior native two-entry history without changing any bytes:
823-byte ISC record at sequence 1 and 2723-byte state-command record at sequence
2. All 3546 bytes are consumed, with the original record order and no tail. The
separate actual 411-byte partial-write observation is retained as torn with zero
consumed bytes. Source-pinned Python checks verify these exact byte partitions
against the unchanged prior Windows native output, including the same original
receipt after the state command. No new native run is claimed.

Smaller separately synthetic examples check complete/empty/multiple records,
short and incomplete tails, corrupt later frames, exact consumed offsets and
sequence substitution. Their constant digest adapter is not a cryptographic
model. The real-byte examples use only finite exact-preimage digest samples;
SHA implementation/collision resistance, native C++ equivalence, filesystem
identity, scan authentication, physical durability and concurrent writes are
outside these proofs. A complete record without a returned receipt remains
distinct from an incomplete observation or authenticated absence.

The mandatory project and axiom audit include both new modules. The general
relation covers arbitrary supplied byte lists under the named hash parameter;
the concrete examples remain finite. Native runtime semantics for state commands,
logical time, request deduplication, vote admission/caches, policy producer and
snapshots are still missing. Next bind the computed entries to those replay
operations and to authenticated full public histories, including crash/unknown,
phase/send/delivery/QC/current behavior. nativeArithmeticRecoveryRefines remains
OPEN. Contract freeze, clean offline reproduction, independent review and joined
profile/GPU/Docker gates remain mandatory. No formal or local GO follows.
