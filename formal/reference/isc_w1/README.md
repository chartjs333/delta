# W1 local storage reference

`REFERENCE_ONLY_NOT_PRODUCTION` — ISC-S16-B01 / T016 / T053 / HR008-001/002/018.

This standalone Python experiment implements the approved local DRW1/W1 byte
framing from `docs/adr/0014-isc-finalization-wal-capsule-v1.md`. It is deliberately
outside every production target and the mandatory TLA/Lean semantic source set.
The controlling task is the HTTP-assigned ISC-S16-B01 and the continuous sprint's
lane task; the historical pipelined lane describes the quarantined directory.

Run from the repository root:

```text
python -m unittest discover -s formal/reference/isc_w1 -p "test_*.py" -v
```

`codec.py` encodes and decodes the original big-endian DRW1 frame, all four kind-3
sections, fixed local section headers, lengths/counts, checksums and physical slot.
Kind 1 preserves its four opaque payloads; kind 2 preserves its vote payload
and original opaque fourth field, requiring only state/effects to be empty.
The native runtime writes its 64 ASCII hex admission-policy digest into that
fourth field; framing alone does not establish the policy binding. Policy, certificate and existing
nested envelope bounds are checked before copying their fields. The necessary
16 MiB receipt/effect/certificate payload sum is checked without inventing the
consolidated draft's result wire format. Arbitrary noncanonical nested payloads
remain opaque: framing success is explicitly not a native admission result.

`harness.py` appends exact frames to a newly created test file, calls actual file
fsync, retains a complete structural snapshot and returns bytes only after the
barrier. It checks original IFQ1 prefix length/hash and every physical slot. A
fresh scan reads all kinds; kind 2 alone increments the diagnostic vote count.
Replay takes the exact original frame at its physical slot and returns its original
four sections without appending. It does not reconstruct a request-ID namespace,
compute b/c, choose a signer set, or implement semantic FinalizeISC replay.

Injected cuts cover before append, partial append, complete append before barrier,
barrier failure and barrier completion before exposure. A write attempt that fails
fences that handle until close/reopen. Reopen requires an existing file, checks the
entire file and optional independently retained exact prefix floor, then performs
a new file barrier. Complete surviving frames retain their original slot and bytes.
Torn, corrupt, unknown-kind or inconsistent data is never truncated, skipped or
repaired. An empty/missing file is not authenticated proof of an absent write.

All fixtures are public synthetic opaque bytes. Checksums prove integrity only.
The caller must separately provide authoritative source/epoch/keys, semantic pins,
canonical nested codecs, full source inventory, quorum/signature checks, P0→P1
recomputation and exact output identity checks before any production admission.
The optional byte floor does not authenticate itself. The harness does not claim
directory durability, adversarial path binding, concurrent writer exclusion,
process/power-loss behavior, native crash isolation or production recovery (R3).
Single-writer temporary test files are its execution environment.

No draft numeric evidence budgets, deployment semantics ID, new authority,
production integration, guard removal, R2.3/R3, TLA/Lean theorem or Formal GO is
introduced. The accepted historical formal ID cannot authorize the pending ISC
amendment; this reference task is not an implementation task in features 001–011.
Historical B01 results and source hashes remain in `evidence.json`; later source
qualification corrections have separate receipts and do not relabel that evidence.
