# Certificate and Apply Operations

Feature 008 implements the certificate graph and current-checkpoint decision in native C++.
Operators may route opaque bytes, schedule opaque logical timers and execute validated artifact
effects in Java, but no JVM or Python component is certificate authority.

## Startup and compatibility

Before accepting traffic, verify the runtime descriptor, formal semantics ID
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`, schema registry,
validator epoch and exact RoundConfig-derived requirement matrix. Recover the native vote journal
and current-pointer WAL completely before exposing a sendable vote or processing a proposal.
Unknown media, domain, profile, signer role, epoch, context or parent is a hard rejection.

## Runtime signals

Record counters by stable rejection code and vote class, without logging certificate bodies or
signature material. The minimum useful signals are journal append/barrier failures, recovered and
replayed votes, conflicting durable bodies, stale timer tokens, missing required shard keys,
duplicate/mixed-view roots, accumulator-bound rejection, Apply overflow, artifact repair attempts,
pointer CAS conflict and ApplyQC replay. Alert on any current-pointer command that fails its
ApplyQC binding and on repeated post-ISC availability loss.

## Failure and recovery

Every QC vote follows prepare, persist, durability barrier, expose and send. A crash before the
barrier leaves no sendable vote. After restart, the journal is recovered before new work; an exact
body replays idempotently and a conflicting body for the same context is rejected. A torn
current-pointer WAL tail is truncated to the last complete checksummed record. A durable ApplyQC
command is replayed to repair an uncommitted pointer and becomes a no-op once the same checkpoint,
optimizer and height are current.

Java artifact writes use bounded native commands and effects. Staging or storage success never
chooses current state. Only the native ApplyQC-authorized compare-and-set advances the pointer.

## Rollback

Stop certificate delivery, retain the vote and pointer journals, retain all content-addressed
artifacts referenced by the last valid ApplyQC, and restart the previous binary against the same
formal/schema IDs. Do not delete WAL files, rewrite ISC membership, weaken a distribution policy,
assemble a root from observed leaves, or manually edit the current pointer. If compatibility
identifiers differ, remain stopped and restore a matching binary/configuration set.

## Security boundary

Certificate and effect buffers are bounded before allocation. The borrowed ABI retains no pointer;
the copy ABI owns data only for the synchronous call. Authenticated transport identity is checked
before native delivery, while native verification remains responsible for validator membership,
role, epoch, quorum, lineage, arithmetic and replay safety. Wall-clock time and packet arrival order
are not consensus inputs.

## Feature-009 boundary

This phase does not implement QLoRA, GPU memory budgeting, adapter training, model quality, WAN
performance or convergence claims. Feature 009 may consume only the frozen ApplyQC/current
checkpoint and ticket contracts after this phase reports `PASS`; it may not add certificate
parents, floating-point consensus arithmetic, device-weighted voting or an alternate current-state
path.
