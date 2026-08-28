# Canonical fixed-point and shard encoding v1

`int16-fixed-v1` is the only DeltaReduce v1 consensus contribution profile. Its immutable rules
are:

- q range is symmetric `[-32767, 32767]`; the raw INT16 value `-32768` is invalid;
- each canonical parameter segment has one RoundConfig-fixed reduced positive rational quantum
  `numerator / denominator`; worker-local or block-local dynamic scales are invalid;
- canonical normalized source values are reduced rationals with a signed INT64 decimal numerator
  and a positive UINT32 denominator; zero is exactly `{numerator:"0", denominator:1}`;
- `q = round_ties_even(source / quantum)` with sign applied after rounding the magnitude;
- both `abs(source.numerator) * quantum.denominator` and
  `source.denominator * quantum.numerator` must fit signed INT64 before division;
- q values are two-byte signed two's-complement integers in little-endian order;
- range excess, intermediate overflow, non-finite adapter input and any malformed rational reject;
  saturation, wraparound and q-to-float reduction are forbidden;
- residual/error-feedback fields are not part of this version and therefore reject as unknown
  critical data.

## DRQ1 envelope

All integer fields in the fixed prefix are unsigned little-endian. The prefix is exactly 16 bytes:

```text
offset  size  value
0       4     ASCII "DRQ1"
4       2     major = 1
6       2     minor = 0
8       4     canonical JSON header byte length
12      4     payload byte length
```

The prefix is followed by the exact RFC 8785-compatible DeltaReduce canonical JSON header bytes
(UTF-8, sorted keys, no insignificant whitespace, finite JSON values only) and then the raw INT16
payload. Header length is at most 65,536 bytes, payload length at most 1,048,576 bytes, and a plan
contains at most 4,096 shards. The parser validates prefix arithmetic, all context identifiers,
canonical header bytes, element range, `payload_length == 2 * element_count`, payload hash and the
absence of trailing bytes before exposing payload.

## Content identities

Content IDs are lowercase `sha256:<64 hex>` over `ASCII(domain) || 0x00 || bytes`.

```text
deltareduce.004.profile.v1
deltareduce.004.scale-table.v1
deltareduce.004.shard-plan.v1
deltareduce.004.proof-instance.v1
deltareduce.004.shard-leaf.v1
deltareduce.004.manifest.v1
```

The ordered Merkle root uses raw 32-byte child hashes and
`SHA256("deltareduce.004.merkle-node.v1" || 0x00 || left || right)`. At every level an odd final
node is duplicated. Empty shard tables are invalid. Reordering therefore changes the root.

## Accumulator selection

The proof instance records `Q`, `A`, `Nmax`, the maximum product `Q*A`, every canonical prefix
bound and the final bound `Nmax*Q*A`. INT64 is selected only when product, every prefix and final
bound are at most `2^63-1`; otherwise portable signed INT128 is selected under the analogous
`2^127-1` bound. Any larger instance rejects. No proof accepts saturation or unchecked arithmetic.

The accepted Lean PO-A1/PO-A2 theorem names and source identity are bound by each proof instance.
PO-A3 remains bound as the canonical rational-coefficient theorem family; it is not claimed as a
proof of the worker ties-to-even rule above, which is checked by independent exact-byte encoders.
