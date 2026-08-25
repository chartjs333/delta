# Formal Prerequisite and Runtime Trace Obligations: 011 Multi-Region Pilot

This file is normative for `011-multiregion-pilot`.

## Dual prerequisite

No remote provisioning or training task may begin unless both verify:

1. exact compatible `FormalVerificationReport(decision=GO)` and `formal_semantics_id` from 000;
2. exact compatible `BenchmarkResultQC(decision=GO)` from 010 whose mandatory formal-regression gate references the same semantics/proof/trace identities.

`PilotDefinition` MUST bind both report roots, evidence roots, source/protocol/profile compatibility and permitted validity window. A mismatch forces STOP even if either signature set is otherwise valid.

## Pilot runtime refinement

The pilot evidence policy MUST project and verify protocol traces for:

- normal certified rounds;
- soft timeout/view change and hard abort;
- validator crash before/after durable vote/send;
- restart/journal recovery and replay;
- pre/post-ISC storage loss and exact repair/irrecoverable abort;
- partition with/without quorum;
- Frankenstein/mixed certificate attempts;
- apply disagreement/quorum loss;
- crash after ApplyQC before artifact/current pointer;
- P2P seed loss without certified-state rollback;
- emergency stop and epoch/key rotation boundaries.

The PilotDefinition chooses whether every event or a formally justified complete sample is checked, but all mandatory chaos traces and every finalized certificate/current transition are always included.

## Safety rule

Any real behavior that cannot project to an allowed formal transition, violates a theorem precondition, or differs from the declared terminal outcome is a mandatory pilot gate failure. Operators may stop/rollback services, but cannot reinterpret the trace or promote an uncertified checkpoint.

## Final decision

`PilotResultQC(decision=GO)` requires verified dual prerequisites, complete formal trace/refinement evidence and no unresolved model-versus-runtime discrepancy. Missing/unverifiable formal evidence yields `INCONCLUSIVE` or `NO_GO` according to the frozen decision policy, never GO.
