# DeltaTorrent concept memo — source provenance

**Original supplied file**: `Pasted markdown(1).md`  
**Imported**: 2026-08-21  
**SHA-256 of the supplied source**: `c37cadc9078323c1eb0b1d5c7c7a6834c5928a8a1a1c8a8f3674f749f7b4dc82`

This file records the source basis used to derive the Spec Kit artifacts. The complete original memo was supplied in the project conversation; this repository stores its provenance and implementation-relevant requirements rather than treating the memo as independently verified evidence.

## Source-derived architectural direction

- Split **training time**, not individual Transformer layers/tokens, across WAN workers.
- Each worker starts from one named parent model, performs many local optimizer steps and emits one pseudo-gradient.
- Weight contributions by the number of actually processed non-padding tokens.
- Separate the **reduce plane** from the **distribution plane**.
- Reduce distinct local updates first; only identical immutable global objects enter torrent-like P2P distribution.
- Use canonical shards, content hashes, resumable transfer and global manifests.
- Reduce regionally before global combination to limit inter-region fan-in.
- Compress pseudo-gradients, initially with INT8 and worker-local error feedback.
- Bound heterogeneity and staleness; strict synchronous operation remains the safe reference.
- Start with a permissioned network and explicit validation rather than claiming permissionless compute verification.
- Treat LoRA/QLoRA as the practical first mode for 8 GB GPUs.
- Evaluate downstream/post-training quality, not only training loss.

## Source-derived experimental target

The concept proposes a first convincing real-WAN prototype with:

- 20–50 remote workers;
- 8 GB-class GPUs;
- 3–5 regional groups;
- a 100–300M-parameter full-training workload or QLoRA;
- local rounds primarily in the 128–512-step range;
- INT8 pseudo-gradients with error feedback;
- regional aggregation;
- P2P distribution of already aggregated global deltas;
- fault scenarios involving approximately 10% worker loss.

The memo frames network share below 10–15%, GPU utilization above 75–80%, churn tolerance and absence of a single distribution bottleneck as **experimental engineering goals**, not guaranteed outcomes.

## Deliberately deferred

- permissionless participation, Sybil resistance and economic incentives;
- proof that arbitrary remote training work was honestly computed;
- dense multi-billion pretraining on a single isolated 8 GB GPU;
- WAN tensor/sequence parallelism as the first implementation;
- advanced sparse/low-rank/streaming codecs before the reference protocol is correct.

The detailed staged interpretation is defined by `specs/ROADMAP.md` and the stacked feature specifications.
