# R2.3 seed reference work checkpoint — 27 October 2026

T047/T053 / ISC-S16-D01. **Active work, R2.3 OPEN, Formal NO_GO.** This is not
a worker result, a new scope request, substantive R2.3 closure or an independent
review. Current technical-rework assignment `e24da198-6836-4614-8005-8b120cc40d7c`, role 2753,
`agent/isc-s16-formal-linkage`. Exact scope revision 3 ACK
`scope-ack-0515366a48c97c9b20e4ac9c5b013c50` was GET-confirmed. Its additional
existing-validator seed purpose resolves the former permission boundary; the
seed proof/source obligations themselves still require work.

The selected component and agreement contracts are in
`seed-pvss-component-contract.md` and `seed-agreement-contract.md`. They use the
original enrolled keys, deterministic private derivation, public encrypted
polynomial-share proofs, a prepared/commit/view-change agreement on encrypted
contributions and release after agreement. No new trust root, external beacon,
runtime, physical WAL kind, existing QC identity or production semantics ID is
introduced. Historical seed shape fixtures are not reclassified as new evidence.

## Concrete reduction inside the existing seed-source obligation

* The reference verifies exact canonical seed-purpose signatures, complete
  context, every encrypted recipient share, both distribution/opening DLEQ
  proofs and reconstruction. Any three original recipients recover the same
  dealer point, including zero evaluations. Lean proves the interpolation and
  response algebra; it does not prove the computational cryptographic premises.
* The agreement evidence checker resolves every reference from the original
  earlier prefix, checks concrete signed proposal/prepare/commit/STATUS bytes,
  carries the highest prepared selection to a new view, and keeps all rejected
  and repeated occurrences. It never retroactively legitimizes a forward ref.
* Deterministic generation reuses the original enrolled Ed25519 seed. It does
  not read production secrets. Synthetic fixtures exercise the specified KDF;
  they are not evidence of actual entropy, a deployed producer or a source run.
* Native seed bytes derive b from the exact original B preimage. They preserve
  the existing schema-2 fields and the exact selected DEAL identities. COMMIT
  witness subsets and reconstruction subsets do not change the resulting native
  transcript bytes/ID. Certificate c cannot be supplied as B.
* Pure producer guards derive highest prepared state from prior original
  evidence, reject a conflicting own intent, reject new old-view signing and
  preserve exact retries. The Lean intent kernel proves retention and absence
  of conflicting accepted bodies from its explicit empty start. The kernel is
  an overapproximation, not a complete byte/protocol/storage-source refinement.
* The selected `PROFILE-SEED-PRODUCER-V1` companion now binds complete RECEIVE,
  INTENT and SIGNED originals, including duplicate/invalid knowledge. The
  primitive machine requires intent barrier/commit before its own signing action
  and a second artifact barrier/commit before exposure. OPEN additionally needs
  an original COMMIT quorum selecting its dealer. Exact retries use existing
  ordinals. Crash/recovery retains complete original bytes and blocks torn or
  foreign tails; original native WAL remains unchanged. The reference private
  producer recomputes the selected existing-key KDF before DEAL/OPEN signing.
* Lean proves the two-barrier transaction kernel and derives the local STATUS
  floor from an empty-start, monotone knowledge/commit/view kernel. The global
  cross-view certificate induction reuses PO-Q1 and explicit local rules; it
  proves no conflicting committed values under those local rules. Deriving ALL
  of these rules from the original authenticated byte/source fold is still open.
  This factor theorem is not represented as full protocol qualification.

Applicable component evidence is recorded in `evidence/profile-seed-pvss` and
`evidence/profile-seed-agreement`. Both receipts explicitly keep R2.3 OPEN.
Their source hashes use Git LF-normalized TEXT; signed/original artifact bytes
are never normalized. This corrects the first receipt's Windows/Git text-hash
portability issue without changing any signed bytes. The initial regression
runner import-path failure is retained; the corrected invocation passed.
No full formal-check, fully composed PBFT safety/progress or complete recovery
result is claimed by these component receipts. The first durability qualification
stopped on a checker line-length error; the error was corrected and the whole
applicable component qualification rerun successfully.

The first component worker result was accepted as NO_GO; architecture reviewer
2791 rejected head `3f51e324` with a concrete repeated-crash counterexample.
nginx-qa returned the task to the worker through its normal rework path. The
review report/log at `f2845349` is preserved. The correction keeps the unresolved
original append base/target across all repeated crashes until verified commit,
adds corresponding regression cases and a Lean origin-retention lemma. The
applicable qualification passed again (receipt SHA256
`9127a99bfbf51710ef537a5606b9dc68de03ec2a0c2e3792756d5f2fd44d7b26`).
The corrected result still requires its normal reviews. This is an in-envelope
technical correction, not a new semantic Pending decision or R2.3 closure.
Same-executor process review is not independent attestation.

## Exact remaining boundary of this checkpoint

The candidate verifier is deliberately NOT an admitted-seed API. Before using
its output in the full source relation, the producer fold must bind the checked
local intent/knowledge/companion machine to original indexed source occurrences,
derive the cross-view local-rule premises from that exact byte fold and preserve
the existing-policy progress obligations. The primitive persist-before-sign/
expose and release guard is checked but is not itself that complete source join. The
complete original source-index/ISC-finalization/clock/context/native-state join
must then establish the input premises for the existing EC/storage components.
Neither signature validity nor a checked seed candidate supplies those facts.

The three frozen R2.3 residuals remain OPEN as complete obligations:
full source/configuration/aliases/units; complete certificate/candidate/current/
environment collections and public state; initial/incomplete and sufficient
ABORT preserving downstream lineage. This work reduces the original seed edge
inside them; it does not replace or expand that list. Continue inside standing
scope, with no new Pending decision for these delegated details. The named
recovery theorem starts only after substantive reviewed R2.3 closure.
