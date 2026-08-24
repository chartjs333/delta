# Independent formal review records

Formal GO requires two review records from distinct independent reviewers. Each
record must be canonical JSON containing `reviewer_id`, `independent`, `status`,
the exact `formal_semantics_id`, the exact `reviewed_commit`, and the exact scope
array `COVERAGE`, `LIVENESS`, `MODEL`, `PROOFS`. Reviewers
must inspect the model scope, liveness assumptions, Lean statements and executed
coverage evidence; a generated or self-attested approval is not acceptable.

Until two such records exist and verify, the report generator intentionally
produces `NO_GO` with `INSUFFICIENT_INDEPENDENT_REVIEWS`.

`reviewed_commit` names the latest non-evidence source commit. Generated machine
evidence and `formal/reports/reviews/*.json` are an evidence overlay and do not
change that commit, so review records can be added without creating a circular
self-reference.

Example shape (serialize canonically before use):

```json
{"formal_semantics_id":"sha256:<64 lowercase hex>","independent":true,"reviewed_commit":"<40 lowercase hex>","reviewer_id":"<stable identity>","scope":["COVERAGE","LIVENESS","MODEL","PROOFS"],"status":"PASS"}
```
