# Delta Working Version: single-host runbook

This runbook starts the reviewable morning working version on one machine. The local profile is
loopback-only and requires no Docker service. It runs the Step 5C Controller HTTP host, constrained
Python Worker subprocesses, and the live Admin UI static artifact. The native C++ runtime and JVM
node remain reference-only: this launcher does not start them and makes no consensus, WAN, or
multi-region qualification claim.

## Runtime identity

Every process is bound to these compatibility facts at startup:

- `build_id`: the exact 40-character Git `HEAD` passed by the launcher;
- HTTP protocol: `deltareduce.step5c.http.v1`;
- contract schema: `1.0.0`;
- formal semantics: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

Startup fails closed when the deployment descriptor disagrees with those values. The current build
ID and compatibility facts are also exposed by the health/readiness documents.

## Prerequisites

- Git;
- PowerShell 7 (`pwsh`);
- Python 3.12;
- `uv 0.6.14` or the repository-approved compatible `uv`;
- Node.js 22 and npm.

From a clean checkout, no separate install command is required. The `start` action runs the locked
installs and live build:

```powershell
uv sync --frozen
npm --prefix tools/admin-ui ci --ignore-scripts
npm --prefix tools/admin-ui run build:live
```

The checked-in source descriptor is
`configs/working-version/local.json`. It binds exactly `127.0.0.1:8765` and allows only the exact
origin `http://127.0.0.1:8765`.

## Start, inspect, smoke, and stop

Run all commands from the repository root.

```powershell
pwsh -NoProfile -File tools/working-version/delta-local.ps1 start
pwsh -NoProfile -File tools/working-version/delta-local.ps1 status
pwsh -NoProfile -File tools/working-version/delta-local.ps1 smoke
pwsh -NoProfile -File tools/working-version/delta-local.ps1 stop
```

`start` refuses a dirty checkout by default, resolves the exact Git `HEAD`, installs from
`uv.lock`/`package-lock.json`, builds `tools/admin-ui/dist-live`, starts
`uv run delta-working-version` in a hidden background process, and waits for `GET /readyz`.
`status` returns `READY`, `RUNNING_NOT_READY`, `STALE_METADATA`, or `STOPPED`. `stop` creates the
launch-scoped shutdown request and waits for the exact PID/start-time identity to exit. It reports
`graceful=true` and removes lifecycle metadata only after the supervisor durably records exit code
zero; it deliberately does not force-kill a process that misses the grace period.
Startup rollback follows the same rule: if the supervised process tree does not acknowledge its
launch-scoped shutdown request, the launcher retains PID/start-time metadata instead of killing
only the supervisor and orphaning its `uv`/Controller descendants.

Open `http://127.0.0.1:8765/` after readiness. The host serves the live UI and API from the same
origin. The separate offline UI remains selectable through its normal offline build and retains
`connect-src 'none'`.

The smoke action performs real loopback HTTP calls:

1. health and readiness;
2. transport rejection without `X-Delta-Request: 1`;
3. submit followed by immediate cancellation and proof that no success receipt exists;
4. submit, status polling, terminal receipt retrieval, and exact intent/admission/execution lineage
   checks.

For a development-only uncommitted candidate, add `-AllowDirty`. To reuse an already materialized
Python environment and `dist-live`, add `-SkipInstall`. Neither switch belongs in release evidence.

## Durable data and restart

The default data directory is
`$env:LOCALAPPDATA\DeltaReduce\working-version` (or the OS temporary directory only when
`LOCALAPPDATA` is unavailable). Override it explicitly when needed:

```powershell
pwsh -NoProfile -File tools/working-version/delta-local.ps1 start `
  -DataDir D:\delta-data\working-version
```

The launcher refuses a reparse-point data directory. The host takes an exclusive lease and owns:

- the append-only idempotency ledger and terminal receipts;
- the Controller Ed25519 private signing key;
- the Worker public trust-root document;
- redacted audit/runtime logs and lifecycle state.

The private key and trust roots are generated only by the explicit local
`--bootstrap-local-identity` startup. The browser bundle and repository never receive them.
The local profile does not inherit the remote `DELTA_*` key, authentication, or TLS path
variables from the operator shell; explicit local/remote security inputs cannot be mixed.
Protect, back up, and restore the data directory as one unit. Do not copy only the private key or
only the trust-root file: startup rejects a mismatched pair.

The Worker is a fixed-command child process with a sanitized environment and validated output,
not an OS privilege or hostile-code sandbox. It runs as the same account as the Controller. Do not
install unreviewed plugins or claim key isolation, crash containment, or malicious-Worker
containment from this profile. An abrupt parent crash can leave an already-started child alive
until its execution deadline; restart marks the durable non-terminal record failed and never
publishes its receipt, but stronger process containment requires a separate OS identity/sandbox.

Restart without deleting or moving the data directory:

```powershell
pwsh -NoProfile -File tools/working-version/delta-local.ps1 stop
pwsh -NoProfile -File tools/working-version/delta-local.ps1 start -SkipInstall
```

Completed status and receipt documents survive this restart. A non-terminal job interrupted by a
process restart is recovered fail-closed and cannot fabricate a success receipt; retry it with a
fresh `intent_id`.

## Local authentication and HTTP controls

The local profile derives `AuthenticatedSubject` only from the accepted socket peer
`127.0.0.1`. Client JSON, `declared_operator`, query parameters, and identity-like headers cannot
select the trusted subject or roles. The configured local subject is `local.operator` with the
effective `OPERATOR` role.

API requests require:

- an exact configured `Origin` whenever the client supplies that header (the shipped browser and
  smoke client do);
- `X-Delta-Request: 1`;
- `Content-Type: application/json` for POST bodies;
- a declared body length no greater than 10 MiB;
- JSON nesting depth no greater than 32.

The HTTP mapping is intentionally explicit: malformed/CSRF requests are `400`, missing or invalid
remote credentials are `401`, policy/ownership failures are `403`, identity/idempotency or terminal
cancel conflicts are `409`, oversized bodies are `413`, and quota/backpressure rejection is `429`.
TLS handshake, HTTP headers, and HTTP body intake share one absolute 30-second monotonic deadline;
a client cannot extend it by trickling bytes. The queue, in-flight requests, and Worker process
count are bounded by the descriptor. This deadline does not claim to interrupt an in-progress
durability operation inside the trusted Controller (for example an OS/filesystem call that never
returns). On such a storage/runtime stall, graceful stop intentionally remains fail-closed and
keeps the data-directory lease instead of allowing a second Controller to open the same state;
the launcher reports the stop timeout and retains metadata/diagnostics for operator recovery.

The public working-version endpoints are:

```text
GET  /healthz
GET  /readyz
POST /api/v1/intent/submit
GET  /api/v1/execution/{execution_id}/status
GET  /api/v1/execution/{execution_id}/receipt
POST /api/v1/execution/{execution_id}/cancel
```

## Configuration and environment

Local lifecycle settings are launcher parameters, not secrets:

| Setting | Default | Meaning |
| --- | --- | --- |
| `-Config` | `configs/working-version/local.json` | Deployment descriptor |
| `-DataDir` | `%LOCALAPPDATA%\DeltaReduce\working-version` | Durable owner directory |
| `-ReadyTimeoutSeconds` | `90` | Readiness wait |
| `-ShutdownTimeoutSeconds` | `75` | Graceful-stop observation bound; timeout retains the exact process metadata and does not force-kill |
| `-SkipInstall` | off | Reuse locked dependencies and `dist-live` |
| `-AllowDirty` | off | Development-only dirty-tree override |

`configs/working-version/remote.example.json` is a fail-closed configuration example, not a WAN
qualification. A remote start requires all of the following external secret/config paths:

- `DELTA_TLS_CERT_FILE`: server certificate chain;
- `DELTA_TLS_KEY_FILE`: matching TLS private key;
- `DELTA_REMOTE_AUTH_CONFIG`: bearer-token SHA-256 fingerprint and subject mapping;
- `DELTA_SIGNING_KEY_FILE`: explicit Controller Ed25519 private-key path;
- `DELTA_WORKER_TRUST_ROOTS_FILE`: explicit matching Worker public trust-root path.

The remote auth configuration contains fingerprints, never bearer plaintext:

```json
{
  "schema_version": "1.0.0",
  "token_subjects": [
    {
      "token_sha256": "64-lowercase-hex-characters",
      "subject_id": "operator.example",
      "effective_roles": ["OPERATOR"]
    }
  ]
}
```

An HTTPS API client sends the corresponding raw bearer value only in the `Authorization` header.
The server hashes it before lookup. The live browser bundle never reads or constructs that secret;
therefore a remote browser UI additionally requires a separately reviewed same-origin
authentication gateway that owns the browser session and injects the Bearer header server-side.
That gateway is not shipped or qualified by this single-host working version. Remote mode never
bootstraps an Admission signing identity; both the private signing key and matching public trust
roots must already exist.

Remote origins must be explicit `https://` origins; wildcards and cleartext remote binds are
rejected. Never put token plaintext, TLS private keys, or the Admission private key in a descriptor,
browser bundle, command-line argument, or repository file.

## Verification and logs

The local process writes stdout/stderr beneath the selected data directory. Audit logging redacts
authorization and secret-bearing values. When startup fails before readiness, the launcher reports
the tail of stderr without printing credentials.

Run the black-box clean-checkout lifecycle test with:

```powershell
uv run pytest integration/working-version -q
```

Run the component/repository gates before publishing:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy delta-controller-python/src delta-worker-python/src
uv run pytest delta-controller-python/tests
uv run pytest delta-worker-python/tests/live_execution
uv run pytest specs/admin-ui/step5c-controlled-live-execution/contracts/tests
uv run pytest specs/admin-ui/step5c-controlled-live-execution/tests
npm --prefix tools/admin-ui run check
npm --prefix tools/admin-ui run check:live
npm --prefix tools/admin-ui run audit:repository
git diff --check
```

This profile proves one-machine controlled execution only. It does not qualify public Internet
exposure, WAN or multi-region operation, native/JVM consensus participation, crash isolation for an
embedded native runtime, or `STAGE_C_REAL_DRQ1`.
