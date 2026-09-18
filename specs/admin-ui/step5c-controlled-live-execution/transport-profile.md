# Transport Implementation Profile: Step 5C Controlled Live Execution

**Status**: Accepted  
**Increment**: Step 5C  
**Base ADR**: ADR 0002 (Controlled Live Execution)  
**Security Boundary**: Zone 1 (Untrusted Browser) <-> Zone 2 (Trusted Authorization Gate) <-> Zone 3 (Constrained Worker)  

---

## 1. Scope and Trust Invariants

This profile specifies the concrete HTTP/JSON transport bindings for Step 5C controlled live execution between the Admin UI (Zone 1) and the Authorization Gate / Controller (Zone 2), and internal execution bridging to the Constrained Worker (Zone 3).

### Strict Invariants:
1. **Zero Consensus Mutation**: Step 5C transport has no socket, RPC, or memory connection to Zone 4 (Delta Consensus Spine: `delta-core-cpp`, `delta-runtime-cpp`, `delta-ffi`, `delta-node-java`).
2. **Untrusted Client Metadata**: `declared_operator` in `ExecutionIntent` is client metadata only. Authorization is derived solely from transport-level authenticated identity (`AuthenticatedSubject`).
3. **Fail-Closed Verification**: Any malformed payload, signature mismatch, JCS digest mismatch, expired TTL, or unrecognized schema version results in immediate typed preflight rejection without starting a worker.
4. **Idempotency Guarantee**: Identical resubmission under the same `intent_id` and caller subject returns cached state; conflicting payload or conflicting subject under the same `intent_id` is rejected; digest collision under a new ID fails closed (`ERR_INTENT_COLLISION_DETECTED`).

---

## 2. API Endpoints and Transport Protocols

Transport: HTTP/1.1 or HTTP/2 over TLS (HTTPS) in remote deployments; HTTP over loopback (`127.0.0.1`) allowed for local-only testing.

### 2.1 Intent Submission
- **Method**: `POST /api/v1/intent/submit`
- **Request Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` or peer credential header
  - `X-Delta-Request: 1` (anti-CSRF protection)
- **Request Body**: `ExecutionIntent` JSON document (max 10 MB).
- **Responses**:
  - `201 Created`: Newly admitted intent. Body contains `action: "ADMITTED"`, `admission: <AdmissionRecord>`, `status: <ExecutionStatus>`.
  - `200 OK`: Idempotent resubmission of already admitted intent. Body contains `action: "ALREADY_ADMITTED"`, `admission`, `status`, `receipt` (if completed).
  - `400 Bad Request`: `ERR_SCHEMA_VALIDATION_FAILED` or `ERR_INTENT_DIGEST_MISMATCH`.
  - `401 Unauthorized`: `ERR_UNAUTHORIZED_CALLER` (missing/invalid credential).
  - `403 Forbidden`: `ERR_OPERATION_SCOPE_UNSUPPORTED` or role permission failure.
  - `409 Conflict`: `ERR_INTENT_ID_DIGEST_CONFLICT` or `ERR_INTENT_COLLISION_DETECTED`.
  - `413 Payload Too Large`: Body exceeds 10 MB limit.
  - `429 Too Many Requests`: `ERR_CONCURRENCY_LIMIT_EXCEEDED` (quota/concurrency limit).

### 2.2 Status Inquiry
- **Method**: `GET /api/v1/execution/{execution_id}/status`
- **Responses**:
  - `200 OK`: `ExecutionStatus` read model conforming to `execution-status.schema.json`.
  - `404 Not Found`: Execution ID unknown.
  - `401 / 403`: Caller not authorized to inspect this execution.

### 2.3 Terminal Receipt Retrieval
- **Method**: `GET /api/v1/execution/{execution_id}/receipt`
- **Responses**:
  - `200 OK`: Terminal `ExecutionReceipt` JSON document.
  - `404 Not Found`: Execution incomplete, failed, or operation not receipt-eligible (`MATERIALIZE_DATASET`).

### 2.4 Cancellation Request
- **Method**: `POST /api/v1/execution/{execution_id}/cancel`
- **Responses**:
  - `200 OK`: `ExecutionStatus` updated to `CANCELLED`.
  - `409 Conflict`: Execution already in terminal state.

---

## 3. Security, Quotas, and Operational Safeguards

1. **Size Limits**:
   - Max Request Size: 10,485,760 bytes (10 MB).
   - Max JSON Parsing Depth: 32.
   - Max Coordinate Array Length: 4096 items (signed 32-bit integers).
2. **Backpressure and Quotas**:
   - Controller tracks active concurrent executions via `IdempotencyLedger.active_count()`.
   - Global concurrency cap: default 4 concurrent jobs.
   - Per-operator quota: default 2 concurrent jobs.
   - Exceeded quotas return HTTP 429 with `ERR_CONCURRENCY_LIMIT_EXCEEDED` without starting a worker.
3. **Timeouts**:
   - HTTP transport socket timeout: 30 seconds.
   - Admission TTL (`admission_expires_at`): default 300 seconds (cannot exceed `intent.expires_at`).
   - Worker execution timeout: bounded by `resource_grants.timeout_seconds` (max 3600 seconds).
4. **Secret Handling**:
   - Private Ed25519 signing keys reside exclusively in Zone 2 memory/keystore.
   - Authorization tokens and credentials are redacted in all logs and audit events (`[REDACTED]`).
   - Zero sensitive tokens in URL query strings.
5. **CORS and Origin Isolation**:
   - Origin header validated against configured allowed origins (`http://localhost:*` in local mode).
   - Requests without `X-Delta-Request: 1` rejected with HTTP 400.
