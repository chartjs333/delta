# Separate native certificate JSON bound

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO remains.**

While inspecting aggregate-root support, source review found that the preceding
Lean certificate helpers model shape, parents and hashing but omit the native
`DELTA_CERTIFICATE_ID` macro's whole-JSON byte limit. A bounded policy wire does
not imply bounded expanded JSON. Native already enforces this limit; this is a
gap in the formal model, not a newly discovered native runtime defect.

Four fresh component cases compile the unchanged canonical.cpp, sha256.cpp and
contracts.cpp at pinned source60c692f6e391f839829dfc64e93380db54cd507b with
MSVC19.29.30146, /std:c++20 /EHsc /W4 /WX. Each calls actual canonical_json and
content_id for NormEvidence. Sorted unique tickets, canonical zero norms and
positive unit scales satisfy native shape checks. The large cases have65523
entries, below the100000 entry limit. JSON lengths4194303/4194304/4194305 produce
ACCEPT/ACCEPT/limit_exceeded(16). In all four cases canonical_json succeeds.
The corresponding separately encoded norm policy components are515/1507570/
1507571/1507572 bytes. This is not an accepted complete policy/runtime trace;
the wire sizes come from the existing Python grammar, not a new C++ wire run.
Native JSON lengths, full JSON SHA256 and accepted contentIDs are compared with
independent Python canonical encoding. Logs store compact hashes/outcomes instead
of multi-megabyte payloads; source pins, exact harness and compiler log are retained.

NativeContractSize provides a distinct bounded certificate hash with the exact
4194304-byte inclusive bound. It does not change the unbounded domain-hash
primitive used elsewhere. General theorems extract the original bytes/hash and
bound from success; oversized bytes reject for every hash function. Whole-list
checking preserves every source, order, position and count, checks optional
finalized identity, and rejects any oversized member. Raw helper acceptance
does not prove certificate syntax; the enclosing checked section supplies it.

NativeSizedParameterSection executes the actual existing PARAMETER and parent
section, constructs JSON from its original parsed certificate records and checks
all nine groups: finalizedISC, norms, seeds, proposed/finalizedEC,
proposed/finalizedAPC, proposed/finalizedPARAMETER. No caller supplies JSON,
approval flags or complete translated records. Proposed certificates use the
same synthetic configured-committee view already used by the original source
verifiers; their computed certificateID is distinct from the stored vote-bodyID.
Finalized certificate identities must equal the original checked IDs. Original
body/parent/source records remain unchanged. General group-length, membership,
position, hash, bound and preceding-section witnesses are derived from success.
Subsequent ROOT composition must use this sized entry point.

The wrapper checks sizes after the previous pure formal checks and hashes;
it does not claim native rejection ordering, allocation behavior or resource-use
equivalence. Earlier raw certificate/section helpers are explicitly lower layers,
not complete native admission. This wrapper does not include the separate
proposedISC admission path, later ROOT/APPLY/current or the whole snapshot.
Those paths must bind their own actual bounded certificate calls when joined.

Small kernel examples cover the inclusive limit and one-byte overflow without
reducing a4MiB list, plus missing/short hash, wrong identity, full ordered list and
oversized interior row. One original norm composes its existing checked
parse/shape/finalized-parent/hash with the new computed JSON bound. Constant-hash
examples are explicitly synthetic; the norm reuses original finite SHA samples.
There is no new general SHA proof, native exporter authentication, full policy
execution, TLA run, production mutant or physical WAL/recovery result.

The original negative-zero/leading-zero native decimal defect remains unresolved.
Full arithmetic/source admission, aggregate/Merkle/APPLY/current, complete public
state relation and nativeArithmeticRecoveryRefines remain open. Contract freeze,
offline reproduction and independent review are still required. Runtime guards,
healthy demos and frozen refs are unchanged; no local PASS or formal GO.

Reproduce native component checks with:
`python formal/scripts/check_native_contract_size.py --vcvars <vcvars64.bat>`.
Without --vcvars, it verifies retained source/harness/observations only.
`python -m unittest discover -s formal/tests -p test_native_contract_size.py -v`
checks exact boundaries, source/outcome substitution, output completeness and
scope flags. `lake --no-cache build DeltaReduce` includes the new generic and
example kernels; every new named definition/theorem is in AxiomAudit.
