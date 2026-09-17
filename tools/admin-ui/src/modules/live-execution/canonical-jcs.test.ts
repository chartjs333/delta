import { describe, expect, it } from "vitest";

import goldenVectorsDoc from "../../../../../specs/admin-ui/step5c-controlled-live-execution/contracts/vectors/jcs-golden-vectors.json";
import {
  computeIntentDigest,
  computeSha256Prefixed,
  jcsCanonicalize,
  verifyIntentDigest,
} from "./canonical-jcs";

describe("RFC 8785 Canonical JCS & SHA-256 Digest Verification", () => {
  it("matches all T008 golden vectors exactly", async () => {
    for (const vector of goldenVectorsDoc.vectors) {
      const canonical = jcsCanonicalize(vector.value);
      expect(canonical).toBe(vector.canonical_json);

      const digest = await computeSha256Prefixed(canonical);
      expect(digest).toBe(vector.sha256);
    }
  });

  it("handles negative zero per RFC 8785 section 3.2.2.3", () => {
    expect(jcsCanonicalize({ val: -0 })).toBe('{"val":0}');
    expect(jcsCanonicalize(-0)).toBe("0");
  });

  it("throws on non-finite numbers", () => {
    expect(() => jcsCanonicalize({ val: Number.NaN })).toThrow(/non-finite/u);
    expect(() => jcsCanonicalize({ val: Number.POSITIVE_INFINITY })).toThrow(/non-finite/u);
    expect(() => jcsCanonicalize({ val: Number.NEGATIVE_INFINITY })).toThrow(/non-finite/u);
  });

  it("sorts object keys strictly by UTF-16 code units", () => {
    const obj = {
      z: 1,
      a: 2,
      "\u00e9": 3,
      nested: { B: 1, A: 2 },
    };
    expect(jcsCanonicalize(obj)).toBe(
      '{"a":2,"nested":{"A":2,"B":1},"z":1,"\u00e9":3}',
    );
  });

  it("computes and verifies intent digests with intent_digest stripped", async () => {
    const sampleTrainIntent = {
      schema_version: "1.0.0",
      intent_id: "11111111-1111-4111-8111-111111111111",
      created_at: "2026-09-17T14:30:00.000Z",
      expires_at: "2026-09-17T14:40:00.000Z",
      declared_operator: {
        role: "OPERATOR",
        subject_id: "operator.alpha",
      },
      workload: {
        model_plugin_id: "tabular-10gene-phenotype-v1",
        dataset_id: "synthetic-10gene-cohort-v1",
        requested_scope: "PLUGIN_BOUNDARY",
        catalog_backend_ref: "670b58f6458fe84620f4f9f46401f855d04ae05d",
      },
      operation: "TRAIN_TICKET",
      operation_payload: {
        ticket_id: "ticket_A-0001",
        partition_id: "partition_00",
      },
      execution_constraints: {
        timeout_seconds: 900,
        requested_allow_downloads: false,
        retry_of_intent_id: "00000000-0000-4000-8000-000000000001",
      },
    };

    const digest = await computeIntentDigest(sampleTrainIntent);
    expect(digest).toBe(
      "sha256:957aa9206bd8af232fdaed976e19b2d52ec4d8a502b84b643eb96fbeeafa8d76",
    );

    const intentWithDigest = {
      ...sampleTrainIntent,
      intent_digest: digest,
    };

    const check = await verifyIntentDigest(intentWithDigest);
    expect(check.valid).toBe(true);
    expect(check.expectedDigest).toBe(digest);

    const tampered = {
      ...intentWithDigest,
      intent_digest: "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    };
    const tamperedCheck = await verifyIntentDigest(tampered);
    expect(tamperedCheck.valid).toBe(false);
  });
});
