import { expect, test } from "@playwright/test";

import {
  computeSha256PrefixedSync,
  jcsCanonicalize,
} from "../../src/modules/live-execution/canonical-jcs";

const EXECUTION_IDS = [
  "55555555-5555-4555-8555-555555555555",
  "66666666-6666-4666-8666-666666666666",
] as const;
const ADMISSION_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const ADMISSION_DIGEST = `sha256:${"2".repeat(64)}`;
const BUILD_ID = "b".repeat(40);
const WORKLOAD_CONFIG_DIGEST =
  "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8";

test("explicit live entry submits, reads status and receipt, and cancels over same origin", async ({
  page,
}) => {
  const records = new Map<
    string,
    { intentId: string; intentDigest: string; operation: string }
  >();
  const apiRequests: string[] = [];
  let readinessRequests = 0;
  let submissions = 0;

  await page.route("**/readyz", async (route) => {
    const request = route.request();
    readinessRequests += 1;
    expect(request.method()).toBe("GET");
    expect(request.headers()["authorization"]).toBeUndefined();
    expect(request.headers()["x-delta-request"]).toBeUndefined();
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        schema_version: "1.0.0",
        status: "READY",
        build_id: BUILD_ID,
        protocol_id: "deltareduce.step5c.http.v1",
        contract_schema_version: "1.0.0",
        formal_semantics_id:
          "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
      }),
    });
  });

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    apiRequests.push(`${request.method()} ${url.pathname}`);
    expect(url.origin).toBe("http://127.0.0.1:4176");
    expect(request.headers()["x-delta-request"]).toBe("1");
    expect(request.headers()["authorization"]).toBeUndefined();

    if (url.pathname === "/api/v1/intent/submit") {
      expect(request.headers()["content-type"]).toContain("application/json");
      const intent = request.postDataJSON() as {
        intent_id: string;
        intent_digest: string;
        operation: string;
      };
      const executionId = EXECUTION_IDS[submissions];
      const state = submissions === 0 ? "RUNNING" : "COMPLETED";
      submissions += 1;
      records.set(executionId, {
        intentId: intent.intent_id,
        intentDigest: intent.intent_digest,
        operation: intent.operation,
      });
      await route.fulfill({
        contentType: "application/json",
        status: 201,
        body: JSON.stringify({
          action: "ADMITTED",
          admission: admissionDocument(executionId, records.get(executionId)!),
          status: statusDocument(executionId, records.get(executionId)!, state),
        }),
      });
      return;
    }

    const match = url.pathname.match(
      /^\/api\/v1\/execution\/([0-9a-f-]{36})\/(status|receipt|cancel)$/u,
    );
    expect(match).toBeTruthy();
    const executionId = match?.[1] ?? "";
    const operation = match?.[2];
    const record = records.get(executionId);
    expect(record).toBeDefined();

    if (operation === "receipt") {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(receiptDocument(executionId, record!)),
      });
      return;
    }
    const state = operation === "cancel" ? "CANCELLED" : "RUNNING";
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(statusDocument(executionId, record!, state)),
    });
  });

  await page.goto("/live.html");
  await expect(page.getByText("HTTP live · unattested")).toBeVisible();
  await expect(page.getByText("HTTP LIVE", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/#\/live-execution$/u);

  await page
    .getByRole("button", { name: "ExecutionIntent builder" })
    .click();
  await page.getByRole("button", { name: "Submit to Controller" }).click();
  await expect(page.getByRole("heading", { name: "Running" })).toBeVisible();
  await expect(page.getByText("UNATTESTED_CONTROLLER_STATUS")).toBeVisible();

  await page.getByRole("button", { name: "Refresh status" }).click();
  await page.getByRole("button", { name: "Cancel execution" }).click();
  await expect(page.getByRole("heading", { name: "Cancelled" })).toBeVisible();

  await page
    .getByRole("button", { name: "ExecutionIntent builder" })
    .click();
  await page.getByRole("button", { name: "Submit to Controller" }).click();
  await expect(page.getByRole("heading", { name: "Completed" })).toBeVisible();
  await page.getByRole("button", { name: "Load terminal receipt" }).click();
  await expect(page.getByRole("heading", { name: "Terminal receipt" })).toBeVisible();
  await expect(page.getByText("UNATTESTED PLUGIN RECORD")).toBeVisible();
  await expect(page.getByText(/not a consensus certificate/iu)).toBeVisible();

  expect(apiRequests).toEqual([
    "POST /api/v1/intent/submit",
    `GET /api/v1/execution/${EXECUTION_IDS[0]}/status`,
    `POST /api/v1/execution/${EXECUTION_IDS[0]}/cancel`,
    "POST /api/v1/intent/submit",
    `GET /api/v1/execution/${EXECUTION_IDS[1]}/receipt`,
  ]);
  expect(readinessRequests).toBe(1);
});

function admissionDocument(
  executionId: string,
  record: { intentId: string; intentDigest: string },
) {
  return {
    schema_version: "1.0.0",
    admission_id: ADMISSION_ID,
    intent_id: record.intentId,
    intent_digest: record.intentDigest,
    execution_id: executionId,
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

function statusDocument(
  executionId: string,
  record: { intentId: string; intentDigest: string; operation: string },
  state: string,
) {
  const terminal = ["COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"].includes(
    state,
  );
  return {
    schema_version: "1.0.0",
    execution_id: executionId,
    intent_id: record.intentId,
    intent_digest: record.intentDigest,
    admission_id: ADMISSION_ID,
    admission_digest: ADMISSION_DIGEST,
    operation: record.operation,
    state,
    terminal,
    updated_at: "2026-09-20T08:00:00.000Z",
    ...(state === "COMPLETED"
      ? {
          receipt_digest: computeSha256PrefixedSync(
            jcsCanonicalize(receiptDocument(executionId, record)),
          ),
        }
      : {}),
    ...(["FAILED", "TIMED_OUT", "CANCELLED"].includes(state)
      ? { error: { code: "ERR_EXECUTION_TERMINAL", message: "terminal" } }
      : {}),
  };
}

function receiptDocument(
  executionId: string,
  record: { intentId: string; intentDigest: string },
) {
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
      intent_id: record.intentId,
      intent_digest: record.intentDigest,
      admission_id: ADMISSION_ID,
      admission_digest: ADMISSION_DIGEST,
      execution_id: executionId,
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
