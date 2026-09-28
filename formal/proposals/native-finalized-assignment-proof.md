# Correct finalized-certificate assignment checks

Tasks T044/T048/T053/T054/T056/T057; amendment 0001. NO_GO remains.

The preceding original aggregate binding had an unsatisfiable condition for
every nonempty finalized PARAMETER corpus. `NativeCertifiedCorpus.LeafChecks`
called `NativeVectorAuthority.AssignmentChecks`, which requires a nonempty
proposed-vote context. The actual finalized certificate decoder sets that field
to the empty list: the certificate wire has no such field. Thus its conditional
success theorems did not establish an executable positive finalized-corpus path.
Earlier component/encoding examples did not exercise this join. The prior
evidence is retained as historical evidence, not treated as a successful run.

`NativeFinalizedAssignment.decodedContext` and `originalContext` derive the empty
field from the actual decoder and executed finalized lineage check.
`proposedPredicateImpossible` proves the conflict for every checked finalized
edge and every vector bound/assignment, not just one fixture.

The corrected corpus calls a distinct finalized-certificate predicate. It checks
the original empty field, full native certificate context, all ISC/EC/PLAN IDs
and denominator. The computed assignment context stays in the computed body; it
is not copied into or claimed to occur in the original certificate. The existing
frame, domain, shard ordinal, full computed body, ordered corpus, full Q leaves,
native computation and exact decimal checks remain. This neither relaxes native
admission nor proves these stronger projection checks equivalent to it. Original
native certificate/proposed IDs and preimages remain distinct.

`leafFromComponents` reconstructs the real corrected executable leaf checker
from its exact ordinal, vector join, original Q extraction and field/body checks.
The successful checker proves the empty source context; independently, actual
finalized lineage derives the same property for every loaded ROOT leaf. No
proposed-body lookup, fresh-vote admission or future APPLY is added to that path.

Regression examples reuse the pinned original finalized parser/check and hash
proofs, show the former predicate impossible for any assignment, and exercise
the corrected field predicate positively on that exact certificate. Mutations
of native context, each parent, denominator and fabricated vote context reject.
These are component proofs, not a new positive whole vector/corpus/ROOT run.
The independent Python check compares the original certificate/proposal payloads
and schema inventories: only the proposal carries `vote_context_id`.

No full raw positive original/draft corpus execution is claimed. ROOT public body,
nonempty ABORT lineage, shared source/configuration/unit/alias authentication,
complete public durable sets, all-actor sequences and phase/send/delivery/QC/
current/crash/unknown/repair/persist-before-expose refinement remain open.
Concrete bounded codec/hash/exporter resources, native decimal compatibility,
arbitrary snapshots, contract freeze, offline reproduction and independent review
remain required. No new native capture, runtime/guard change, local PASS or GO.
