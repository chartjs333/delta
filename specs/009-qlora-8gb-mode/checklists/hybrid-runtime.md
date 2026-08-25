# Checklist: 009 QLoRA Runtime

- [x] Python owns adapter training and memory qualification.
- [x] C++ owns adapter certificate/reduce/apply semantics.
- [x] Java owns immutable base/adapter transfer only.
- [x] The base cannot enter trainable or aggregated state.
- [x] Fixed tickets and `A_j=H` remain mandatory.
- [x] The 8 GiB claim is exact-profile evidence, not a general promise.
