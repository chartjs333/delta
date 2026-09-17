# Step 5C Contract Pack

Canonical, runtime-neutral contracts for Step 5C controlled live execution.

This directory is owned by `feature/step5c-contracts` and covers
`step5c:T005-T009`.

## Contents

- `schemas/`: Draft 2020-12 JSON Schemas for `ExecutionIntent`,
  `AdmissionRecord`, `AuthorizedExecution`, `ExecutionStatus`, preflight
  errors, and receipt-lineage extension.
- `taxonomy/`: frozen preflight/runtime error taxonomy.
- `fixtures/valid/`: valid contract examples.
- `fixtures/invalid/`: invalid examples and expected rejection reasons.
- `vectors/`: RFC 8785/JCS SHA-256 and Ed25519 fixtures.
- `evidence/`: generated artifact manifest and validation report.
- `scripts/contract_tools.py`: materializer and verifier.
- `tests/test_contracts.py`: pytest coverage for the materialized contracts.

## Commands

Regenerate all materialized artifacts:

```powershell
python specs/admin-ui/step5c-controlled-live-execution/contracts/scripts/contract_tools.py materialize
```

Verify schemas, fixtures, digests, signatures, and artifact hashes:

```powershell
python specs/admin-ui/step5c-controlled-live-execution/contracts/scripts/contract_tools.py verify --write-report
python -m pytest specs/admin-ui/step5c-controlled-live-execution/contracts/tests
```

