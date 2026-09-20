# Runtime Profile: Feature 010 Reconciliation

**Python/PyTorch** owns local training, evaluation, token/domain accounting, and
quality analysis.
**C++ core/runtime** owns deterministic transitions, checked arithmetic,
certificate admission, WAL/replay, and current-state authority.
**Java/Netty** owns TLS, framing, peer routing, rate limits, backpressure, and
opaque transport.
**Formal impact**: `NONE`.

## Identity binding

Every eligible result must bind the exact source/tree, formal report and semantics
ID, ABI/schema/protocol/build IDs, compiler/JDK/Python/CUDA locks, model/data/
evaluator content, hardware inventory, deployment profile, network/fault profile,
and governance/evidence roots. A result from another identity is audit history,
not a compatible observation.

## Mandatory runtime gates

- exact cross-language canonical bytes, state/effect roots, and negative outcomes;
- GCC/Clang and supported architecture agreement;
- direct/copy FFM equivalence with bounded copy fallback;
- ASan/UBSan, separate TSan, parser fuzzing, pointer lifetime, and ABI mismatch;
- native persist-before-expose crash/replay and current-pointer idempotency;
- JDK 25 primary/JDK 26 compatibility, Netty lifetime, backpressure, and event-loop
  non-blocking checks;
- explicit embedded-versus-sidecar selection and honest crash-containment scope;
- physical CUDA execution for the exact scientific profile, without CPU/mock
  substitution;
- approved real-WAN TLS endpoints after simulated gates pass.

## Current environment observation

The timestamped commands and sanitized observations are in
`evidence/environment-audit.md`; they are diagnostic and confer no authority.

The host exposes an NVIDIA GeForce RTX 3070 Laptop GPU with 8192 MiB and compute
capability 8.6. The exact Worker environment instantiated from the current base is
PyTorch `2.6.0+cpu`, reports `torch.cuda.is_available() == false`, and has no CUDA
runtime. A separate untracked local environment exposes PyTorch `2.6.0+cu124`, but
it is not bound to the current candidate or a current-lineage Campaign 02
definition, its Torch-visible memory is 512 KiB below the historical literal 8 GiB
threshold, the required container image is absent, and the required evaluation
datasets are unavailable. Neither environment is an eligible current Campaign 02
execution identity.

An untracked local controller worksheet/approval record exists, but its registered
custodial private keys were not available and local demo keys do not match it. No
repository secret or variable names advertise controller custody, pilot TLS,
real-WAN endpoints, cloud regions, model credentials, or dataset credentials.
Only CUDA installation path variable names were observed; they grant no execution
or data authority.
