# Runtime Profile: 008 Certificates and Apply Consensus

**Primary runtime**: C++ certificate/robust/apply core and native durability runtime  
**Transport runtime**: Java TLS/message delivery, opaque timers and bounded artifact adapters  
**Formal impact**: `REFINEMENT_ONLY`; full certificate graph must match accepted formal semantics exactly

## Native ownership

C++ owns the complete graph:

```text
ISC → SeedTranscript → EC → APC
→ ParameterShardQC → AggregateRootQC
→ ApplyQC → AdvanceCurrentCheckpoint
```

It also owns exact integer/rational norm evidence, trimming, bucketing inputs, fixed-iteration centered clipping, APC coefficients, accumulator revalidation, complete domain×shard coverage, domain mixture and outer optimizer.

Java cannot select members, reveal/generate an unbound seed, alter robust policy, sign a different body, assemble a root, choose `pi_d`, apply momentum or move current state.

## Vote lifecycle

Every certificate vote class uses the same native lifecycle:

```text
prepare canonical body → persist durable vote intent
→ durability barrier → expose signature/frame effect
```

Java sends only the returned canonical frame. Duplicate delivery is idempotent; conflicting body reuse is rejected by native vote context.

## Seed and timers

Java may transport threshold/beacon shares and schedule opaque timers. Native verification binds every share/transcript to ISC/epoch/profile. Timer delivery carries only a token; C++ decides view change, retry, abort or no-op.

## Artifact adapters

Java may execute bounded CAS read/write/repair requests emitted as native effects. It returns content ID, length and typed result through a canonical command. C++ verifies identity and controls certificate/current transitions. Java storage success cannot independently make a checkpoint current.

## Apply boundary

C++ produces exact next model/optimizer bytes or canonical artifact chunks/hashes under `ApplyArithmeticProfile`. Large artifact I/O may be adapter-driven, but ApplyQC/current ordering must remain the accepted formal transaction. Any need for an unmodeled partial-apply state is a semantic STOP.

## Exit additions

- all QC types pass native persist/send/crash/recovery matrix;
- Java message reorder/duplicate/drop does not change finalized bytes;
- early seed, wrong parent, mixed-view and incomplete matrix fail in native verification;
- four native apply validators produce identical artifact/effect/state roots;
- current pointer changes only through valid ApplyQC and idempotent replay;
- full Java+C++ traces pass the feature-000 checker;
- C++ has no network dependency and Java has no robust/apply implementation.
