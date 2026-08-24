# Executed TLC coverage evidence

All counts below come from the checked-in deterministic config manifest and the corresponding retained TLC log. No TLC symmetry set or state constraint is used. Bounds reduce constants only; every required action is checked for non-zero invocation coverage.

| Config | Kind | States | Distinct | Diameter | Terminal outcome classes | Required actions |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| CFG-CONFIG-QC | safety | 14893 | 2719 | 24 | none | 0 |
| CFG-SAFETY-F1 | safety | 1060 | 485 | 14 | ABORTED | 6 |
| CFG-VOTE-CRASH-RECOVERY | safety | 457625 | 46852 | 33 | none | 5 |
| CFG-TICKET-LEASE-AVAILABILITY | safety | 15519 | 4330 | 19 | none | 9 |
| CFG-AVAILABILITY-LOSS-REPAIR | safety | 127033 | 28742 | 25 | none | 11 |
| CFG-INPUT-FREEZE-SEED | safety | 137523 | 23784 | 26 | none | 17 |
| CFG-CERTIFICATE-FRANKENSTEIN | safety | 628715 | 12308 | 25 | none | 8 |
| CFG-SPLIT-BRAIN-PARTITION | safety | 387073 | 41472 | 19 | none | 5 |
| CFG-ARITHMETIC-BOUNDARY | safety | 6113 | 2190 | 28 | none | 7 |
| CFG-APPLY-RECOVERY | safety | 11564 | 2416 | 20 | APPLIED | 21 |
| CFG-LIVENESS-EVENTUAL-SYNCHRONY | liveness | 203 | 167 | 16 | ABORTED | 6 |
