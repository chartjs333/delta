/**
 * Independent ECMAScript / Node.js generator for RFC 8785 (JCS) golden vectors.
 * 
 * Provides an authoritative, independent reference implementation conforming strictly
 * to RFC 8785 and ECMA-262 Section 7.1.12.1 (ToString Applied to the Number Type).
 * 
 * Execution: node generate_jcs_vectors.mjs
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const VECTORS_DIR = path.resolve(__dirname, '..', 'vectors');
const OUTPUT_FILE = path.join(VECTORS_DIR, 'jcs-golden-vectors.json');

/**
 * Canonicalizes a JSON-serializable value per RFC 8785.
 * Key ordering uses UTF-16 code unit values.
 * Number serialization follows ECMA-262 ToString(Number).
 */
export function canonicalizeJcs(obj) {
  if (obj === null) return "null";
  if (obj === true) return "true";
  if (obj === false) return "false";
  if (typeof obj === "number") {
    if (!Number.isFinite(obj)) {
      throw new TypeError("Non-finite numbers are forbidden in JCS");
    }
    // Rule 2: +0 and -0 MUST serialize as "0"
    if (Object.is(obj, -0) || obj === 0) return "0";
    // In V8/Node.js ES6+, JSON.stringify(number) implements ToString(Number) per ECMA-262
    return JSON.stringify(obj);
  }
  if (typeof obj === "string") {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return "[" + obj.map(item => canonicalizeJcs(item)).join(",") + "]";
  }
  if (typeof obj === "object") {
    // Sort keys by UTF-16 code units (RFC 8785 Section 3.2.3)
    const keys = Object.keys(obj).sort((a, b) => {
      const minLen = Math.min(a.length, b.length);
      for (let i = 0; i < minLen; i++) {
        const codeA = a.charCodeAt(i);
        const codeB = b.charCodeAt(i);
        if (codeA !== codeB) return codeA - codeB;
      }
      return a.length - b.length;
    });
    return "{" + keys.map(k => `${JSON.stringify(k)}:${canonicalizeJcs(obj[k])}`).join(",") + "}";
  }
  throw new TypeError(`Unsupported type for JCS: ${typeof obj}`);
}

export function sha256Hex(utf8String) {
  return "sha256:" + crypto.createHash("sha256").update(Buffer.from(utf8String, "utf-8")).digest("hex");
}

// Full suite of reference cases including IEEE-754 and exponential boundary cases
const vectorDefinitions = [
  {
    name: "unicode-key-order",
    value: {
      "z": "last",
      "a": "first",
      "é": "latin-small-e-acute",
      "emoji": "😀",
      "nested": {
        "Ω": 1,
        "A": 2
      }
    }
  },
  {
    name: "execution-intent-train-ticket-without-digest",
    value: {
      "schema_version": "1.0.0",
      "intent_id": "11111111-1111-4111-8111-111111111111",
      "operation": "TRAIN_TICKET",
      "workload": {
        "model_plugin_id": "tabular-10gene-phenotype-v1",
        "dataset_id": "synthetic-10gene-cohort-v1",
        "catalog_backend_ref": "670b58f6458fe84620f4f9f46401f855d04ae05d",
        "requested_scope": "PLUGIN_BOUNDARY"
      },
      "operation_payload": {
        "ticket_id": "ticket_A-0001",
        "partition_id": "partition_00"
      },
      "execution_constraints": {
        "timeout_seconds": 900,
        "requested_allow_downloads": false,
        "retry_of_intent_id": "00000000-0000-4000-8000-000000000001"
      },
      "declared_operator": {
        "subject_id": "operator.alpha",
        "role": "OPERATOR"
      },
      "created_at": "2026-09-17T14:30:00.000Z",
      "expires_at": "2026-09-17T14:40:00.000Z"
    }
  },
  {
    name: "admission-record-without-digest-authenticator",
    value: {
      "schema_version": "1.0.0",
      "admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      "intent_id": "11111111-1111-4111-8111-111111111111",
      "intent_digest": "sha256:957aa9206bd8af232fdaed976e19b2d52ec4d8a502b84b643eb96fbeeafa8d76",
      "execution_id": "55555555-5555-4555-8555-555555555555",
      "authenticated_subject": {
        "subject_id": "operator.alpha",
        "effective_roles": ["OPERATOR"],
        "authenticated_via": "LOCAL_PEER_CREDENTIAL"
      },
      "policy_context": {
        "policy_version": "step5c-policy-v1",
        "controller_commit": "66e3e7e5bb07a48aadbee8d9c4683144b812d229",
        "verdict": "ADMITTED"
      },
      "resource_grants": {
        "allow_downloads": false,
        "max_memory_bytes": 2147483648,
        "timeout_seconds": 900
      },
      "admitted_at": "2026-09-17T14:30:05.000Z",
      "admission_expires_at": "2026-09-17T14:35:00.000Z"
    }
  },
  {
    name: "admission-record-without-signature",
    value: {
      "schema_version": "1.0.0",
      "admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      "intent_id": "11111111-1111-4111-8111-111111111111",
      "intent_digest": "sha256:957aa9206bd8af232fdaed976e19b2d52ec4d8a502b84b643eb96fbeeafa8d76",
      "execution_id": "55555555-5555-4555-8555-555555555555",
      "admission_digest": "sha256:592c4cef6326853d9d3a34e96cc42552c1dd54899a152678b4a745c17db1c3b1",
      "authenticated_subject": {
        "subject_id": "operator.alpha",
        "effective_roles": ["OPERATOR"],
        "authenticated_via": "LOCAL_PEER_CREDENTIAL"
      },
      "policy_context": {
        "policy_version": "step5c-policy-v1",
        "controller_commit": "66e3e7e5bb07a48aadbee8d9c4683144b812d229",
        "verdict": "ADMITTED"
      },
      "resource_grants": {
        "allow_downloads": false,
        "max_memory_bytes": 2147483648,
        "timeout_seconds": 900
      },
      "admitted_at": "2026-09-17T14:30:05.000Z",
      "admission_expires_at": "2026-09-17T14:35:00.000Z",
      "authenticator": {
        "issuer_id": "step5c-fixture-controller",
        "key_id": "step5c-fixture-ed25519",
        "algorithm": "ED25519"
      }
    }
  },
  {
    name: "execution-status-completed",
    value: {
      "schema_version": "1.0.0",
      "execution_id": "55555555-5555-4555-8555-555555555555",
      "intent_id": "11111111-1111-4111-8111-111111111111",
      "intent_digest": "sha256:957aa9206bd8af232fdaed976e19b2d52ec4d8a502b84b643eb96fbeeafa8d76",
      "admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      "admission_digest": "sha256:592c4cef6326853d9d3a34e96cc42552c1dd54899a152678b4a745c17db1c3b1",
      "state": "COMPLETED",
      "receipt_digest": "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8",
      "terminal": true,
      "updated_at": "2026-09-17T14:35:30.000Z",
      "operation": "TRAIN_TICKET"
    }
  },
  {
    name: "execution-receipt-lineage-extension",
    value: {
      "schema_version": "1.0.0",
      "receipt_type": "DELTAREDUCE_EXECUTION_RECEIPT",
      "provenance": {
        "repository": "chartjs333/delta",
        "backend_commit": "4cf2aa8c05001c37b7b1e42b2f6ef3fbaebc1a01",
        "catalog_backend_ref": "670b58f6458fe84620f4f9f46401f855d04ae05d",
        "producer_commit": "4992d9eca319da21b5a2c7b94593f3668b92329c",
        "controller_commit": "66e3e7e5bb07a48aadbee8d9c4683144b812d229",
        "produced_at": "2026-09-17T14:35:25.000Z",
        "intent_id": "11111111-1111-4111-8111-111111111111",
        "intent_digest": "sha256:957aa9206bd8af232fdaed976e19b2d52ec4d8a502b84b643eb96fbeeafa8d76",
        "admission_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "admission_digest": "sha256:592c4cef6326853d9d3a34e96cc42552c1dd54899a152678b4a745c17db1c3b1",
        "execution_id": "55555555-5555-4555-8555-555555555555"
      },
      "workload": {
        "model_plugin_id": "tabular-10gene-phenotype-v1",
        "dataset_id": "synthetic-10gene-cohort-v1",
        "executed_scope": "PLUGIN_BOUNDARY",
        "workload_config_digest": "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8"
      },
      "execution": {
        "verdict": "SUCCESS",
        "terminal_status": "COMPLETED"
      }
    }
  },
  {
    name: "numbers-integers-and-zero",
    value: {
      "pos_zero": 0,
      "neg_zero": -0,
      "one": 1,
      "neg_one": -1,
      "answer": 42,
      "neg_answer": -42,
      "max_safe_int": Number.MAX_SAFE_INTEGER,
      "min_safe_int": Number.MIN_SAFE_INTEGER
    }
  },
  {
    name: "numbers-floats-standard",
    value: {
      "quarter": 0.25,
      "one_point_twenty_five": 1.25,
      "eighth": 0.125,
      "negative_fraction": -1.25,
      "tenth": 0.1,
      "sub_millionth_decimal": 0.000001
    }
  },
  {
    name: "numbers-exponential-boundaries",
    value: {
      "exp_pos_large": 1e21,
      "exp_pos_twenty": 1e20,
      "exp_neg_small": 1e-7,
      "exp_neg_six": 1e-6,
      "exp_neg_five": 1e-5,
      "exp_complex_pos": 1.23456789012345e+20,
      "exp_complex_neg": 1.23456789012345e-20
    }
  },
  {
    name: "empty-structures",
    value: {
      "empty_array": [],
      "empty_object": {}
    }
  },
  {
    name: "whitespace-and-escapes",
    value: {
      "escapes": "\"\\\b\f\n\r\t",
      "slash": "a/b/c",
      "space": "   "
    }
  },
  {
    name: "surrogate-pairs-and-unicode",
    value: {
      "emoji_rainbow": "🌈",
      "emoji_flag": "🇺🇳",
      "japanese": "日本語",
      "math_symbols": "∀x∈ℝ: x²≥0"
    }
  },
  {
    name: "number-zero",
    value: { "val": 0 }
  },
  {
    name: "number-negative-zero",
    value: { "val": -0 }
  },
  {
    name: "number-positive-int",
    value: { "val": 42 }
  },
  {
    name: "number-negative-int",
    value: { "val": -42 }
  },
  {
    name: "number-max-safe-int",
    value: { "val": 9007199254740991 }
  },
  {
    name: "number-min-safe-int",
    value: { "val": -9007199254740991 }
  },
  {
    name: "number-fraction",
    value: { "val": 1.25 }
  },
  {
    name: "number-exponential-small",
    value: { "val": 1e-7 }
  },
  {
    name: "number-exponential-large",
    value: { "val": 1e21 }
  }
];

export function generateGoldenVectors() {
  const vectors = vectorDefinitions.map(def => {
    const canonical_json = canonicalizeJcs(def.value);
    const sha256 = sha256Hex(canonical_json);
    return {
      name: def.name,
      value: def.value,
      canonical_json: canonical_json,
      sha256: sha256
    };
  });

  const output = {
    schema_version: "1.0.0",
    generator: "independent-ecmascript-rfc8785-v1",
    vectors: vectors
  };

  fs.mkdirSync(VECTORS_DIR, { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2) + "\n", "utf-8");
  console.log(`Generated ${vectors.length} golden vectors to ${OUTPUT_FILE}`);
  return output;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  generateGoldenVectors();
}
