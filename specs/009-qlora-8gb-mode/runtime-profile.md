# Runtime Profile: 009 Certified QLoRA 8 GiB Mode

**Training runtime**: Python/PyTorch  
**Consensus runtime**: C++ adapter fixed-point/certificate/apply path  
**Transport runtime**: Java base/adapter artifact transfer and node shell  
**Formal impact**: `REFINEMENT_ONLY` specialization of the existing certificate graph
**Exact predecessor**: feature-008 merge `62124e58062d876dc4c2fd903b57cfc7d89872d7`
**Formal semantics ID**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`
**Semantic completeness claimed**: `false`

## Python worker ownership

Python loads the immutable quantized base, resolves the exact adapter schema, performs fixed-ticket adapter-only training, verifies `A_j=H`, computes `parent_adapter-final_adapter`, normalizes it and emits canonical feature-004 q-shard inputs.

Base parameters and disallowed buffers cannot enter gradients, optimizer groups, contribution, residual, aggregate or outer optimizer state.

## C++ ownership

C++ validates mode/base/tokenizer/quantization/schema fingerprints, executes exact adapter norm/APC/reduce/coverage/apply semantics and forms AggregateRootQC/ApplyQC. The base is represented by an immutable content ID and is not part of adapter parameter coverage.

## Java ownership

Java transfers and caches immutable base/tokenizer objects, transports adapter contributions/certificates and distributes ApplyQC-certified global adapters. It cannot merge/mutate the base or make an adapter current without native ApplyQC.

## Memory qualification

The 8 GiB claim is bound to an exact profile: physical device, available/nominal VRAM, driver/runtime, model revision, sequence/batch/accumulation, fixed `B/H`, adapter config, kernels, offload/checkpoint flags and peak allocated/reserved memory.

Python records memory evidence. Java/C++ processes record their own host/off-heap/native memory separately. No generalized 8 GiB claim follows from a tiny mock run.

The physical runner identity and immutable qualification profile are hard evidence prerequisites.
If no qualifying physical runner is available, offline Python, native C++ and Java work may proceed,
but the feature exit remains `BLOCKED_HARDWARE` and cannot be reported as `PASS`.

No runtime may introduce a QLoRA-specific certificate hierarchy. QLoRA state is a context-bound
specialization of the feature-008 ISC/EC/APC/shard/root/ApplyQC/current chain.

## Exit additions

- offline tiny Python fixture and physical 8 GiB profile;
- no base tensor in Python optimizer/gradient/payload or C++ coverage/apply;
- exact adapter q/certificate/apply bytes across runtimes;
- base cache prevents unchanged retransmission;
- incompatible base/schema/mode fails at every boundary;
- four native apply validators agree exactly;
- embedded Java/native crash does not corrupt certified history; sidecar evaluation is deferred to 010 if not implemented here.
