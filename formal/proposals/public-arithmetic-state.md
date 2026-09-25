# Complete arithmetic state/action replay (candidate)

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060; amendment 0001.
This extends the complete-state proposal; it does not change native runtime
behavior, authorize admission or discharge `nativeArithmeticRecoveryRefines`.

## Immutable input boundary

`derive_public_arithmetic_inputs.py` independently pins the existing native
normal-apply bundle by SHA-256, checks every artifact ID, and invokes the checked
typed graph oracle with its original anchor. It derives a two-shard embedding
from the twelve exact artifact byte strings: ticket order/domain, contributions,
weights, denominator, schema offsets, Q values/quanta, model, optimizer and
arithmetic coefficients. Whole certified PARAMETER bodies are checked before
deriving APPLY. Any changed bundle rejects before writing outputs. The resulting
input manifest records every artifact digest, exact expected bodies and explicit
symbol-to-native mappings. Neither an unpinned input set nor a supplied arithmetic
acceptance Boolean is used.

The generated `DeltaReduceFixtureInputs.tla` and registered configuration bind
their actual immutable values/source. They replace ZeroArithmeticInputs only for
this named replay profile. The complete-state model identity includes the extra
module and exact configuration hash. No existing production operator is edited.

This is a finite mathematical embedding, not a native decoder/execution claim.
The native profile is INT64; TLC uses checked intermediate bounds [-128,127]
within its own integer implementation. This path fits both, but the configuration
does not establish full-width admission/refinement. There is one ticket/domain,
two scalar shards and three honest voters out of four at f=1. Native artifact
hashes and TLA structured model/optimizer values are related by the explicit
manifest, not by a proved cryptographic abstraction. Config/content/storage/seed
symbols retain their abstract-model scope; certificate authenticity is not proved.

## Complete path and original observations

The new path starts at production Init and contains 132 complete states and 131
steps. Each state contains all 64 ProtocolVariables and its full canonical hash
preimage. The generator constructs candidates; the separate locked TLC replay
checks production Init, TypeOK, Next and every named action over exact adjacent
states. Python does not approve a transition or implement a replacement Next.

The path covers configuration, ticket issue/lease/commit, two-shard upload and
availability attestation, AC, input closure/ISC, seed, EC/APC, two PARAMETER QCs,
aggregate QC, APPLY QC and current checkpoint advancement. Every one of the 24
votes has a separate production send and delivery. Thirty-five logical clock
steps align all 36 original public event times. Each actor retains sequences
1..8, including arithmetic sequences 5/6/8; no arithmetic-only renumbering occurs.
PARAMETER produces [1] and [-2]; APPLY produces model [19,-19] and optimizer [2,-2].
Those outputs are independently checked by production arithmetic actions.

The correspondence records old/new state indices and roots. **Old snapshot roots
are incompatible opaque label hashes**, not hashes of these complete states.
They are retained verbatim, never backfilled or silently rewritten. This mapping
therefore does not bind PublicSnapshot's original metadata to these state roots,
nor compose the Lean reachable native journal with the production action relation.
All legacy public fixtures remain honestly scoped. The path has no arithmetic
crash/unknown-append case; the separately rechecked config crash/recovery example
and existing conditional Lean recovery proofs retain their respective scopes.

Three mechanical negative recipes change a PARAMETER numerator, next optimizer,
or advance current before ApplyQC. They recompute valid state hashes and retain
complete prefixes; the actual production action property rejects all three.
These are replay counterchecks, not additions to the production-mutant suite.

## Storage, limits and reproduction

`FIELD_POOL_V1` pools repeated whole variable values by a domain-separated SHA-256
ID. Expansion reconstructs the exact original state preimages; no variable or
substructure is summarized. Every reference/hash is checked and extra, missing,
duplicate, noncanonical or unused values reject. The state profile is unchanged.
The registered arithmetic path needs a 256-observation tooling limit and 250,000
tagged items per complete state; the existing 4 MiB/state and depth-64 bounds
remain. These limits concern evidence tooling, not native admission. Generated
TLA operators intern repeated values without changing their value or bindings.

Reproduce with the pinned Java/TLC environment:

```text
python formal/scripts/derive_public_arithmetic_inputs.py
python formal/scripts/generate_public_arithmetic_vectors.py
python formal/scripts/check_public_state_replay.py --configuration native-arithmetic --vectors formal/proposals/public-arithmetic-vectors.json --output formal/build/public-arithmetic-replay
```

Evidence retains exact generated replay modules/configurations and full TLC logs.
Large negative logs are stored as deterministic gzip; their decompressed SHA-256
must equal the runner's recorded raw log digest. No counterexample is truncated.

## Remaining authority gap

The next integration must bind authenticated complete public snapshots and native
event/command/body/context metadata to this relation, with explicit source/graph
and state-root identities, then compose native replay, global exposure/quorum
and current advancement. Unknown/incomplete durability cannot be represented by
inventing a complete state; authenticated presence/absence and fail-closed scans
remain mandatory. General bounded decoder/hash/exporter/WAL refinement, arbitrary
initial snapshots/availability/failures/repair, contract freeze, offline clean
reproduction and independent review are still open. No new Lean proof is claimed;
the mandatory audit remains 44/45 and formal authority remains NO_GO.
