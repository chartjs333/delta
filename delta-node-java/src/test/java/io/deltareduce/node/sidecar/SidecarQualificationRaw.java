package io.deltareduce.node.sidecar;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Minimal canonical-JSON writer for raw sidecar qualification observations. */
final class SidecarQualificationRaw {
  private SidecarQualificationRaw() {}

  record Evidence(Map<String, Object> value, String sha256) {
    Evidence {
      value = immutableSortedMap(Objects.requireNonNull(value, "value"));
      Objects.requireNonNull(sha256, "sha256");
    }
  }

  static Evidence evidence(Map<String, Boolean> checks, Map<String, Object> observations) {
    Objects.requireNonNull(checks, "checks");
    Objects.requireNonNull(observations, "observations");
    require(!checks.isEmpty(), "evidence checks are empty");
    require(!observations.isEmpty(), "evidence observations are empty");
    var canonicalChecks = new TreeMap<String, Object>();
    for (var entry : checks.entrySet()) {
      require(Boolean.TRUE.equals(entry.getValue()), "evidence check is not true: " + entry.getKey());
      canonicalChecks.put(canonicalText(entry.getKey()), true);
    }
    var canonicalObservations = canonicalMap(observations);
    var value = new TreeMap<String, Object>();
    value.put("artifact_sha256", sha256Id(canonicalBytes(canonicalObservations)));
    value.put("checks", canonicalChecks);
    value.put("observations", canonicalObservations);
    var immutable = immutableSortedMap(value);
    return new Evidence(immutable, sha256Id(canonicalBytes(immutable)));
  }

  static byte[] canonicalBytes(Object value) {
    var output = new ByteArrayOutputStream();
    writeValue(output, value);
    return output.toByteArray();
  }

  static void writeAtomically(Path output, Object value) throws IOException {
    var exactOutput = Objects.requireNonNull(output, "output").toAbsolutePath().normalize();
    var parent = exactOutput.getParent();
    require(parent != null, "output has no parent directory");
    Files.createDirectories(parent);
    var bytes = canonicalBytes(value);
    var withNewline = new byte[Math.addExact(bytes.length, 1)];
    System.arraycopy(bytes, 0, withNewline, 0, bytes.length);
    withNewline[bytes.length] = (byte) '\n';
    var temporary = Files.createTempFile(parent, exactOutput.getFileName().toString() + ".", ".tmp");
    var moved = false;
    try {
      try (var channel = FileChannel.open(
          temporary, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)) {
        var buffer = ByteBuffer.wrap(withNewline);
        while (buffer.hasRemaining()) {
          channel.write(buffer);
        }
        channel.force(true);
      }
      try {
        Files.move(
            temporary,
            exactOutput,
            StandardCopyOption.ATOMIC_MOVE,
            StandardCopyOption.REPLACE_EXISTING);
      } catch (AtomicMoveNotSupportedException unsupported) {
        throw new IOException("canonical raw output requires an atomic same-filesystem move", unsupported);
      }
      moved = true;
    } finally {
      if (!moved) {
        Files.deleteIfExists(temporary);
      }
    }
  }

  static String sha256Id(byte[] value) {
    try {
      return "sha256:" + HexFormat.of().formatHex(
          MessageDigest.getInstance("SHA-256").digest(Objects.requireNonNull(value, "value")));
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  static String sha256Id(Path value) throws IOException {
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      try (var input = Files.newInputStream(Objects.requireNonNull(value, "value"))) {
        var block = new byte[64 * 1024];
        int count;
        while ((count = input.read(block)) >= 0) {
          if (count > 0) {
            digest.update(block, 0, count);
          }
        }
      }
      return "sha256:" + HexFormat.of().formatHex(digest.digest());
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  static Map<String, Object> canonicalMap(Map<String, ?> source) {
    var result = new TreeMap<String, Object>();
    for (var entry : Objects.requireNonNull(source, "source").entrySet()) {
      var prior = result.put(canonicalText(entry.getKey()), canonicalValue(entry.getValue()));
      require(prior == null, "duplicate canonical JSON key");
    }
    return Collections.unmodifiableNavigableMap(result);
  }

  private static Map<String, Object> immutableSortedMap(Map<String, ?> source) {
    var result = new TreeMap<String, Object>();
    for (var entry : source.entrySet()) {
      result.put(canonicalText(entry.getKey()), canonicalValue(entry.getValue()));
    }
    return Collections.unmodifiableNavigableMap(result);
  }

  private static Object canonicalValue(Object value) {
    if (value == null || value instanceof Boolean) {
      return value;
    }
    if (value instanceof String text) {
      return canonicalText(text);
    }
    if (value instanceof Byte byteValue) {
      return nonnegative(byteValue.longValue());
    }
    if (value instanceof Short shortValue) {
      return nonnegative(shortValue.longValue());
    }
    if (value instanceof Integer integerValue) {
      return nonnegative(integerValue.longValue());
    }
    if (value instanceof Long longValue) {
      return nonnegative(longValue);
    }
    if (value instanceof Map<?, ?> rawMap) {
      var typed = new LinkedHashMap<String, Object>();
      for (var entry : rawMap.entrySet()) {
        require(entry.getKey() instanceof String, "canonical JSON object key is not text");
        typed.put((String) entry.getKey(), entry.getValue());
      }
      return canonicalMap(typed);
    }
    if (value instanceof List<?> list) {
      var result = new ArrayList<Object>(list.size());
      for (var item : list) {
        result.add(canonicalValue(item));
      }
      return List.copyOf(result);
    }
    throw new IllegalArgumentException(
        "unsupported canonical JSON value: " + value.getClass().getName());
  }

  private static long nonnegative(long value) {
    require(value >= 0, "canonical qualification integer is negative");
    return value;
  }

  private static String canonicalText(String value) {
    Objects.requireNonNull(value, "text");
    require(value.indexOf('\0') < 0, "canonical qualification text contains NUL");
    require(Normalizer.isNormalized(value, Normalizer.Form.NFC),
        "canonical qualification text is not NFC");
    for (var index = 0; index < value.length(); ++index) {
      var item = value.charAt(index);
      if (Character.isHighSurrogate(item)) {
        require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)),
            "canonical qualification text has an unpaired surrogate");
        ++index;
      } else {
        require(!Character.isLowSurrogate(item),
            "canonical qualification text has an unpaired surrogate");
      }
    }
    return value;
  }

  private static void writeValue(ByteArrayOutputStream output, Object raw) {
    var value = canonicalValue(raw);
    if (value == null) {
      writeAscii(output, "null");
    } else if (value instanceof Boolean bool) {
      writeAscii(output, bool ? "true" : "false");
    } else if (value instanceof Long integer) {
      writeAscii(output, Long.toString(integer));
    } else if (value instanceof String text) {
      writeString(output, text);
    } else if (value instanceof Map<?, ?> map) {
      output.write('{');
      var first = true;
      for (var entry : map.entrySet()) {
        if (!first) {
          output.write(',');
        }
        first = false;
        writeString(output, (String) entry.getKey());
        output.write(':');
        writeValue(output, entry.getValue());
      }
      output.write('}');
    } else if (value instanceof List<?> list) {
      output.write('[');
      for (var index = 0; index < list.size(); ++index) {
        if (index != 0) {
          output.write(',');
        }
        writeValue(output, list.get(index));
      }
      output.write(']');
    } else {
      throw new IllegalStateException("canonical value normalization failed");
    }
  }

  private static void writeString(ByteArrayOutputStream output, String value) {
    output.write('"');
    var plainStart = 0;
    for (var index = 0; index < value.length(); ++index) {
      var item = value.charAt(index);
      String escape = switch (item) {
        case '"' -> "\\\"";
        case '\\' -> "\\\\";
        case '\b' -> "\\b";
        case '\f' -> "\\f";
        case '\n' -> "\\n";
        case '\r' -> "\\r";
        case '\t' -> "\\t";
        default -> item < 0x20 ? String.format("\\u%04x", (int) item) : null;
      };
      if (escape != null) {
        if (plainStart < index) {
          writeUtf8(output, value.substring(plainStart, index));
        }
        writeAscii(output, escape);
        plainStart = index + 1;
      }
    }
    if (plainStart < value.length()) {
      writeUtf8(output, value.substring(plainStart));
    }
    output.write('"');
  }

  private static void writeAscii(ByteArrayOutputStream output, String value) {
    output.writeBytes(value.getBytes(StandardCharsets.US_ASCII));
  }

  private static void writeUtf8(ByteArrayOutputStream output, String value) {
    output.writeBytes(value.getBytes(StandardCharsets.UTF_8));
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
