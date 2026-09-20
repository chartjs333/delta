import { describe, expect, it, vi } from "vitest";

import { AdminUiError } from "../src/core/errors";
import {
  computeSha256PrefixedSync,
  jcsCanonicalize,
} from "../src/modules/live-execution/canonical-jcs";
import { HttpLiveExecutionAdapter } from "./http-live-execution-adapter";

const INTENT_ID = "11111111-1111-4111-8111-111111111111";
const ADMISSION_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const EXECUTION_ID = "55555555-5555-4555-8555-555555555555";
const INTENT_DIGEST = `sha256:${"1".repeat(64)}`;
const ADMISSION_DIGEST = `sha256:${"2".repeat(64)}`;
const BUILD_ID = "b".repeat(40);
const OTHER_BUILD_ID = "c".repeat(40);
const WORKLOAD_CONFIG_DIGEST =
  "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8";

const intent = {
  schema_version: "1.0.0",
  intent_id: INTENT_ID,
  intent_digest: INTENT_DIGEST,
  workload: {
    model_plugin_id: "tabular-10gene-phenotype-v1",
    dataset_id: "synthetic-10gene-cohort-v1",
    requested_scope: "PLUGIN_BOUNDARY",
  },
  operation: "TRAIN_TICKET",
};

function status(
  state: string,
  terminal = ["COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"].includes(state),
) {
  return {
    schema_version: "1.0.0",
    execution_id: EXECUTION_ID,
    intent_id: INTENT_ID,
    intent_digest: INTENT_DIGEST,
    admission_id: ADMISSION_ID,
    admission_digest: ADMISSION_DIGEST,
    operation: "TRAIN_TICKET",
    state,
    terminal,
    updated_at: "2026-09-20T08:00:00.000Z",
    ...(state === "COMPLETED"
      ? {
          receipt_digest: computeSha256PrefixedSync(
            jcsCanonicalize(receipt()),
          ),
        }
      : {}),
    ...(["FAILED", "TIMED_OUT", "CANCELLED"].includes(state)
      ? { error: { code: "ERR_EXECUTION_TERMINAL", message: "terminal" } }
      : {}),
  };
}

function readiness(overrides: Record<string, unknown> = {}) {
  return {
    schema_version: "1.0.0",
    status: "READY",
    build_id: BUILD_ID,
    protocol_id: "deltareduce.step5c.http.v1",
    contract_schema_version: "1.0.0",
    formal_semantics_id:
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
    ...overrides,
  };
}

function admission() {
  return {
    schema_version: "1.0.0",
    admission_id: ADMISSION_ID,
    intent_id: INTENT_ID,
    intent_digest: INTENT_DIGEST,
    execution_id: EXECUTION_ID,
    authenticated_subject: {
      subject_id: "operator.local",
      authenticated_via: "LOCAL_PEER_CREDENTIAL",
      effective_roles: ["OPERATOR"],
    },
    policy_context: {
      policy_version: "step5c-policy-v1",
      controller_commit: BUILD_ID,
      verdict: "ADMITTED",
    },
    resource_grants: {
      max_memory_bytes: 2_147_483_648,
      timeout_seconds: 900,
      allow_downloads: false,
    },
    admitted_at: "2026-09-20T08:00:00.000Z",
    admission_expires_at: "2026-09-20T08:15:00.000Z",
    admission_digest: ADMISSION_DIGEST,
    authenticator: {
      issuer_id: "working-version-controller",
      key_id: "working-version-key",
      algorithm: "ED25519",
      signature: "0".repeat(128),
    },
  };
}

function receipt() {
  return {
    schema_version: "1.0.0",
    receipt_type: "DELTAREDUCE_EXECUTION_RECEIPT",
    provenance: {
      repository: "chartjs333/delta",
      backend_commit: "670b58f6458fe84620f4f9f46401f855d04ae05d",
      catalog_backend_ref: "670b58f6458fe84620f4f9f46401f855d04ae05d",
      producer_commit: BUILD_ID,
      controller_commit: BUILD_ID,
      produced_at: "2026-09-20T08:00:00.000Z",
      intent_id: INTENT_ID,
      intent_digest: INTENT_DIGEST,
      admission_id: ADMISSION_ID,
      admission_digest: ADMISSION_DIGEST,
      execution_id: EXECUTION_ID,
    },
    workload: {
      model_plugin_id: "tabular-10gene-phenotype-v1",
      dataset_id: "synthetic-10gene-cohort-v1",
      executed_scope: "PLUGIN_BOUNDARY",
      workload_config_digest: WORKLOAD_CONFIG_DIGEST,
    },
    execution: { verdict: "SUCCESS", terminal_status: "COMPLETED" },
  };
}

function jsonResponse(body: unknown, statusCode = 200): Response {
  const text = JSON.stringify(body);
  return {
    ok: statusCode >= 200 && statusCode < 300,
    status: statusCode,
    headers: {
      get(name: string) {
        return name.toLowerCase() === "content-length"
          ? String(new TextEncoder().encode(text).byteLength)
          : null;
      },
    },
    text: async () => text,
  } as Response;
}

type FetchHandler = (
  input: string | URL | Request,
  init?: RequestInit,
) => Response | Promise<Response>;

function fetchWithReadiness(
  handler: FetchHandler,
  readinessDocument: Record<string, unknown> = readiness(),
) {
  return vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    if (String(input) === "/readyz") return jsonResponse(readinessDocument);
    return handler(input, init);
  });
}

function nestedArrays(count: number): unknown {
  let value: unknown = "leaf";
  for (let level = 0; level < count; level += 1) value = [value];
  return value;
}

function adapterFor(fetchMock: ReturnType<typeof vi.fn>) {
  return new HttpLiveExecutionAdapter({
    fetchImpl: fetchMock as unknown as typeof fetch,
    pageUrl: new URL("http://127.0.0.1:8765/live.html"),
  });
}

describe("HttpLiveExecutionAdapter", () => {
  it("allows loopback HTTP or HTTPS and rejects remote plaintext HTTP", async () => {
    const fetchMock = fetchWithReadiness(() => {
      throw new Error("Unexpected API request");
    });
    const loopback = adapterFor(fetchMock);
    expect((await loopback.describeLiveSource()).transportProfile).toBe(
      "HTTP_SAME_ORIGIN_LOOPBACK",
    );

    const secure = new HttpLiveExecutionAdapter({
      fetchImpl: fetchMock as unknown as typeof fetch,
      pageUrl: new URL("https://delta.example.test/live.html"),
    });
    expect((await secure.describeLiveSource()).transportProfile).toBe(
      "HTTPS_SAME_ORIGIN",
    );

    expect(
      () =>
        new HttpLiveExecutionAdapter({
          fetchImpl: fetchMock as unknown as typeof fetch,
          pageUrl: new URL("http://delta.example.test/live.html"),
        }),
    ).toThrowError(AdminUiError);
  });

  it.each([
    ["readiness schema", { schema_version: "2.0.0" }],
    ["readiness state", { status: "DRAINING" }],
    ["HTTP protocol", { protocol_id: "deltareduce.step5c.http.v2" }],
    ["contract schema", { contract_schema_version: "2.0.0" }],
    ["formal semantics", { formal_semantics_id: `sha256:${"0".repeat(64)}` }],
    ["build identity", { build_id: BUILD_ID.toUpperCase() }],
  ])("fails closed and caches an incompatible %s handshake", async (_label, overrides) => {
    const fetchMock = fetchWithReadiness(
      () => {
        throw new Error("API request must not follow a failed handshake");
      },
      readiness(overrides),
    );
    const adapter = adapterFor(fetchMock);

    await expect(adapter.describeLiveSource()).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
    await expect(adapter.submitIntent(intent)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
    expect(fetchMock.mock.calls.map(([path]) => String(path))).toEqual([
      "/readyz",
    ]);
  });

  it("uses the Controller/Worker root-depth convention at the depth-32 boundary", async () => {
    const accepted = adapterFor(
      fetchWithReadiness(
        () => {
          throw new Error("Unexpected API request");
        },
        readiness({ padding: nestedArrays(30) }),
      ),
    );
    await expect(accepted.describeLiveSource()).resolves.toMatchObject({
      mode: "HTTP_LIVE",
    });

    const rejected = adapterFor(
      fetchWithReadiness(
        () => {
          throw new Error("Unexpected API request");
        },
        readiness({ padding: nestedArrays(31) }),
      ),
    );
    await expect(rejected.describeLiveSource()).rejects.toMatchObject({
      code: "INPUT_LIMIT_EXCEEDED",
    });
  });

  it("submits only to the same-origin API with anti-CSRF headers and no script token", async () => {
    const fetchMock = fetchWithReadiness(async () =>
      jsonResponse(
        { action: "ADMITTED", admission: admission(), status: status("RUNNING") },
        201,
      ),
    );
    const adapter = adapterFor(fetchMock);

    const result = await adapter.submitIntent(intent);
    expect(result.state).toBe("RUNNING");
    expect(result.authority).toBe("CONTROLLER_HTTP_STATUS");
    expect(result.workload?.modelPluginId).toBe(
      "tabular-10gene-phenotype-v1",
    );

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [readinessPath, readinessInit] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(readinessPath).toBe("/readyz");
    expect(readinessInit).toMatchObject({
      method: "GET",
      cache: "no-store",
      credentials: "same-origin",
      redirect: "error",
    });
    expect(readinessInit.headers).toEqual({ Accept: "application/json" });

    const [path, init] = fetchMock.mock.calls[1] as unknown as [
      string,
      RequestInit,
    ];
    expect(path).toBe("/api/v1/intent/submit");
    expect(init.credentials).toBe("same-origin");
    expect(init.cache).toBe("no-store");
    expect(init.redirect).toBe("error");
    expect(init.headers).toMatchObject({
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-Delta-Request": "1",
    });
    expect(
      Object.keys(init.headers as Record<string, string>).map((key) =>
        key.toLowerCase(),
      ),
    ).not.toContain("authorization");
    expect(JSON.parse(String(init.body))).toEqual(intent);
  });

  it.each([
    [
      "admission intent ID",
      (nextAdmission: ReturnType<typeof admission>) => {
        nextAdmission.intent_id = "22222222-2222-4222-8222-222222222222";
      },
    ],
    [
      "admission execution ID",
      (nextAdmission: ReturnType<typeof admission>) => {
        nextAdmission.execution_id = "66666666-6666-4666-8666-666666666666";
      },
    ],
    [
      "admission digest",
      (
        nextAdmission: ReturnType<typeof admission>,
        nextStatus: ReturnType<typeof status>,
      ) => {
        nextStatus.admission_digest = `sha256:${"3".repeat(64)}`;
        nextAdmission.admission_digest = ADMISSION_DIGEST;
      },
    ],
    [
      "status intent digest",
      (
        _nextAdmission: ReturnType<typeof admission>,
        nextStatus: ReturnType<typeof status>,
      ) => {
        nextStatus.intent_digest = `sha256:${"4".repeat(64)}`;
      },
    ],
    [
      "status operation",
      (
        _nextAdmission: ReturnType<typeof admission>,
        nextStatus: ReturnType<typeof status>,
      ) => {
        nextStatus.operation = "EVALUATE_CHECKPOINT";
      },
    ],
    [
      "controller build",
      (nextAdmission: ReturnType<typeof admission>) => {
        nextAdmission.policy_context.controller_commit = OTHER_BUILD_ID;
      },
    ],
  ])("rejects a submission with mismatched %s lineage", async (_label, mutate) => {
    const nextAdmission = admission();
    const nextStatus = status("RUNNING");
    mutate(nextAdmission, nextStatus);
    const fetchMock = fetchWithReadiness(async () =>
      jsonResponse(
        { action: "ADMITTED", admission: nextAdmission, status: nextStatus },
        201,
      ),
    );
    const adapter = adapterFor(fetchMock);

    await expect(adapter.submitIntent(intent)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
    expect(await adapter.listStatuses()).toEqual([]);
  });

  it.each([
    [
      "nonterminal state marked terminal",
      (nextStatus: ReturnType<typeof status>) => {
        nextStatus.terminal = true;
      },
    ],
    [
      "terminal state marked nonterminal",
      (nextStatus: ReturnType<typeof status>) => {
        nextStatus.state = "COMPLETED";
        nextStatus.terminal = false;
        nextStatus.receipt_digest = computeSha256PrefixedSync(
          jcsCanonicalize(receipt()),
        );
      },
    ],
    [
      "completed receipt digest omitted",
      (nextStatus: ReturnType<typeof status>) => {
        nextStatus.state = "COMPLETED";
        nextStatus.terminal = true;
        delete nextStatus.receipt_digest;
      },
    ],
    [
      "non-completed receipt digest present",
      (nextStatus: ReturnType<typeof status>) => {
        nextStatus.receipt_digest = computeSha256PrefixedSync(
          jcsCanonicalize(receipt()),
        );
      },
    ],
    [
      "failed state without error",
      (nextStatus: ReturnType<typeof status>) => {
        nextStatus.state = "FAILED";
        nextStatus.terminal = true;
        delete nextStatus.error;
      },
    ],
  ])("rejects incoherent status metadata: %s", async (_label, mutate) => {
    const nextStatus = status("RUNNING");
    mutate(nextStatus);
    const fetchMock = fetchWithReadiness(async () =>
      jsonResponse(
        { action: "ADMITTED", admission: admission(), status: nextStatus },
        201,
      ),
    );
    const adapter = adapterFor(fetchMock);

    await expect(adapter.submitIntent(intent)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
    expect(await adapter.listStatuses()).toEqual([]);
  });

  it("uses the exact status, receipt, and cancellation endpoints with session-local cache", async () => {
    const fetchMock = fetchWithReadiness(async (input: string | URL | Request) => {
      const path = String(input);
      if (path.endsWith("/status")) return jsonResponse(status("COMPLETED"));
      if (path.endsWith("/receipt")) return jsonResponse(receipt());
      if (path.endsWith("/cancel")) return jsonResponse(status("CANCELLED"));
      return jsonResponse(
        { action: "ADMITTED", admission: admission(), status: status("RUNNING") },
        201,
      );
    });
    const adapter = adapterFor(fetchMock);
    await adapter.submitIntent(intent);

    const refreshed = await adapter.getStatus(EXECUTION_ID);
    expect(refreshed.state).toBe("COMPLETED");
    expect(refreshed.trustBadge).toBe("UNATTESTED_CONTROLLER_STATUS");

    const terminalReceipt = await adapter.getReceipt(EXECUTION_ID);
    expect(terminalReceipt.provenance.execution_id).toBe(EXECUTION_ID);
    expect(terminalReceipt.provenance.intent_id).toBe(INTENT_ID);

    const cancelled = await adapter.cancelExecution(EXECUTION_ID);
    expect(cancelled.state).toBe("CANCELLED");
    expect((await adapter.listStatuses()).map((item) => item.state)).toEqual([
      "CANCELLED",
    ]);

    expect(fetchMock.mock.calls.map(([path]) => String(path))).toEqual([
      "/readyz",
      "/api/v1/intent/submit",
      `/api/v1/execution/${EXECUTION_ID}/status`,
      `/api/v1/execution/${EXECUTION_ID}/receipt`,
      `/api/v1/execution/${EXECUTION_ID}/cancel`,
    ]);
  });

  it("fails closed when receipt lineage differs from the requested execution", async () => {
    const mismatched = receipt();
    mismatched.provenance.execution_id =
      "66666666-6666-4666-8666-666666666666";
    const fetchMock = fetchWithReadiness(async (input: string | URL | Request) => {
      const path = String(input);
      if (path.endsWith("/receipt")) return jsonResponse(mismatched);
      return jsonResponse(
        { action: "ADMITTED", admission: admission(), status: status("COMPLETED") },
        201,
      );
    });
    const adapter = adapterFor(fetchMock);
    await adapter.submitIntent(intent);

    await expect(adapter.getReceipt(EXECUTION_ID)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
  });

  it.each(["controller_commit", "producer_commit"] as const)(
    "rejects a receipt whose %s differs from the ready runtime build",
    async (field) => {
      const mismatched = receipt();
      mismatched.provenance[field] = OTHER_BUILD_ID;
      const fetchMock = fetchWithReadiness(async (input: string | URL | Request) => {
        if (String(input).endsWith("/receipt")) return jsonResponse(mismatched);
        return jsonResponse(
          {
            action: "ADMITTED",
            admission: admission(),
            status: status("COMPLETED"),
          },
          201,
        );
      });
      const adapter = adapterFor(fetchMock);
      await adapter.submitIntent(intent);

      await expect(adapter.getReceipt(EXECUTION_ID)).rejects.toMatchObject({
        code: "CAPABILITY_CONTRACT_VIOLATED",
      });
    },
  );

  it("rejects a structurally valid receipt whose JCS digest differs from status", async () => {
    const mismatched = receipt();
    mismatched.workload.workload_config_digest = `sha256:${"8".repeat(64)}`;
    const fetchMock = fetchWithReadiness(async (input: string | URL | Request) => {
      if (String(input).endsWith("/receipt")) return jsonResponse(mismatched);
      return jsonResponse(
        {
          action: "ADMITTED",
          admission: admission(),
          status: status("COMPLETED"),
        },
        201,
      );
    });
    const adapter = adapterFor(fetchMock);
    await adapter.submitIntent(intent);

    await expect(adapter.getReceipt(EXECUTION_ID)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
  });

  it("rejects a refreshed status that changes cached execution lineage", async () => {
    let submitted = false;
    const changedStatus = status("RUNNING");
    changedStatus.admission_digest = `sha256:${"7".repeat(64)}`;
    const fetchMock = fetchWithReadiness(async () => {
      if (submitted) return jsonResponse(changedStatus);
      submitted = true;
      return jsonResponse(
        { action: "ADMITTED", admission: admission(), status: status("RUNNING") },
        201,
      );
    });
    const adapter = adapterFor(fetchMock);
    await adapter.submitIntent(intent);

    await expect(adapter.getStatus(EXECUTION_ID)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
    expect((await adapter.listStatuses())[0]?.lineage.admissionDigest).toBe(
      ADMISSION_DIGEST,
    );
  });

  it("rejects nested consensus claims in a local-execution receipt", async () => {
    const inflated = receipt() as ReturnType<typeof receipt> & {
      details?: Record<string, unknown>;
    };
    inflated.details = { nested: { state_root: `sha256:${"9".repeat(64)}` } };
    const fetchMock = fetchWithReadiness(async (input: string | URL | Request) => {
      if (String(input).endsWith("/receipt")) return jsonResponse(inflated);
      return jsonResponse(
        { action: "ADMITTED", admission: admission(), status: status("COMPLETED") },
        201,
      );
    });
    const adapter = adapterFor(fetchMock);
    await adapter.submitIntent(intent);

    await expect(adapter.getReceipt(EXECUTION_ID)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });
  });

  it.each([
    [400, "DOCUMENT_STRUCTURALLY_INVALID"],
    [401, "ACCESS_DENIED"],
    [403, "ACCESS_DENIED"],
    [409, "CAPABILITY_CONTRACT_VIOLATED"],
    [413, "INPUT_LIMIT_EXCEEDED"],
    [429, "SOURCE_UNAVAILABLE"],
  ])("maps HTTP %i to typed UI error %s without reflecting server detail", async (
    statusCode,
    expectedCode,
  ) => {
    const fetchMock = fetchWithReadiness(async () =>
      jsonResponse(
        {
          error: {
            error_code: "ERR_QUOTA_EXCEEDED",
            message: "sensitive credential detail must not be reflected",
          },
        },
        statusCode,
      ),
    );
    const adapter = adapterFor(fetchMock);

    try {
      await adapter.submitIntent(intent);
      throw new Error("Expected request failure");
    } catch (error: unknown) {
      expect(error).toBeInstanceOf(AdminUiError);
      expect((error as AdminUiError).code).toBe(expectedCode);
      expect((error as Error).message).not.toContain("sensitive credential");
    }
  });

  it("rejects malformed and excessively deep Controller JSON", async () => {
    const malformedFetch = fetchWithReadiness(
      async () =>
        ({
          ok: true,
          status: 200,
          headers: { get: () => null },
          text: async () => "{bad-json",
        }) as unknown as Response,
    ) as unknown as typeof fetch;
    const malformedAdapter = new HttpLiveExecutionAdapter({
      fetchImpl: malformedFetch,
      pageUrl: new URL("http://127.0.0.1:8765/live.html"),
    });
    await expect(malformedAdapter.submitIntent(intent)).rejects.toMatchObject({
      code: "CAPABILITY_CONTRACT_VIOLATED",
    });

    let deep: unknown = "leaf";
    for (let level = 0; level < 33; level += 1) deep = [deep];
    const deepAdapter = adapterFor(
      fetchWithReadiness(async () => jsonResponse(deep)),
    );
    await expect(deepAdapter.submitIntent(intent)).rejects.toMatchObject({
      code: "INPUT_LIMIT_EXCEEDED",
    });
  });
});
