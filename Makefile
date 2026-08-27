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

.PHONY: formal-phase0 formal-contracts formal-toolchain formal-parse formal-safety formal-liveness \
	formal-proofs formal-mutants formal-refinement formal-clean-reproduction formal-report formal-check \
	prerequisite protocol-check python-check foundation-check conformance local-round-check \
	bft-preflight bft-contracts bft-core-architecture bft-native

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

bft-native: bft-contracts bft-core-architecture
	cmake --preset cpp20
	cmake --build --preset cpp20 --parallel
	ctest --preset cpp20
	cmake --preset cpp23
	cmake --build --preset cpp23 --parallel
	ctest --preset cpp23
