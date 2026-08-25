# Runtime Profile: 002 Local Round Engine

**Status**: Normative hybrid-runtime addendum  
**Runtime owner**: Python 3.12 + PyTorch worker  
**Formal impact**: `REFINEMENT_ONLY`

## Boundary

Feature 002 implements worker-local fixed-ticket training only. It does not load the native validator library, open validator sockets or mutate replicated consensus state.

The Python worker consumes a canonical `DomainPureWorkTicket`, executes exactly its fixed data range, `B` and `H`, requires `A_j = H`, computes `Delta_j = parent - final`, normalizes by `A_j` and publishes a contribution candidate through runtime-neutral `delta-protocol` contracts.

## Required output boundary

The local engine emits:

- parent/model/schema/ticket/domain identifiers;
- exact effective step and non-padding token counts;
- safe tensor artifact for the normalized pseudo-gradient reference;
- canonical metadata and content hashes;
- complete/incomplete/cancelled/OOM terminal reason;
- formal trace projection for the local completion handoff.

Feature 002 does not define accepted consensus q-bytes; canonical fixed-point encoding is feature 004. It may emit deterministic fixture inputs used later by independent C++ encoders.

## Prohibitions

- no adaptive `H_i` or memory/speed-driven ticket mutation;
- no partial-ticket eligibility;
- no Java/C++ consensus shortcut;
- no pickle/network object serialization;
- no worker-speed field in mathematical weight;
- no current-checkpoint decision at the worker.

## Exit additions

- same ticket/config and reproducibility class yields the same processed data/counts and normalized reference artifact;
- incomplete work produces no commit-eligible candidate;
- canonical metadata matches `delta-protocol` fixtures;
- future C++/Java runtimes can consume the artifact without importing Python object definitions.
