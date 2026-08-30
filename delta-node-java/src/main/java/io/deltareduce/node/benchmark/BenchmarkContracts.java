package io.deltareduce.node.benchmark;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/** Shared bounded validation for benchmark adapters; this package has no protocol authority. */
final class BenchmarkContracts {
  static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";

  private BenchmarkContracts() {}

  static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }

  static void requireContentId(String value, String name) {
    require(value != null && value.matches("sha256:[0-9a-f]{64}"), name + " is invalid");
  }

  static String sha256(byte[] value) {
    try {
      return "sha256:"
          + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException(error);
    }
  }
}
