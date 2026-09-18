PYTHON ?= python3
UV ?= uv
FORMAL_RUNNER := $(PYTHON) formal/scripts/run_formal_gate.py
PREREQUISITE := specs/001-reproducible-training-baseline/scripts/verify_formal_prerequisite.py
FOUNDATION := specs/001-reproducible-training-baseline/scripts/verify_foundation.py
LOCAL_ROUND_PREDECESSOR := specs/002-local-round-engine/scripts/verify_predecessor.py
LOCAL_ROUND_COMPATIBILITY := specs/002-local-round-engine/scripts/verify_final_compatibility.py
BFT_PREFLIGHT := specs/003-bft-round-state-machine/scripts/verify_preflight.py
BFT_TOOLCHAINS := specs/003-bft-round-state-machine/scripts/verify_native_toolchains.py
BFT_PROTOCOL := specs/003-bft-round-state-machine/scripts/verify_protocol_contracts.py
BFT_CORE_ARCHITECTURE := specs/003-bft-round-state-machine/scripts/verify_core_architecture.py
BFT_SUPPLY_CHAIN := specs/003-bft-round-state-machine/scripts/verify_native_supply_chain.py
BFT_TOOLCHAIN_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_toolchain_execution.py
BFT_CORE_PROTOCOL_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_core_protocol_execution.py
BFT_CORE_ARITHMETIC_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_core_arithmetic_execution.py
BFT_CORE_TRANSITION_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_core_transition_execution.py
BFT_CORE_CONSENSUS_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_core_consensus_execution.py
BFT_CORE_PORTABILITY_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_core_portability_execution.py
BFT_PREPARED_100_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_prepared_100_execution.py
BFT_RUNTIME_DURABILITY_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_runtime_durability_execution.py
BFT_ABI_FFM_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_abi_ffm_execution.py
BFT_NATIVE_REFINEMENT := specs/003-bft-round-state-machine/scripts/verify_native_refinement.py
BFT_NATIVE_PHASE6_EXECUTION := specs/003-bft-round-state-machine/scripts/verify_native_phase6_execution.py
BFT_FINAL_COMPATIBILITY := specs/003-bft-round-state-machine/scripts/verify_final_compatibility.py
FIXEDPOINT_PREFLIGHT := specs/004-compressed-delta-protocol/scripts/verify_preflight.py
FIXEDPOINT_CONTRACTS := specs/004-compressed-delta-protocol/scripts/verify_protocol_contracts.py
FIXEDPOINT_ARCHITECTURE := specs/004-compressed-delta-protocol/scripts/verify_native_architecture.py
FIXEDPOINT_PROOFS := specs/004-compressed-delta-protocol/scripts/verify_proof_instances.py
FIXEDPOINT_REFINEMENT := specs/004-compressed-delta-protocol/scripts/verify_direct_q_refinement.py
FIXEDPOINT_PHASE_EVIDENCE := specs/004-compressed-delta-protocol/scripts/verify_phase_evidence.py
FIXEDPOINT_NATIVE_EXECUTION := specs/004-compressed-delta-protocol/scripts/verify_native_execution.py
FIXEDPOINT_FINAL := specs/004-compressed-delta-protocol/scripts/verify_final_compatibility.py
DISTRIBUTION_PREFLIGHT := specs/005-content-addressed-p2p-distribution/scripts/verify_preflight.py
DISTRIBUTION_CONTRACTS := specs/005-content-addressed-p2p-distribution/scripts/verify_protocol_contracts.py
DISTRIBUTION_REFINEMENT := specs/005-content-addressed-p2p-distribution/scripts/verify_distribution_refinement.py
DISTRIBUTION_PHASE_EVIDENCE := specs/005-content-addressed-p2p-distribution/scripts/verify_phase_evidence.py
DISTRIBUTION_FINAL := specs/005-content-addressed-p2p-distribution/scripts/verify_final_compatibility.py
HIERARCHY_PREFLIGHT := specs/006-regional-hierarchical-reduce/scripts/verify_preflight.py
HIERARCHY_CONTRACTS := specs/006-regional-hierarchical-reduce/scripts/verify_protocol_contracts.py
HIERARCHY_NATIVE_TOPOLOGY := specs/006-regional-hierarchical-reduce/scripts/verify_native_topology.py
HIERARCHY_EXECUTION := specs/006-regional-hierarchical-reduce/scripts/verify_hierarchy_execution.py
HIERARCHY_NATIVE := specs/006-regional-hierarchical-reduce/scripts/verify_native_hierarchy.py
HIERARCHY_CI := specs/006-regional-hierarchical-reduce/scripts/capture_hierarchy_ci.py
HIERARCHY_FINAL := specs/006-regional-hierarchical-reduce/scripts/verify_final_compatibility.py
SCHEDULING_PREFLIGHT := specs/007-domain-pure-ticket-scheduling/scripts/verify_preflight.py
SCHEDULING_CONTRACTS := specs/007-domain-pure-ticket-scheduling/scripts/verify_protocol_contracts.py
SCHEDULING_NATIVE := specs/007-domain-pure-ticket-scheduling/scripts/verify_native_planner.py
SCHEDULING_ADMISSION := specs/007-domain-pure-ticket-scheduling/scripts/verify_native_admission.py
SCHEDULING_LIFECYCLE := specs/007-domain-pure-ticket-scheduling/scripts/verify_native_lifecycle.py
SCHEDULING_BOUNDARY := specs/007-domain-pure-ticket-scheduling/scripts/verify_scheduling_boundary.py
SCHEDULING_REFINEMENT := specs/007-domain-pure-ticket-scheduling/scripts/verify_scheduling_refinement.py
SCHEDULING_CI := specs/007-domain-pure-ticket-scheduling/scripts/capture_scheduling_ci.py
SCHEDULING_FINAL := specs/007-domain-pure-ticket-scheduling/scripts/verify_final_compatibility.py
CERTIFICATES_PREFLIGHT := specs/008-certificates-and-consensus/scripts/verify_preflight.py
CERTIFICATES_CONTRACTS := specs/008-certificates-and-consensus/scripts/verify_protocol_contracts.py
CERTIFICATES_NATIVE := specs/008-certificates-and-consensus/scripts/verify_native_execution.py
CERTIFICATES_REFINEMENT := specs/008-certificates-and-consensus/scripts/verify_certificate_refinement.py
CERTIFICATES_CI := specs/008-certificates-and-consensus/scripts/capture_certificate_ci.py
CERTIFICATES_FINAL := specs/008-certificates-and-consensus/scripts/verify_final_compatibility.py
BENCHMARK_PREFLIGHT := specs/010-wan-benchmark-and-quality/scripts/verify_preflight.py
BENCHMARK_CONTRACTS := specs/010-wan-benchmark-and-quality/scripts/benchmark_contracts.py
BENCHMARK_PRIMARY := specs/010-wan-benchmark-and-quality/scripts/primary_contracts.py
BENCHMARK_STAGE_B_PRERUN := specs/010-wan-benchmark-and-quality/scripts/verify_stage_b_scientific_prerun.py
BENCHMARK_RUNTIME := specs/010-wan-benchmark-and-quality/scripts/verify_runtime_adapters.py
BENCHMARK_ATTACKS := specs/010-wan-benchmark-and-quality/scripts/verify_production_attacks.py
BENCHMARK_FORMAL := specs/010-wan-benchmark-and-quality/scripts/verify_formal_regression.py

.PHONY: formal-phase0 formal-contracts formal-toolchain formal-parse formal-safety formal-liveness \
	formal-proofs formal-mutants formal-refinement formal-clean-reproduction formal-report formal-check \
	prerequisite protocol-check python-check foundation-check conformance local-round-check \
	bft-preflight bft-contracts bft-core-architecture bft-final bft-check bft-native \
	fixedpoint-preflight fixedpoint-contracts fixedpoint-architecture fixedpoint-proofs \
	fixedpoint-refinement fixedpoint-evidence fixedpoint-final fixedpoint-check \
	distribution-preflight distribution-contracts distribution-refinement \
	distribution-evidence distribution-final distribution-check hierarchy-preflight hierarchy-contracts \
	hierarchy-native-topology hierarchy-execution hierarchy-evidence hierarchy-final hierarchy-check \
	scheduling-preflight scheduling-contracts scheduling-native-planner scheduling-native-admission \
	scheduling-native-lifecycle scheduling-boundary scheduling-refinement scheduling-ci \
	scheduling-final scheduling-check certificates-preflight certificates-contracts \
	certificates-native certificates-refinement certificates-ci certificates-final \
	certificates-check benchmark-contracts benchmark-runtime benchmark-formal benchmark-attacks benchmark-check

formal-phase0:
	$(PYTHON) formal/scripts/verify_phase0.py

formal-contracts:
	$(PYTHON) -m unittest discover -s formal/tests -p "test_*.py"

formal-toolchain:
	$(PYTHON) formal/toolchain/verify_locks.py

formal-parse:
	$(FORMAL_RUNNER) parse

formal-safety:
	$(FORMAL_RUNNER) safety

formal-liveness:
	$(FORMAL_RUNNER) liveness

formal-proofs:
	$(FORMAL_RUNNER) proofs

formal-mutants:
	$(FORMAL_RUNNER) mutants

formal-refinement:
	$(FORMAL_RUNNER) refinement

formal-clean-reproduction:
	$(PYTHON) formal/scripts/run_clean_offline_reproduction.py

formal-report:
	$(FORMAL_RUNNER) report

formal-check: formal-phase0 formal-contracts formal-toolchain formal-parse formal-safety \
	formal-liveness formal-proofs formal-mutants formal-refinement formal-report

prerequisite:
	$(UV) run python $(PREREQUISITE) --check-only

protocol-check:
	$(UV) run pytest delta-worker-python/tests/contract delta-worker-python/tests/architecture

python-check:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy delta-worker-python/src
	$(UV) run pytest delta-worker-python/tests

foundation-check:
	$(UV) run python $(FOUNDATION) --check-only

conformance: prerequisite protocol-check foundation-check

local-round-check: protocol-check python-check
	$(UV) run python $(LOCAL_ROUND_PREDECESSOR) --check-only
	$(UV) run python $(LOCAL_ROUND_COMPATIBILITY) --check-only

bft-preflight:
	$(UV) run python $(BFT_PREFLIGHT) --check-only
	$(UV) run python $(BFT_TOOLCHAINS) --check-only

bft-contracts: bft-preflight protocol-check
	$(UV) run python $(BFT_PROTOCOL) --check-only
	$(UV) run pytest specs/003-bft-round-state-machine/tests

bft-core-architecture:
	$(UV) run python $(BFT_CORE_ARCHITECTURE) --check-only
	$(UV) run python $(BFT_SUPPLY_CHAIN) --check-only
	$(UV) run python $(BFT_TOOLCHAIN_EXECUTION) --check-only
	$(UV) run python $(BFT_CORE_PROTOCOL_EXECUTION) --check-only
	$(UV) run python $(BFT_CORE_ARITHMETIC_EXECUTION) --check-only
	$(UV) run python $(BFT_CORE_TRANSITION_EXECUTION) --check-only
	$(UV) run python $(BFT_CORE_CONSENSUS_EXECUTION) --check-only
	$(UV) run python $(BFT_CORE_PORTABILITY_EXECUTION) --check-only
	$(UV) run python $(BFT_PREPARED_100_EXECUTION) --check-only
	$(UV) run python $(BFT_RUNTIME_DURABILITY_EXECUTION) --check-only
	$(UV) run python $(BFT_ABI_FFM_EXECUTION) --check-only
	$(UV) run python $(BFT_NATIVE_REFINEMENT) --check-only
	$(UV) run python $(BFT_NATIVE_PHASE6_EXECUTION) --check-only

bft-final: bft-contracts bft-core-architecture
	$(UV) run python $(BFT_FINAL_COMPATIBILITY) --check-only

bft-check: python-check bft-final

fixedpoint-preflight:
	$(UV) run python $(FIXEDPOINT_PREFLIGHT) --check-only
	$(UV) run pytest specs/004-compressed-delta-protocol/tests

fixedpoint-contracts: fixedpoint-preflight
	$(UV) run python $(FIXEDPOINT_CONTRACTS) --check-only
	$(UV) run pytest delta-worker-python/tests/contract/test_fixedpoint_reference.py \
		specs/004-compressed-delta-protocol/tests/test_verify_protocol_contracts.py

fixedpoint-architecture: fixedpoint-contracts
	$(UV) run python $(FIXEDPOINT_ARCHITECTURE) --check-only
	$(UV) run pytest specs/004-compressed-delta-protocol/tests/test_verify_native_architecture.py

fixedpoint-proofs: fixedpoint-architecture
	$(UV) run python $(FIXEDPOINT_PROOFS) --check-only
	$(UV) run pytest specs/004-compressed-delta-protocol/tests/test_verify_proof_instances.py

fixedpoint-refinement: fixedpoint-proofs
	$(UV) run python $(FIXEDPOINT_REFINEMENT) --check-only
	$(UV) run pytest specs/004-compressed-delta-protocol/tests/test_verify_direct_q_refinement.py

fixedpoint-evidence: fixedpoint-refinement
	$(UV) run python $(FIXEDPOINT_PHASE_EVIDENCE) --check-only
	$(UV) run python $(FIXEDPOINT_NATIVE_EXECUTION) --check-only

fixedpoint-final: fixedpoint-evidence
	$(UV) run python $(FIXEDPOINT_FINAL) --check-only

fixedpoint-check: python-check fixedpoint-final

distribution-preflight:
	$(UV) run python $(DISTRIBUTION_PREFLIGHT) --check-only

distribution-contracts: distribution-preflight
	$(UV) run python $(DISTRIBUTION_CONTRACTS) --check-only
	$(UV) run pytest specs/005-content-addressed-p2p-distribution/tests/test_verify_protocol_contracts.py

distribution-refinement: distribution-contracts
	$(UV) run python $(DISTRIBUTION_REFINEMENT) --check-only
	$(UV) run pytest specs/005-content-addressed-p2p-distribution/tests/test_verify_distribution_refinement.py

distribution-evidence: distribution-refinement
	$(UV) run python $(DISTRIBUTION_PHASE_EVIDENCE) --check-only

distribution-final: distribution-evidence
	$(UV) run python $(DISTRIBUTION_FINAL) --check-only

distribution-check: python-check distribution-final

hierarchy-preflight:
	$(UV) run python $(HIERARCHY_PREFLIGHT) --check-only
	$(UV) run pytest specs/006-regional-hierarchical-reduce/tests/test_verify_preflight.py

hierarchy-contracts: hierarchy-preflight
	$(UV) run python $(HIERARCHY_CONTRACTS) --check-only
	$(UV) run pytest specs/006-regional-hierarchical-reduce/tests/test_verify_protocol_contracts.py

hierarchy-native-topology: hierarchy-contracts
	$(UV) run python $(HIERARCHY_NATIVE_TOPOLOGY) --check-only
	$(UV) run pytest specs/006-regional-hierarchical-reduce/tests/test_verify_native_topology.py

hierarchy-execution: hierarchy-native-topology
	cmake --preset cpp20
	cmake --build --preset cpp20 --parallel
	ctest --preset cpp20 -R "delta_core.hierarchy|delta_ffi.hierarchy" --output-on-failure
	$(UV) run python $(HIERARCHY_EXECUTION) --trace-dir out/build/cpp20/hierarchy-traces
	$(UV) run pytest specs/006-regional-hierarchical-reduce/tests/test_verify_hierarchy_execution.py

hierarchy-evidence: hierarchy-execution
	$(UV) run python $(HIERARCHY_NATIVE) --check-only --trace-dir out/build/cpp20/hierarchy-traces
	$(UV) run python $(HIERARCHY_CI) --check-only

hierarchy-final: hierarchy-evidence
	$(UV) run python $(HIERARCHY_FINAL) --check-only --trace-dir out/build/cpp20/hierarchy-traces

hierarchy-check: python-check hierarchy-final

scheduling-preflight:
	$(UV) run python $(SCHEDULING_PREFLIGHT) --check-only
	$(UV) run pytest specs/007-domain-pure-ticket-scheduling/tests/test_verify_preflight.py

scheduling-contracts: scheduling-preflight
	$(UV) run python specs/007-domain-pure-ticket-scheduling/scripts/scheduling_contracts.py --check
	$(UV) run python $(SCHEDULING_CONTRACTS) --check-only
	$(UV) run pytest specs/007-domain-pure-ticket-scheduling/tests/test_scheduling_contracts.py

scheduling-native-planner: scheduling-contracts
	cmake --preset cpp20
	cmake --build --preset cpp20 --parallel --target delta_scheduling_planner_test \
		delta_scheduling_adapt_work_mutant_test delta_scheduling_overlap_ranges_mutant_test \
		delta_scheduling_skip_infeasibility_mutant_test delta_scheduling_contract_fuzz
	ctest --preset cpp20 -R "delta_core.scheduling" --output-on-failure
	$(UV) run python $(SCHEDULING_NATIVE) --check-only

scheduling-native-admission: scheduling-native-planner
	cmake --build --preset cpp20 --parallel --target delta_scheduling_eligibility_test
	ctest --preset cpp20 -R "delta_core.scheduling_eligibility" --output-on-failure
	$(UV) run python $(SCHEDULING_ADMISSION) --check-only

scheduling-native-lifecycle: scheduling-native-admission
	cmake --build --preset cpp20 --parallel --target delta_scheduling_lifecycle_test \
		delta_scheduling_durability_mutant_test
	ctest --preset cpp20 -R "delta_core.scheduling_(lifecycle|mutant_expose_before_durability)" \
		--output-on-failure
	$(UV) run python $(SCHEDULING_LIFECYCLE) --check-only

scheduling-boundary: scheduling-native-lifecycle
	cmake --build --preset cpp20 --parallel --target delta_ffi_scheduling_test
	ctest --preset cpp20 -R "delta_ffi.scheduling" --output-on-failure
	$(UV) run python $(SCHEDULING_BOUNDARY) --check-only

scheduling-refinement: scheduling-boundary
	cmake --build --preset cpp20 --parallel --target delta_scheduling_lifecycle_test
	ctest --preset cpp20 -R "delta_core.scheduling_trace_export" --output-on-failure
	$(UV) run python $(SCHEDULING_REFINEMENT) --check-only \
		--trace-dir out/build/cpp20/scheduling-traces

scheduling-ci:
	$(UV) run python $(SCHEDULING_CI) --check-only

scheduling-final: scheduling-refinement scheduling-ci
	$(UV) run python $(SCHEDULING_FINAL) --check-only \
		--trace-dir out/build/cpp20/scheduling-traces

scheduling-check: python-check scheduling-final

certificates-preflight:
	$(UV) run python $(CERTIFICATES_PREFLIGHT) --check-only
	$(UV) run pytest specs/008-certificates-and-consensus/tests/test_verify_preflight.py

certificates-contracts: certificates-preflight
	$(UV) run python specs/008-certificates-and-consensus/scripts/certificate_contracts.py --check
	$(UV) run python $(CERTIFICATES_CONTRACTS) --check-only
	$(UV) run pytest specs/008-certificates-and-consensus/tests/test_certificate_contracts.py \
		specs/008-certificates-and-consensus/tests/test_verify_protocol_contracts.py

certificates-native: certificates-contracts
	cmake --preset cpp20
	cmake --build --preset cpp20 --parallel --target delta_certificates_test \
		delta_ffi_certificates_test delta_certificate_contract_fuzz \
		delta_certificates_seed_parent_mutant_test \
		delta_certificates_observed_coverage_mutant_test \
		delta_robust_coefficient_mutant_test delta_current_apply_qc_mutant_test
	ctest --preset cpp20 -R "delta_core.certificates|delta_core.certificate_mutant|delta_core.certificate_contract_fuzz|delta_ffi.certificates" \
		--output-on-failure
	$(UV) run python $(CERTIFICATES_NATIVE) --check-only

certificates-refinement: certificates-native
	$(UV) run python specs/008-certificates-and-consensus/scripts/generate_refinement_traces.py --check
	$(UV) run python $(CERTIFICATES_REFINEMENT) --check-only

certificates-ci:
	$(UV) run python $(CERTIFICATES_CI) --check-only

certificates-final: certificates-refinement certificates-ci
	$(UV) run python $(CERTIFICATES_FINAL) --check-only

certificates-check: python-check certificates-final

benchmark-contracts:
	$(UV) run python $(BENCHMARK_PREFLIGHT) --check-only
	$(UV) run python $(BENCHMARK_CONTRACTS)
	$(UV) run python $(BENCHMARK_PRIMARY)
	$(UV) run python $(BENCHMARK_STAGE_B_PRERUN) --check-only
	$(UV) run pytest specs/010-wan-benchmark-and-quality/tests

benchmark-runtime: benchmark-contracts
	$(UV) run python $(BENCHMARK_RUNTIME) --check-only

benchmark-formal: benchmark-runtime
	$(UV) run python $(BENCHMARK_FORMAL) --check-only

benchmark-attacks: benchmark-formal
	$(UV) run python $(BENCHMARK_ATTACKS) --check-only

benchmark-check: python-check benchmark-attacks

bft-native: bft-contracts bft-core-architecture
	cmake --preset cpp20
	cmake --build --preset cpp20 --parallel
	ctest --preset cpp20
	cmake --preset cpp23
	cmake --build --preset cpp23 --parallel
	ctest --preset cpp23
