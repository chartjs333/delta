# ADR0017: audit recheck after reported disk exhaustion

7 October 2026. T047/T053. **Documentary E audit completed/reverified now;
E_ABSENT_IN_AVAILABLE_CORPUS. F/O NOT SELECTED. R2.3 OPEN / Formal NO_GO.**

The user clarified that the disk-full interruption concerned the E audit of
6 October. Its old completion marker was therefore not treated as sufficient
evidence. This check re-established completeness from readable immutable objects;
it does not assert that no earlier disk-full event occurred or reconstruct the
exact time of that event. No old receipt or failure was deleted or relabeled.

## What was rechecked

The original audit is pinned at
`08e86bad8be9b5af3c61e29a2e5f77a4e970374b`. Its document, source audit and corpus
index are retained unchanged. The fresh full pass ran from
`2026-10-07T14:49:28Z` to `2026-10-07T14:55:27Z` (16:49–16:55 Europe/Berlin).

Re-enumeration and full-byte reading covered the original 22,126 blobs, including
22,059 text blobs and the 67 recorded binary exclusions. Every object was read
to its declared length; `git cat-file` exited successfully. All candidate
matches and hashes reproduced exactly. These counts establish coverage of the
rerun, not additional formal progress. No new corpus or source-domain restriction
was substituted for the original one.

The pinned primary source/document hashes and candidate version references were
also checked. Relevant compressed formal logs/graphs decompressed and matched
their saved hashes; presentation/demo ZIP integrity and the retained external
demo bootstrap files were checked. The existing semantic dispositions remain:
local I/O, authenticated statements, generated fault schedules and formal traces
do not supply complete physical storage history at the original cuts. This is
not a new native test, Lean proof, graph review or independent attestation.

## Reproduction defect found and corrected

The first reconstruction from the recorded root list did **not** match the saved
object universe. The old scan used `git rev-list --objects --all`; its root list
recorded heads/remotes/tags plus remote refs and worktree HEADs, but omitted
auxiliary tree refs included by `--all`. This is a reproducibility defect in the
audit metadata, not evidence that those objects were missing from the old scan.

The exact supplemental immutable tree roots are:

- `9a0cdd9a98d7824f41f5ecf111c3d6c47a9038e5`
- `9cc34895e271a15bca9e007b79cb309f4a0f8f19`
- `d0677af957aba077671c1f13e816e1ef3265a3f9`

Their union adds the 167 blobs and 34 trees already present in the original
object inventory. With these roots, the entire object-ID/type/size set matches
that inventory. No object was added to or removed from the original search.
Its saved inventory SHA-256 is
`6c0d2e1952e73b77b137167991fa6a26746b335f4ae3418cdef762eef8f6fece`.

The sole original text-search hit in that supplementary subset is blob
`1309f23f597f31cf1496a9a4b3c4c50544f8f987`,
`presentation-output-20260924/Paper_Discussion_QA_EN.md`: it restates conditional
liveness/artifact availability and distinguishes reduction from distribution.
It supplies no producer contract or original storage observation receipts.

For reproduction, combine the **object IDs** in the original corpus index's
`started_roots.local_refs`, `started_roots.remote_refs`, `extra_roots` and saved
HEAD with the three tree roots above. Traverse that explicit union with
`git rev-list --objects`, inspect object types/sizes, read every blob, and apply
the original recorded patterns. Compare all candidate IDs/hash/match sets,
binary exclusions and coverage totals, not merely a successful process exit.
Future ref names and future `--all` contents must not replace those immutable roots.
The corrected roots and fresh result are recorded in
[the recheck evidence](evidence/0017-audit-recheck-20261007.json).

## Result and stop boundary

The source-search conclusion is reissued on **7 October after this successful
pass**, rather than inferred from the old completion claim. E remains absent
within the recorded accessible corpus; this is not an impossibility claim about
undisclosed external evidence. The detailed candidate analysis and separate F/O
consequences remain in the original
[audit addendum](0017-existing-storage-producer-audit.md).

No sufficient E references were found for a new Pending decision. No F/O choice,
new producer/observer, source predicate, protocol/schema/runtime/proof change,
amendment/ACK, RESUME, duplicate result or review was made. The official API
checkpoint is recorded with the evidence. The earlier statement that this
documentary audit had no graph review remains true. **STOP is preserved.**
