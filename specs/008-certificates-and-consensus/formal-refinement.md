# Formal Refinement Obligations: 008 Certificates and Apply Consensus

This file is normative for `008-certificates-and-consensus`.

## Bound formal graph

Implementation MUST refine the exact certificate/action graph:

`ISC → SeedTranscript → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC → AdvanceCurrentCheckpoint`.

Every body/vote/QC must bind the same formal context identifiers and parent hashes declared by the compatible 000 semantics ID.

## Mandatory refinement properties

- no valid seed/EC/APC action before finalized ISC;
- EC accepted set is an ISC subset and APC cannot alter membership;
- exact integer/rational norm, clipping and coefficient decisions satisfy bound/proof preconditions;
- every shard QC has one exact config/ISC/EC/APC/domain/shard/profile context;
- AggregateRootQC has complete exact coverage and rejects every mixed view;
- apply votes are persist-before-sign and deterministic over one parent/aggregate/profile;
- only ApplyQC can advance current; replay repairs the pointer exactly once;
- insufficient quorum, overflow, unavailable required bytes or disagreement ends in retry/view change then hard abort with parent preserved.

## Required evidence

1. Full legal certificate/apply trace accepted by the formal checker.
2. Early-seed, EC/APC membership mutation, wrong-parent shard, incomplete/duplicate root, conflicting apply and current-without-ApplyQC traces rejected.
3. Mandatory automated Frankenstein mixed-view test maps to the formal `ShardViewAtomicity/AggregateCompleteness` failure.
4. Four apply validators produce one concrete byte-identical tuple and a legal abstract trace.
5. Quorum/apply/coverage theorem artifacts and concrete preconditions are verified.
6. All relevant 000 mutants still produce expected counterexamples.
7. Crash/restart/replay across vote, certificate, artifact and pointer boundaries refines formal recovery behavior.

Any new certificate type, parent edge, fallback, view/deadline or apply transition requires branch-000 amendment and new Formal GO before code.
