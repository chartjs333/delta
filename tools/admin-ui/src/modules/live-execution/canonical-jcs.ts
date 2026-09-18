/**
 * RFC 8785 JSON Canonicalization Scheme (JCS) and SHA-256 digest computation.
 *
 * Requirements:
 * - Deterministic UTF-16 code-unit sorted object keys
 * - Standard ECMAScript number and string serialization without whitespace
 * - UTF-8 byte encoding and SHA-256 digest calculation with "sha256:" prefix
 * - Informational in the browser: Gate recomputation remains authoritative.
 */

export function jcsCanonicalize(value: unknown): string {
  if (value === null) {
    return "null";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("JCS does not support non-finite numbers");
    }
    if (Object.is(value, -0)) {
      return "0";
    }
    return JSON.stringify(value);
  }
  if (typeof value === "string") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return "[" + value.map(jcsCanonicalize).join(",") + "]";
  }
  if (typeof value === "object") {
    const keys = Object.keys(value as Record<string, unknown>).sort((a, b) => {
      return a < b ? -1 : a > b ? 1 : 0;
    });
    const entries = keys.map((key) => {
      return (
        JSON.stringify(key) +
        ":" +
        jcsCanonicalize((value as Record<string, unknown>)[key])
      );
    });
    return "{" + entries.join(",") + "}";
  }
  throw new TypeError(`JCS unsupported value type: ${typeof value}`);
}

export function sha256Utf8Sync(utf8Bytes: Uint8Array): string {
  function rightRotate(value: number, amount: number): number {
    return (value >>> amount) | (value << (32 - amount));
  }

  const mathPow = Math.pow;
  const maxWord = mathPow(2, 32);
  const words: number[] = [];
  const bitLength = utf8Bytes.length * 8;

  const hash: number[] = [];
  const k: number[] = [];
  let primeCounter = 0;

  const isComposite: Record<number, number> = {};
  for (let candidate = 2; primeCounter < 64; candidate++) {
    if (!isComposite[candidate]) {
      for (let i = 0; i < 313; i += candidate) {
        isComposite[i] = candidate;
      }
      hash[primeCounter] = (mathPow(candidate, 0.5) * maxWord) | 0;
      k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
    }
  }

  // Convert Uint8Array to binary string for standard 32-bit chunking
  let binaryStr = "";
  for (let i = 0; i < utf8Bytes.length; i++) {
    binaryStr += String.fromCharCode(utf8Bytes[i]);
  }

  let formattedAscii = binaryStr + "\x80";
  while ((formattedAscii.length % 64) - 56) formattedAscii += "\x00";
  for (let i = 0; i < formattedAscii.length; i++) {
    const j = formattedAscii.charCodeAt(i);
    words[i >> 2] |= j << ((3 - (i % 4)) * 8);
  }
  words[words.length] = (bitLength / maxWord) | 0;
  words[words.length] = bitLength;

  for (let j = 0; j < words.length; ) {
    const w = words.slice(j, (j += 16));
    const oldHash = hash.slice(0);

    for (let i = 0; i < 64; i++) {
      const w15 = w[i - 15];
      const w2 = w[i - 2];

      const a = hash[0];
      const e = hash[4];
      const temp1 =
        hash[7] +
        (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25)) +
        ((e & hash[5]) ^ (~e & hash[6])) +
        k[i] +
        (w[i] =
          i < 16
            ? w[i]
            : (w[i - 16] +
                (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3)) +
                w[i - 7] +
                (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10))) |
              0);
      const temp2 =
        (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22)) +
        ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));

      hash[7] = hash[6];
      hash[6] = hash[5];
      hash[5] = hash[4];
      hash[4] = (hash[3] + temp1) | 0;
      hash[3] = hash[2];
      hash[2] = hash[1];
      hash[1] = hash[0];
      hash[0] = (temp1 + temp2) | 0;
    }

    for (let i = 0; i < 8; i++) {
      hash[i] = (hash[i] + oldHash[i]) | 0;
    }
  }

  let result = "";
  for (let i = 0; i < 8; i++) {
    for (let i2 = 3; i2 >= 0; i2--) {
      const b = (hash[i] >> (i2 * 8)) & 255;
      result += (b < 16 ? "0" : "") + b.toString(16);
    }
  }
  return result;
}

export function computeSha256PrefixedSync(canonicalJson: string): string {
  const utf8Bytes = new TextEncoder().encode(canonicalJson);
  const hex = sha256Utf8Sync(utf8Bytes);
  return `sha256:${hex}`;
}

export async function computeSha256Prefixed(
  canonicalJson: string,
): Promise<string> {
  return computeSha256PrefixedSync(canonicalJson);
}

export function computeIntentDigestSync(
  intent: Readonly<Record<string, unknown>>,
): string {
  // Strip intent_digest if present to compute the digest over intent \ {intent_digest}
  const { intent_digest: _, ...intentWithoutDigest } = intent;
  const canonical = jcsCanonicalize(intentWithoutDigest);
  return computeSha256PrefixedSync(canonical);
}

export async function computeIntentDigest(
  intent: Readonly<Record<string, unknown>>,
): Promise<string> {
  return computeIntentDigestSync(intent);
}

export function verifyIntentDigestSync(
  intent: Readonly<Record<string, unknown>>,
): { readonly valid: boolean; readonly expectedDigest: string } {
  const expectedDigest = computeIntentDigestSync(intent);
  const actualDigest = intent.intent_digest;
  return {
    valid: actualDigest === expectedDigest,
    expectedDigest,
  };
}

export async function verifyIntentDigest(
  intent: Readonly<Record<string, unknown>>,
): Promise<{ readonly valid: boolean; readonly expectedDigest: string }> {
  return verifyIntentDigestSync(intent);
}
