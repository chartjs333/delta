# Executed TLC coverage evidence

All metrics below come from the checked-in deterministic config manifest and a validated TLC semantic-result projection. Raw PID, timing, host telemetry and coverage counters are diagnostic only and are not content-addressed. No TLC symmetry set or state constraint is used. Bounds reduce constants only; every required action is checked for non-zero reachability.

| Config | Kind | States | Distinct | Diameter | Terminal outcome classes | Required actions |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| CFG-CONFIG-QC | safety | 3348 | 818 | 19 | none | 0 |
| CFG-SAFETY-F1 | safety | 376812 | 75077 | 30 | ABORTED | 6 |
| CFG-VOTE-CRASH-RECOVERY | safety | 722325 | 24332 | 26 | none | 3 |
| CFG-VOTE-LIFECYCLE-CONFIG | safety | 639 | 204 | 17 | none | 10 |
| CFG-VOTE-LIFECYCLE-ISC | safety | 642 | 212 | 28 | none | 10 |
| CFG-VOTE-LIFECYCLE-EC | safety | 647 | 217 | 33 | none | 10 |
| CFG-VOTE-LIFECYCLE-APC | safety | 651 | 221 | 37 | none | 10 |
| CFG-VOTE-LIFECYCLE-PARAMETER | safety | 664 | 229 | 42 | none | 10 |
| CFG-VOTE-LIFECYCLE-AGGREGATE | safety | 669 | 234 | 47 | none | 10 |
| CFG-VOTE-LIFECYCLE-APPLY | safety | 674 | 239 | 52 | none | 10 |
| CFG-VOTE-LIFECYCLE-VIEW | safety | 1396 | 403 | 19 | none | 10 |
| CFG-VOTE-LIFECYCLE-ABORT | safety | 632 | 202 | 18 | ABORTED | 10 |
| CFG-TICKET-LEASE-AVAILABILITY | safety | 5599 | 2167 | 18 | none | 9 |
| CFG-AVAILABILITY-LOSS-REPAIR | safety | 81394 | 23113 | 26 | none | 11 |
| CFG-INPUT-FREEZE-SEED | safety | 97396 | 19868 | 31 | none | 17 |
| CFG-CERTIFICATE-FRANKENSTEIN | safety | 404838 | 8270 | 28 | none | 8 |
| CFG-SPLIT-BRAIN-PARTITION | safety | 1572865 | 131072 | 19 | none | 5 |
| CFG-ARITHMETIC-BOUNDARY | safety | 40 | 25 | 7 | none | 7 |
| CFG-APPLY-RECOVERY | safety | 15194 | 3252 | 28 | APPLIED | 21 |
| CFG-NATIVE-ARITHMETIC-BINDING | safety | 15194 | 3252 | 28 | APPLIED | 21 |
| CFG-LIVENESS-CONFIG-QC | liveness | 6 | 6 | 6 | none | 5 |
| CFG-LIVENESS-ISC | liveness | 17 | 17 | 17 | none | 6 |
| CFG-LIVENESS-PLAN | liveness | 26 | 26 | 26 | none | 5 |
| CFG-LIVENESS-VIEW-CHANGE | liveness | 7 | 7 | 7 | none | 6 |
| CFG-LIVENESS-ABORT-QC | liveness | 7 | 7 | 7 | ABORTED | 5 |
| CFG-NATIVE-ARITHMETIC-LIVENESS | liveness | 42 | 42 | 42 | APPLIED | 10 |
| CFG-CURRENT-BINDING | safety | 35 | 35 | 35 | none | 10 |
| CFG-CURRENT-BINDING-RECOVERY | safety | 38 | 38 | 38 | none | 13 |
| CFG-HETEROGENEOUS-POSITIVE | safety | 72 | 72 | 72 | APPLIED | 12 |
| CFG-HETEROGENEOUS-PREFIX | safety | 2 | 2 | 2 | none | 1 |
| CFG-HETEROGENEOUS-PRODUCT | safety | 2 | 2 | 2 | none | 1 |
| CFG-HETEROGENEOUS-CONVERSION | safety | 57 | 57 | 57 | none | 5 |
