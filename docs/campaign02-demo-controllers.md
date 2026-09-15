# Campaign 02 local demo controllers

This development tool creates four fresh, synthetic Ed25519 controllers for local
signature and quorum testing while the real controller-custody governance process
remains open. It does not modify, satisfy, or supersede PR #29.

The generated public validator-set document is intentionally compatible with
`BootstrapValidatorSet.from_dict`, allowing local tests to exercise the production
signature verifier. Every controller and signer ID starts with `demo-campaign02-`,
and the adjacent manifest fixes these boundaries:

- `environment: LOCAL_DEMO_ONLY`;
- `authoritative: false`;
- `governance_eligible: false`;
- `execution_authorized: false`;
- `custody_kind: DEMO_SOFTWARE_FILE`;
- `governance_status: NOT_APPOINTED`;
- `independence_claimed: false`.

The key pairs themselves are real and cryptographically valid. The manifest and
smoke output therefore report `valid_for_demo_testing: true` and
`keys_cryptographically_valid: true`, while always reporting
`valid_for_campaign02_governance: false`.

The tool never persists votes, signatures, attestations, authority bundles,
controller appointments, `BenchmarkDefinitionQC`, `BenchmarkResultQC`, or an
execution authorization. The presentation smoke creates signatures only in memory
and discards them immediately. Passing a local test with demo controllers cannot
satisfy Campaign 02 governance or authorize `REGISTER_ONLY`, `EXECUTE_STAGE_A`,
Feature 010 GO, or Feature 011.

## One-command presentation smoke

For a commission or product walkthrough, use a fresh destination:

```powershell
uv run delta-demo-controllers demo `
  --output-dir artifacts/local/campaign02-demo-controllers/commission-run-01 `
  --pretty
```

The command generates the controllers and then calls the production Campaign 02
bootstrap parser and signature verifier. It verifies a real synthetic `3-of-4`
Ed25519 quorum, proves that `2-of-4` is rejected, and proves that a forged signature
is rejected. The presentation keeps the demo boundary and the absence of execution
authority visible beside the green cryptographic checks.

Omit `--pretty` to receive machine-readable JSON. Successful JSON contains:

```json
{
  "authoritative": false,
  "demo_status": "DEMO_PASS",
  "execution_authorized": false,
  "governance_eligible": false,
  "keys_cryptographically_valid": true,
  "valid_for_campaign02_governance": false,
  "valid_for_demo_testing": true
}
```

The full one-line JSON also lists all four checks, the synthetic mapping ID, the
demo validator-set ID, and the three signer IDs used by the successful quorum. It
never prints or writes vote signatures.

For the visual walkthrough, open `controller-register.demo.json` from the generated
directory in Delta Admin UI. It contains the same four public keys and synthetic
controller identities, carries `authority_class: LOCAL_FIXTURE`, and remains marked
`DEMO_VALID_FOR_TESTING` throughout the presentation. This status means the key
bindings are cryptographically valid inside the demo, never that the controllers
are appointed.

## Generate only

From the repository root:

```powershell
uv run delta-demo-controllers generate `
  --output-dir artifacts/local/campaign02-demo-controllers/run-01
```

The destination must not already exist. The tool refuses to overwrite prior keys.
It creates:

```text
DEMO-ONLY.txt
demo-controller-manifest.json
bootstrap-validator-set.demo.json
controller-register.demo.json
private/
  demo-campaign02-signer-01.demo-controller-private.pem
  demo-campaign02-signer-02.demo-controller-private.pem
  demo-campaign02-signer-03.demo-controller-private.pem
  demo-campaign02-signer-04.demo-controller-private.pem
```

The `artifacts/` root and the demo private-key filename pattern are ignored by Git.
Private keys are unencrypted PKCS#8 software files for disposable local testing.
On Windows, verify the output directory ACL because POSIX-style `0600` modes alone
do not establish a Windows custody boundary.

## Verify

```powershell
uv run delta-demo-controllers verify `
  --output-dir artifacts/local/campaign02-demo-controllers/run-01
```

Verification checks the demo-only markers, exact file inventory, validator-set
content identity, four unique production-parser-compatible public keys, and every
private/public key pair. Delete the entire local output directory after testing.

Never copy demo identities, public keys, private keys, fingerprints, or generated
validator-set bytes into PR #29, governance evidence, CI secrets, production, or a
pilot package.
