PYTHON ?= python3
FORMAL_RUNNER := $(PYTHON) formal/scripts/run_formal_gate.py

.PHONY: formal-phase0 formal-contracts formal-toolchain formal-parse formal-safety formal-liveness \
	formal-proofs formal-mutants formal-refinement formal-clean-reproduction formal-report formal-check

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
