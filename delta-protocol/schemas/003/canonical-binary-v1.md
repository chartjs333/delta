# DeltaReduce feature-003 canonical binary encoding v1

Every feature-003 protocol object is one envelope. Integers are never encoded through host object
layout, locale or floating point.

## Envelope

All multibyte integers are unsigned big-endian.

```text
offset  size  field
0       4     ASCII magic `DRC1`
4       1     encoding major = 1
5       1     encoding minor = 0
6       2     registered type code
8       4     payload byte length
12      n     one canonical typed value; the root value MUST be a map
```

Trailing bytes, an unknown type code, a non-map root, a length mismatch or a non-minimal value are
invalid.

## Typed values

| Tag | Value | Following bytes |
| --- | --- | --- |
| `01` | false | none |
| `02` | true | none |
| `10` | unsigned integer | exactly 8-byte unsigned big-endian |
| `11` | signed integer | exactly 8-byte two's-complement big-endian |
| `20` | byte string | 4-byte length, then bytes |
| `21` | ASCII text | 4-byte length, then bytes |
| `30` | array | 4-byte item count, then encoded values |
| `31` | map | 4-byte pair count, then text key/value pairs |

Map keys are lowercase ASCII schema names, encoded with tag `21`, strictly increasing by raw key
bytes. Duplicate or out-of-order keys are invalid. Schema text values are printable ASCII only.
Empty text/bytes/arrays/maps are encoded with a zero length/count; no alternate empty or integer
encoding exists. Null and floating-point values do not exist in this profile.

Fields declared `u64-decimal` or `i64-decimal` use canonical ASCII decimal text: `0` or a non-zero
digit followed by digits, with one leading `-` only for a negative signed value. `-0`, `+1` and
leading zeros are invalid. This avoids unsigned-host-language ambiguity. Small schema counters
declared `u32` are encoded with tag `10` and MUST fit `0..4294967295`.

## Content IDs

For a registered type, compute:

```text
SHA-256(ASCII(hash_domain) || 00 || complete_envelope)
```

and render lowercase as `sha256:<64 hex>`. The type code and domain are immutable. Hashing payload
bytes without the envelope/domain is invalid.

## Decoder limits

The feature-003 reference limits one envelope to 16 MiB, nesting depth to 32, one collection to
100,000 members and one text/byte value to 4 MiB. Length arithmetic is checked before allocation.
