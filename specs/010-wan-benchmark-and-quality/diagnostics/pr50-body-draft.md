# PR 50 — recovery implementation and sealed diagnostic outcome

## Scope

This PR continues the existing isolated-sidecar source line. It does not open a
second implementation line and does not claim an official profile-selection
campaign.

The source remediation covers native-authoritative `RECORD_VOTE`, POSIX
durable-directory identity and rebind hardening, the mandatory real-SHM path,
supervisor/copy-evidence race closure, and fail-closed diagnostic tooling.
Protected formal semantics remain unchanged at
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

## Frozen identities

- Diagnostic source S: `a745fc15b81de516f5c4899230be39c502f832d6`
- `tree(S)`: `cac8dcc4736a1596301e2e59cbae63f204e8e489`
- Executable manifest M: `a81365b0d4be6b4be3cd2efd30690061b89ccc75`
- Campaign: `s15v2-pr50-diagnostic-20260923-144fab48`
- Allocation manifest:
  `sha256:3ef44c421958e5d12d646950fcb56087251c75538d9db5e051353980da33233a`
- Container image:
  `sha256:717394ce7e252ab0f310b43d2b5f10c7875d4ee8393a4ea5e952529fe8024195`

## One-shot diagnostic outcome

The preregistered campaign passed its non-consuming preflight, durably created
its attempt and execution-started seals, then terminated fail-closed before any
lane began. PowerShell parsed the unparenthesized wait expression as two
collector arguments (`120`, `300`), so the host collector rejected the extra
positional argument.

- Terminal state: `FAILED_NO_RERUN`
- Error type: `HostWrapperFailure`
- Exact message: `A positional parameter cannot be found that accepts argument '300'.`
- Attempt seal:
  `sha256:677acd97ddc2eb96b0e7ac1eb3ebe35d65d2b284da2a0d79bf6431050895571e`
- Execution-started seal:
  `sha256:4000ac2c9cd3f6d73af500e4b94882110f69fab658fd1818666b9ee11ef398cb`
- Failure seal:
  `sha256:fc4fdce2b28c39c8cbc6c49eafe807546a97f68eeccf8ec209a5851db7638a8f`
- Terminal seal:
  `sha256:99a691d363d20a39a3964a65d76653fedc557b8418661b0262e33f16c5badac4`

No evidence directory or lane result was created, so there is no diagnostic
classification to report. It is not relabelled as `INCONCLUSIVE` or as a
runtime result, and the campaign is not rerun. The wrapper defect is fixed by
commit `49e99df256e0ed0cb55d64dbefb834601e231cf9`, with a regression proving the
collector receives exactly nine arguments and the computed wait is 420 seconds.
A fresh campaign requires explicit graph authorization.

## Validation

- Feature 010 Python suite: 320 passed on Windows and 320 passed in the pinned
  Linux image before the one-shot run.
- Diagnostic-focused suite after the wrapper fix: 96 passed.
- Ruff check/format, PowerShell parser, and `git diff --check`: passed.
- Allocation assembly and independent read-only verification: passed; all six
  preregistered JFR events were enabled before sealing.
- Native and Java/SHM conformance evidence remains as recorded in the PR
  history; independent source audits approved the recovery implementation.

## Authority and claims

- Official comparison: not run.
- Frozen offered rate: unchanged at 100/s.
- `selected_profile`: `null`.
- Diagnostic evidence is assembler-ineligible.
- Gate A/B/C/D qualification: none claimed.
- `BenchmarkResultQC`: absent.
- Feature 010 GO: false.
- Feature 011 authority: false.

The three prior comparison attempts remain immutable `INCOMPLETE` history. The
failed diagnostic is retained as immutable terminal evidence and is not used as
input to the official comparison assembler.
