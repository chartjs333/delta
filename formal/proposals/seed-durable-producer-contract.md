# Seed producer durability — selected isolated reference binding

T047/T053, standing scope 3, 27 October 2026. Selected for implementation under
the existing delegation, not a new authority or production storage format.
R2.3 OPEN / Formal NO_GO. This completes the persistence choice of
`seed-agreement-contract.md`; it is not another independent DoD obligation.

Reuse the approved Profile T single-writer, stable-prefix/barrier and custody
primitive, as the EC companion does. One `PROFILE-SEED-PRODUCER-V1` companion
is separate from original native WAL slots and vote ordinals. No old bytes,
identities, sequence numbers, signatures or QC are rewritten. An original
legacy history without this producer is not retrospectively certified by it.

The companion contains RECEIVE, INTENT and SIGNED records. Every raw received
occurrence, including duplicates and invalid bytes, is retained in its original
order. RECEIVE records become usable knowledge only after barrier and commit.
INTENT binds exact unsigned body bytes and the complete committed knowledge
prefix. Agreement intents execute the existing view/no-double-intent/highest-
prepared guards. An OPEN intent additionally binds the three original COMMIT
witness IDs and requires the opened original DEAL in their agreed selection.
DEAL and OPEN algebra is checked before signing, without manufacturing a
signature. Honest DEAL/OPEN creation uses the existing-key deterministic
generation already selected; public proof validation alone does not prove that
private honest algorithm was followed.

Only a committed, durable INTENT permits its exact body to be signed. SIGNED
binds that intent ordinal to the original, concretely verified envelope and
exact body. SIGNED itself requires append, barrier and commit before exposure.
It then also enters knowledge as a distinct self-store occurrence. An exact
retry references the original INTENT/SIGNED ordinal and allocates no record;
repeated external delivery/exposure remains a separate source occurrence.
Neither arbitrary same-key signatures nor a supplied `durable` flag authorize
an effect. A conflicting body at an existing intent key fails before append.

Records reuse strict Profile canonical ASCII JSON and framing
`u32BE(body length) || body || SHA256(domain || body)`, with domain
`deltareduce.profile.seed-producer.record.v1` followed by NUL. Fields are exactly
`type_name`, `schema_version="1"`, `profile_id` (existing Profile v1 literal),
`bootstrap_id`, `actor_id`, `instance_id`, `ordinal`, `previous_record_id`,
`payload_raw_id`, `payload_bytes`, `knowledge_count`, `knowledge_id`,
`intent_ordinal`, and `commit_ids`. The type is RECEIVE/INTENT/SIGNED.
Instance ID hashes canonical seed instance under
`deltareduce.profile.seed-producer.instance.v1` plus NUL. Knowledge ID hashes
the domain `deltareduce.profile.seed-producer.knowledge.v1` plus NUL, count BE64,
then every ordered length BE64 and original envelope, including rejected ones.
Payload references resolve against the complete existing retained artifact
inventory, with recomputed raw SHA256 and byte length. Bodies/envelopes are not
hex-duplicated inline in the journal. `intent_ordinal` is zero except SIGNED;
`commit_ids` is empty except an OPEN INTENT. Ordinals start at one, predecessor
is GENESIS then the exact preceding companion record ID. No extra source cap is
introduced: the existing complete Profile byte/event/record budgets still apply.

The executable primitive model starts with an empty companion and records the
whole original native WAL unchanged. Append validates the next candidate before
changing its volatile buffer. Barrier makes the whole validated buffer stable;
commit derives caches by replay of complete records from empty. Signing and
exposure only consult committed state. Crash preserves all stable bytes and
may leave any bytes inside the attempted write extent, including a torn tail.
Recovery independently replays the entire surviving journal and retained payload
inventory. The retained original producing trace must also bind the pre-crash
stable prefix and attempted write; a different parseable record is not a lawful
substitute. Complete valid surviving original records require a new barrier/commit before
use; torn, conflicting or unknown tails remain retained and BLOCKED. Recovery
never deletes the tail or silently restarts from an empty/shorter history.

Review correction (same selected semantics): the original unresolved base and
attempted write remain fixed through repeated crashes, BLOCKED states, verified
recovery and its barrier. They are released only by successful verified commit.
Neither a second crash nor a parsing success promotes an unknown surviving tail
to a new stable origin. `seed-review-20261027-architecture.md` preserves the
concrete failing pre-correction reference trace; no production history is claimed.

The concrete machine proves only this existing T-primitive binding. Its public
constructor, hash or structurally valid journal is not a source capability.
The enclosing complete producing fold must associate every append/barrier/
commit/sign/expose/crash with original indexed source occurrences and the same
independent bootstrap/T journal inventory. It must preserve all other original
events and bind ISC finality and logical view progress. No clock, timeout,
external source, filesystem implementation or production readiness is created.

Required checks within this binding: premature signing/exposure/opening; exact
retry and conflicting retry; all crash cuts including a complete unacknowledged
record and arbitrary torn tail; post-recovery old-view/double-intent rejection;
whole retained occurrence/payload coverage; unchanged native WAL. Cross-view
agreement and the full source/refinement join are not implied by those checks.
