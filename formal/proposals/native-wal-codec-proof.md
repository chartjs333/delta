# DRW1 entry bytes, sequence and receipt/policy binding (candidate)

T044/T048/T049/T053/T057/T060; amendment0001. NO_GO.

NativeWalBytes reads the actual DRW1 fixed header, total size, uint64 sequence,
kind, reserved bytes and all four sized sections. Its checksum adapter receives
every preceding byte, including the final total-size field, without a domain
prefix. Exactly32 checksum bytes are required. Successful decoding derives
canonical input identity; general inverse and injectivity proofs preserve every
field. No expected Entry or approval Boolean is given to the parser. SHA-256,
collision resistance and C++ implementation equivalence are not proved.

The layers remain distinct. Structural entry decoding permits sequence0 and an
empty vote policy field, as native decode_entry does. It requires all four
transition sections nonempty; a vote requires a nonempty command and empty
state/effect sections. scanHead checks native72-byte minimum/64MiB maximum and
classifies a short header before checking its magic. A full header with invalid
magic/size is corrupt; a valid declared size beyond the observed bytes is torn.
Successful scanHead derives exact complete frame boundaries and decoded entry.
This is one scan step, not an authenticated complete-file scan or truncation.
The decoder inverse has a uint32-size precondition; this deliberately differs
from the scanner's tighter64MiB bound. Resource complexity is not proved.

orderedFrom separately checks ALL WAL entries against successive sequence
numbers; a general position theorem derives each sequence. State commands count
alongside votes. This is not RoundState.durable_sequence, vote count or runtime
semantic replay. It does not reconstruct state commands, logical time, request
deduplication, vote admission caches or snapshots. No sequence is renumbered.

bindReceipt composes actual DRW1 decoding and NativeVoteBytes' semantic DVREC001
receipt decoder. It compares exact original frame, sequence, kind and empty
state/effect fields, and the complete startup-policy digest. The policy identity
is64 ASCII lowercase hex bytes of SHA over the entire provided policy, without
the vote ID's sha256: prefix. The proof derives original WAL/receipt/frame bytes
and vote sequence from successful checks. Hashing a policy does not parse it or
authenticate its producer: DVPOL001 semantic decoding and independent initial
policy provenance remain explicit open boundaries. No receipt is newly exposed
or synthesized from a missing response by this comparison API.

Three exact retained native frames are reused: the original ISC vote, the ISC
vote in the separately configured two-entry history, and its state command.
The first two have sequence1; the state command has sequence2. Full field/hash
checks compose with the previously kernel-checked original semantic receipt.
Historical retry keeps that same receipt after the state command. Retained
native observations also contain complete records without returned receipts at
three cuts; the generator verifies exact equality, rather than inferring absence.
These bytes come from the earlier62-observation Windows native run. No new native
run, OS kill, power loss, unknown-outcome resolution or arithmetic admission is
claimed. PARAMETER/APPLY guards stay intact.

Finite examples use exact-preimage digest lookups and reuse the original DRC1
fixture; all other inputs have no digest. Small separate structural/sequence
counterchecks use an explicitly synthetic constant digest adapter. They test
codec branches, not cryptographic collision resistance. Reordered/missing/
duplicate/gapped sequences, forbidden sections, empty policy binding, bad
checksum and scan boundaries reject. Python also rehashes sequence/policy
substitutions and verifies rejection at the appropriate relation. A truncated
diagnostic input remains incomplete; it is not authenticated absent durability.

Run generate_native_wal_lean.py and unittest test_native_wal_lean.py. Generic
proofs and generated examples belong to the mandatory Lean project and axiom
audit. They add no axiom, expected recovered-state equality or assumed native
admission. Full nativeArithmeticRecoveryRefines remains OPEN. Next connect the
whole scan/replay, native state-command/admission/policy/snapshot semantics and
independently authenticated public history, including unknown outcomes and
phase/send/delivery/QC/current changes. Contract freeze, clean offline
reproduction, independent review and joined runtime/profile/GPU/Docker gates
remain required. This stage authorizes no GO or SIMULATED_LOCAL acceptance.
