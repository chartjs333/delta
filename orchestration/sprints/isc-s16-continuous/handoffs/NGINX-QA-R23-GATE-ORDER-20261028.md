# Developer case: downstream proof used to stop its R2.3 prerequisite

T047/T053 / ISC-S16-D01. 28 October 2026.
Classification: **confirmed executor ordering defect; nginx-qa backend defect
not demonstrated**. This is a developer handoff and coordinator input, not an
instruction to patch/deploy nginx-qa or weaken Delta gates.

## Reproduction and evidence

1. Existing project 9000 / sprint `sprint-0001-fada895e` runs `legacy_sequential`.
   Fresh observability: revision 85, active `formal-linkage`, assignment
   `2fd81f70-bb27-4872-a09c-8a712c0e2311`, no backend blocked reason or pending
   attention gate. Scope3 is acknowledged and its exact core hash is
   `9b7dd90ad3ddaa6ab6ad79f26dea32ab4be401038ec4ea266ba5deb3bdfd47f7`.
2. That effective scope requires substantive reviewed R2.3 closure **before**
   `DeltaReduce.nativeArithmeticRecoveryRefines`. The prerequisite checkpoint
   explains why the named theorem needs the full source-to-family relation.
3. At `e0d0e65b9e4bfe5b87b9f86dc7f0666619f3b564`, fresh component qualification
   passed, then the unchanged aggregate formal-check recipes reached proofs.
   Proofs failed because the downstream declaration and its axiom result are
   absent. Exact preserved result SHA256:
   `c62617f2afb9ae692e6583783bb441843798f9bebb01c957d11ed0726f79020e`.
4. The executor's checkpoint stopped all new proof/code work under the broad
   AGENTS STOP rule. Applied as an entrance condition for preceding R2.3 work,
   this produces a dependency cycle. The user requested coordinator analysis;
   no backend rejection or manually blocked service state was used to reproduce
   this case.

Primary report and machine-readable pins:

- `formal/proposals/isc-s16-r23-gate-applicability-20261028.md`
- `formal/proposals/evidence/r23-gate-applicability-20261028.json`
- `formal/proposals/evidence/profile-unit-storage/mandatory-gates/result.json`

The original failed evidence is immutable. The issue is how the executor applies
that result to phase ordering, not whether the result should become successful.

## Expected orchestration behavior

Retain two separately visible facts: overall proof qualification is FAIL/NO_GO;
the current authorized task is constructing and reviewing its R2.3 prerequisite.
Report the exact failed obligation and dependency direction. Do not present a
missing downstream theorem as evidence of failed predecessor correctness.

The current live graph already supplies a safe route: documentary STOP -> two
process reviews -> coordinator; an accepted applicability decision can use
`RESUME_FORMAL` for R2.3 while Formal remains NO_GO. A future substantive R2.3
candidate can receive reviews under overall NO_GO before the named theorem is
started. No new sprint, node, outcome, semantic Pending or import is needed.

If a client or server nevertheless rejects this predecessor/remediation route
solely for the absent downstream theorem, capture the exact request, response,
assignment, scope context and gate identity as the backend reproduction. No such
rejection has been observed in this case. A developer must not infer a server
patch requirement from the executor stop alone.

Useful regression acceptance cases for phase-aware diagnostics/routing:

- A known downstream declaration/axiom FAIL remains displayed and blocks overall
  qualification/GO, while an existing authorized predecessor/review route works.
- A failure in an applicable R2.3 source proof/model/refinement/compatibility or
  required review blocks acceptance and dependent advancement; the ordering
  distinction cannot hide a genuine predecessor failure.
- A component PASS or approval of an applicability report cannot close R2.3.
- The theorem remains prohibited until exact substantive R2.3 reviews succeed.
- ACK cannot advance execution; old results/reviews cannot be resubmitted;
  existing assignment and historical FAIL/NO_GO evidence remain inspectable.

These are assertions for developer investigation, not an implemented new policy
or gate. No nginx-qa patch, restart, graph mutation or deployment is authorized
by this handoff. Ordinary documented result/review transitions remain the only
execution route.
