# ISC-S16 — storage producing-history memo checkpoint

T047/T053. 6 October 2026. **STOP / R2.3 OPEN / Formal NO_GO.**

## 7 October: recheck after the user's disk-full report

The user specifically identified the 6 October E audit as interrupted. Do not
treat the old completion marker alone as evidence or infer that no disk failure
occurred. A fresh full pass completed on `2026-10-07T14:55:27Z`, followed by source,
archive and API checks. See `docs/adr/0017-audit-recheck-after-disk-exhaustion.md`
and `docs/adr/evidence/0017-audit-recheck-20261007.json`.

The exact original object universe, complete reads, candidate hashes/matches and
binary exclusions reproduce. A real metadata reproduction defect was corrected:
the old root list omitted auxiliary tree refs that the actual `--all` scan had
included. The three exact supplementary roots are now recorded, covering the
already scanned 167 blobs and 34 trees. No original search objects were removed
or added; no new source domain or producer rule was introduced.

**E_ABSENT_IN_AVAILABLE_CORPUS is reverified now, on 7 October.** F/O remain
unselected. Original audit documents and evidence are preserved. API at14:55:49Z
retains execution178/scope8/workflow29 and the same assignment, with no matching
new decision. No graph result/review/ACK/amendment or new Pending request was sent.
Do not repeat this completed recheck without a new substantive reason; keep STOP.

## Subsequent direct user request: exhaust E before any F/O choice

Completed the read-only contract/evidence audit documented in
`docs/adr/0017-existing-storage-producer-audit.md`, with source/corpus evidence in
`docs/adr/evidence/0017-existing-producer-audit.json` and
`docs/adr/evidence/0017-existing-producer-corpus.json`.
**E_ABSENT_IN_AVAILABLE_CORPUS. F and O remain NOT SELECTED.**
The inspected corpus includes all recorded accessible Git histories/remote roots,
worktree HEADs and supplied project evidence, not just native pin N. P2P/CAS,
artifact I/O/journals, benchmark signal producers, demo paths, historical
AvailableQ proofs and generated traces do not establish original physical cuts.
This is not an assertion about an undisclosed external/unreachable artifact.

The addendum separately states F's new factual-history trust/conditional theorem
claim and O's changed observed/certified model and requalification consequences.
Neither is ordinary implementation under general R2.3 authority. No new producer,
predicate, model/schema/proof/runtime or Pending request was created. A new request
with exact E references was authorized only if sufficient E was actually found.
Existing request/history remain intact; unchanged approval of its menu still
selects neither F nor O. Do not re-run the same audit or invent a RESUME.

Final official GET at `2026-10-06T14:20:41Z`: execution178/scope8/workflow29,
same active coordinator assignment, no matching decision for the existing request;
assignments/transitions/scope-control/workflow equal the beginning-of-audit state.
Scope8 ACK was already accepted and GET-confirmed; no duplicate ACK was sent.
The checkpoint JSON now includes this later audit and exact document hashes.

## Earlier scope8 memo checkpoint (preserved)

Scope8's one-document task is complete at
`ff8b8f1e5d538e8969f819512ecc7c4dfc3931ec`, branch
`agent/isc-s16-continuous-sprint`, pushed and remote-verified:

- `docs/adr/0017-storage-producing-history-binding.md`;
- `docs/adr/evidence/0017-storage-producing-history-binding-audit.json`.

Exact ACK `scope-ack-190ebfac12e88037b509574a5f79c8b0` was confirmed by role GET.
The memo maps original storage events and physical cuts to existing actions,
separates local I/O, authentic statements and actual availability, and preserves
AC/ISC after lawful finalization followed by loss. No new producer, observer,
trust assumption, model guard, schema, proof or runtime change was adopted.

Pending request `scope-request-09adbfc8a16275064414fca2743101b1` is persisted
exactly once; POST timed out but official GET confirmed it. Source request is
`ff8b8f1e5d538e8969f819512ecc7c4dfc3931ec:orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-STORAGE-PRODUCER-SEMANTIC-CHOICE.json`.
It asks for an explicit semantic choice through **Edit boundaries**:
E (applicable existing producer/evidence), F (additional factual-history trust,
conditional claim only), or O (availability model/claim redesign).
**Unchanged Approve selects neither F nor O and retains STOP.** Do not invent
the next choice or issue another request merely because this one remains pending
or receives an unchanged approval. General R2.3 authorization remains effective.

GET checkpoint: execution178/scope8/workflow29, same coordinator assignment
`4824b8d9-2e13-4a6f-89d1-917696ff8a43`, active/node. Request registration did not
change execution, assignment or scope. Assignment collection, last transition
and pending transition equal the pre-ACK scope8 snapshot. Full receipt:
`ISC-S16-STORAGE-PRODUCER-MEMO-CHECKPOINT.json`.

No graph result was submitted for the memo: coordinator's allowed RESUME/START
outcomes cannot truthfully represent this STOP. Existing two process reviews
cover worker audit `a2fd1725`, not this memo; neither is independent attestation.
After an actual exact decision, obtain fresh role scope, verify/ACK and follow
the normal graph/review gates. No direct promotion or duplicate old result.

Use only official nginx-qa HTTP state/role APIs at18025; preserve all history,
old objects/QC/WAL, frozen refs and healthy demos. No nginx changes, restart,
reimport, new sprint, subagents, new trust mechanism or automatic R2/R3 work.
