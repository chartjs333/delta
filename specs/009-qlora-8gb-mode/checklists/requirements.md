# Specification Quality Checklist: 009 Certified QLoRA 8 GiB Mode

**Reviewed**: 2026-08-23  
**Status**: Ready for implementation

- [x] Base, tokenizer, quantization and adapter schema are immutable/content-addressed.
- [x] Base parameters/buffers cannot enter optimizer, gradients, deltas, residuals or checkpoints.
- [x] QLoRA uses fixed domain-pure tickets and requires `A_j=H`.
- [x] Adapter pseudo-gradient is normalized and quantized before consensus.
- [x] Full ISC/EC/APC/shard/AggregateRootQC/ApplyQC chain applies to adapters.
- [x] Domain mixture and outer optimizer execute exactly inside consensus.
- [x] P2P reuses the base and distributes only certified global adapters.
- [x] 8 GiB claim is limited to one preregistered physical profile with measured evidence.
- [x] Offline CI, resume/composition, mismatch and license/secret gates are specified.
- [x] No unresolved clarification remains; failed memory, base-integrity or certificate gate blocks feature 010.
