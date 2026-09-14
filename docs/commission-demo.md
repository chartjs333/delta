# DeltaReduce commission demo

This bounded local walkthrough presents a functioning end-to-end product path
without waiting for the separate human governance process in PR #29. It composes
existing repository interfaces instead of replacing their safety checks.

For a commission-facing visual demonstration, prefer the distributed MNIST
workspace documented in `docs/mnist-demo.md`. It shows real handwritten digits,
four isolated data shards, a real Netty/native Delta path through six QC phases to
`APPLIED`, centralized-versus-distributed quality, and durable crash/recovery behind
one **Запустить демо** button. Its execution diagram and source-bound trace make the
participating production components inspectable. The lower-level walkthrough in
this document remains useful for protocol, artifact and WAN smoke evidence.

## What the commission can see

One command demonstrates:

1. the accepted Formal GO and exact formal-semantics identity;
2. four synthetic controllers with freshly generated, cryptographically valid
   Ed25519 key pairs;
3. a real `3-of-4` quorum accepted by the production Campaign 02 verifier;
4. rejection of `2-of-4` and a forged signature;
5. real PyTorch CPU training over the repository's tiny deterministic corpus;
6. content-addressed checkpoint and training-artifact verification;
7. deterministic local WAN delay/loss/reordering behavior;
8. the complete non-primary synthetic benchmark control plane and offline evidence
   verification;
9. a static presentation report with stage-by-stage PASS results.

Run from the repository root with a fresh destination:

```powershell
uv run delta-commission-demo `
  --output-dir artifacts/local/commission-demo/run-01 `
  --open-browser
```

For a prepared Windows presentation, use the one-click wrapper. It runs with
`uv --offline`, chooses a fresh timestamped output directory, and opens the report:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run-commission-demo.ps1
```

Materialize the locked dependencies once before the presentation with
`uv sync --frozen`. The wrapper then makes no public network request. Use
`-NoBrowser` when validating it from CI or a terminal-only session.

The command refuses to overwrite an earlier run. After completion it prints a
machine-readable summary and opens:

```text
artifacts/local/commission-demo/run-01/commission-demo-report.html
```

The same directory contains the JSON report, immutable training bundle, synthetic
benchmark evidence, and the local demo-controller bundle. Everything under
`artifacts/` is excluded from Git.

## Exact presentation wording

Safe statement:

> This is a local end-to-end DeltaReduce product demonstration. It performs real
> CPU model training and artifact verification, exercises deterministic WAN faults,
> and verifies a real three-of-four Ed25519 quorum using four synthetic controllers.

Do not call it a real Campaign 02 run. The report explicitly records:

```text
authoritative: false
governance_eligible: false
execution_authorized: false
feature_010_go_claimed: false
```

The demo does not run `REGISTER_ONLY`, `EXECUTE_STAGE_A`, real-WAN execution,
production or pilot nodes, and does not create `BenchmarkDefinitionQC` or
`BenchmarkResultQC`. PR #29 remains open and unchanged until real controller
identity, custody, independence, and human approvals are complete.
