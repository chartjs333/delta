# ISC-S16-D01: selected arithmetic-unit source component

9 October 2026. T047/T053, ISC-S16-D01. **R2.3 OPEN / Formal NO_GO.**

The existing assignment is `13069d7e-a148-475a-bd49-9885bf2f283d`, role 2753,
branch `agent/isc-s16-formal-linkage`, base
`9f4d23b11fd1fa26586bce6fd8826c657fdfb0d1`. Effective scope revision 15 selects
the exact contract in `arithmetic-unit-source-binding-v1.md` at that base;
its specification-only scope-14 wording remains historical. The effective core
SHA256 is `5a5a6b8f8f68e09eab45a46904e0c304b6812922cc965ca3bb0b99d53ecc02d6`.
The decision-source Git blob SHA256 is
`4f106f712efb8c0294b1b499aa9e800d4c7d576fe6f1d909d46eb4ec5419659b`.

Authenticated fresh GET, exact returned `scope_context` plus outer
`schema_version: 1`, and a confirming GET establish ACK
`scope-ack-3af86533ad045e34125ea0b923d80680`. The POST transport timed out;
GET confirmed the accepted acknowledgement and exact context, so it was not
sent again. The DPAPI role wrapper kept the credential in its HTTP header.
No credential, request headers, restart, reimport or graph transition is part
of this source/evidence. No subagent was used.

## Exact local statements and the remaining recovery dependency

`ProfileArithmeticUnits.decodeNumeric` parses the seven fields of the complete
original R bytes, with the existing native rational and domain-weight rules and
the selected positive reduced I64 quantum. `numericSource` concludes the exact
lexer result, all numeric predicates, actual byte bound and whole canonical
byte equality. `sourceNumbersUnique` and `sourceQuantumUnique` derive uniqueness
from that deterministic parser; no chosen output or candidate profile is an input.
`initialSource` does the corresponding job for U, including its parameter schema.

`selectedSource` checks an original P against the complete P bytes computed from
that decoded R, the supplied original proof ID and selected semantics. Its
conclusions include every retained numeric field, that exact proof reference,
the original P bytes and the domain-separated bounded native identity.
`legacyGenerationRejected` proves that no source/proof/P combination can select
the legacy semantics ID for this generation. No future ID is chosen here.
`selectedNumbersUnique` shows that two successful selections for the same
R/proof/semantics cannot choose different numeric values or original P bytes.
These are byte-selection statements. They **do not establish that a supplied
proof ID came from a legally produced original APC**.

`numericComplete` explicitly requires the fixed-field lexer's successful parse.
It is the converse of the checked conjunction, not yet a universal theorem that
every valid typed R round-trips through that lexer. The fixed positive and
negative kernel vectors are examples, not a substitute for that universal result.

The required registry theorem remains
`DeltaReduce.nativeArithmeticRecoveryRefines`, PO-AB1's
`admission-recovery-refinement` conjunct. Its full required content is unchanged
from `isc-s16-recovery-prerequisite-checkpoint.md`: same complete source-bound
R2 relation at initial/recovered cuts; every original transition represented
by the formal action or permitted stutter; certified current, complete retained
records and exact historical retries preserved; unknown/durable/unexposed/
delivered states distinguished. No declaration under that name is added here.

## Dependency classification

| Class | Current conclusion |
|---|---|
| Existing checked components | Original-domain R1/R2.1/R2.2 arithmetic and constructor results remain closed for their original premises. Original configuration, storage, signature, collection and journal components remain available with their stated boundaries. |
| New local component | Strict Python U/R/P codecs, P derivation, schema-3 DRC1 codec and config parent-unit conjunct; executable Lean U/R parsing and R/proof/P selection. The new receipt identifies exact checked source bytes and all limitations. |
| Permitted external primitives | Previously approved independent bootstrap/floor and enrolled fixed-epoch authority, original byte custody, hash/codec/signature assumptions and durability primitives. This work adds none. |
| Still open | Whole initial/genesis legality and independently derived parent-unit association; original configuration producer/finality plus complete original APC/proof/config join; all current/history and source collections, incomplete/loss/ABORT cases, total family relation and affected qualification. |

**R2.3 is still required.** Scope 15 now permits implementing the selected source
binding inside that existing obligation. No further source-domain or trust
authority change has been inferred. Future-generation model guards and their
qualification remain necessary under the approved contract; old production
`Init/Next` evidence cannot qualify the new predicates. No production artifact,
old object, QC, WAL identity, concrete semantics ID or numeric deployment quantum
is changed or selected.

## Bounded next composition

The new files are `formal/reference/profile_source/arithmetic_units.py`,
`configuration_units.py`, `test_arithmetic_units.py`,
`formal/proposals/b-family-transfer/ProfileArithmeticUnits.lean` and
`check_arithmetic_units.py`. The existing Python `configuration.py` now exposes
the shared original-field checks; each generation still has its own closed
field set and exact version check. No decoder rewrites a schema-2 object as
schema 3 or infers a quantum for an old profile.

Next, join these exact bytes to `ProfileOrigin`/`ProfileImport`, the schema-3
configuration authority and original APC/accumulator proof, then the complete
original current prefix. Preserve initial/config-without-APC states, historical
retries, every source occurrence and unavailable/ABORT lineage. The residual is
the same three frozen R2.3 obligations; a codec receipt does not close them.

Required checks remain exact source/byte/range negatives, Lean kernel and axiom
audit, original-generation regression, complete source/family applicability,
affected model/production-mutant/refinement/compatibility gates and two process
reviews. Neither ACK nor this component permits D01→Q01 advancement. The known
missing-theorem FAIL remains a gate; authorization permits repairing its cause.
There is no graph result or independent Formal GO attestation in this checkpoint.

## Component verification

`evidence/profile-arithmetic-units/receipt.json` records 16 kernel-evaluated
vectors, the full declaration axiom audit and 63 successful commands over 161
exact source/generated-file hashes. The audit uses only `propext`,
`Classical.choice` and `Quot.sound`. The 11 focused unit/configuration tests,
22 existing configuration-module tests and complete 140-test profile-source
regression pass. The earlier combined default-`decide` vector invocation timed
out at 300 seconds and is explicitly retained as TIMEOUT, not PASS. Final
vectors use identical byte values as explicit byte lists and `decide +kernel`,
checked individually; no `native_decide` or evaluation axiom is used.

Baseline phase0, all 778 formal contract tests and toolchain lock checks pass.
The unchanged Makefile gate commands then ran in a source copy: parse, all 28
safety configurations and all 7 liveness configurations pass. The first proof
attempt correctly rejected a dependency-cache junction outside that workspace.
With physical copies of the same pinned dependencies, the Lean build passes;
the proof evidence gate returns **FAIL**, with 44 of 45 conjuncts verified:

- `PO-AB1:admission-recovery-refinement` is missing
  `DeltaReduce.nativeArithmeticRecoveryRefines`;
- that declaration's axiom dependency result is also missing.

The subsequent mutant/refinement/report commands were not run after this
failure. `evidence/profile-arithmetic-units/baseline-checks.json` binds the new
results to exact inputs and logs, including the failed environment attempt.
Historical reports remain unchanged. These unchanged-generation checks do not
qualify the new source-generation model guards, full R2.3 or the named recovery
theorem. The assignment remains active; no graph outcome has been submitted.
