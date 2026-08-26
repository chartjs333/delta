PYTHON ?= python3
UV ?= uv
FORMAL_RUNNER := $(PYTHON) formal/scripts/run_formal_gate.py
PREREQUISITE := specs/001-reproducible-training-baseline/scripts/verify_formal_prerequisite.py
FOUNDATION := specs/001-reproducible-training-baseline/scripts/verify_foundation.py
LOCAL_ROUND_PREDECESSOR := specs/002-local-round-engine/scripts/verify_predecessor.py
LOCAL_ROUND_COMPATIBILITY := specs/002-local-round-engine/scripts/verify_final_compatibility.py

.PHONY: formal-phase0 formal-contracts formal-toolchain formal-parse formal-safety formal-liveness \
	formal-proofs formal-mutants formal-refinement formal-clean-reproduction formal-report formal-check \
	prerequisite protocol-check python-check foundation-check conformance local-round-check

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
