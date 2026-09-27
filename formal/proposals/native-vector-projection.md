# Original vector inputs checked against the draft arithmetic graph

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
`native_vector_projection.py` defines the new proposal profile
`deltareduce.original-vector-inputs.v1-candidate`. It changes no runtime, Lean,
TLA, original fixture or public trace schema. This is an executable content and
arithmetic-input relation, not authenticated admission or recovery refinement.

## Complete original source before projection

`project_inputs` invokes `resolve_plan_available_q` itself. The caller supplies
original APC/observation roots, original bytes and the separately named EC-seed
primitive; it cannot supply decoded Q rows, an expected translated body or an
approval Boolean. The preceding checks resolve all original manifest/schema/
scale/plan/profile/config/proof/DRQ1 bytes, complete eligible membership, actual
final APC weights, original commitment/AC identities and exact leaf coverage.

Every included ticket must share the original parameter schema, worker profile,
proof, config, scale table, shard plan and parent checkpoint. All vector ranges
and quanta agree across tickets. These are explicit projection restrictions,
not a claim of equivalence to every native admission guard. Different ticket
IDs and values remain distinct; no later PARAMETER/aggregate/APPLY is needed.
Original aggregation-step fields stay in the complete source manifests; this
layer does not independently verify worker normalization or actual training.

## Explicit flat-coordinate naming and range relation

For each included parameter in original schema order, a coordinate is named
`<original-name>:<ten-digit-flat-offset>`. The source parameter-name grammar
excludes `:`, and the flat offset comes from its declared shape product. The
profile checks that these labels fit the draft's128-character grammar and are
already strictly sorted; it never sorts values to repair a naming conflict.
An original name longer than117 characters, or names such as `a` and `a.b`
whose derived labels change lexicographic order, are **unrepresentable in this
profile**. They are not newly invalid native schemas. A later more general
naming profile needs its own explicit version and checks.

Each source shard ordinal becomes `s<ten-digit-ordinal>`. Its offset and length
are the original global range. Every interval is positive, consecutive, within
the full coordinate count and tied to the exact parameter and local offset;
gaps, overlaps, reordering, segment substitution and incomplete coverage reject.
Every output coordinate also retains its original parameter, flat offset and
global offset. Tensor-axis memory order is not inferred by this flat relation.

The full source schema remains available with dimensions, dtype, all frozen
declarations, omission policy and tied aliases. Included coordinates follow the
original policy. In the retained original example, `frozen.scale` is omitted
from contributions and `lm_head.weight` aliases `embedding.weight`; neither
becomes an extra update coordinate. This does not prove that actual checkpoint
materialization preserves frozen parameters or implements tied tensor storage.
The draft SCHEMA alone is not an injective encoding of all original schema
metadata. The relation includes the original source identities and preimages;
discarding them loses that information.

The computed SCHEMA/Q_SHARD artifacts use the **existing draft** canonical
format and `deltareduce.000.arithmetic-binding.draft1` hash domain. Their IDs are
different from original004 schema/DRQ1 IDs. The naming profile is a proposed
source-to-draft mapping, not an already authenticated native symbol registry.
Both identity sets remain inspectable; original bytes are never rewritten.

## Full vector arithmetic, with the actual denominator

For every eligible ticket and every source shard the relation constructs the
entire Q_SHARD from the decoded original vector, original ticket/domain, computed
schema/shard reference and exact quantum. Vectors are retained at their original
widths. The original example has36 coordinates in five shards of lengths
`4,8,8,8,8`; this is not the scalar127 TLC path.

Assignments cover the complete eligible domain-by-shard product. Within each
assignment they retain original ticket order, final APC alpha fractions, exact
Q references, quantum and the accumulator proof's **specific** denominator.
There is no minimal-LCM substitution, second multiplication by EC gamma, value
rounding or removal of zero-weight contributions. Coefficients come from the
source proof/weight relation. Every actual coordinate product is checked at the
original product width, and every prefix at the original accumulator width.
The result is also recomputed by the existing draft vector `parameter` oracle.
Draft fraction/denominator/coefficient-sum restrictions remain additional
representability checks; original uint64 fields are not silently narrowed.

The profile caps included coordinates at4096, coordinate×ticket cells at65536,
assignments at4096 and generated draft artifacts at8MiB. Its original resolvers
retain their own bounded source profile. A supplied draft store is separately
limited to4096 entries and8MiB. These are tooling limits, not full native parser
completeness, a new native admission policy or full tensor-model capacity.

## Check the supplied draft graph, and keep its trust limits explicit

`check_draft_inputs` resolves the original source again and constructs the
existing `native_binding.Witness` from a separate draft store, authority reference
and NativeAnchor. It compares the complete computed schema reference, all eligible
ticket/domain rows, every mathematical assignment field, all Q references and
the original accumulator width. It matches original APC round/height/view/epoch
and original manifest parent-checkpoint identity. The ordinary draft graph
loader still checks its full internal parent graph, current hashes, recovery/
deadline prerequisites, assignment coverage and committed Q references.

Then every actual draft PARAMETER computation must agree with the derived source
vector. A new, internally valid and fully rehashed draft graph with changed
schema labels, Q values, quantum, denominator or weights fails the source join.
No supplied equality or finite approval table provides this relation.

**This API checks input correspondence only.** NativeAnchor authentication is a
named independent premise, not satisfied by construction or a hash match.
Original current model/optimizer bytes, full APPLY profile and apply quantum,
assignment vote-context mapping, hard deadline, original-to-draft ISC/EC/APC
identity, primitive EC-seed authenticity, commitment/AC source, signatures,
configuration and producer/build/environment/run/position provenance remain
unclosed. No original current-vector equality follows merely from a matching
parent-checkpoint string. Explicit counterchecks change the draft learning rate,
current model or a valid vote context and still pass this input-only relation.
They demonstrate the remaining boundary, not a new permitted native transition.

## Retained evidence and checks

The first generated example preserves all twelve original004 objects and their
five DRQ1 leaves byte-for-byte; its APC and complete draft wrapper are synthetic.
The second is a **new** synthetic graph with three eligible tickets, two domains,
weights1/3,1/2,0, EC gamma1/7, common denominator12 and36 coordinates per ticket.
Two tickets contribute Q and -Q to the first domain, producing -2Q numerators;
the second domain retains its zero-weight vector and prefix. This example does
not overwrite or authenticate original008 captures or sequences5/6/8. Its
constructed current vectors/profile/contexts are labelled through the example's
synthetic scope; they are not recovered production metadata.

Twenty-four new tests cover all original and draft preimages, exact vector
coverage/values/quanta, original fields and aliases, explicit naming/resource
restrictions, source/APC context and shared-parent mismatches, full target
rehashed substitutions, missing/extra/reordered assignments and anchor guards.
Every coordinate in the multi-ticket example is independently compared with a
Fraction sum. Remaining current/profile/context gaps have positive counterchecks.

```text
python formal/scripts/generate_native_vector_projection.py
python -m unittest discover -s formal/tests -p test_native_vector_projection.py -v
```

Evidence is under `formal/proposals/evidence/native-vector-projection`; complete
source/draft byte examples are in `native-vector-projection-vectors.json`.
No new C++ execution, native exporter, Lean proof/build, production mutant, TLC
run, scalar-model representability or native recovery theorem is claimed.
Existing semantic inputs and semantic identity remain unchanged. Mandatory
`nativeArithmeticRecoveryRefines`, original current/profile/authority provenance,
full64-state phase/send/delivery/QC/current/unknown/repair, general codecs/SHA/
physical WAL/exporter, arbitrary snapshots, contract freeze, offline reproduction
and independent reviews remain required. Runtime STOP is unchanged.
