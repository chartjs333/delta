package io.deltareduce.node;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/** JDK compatibility harness for the frozen feature-003 runtime descriptor bytes. */
public final class RuntimeDescriptorCompatibility {
  private static final int MAX_VALUE_BYTES = 4 * 1024 * 1024;
  private static final int MAX_COLLECTION_MEMBERS = 100_000;
  private static final int MAX_DEPTH = 32;
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final Pattern DESCRIPTOR_VECTOR =
      Pattern.compile(
          "\\\"content_id\\\":\\\"([^\\\"]+)\\\","
              + "\\\"envelope_hex\\\":\\\"([0-9a-f]+)\\\","
              + "\\\"envelope_sha256\\\":\\\"([0-9a-f]+)\\\","
              + "\\\"type_code\\\":9,"
              + "\\\"type_name\\\":\\\"RUNTIME_DESCRIPTOR\\\"");

  private RuntimeDescriptorCompatibility() {}

  public static void main(String[] arguments) throws Exception {
    if (arguments.length != 1) {
      throw new IllegalArgumentException("expected the canonical golden fixture path");
    }
    var fixture = Files.readString(Path.of(arguments[0]), StandardCharsets.US_ASCII);
    var matcher = DESCRIPTOR_VECTOR.matcher(fixture);
    require(matcher.find(), "runtime descriptor golden vector is missing");
    var expectedContentId = matcher.group(1);
    var envelope = HexFormat.of().parseHex(matcher.group(2));
    var expectedEnvelopeHash = matcher.group(3);
    require(!matcher.find(), "runtime descriptor golden vector is duplicated");
    require(sha256Hex(envelope).equals(expectedEnvelopeHash), "envelope SHA-256 mismatch");
    require(contentId(envelope).equals(expectedContentId), "content ID mismatch");

    var fields = decodeEnvelope(envelope);
    require(fields.get("abi_major").equals(1L), "ABI major mismatch");
    require(fields.get("abi_minor").equals(0L), "ABI minor mismatch");
    require(fields.get("formal_semantics_id").equals(FORMAL_SEMANTICS_ID), "formal ID mismatch");
    require(fields.get("protocol_version").equals("003.1.0"), "protocol version mismatch");
    require(fields.get("runtime_profile").equals("embedded-ffm"), "runtime profile mismatch");
    require(fields.get("schema_version").equals("1.0.0"), "schema version mismatch");
    require(fields.get("type_name").equals("RUNTIME_DESCRIPTOR"), "type name mismatch");
    require(fields.get("struct_size").equals(64L), "descriptor size mismatch");

    System.out.println(
        "runtime descriptor compatible on JDK "
            + Runtime.version().feature()
            + ": "
            + expectedContentId);
  }

  private static Map<String, Object> decodeEnvelope(byte[] envelope) {
    require(envelope.length >= 12, "truncated envelope");
    var input = ByteBuffer.wrap(envelope).order(ByteOrder.BIG_ENDIAN);
    var magic = new byte[4];
    input.get(magic);
    require(new String(magic, StandardCharsets.US_ASCII).equals("DRC1"), "bad magic");
    require(Byte.toUnsignedInt(input.get()) == 1, "encoding major mismatch");
    require(Byte.toUnsignedInt(input.get()) == 0, "encoding minor mismatch");
    require(Short.toUnsignedInt(input.getShort()) == 9, "runtime descriptor type code mismatch");
    var payloadLength = input.getInt();
    require(payloadLength >= 0 && payloadLength == input.remaining(), "payload length mismatch");
    var root = decodeValue(input, 0);
    require(!input.hasRemaining(), "trailing bytes");
    require(root instanceof Map<?, ?>, "root is not a map");

    var result = new LinkedHashMap<String, Object>();
    for (var entry : ((Map<?, ?>) root).entrySet()) {
      require(entry.getKey() instanceof String, "map key is not text");
      result.put((String) entry.getKey(), entry.getValue());
    }
    return result;
  }

  private static Object decodeValue(ByteBuffer input, int depth) {
    require(depth <= MAX_DEPTH, "nesting too deep");
    require(input.hasRemaining(), "truncated value tag");
    return switch (Byte.toUnsignedInt(input.get())) {
      case 0x01 -> false;
      case 0x02 -> true;
      case 0x10, 0x11 -> readLong(input);
      case 0x20 -> readBytes(input);
      case 0x21 -> readText(input);
      case 0x30 -> readArray(input, depth);
      case 0x31 -> readMap(input, depth);
      default -> throw new IllegalArgumentException("invalid typed-value tag");
    };
  }

  private static long readLong(ByteBuffer input) {
    require(input.remaining() >= Long.BYTES, "truncated integer");
    return input.getLong();
  }

  private static byte[] readBytes(ByteBuffer input) {
    var length = readBoundedLength(input, MAX_VALUE_BYTES, "byte string");
    var value = new byte[length];
    input.get(value);
    return value;
  }

  private static String readText(ByteBuffer input) {
    var length = readBoundedLength(input, MAX_VALUE_BYTES, "text");
    var value = new byte[length];
    input.get(value);
    for (var item : value) {
      var code = Byte.toUnsignedInt(item);
      require(code >= 0x20 && code <= 0x7e, "text is not printable ASCII");
    }
    return new String(value, StandardCharsets.US_ASCII);
  }

  private static List<Object> readArray(ByteBuffer input, int depth) {
    var count = readBoundedCount(input);
    var result = new ArrayList<Object>(count);
    for (var index = 0; index < count; ++index) {
      result.add(decodeValue(input, depth + 1));
    }
    return result;
  }

  private static Map<String, Object> readMap(ByteBuffer input, int depth) {
    var count = readBoundedCount(input);
    var result = new LinkedHashMap<String, Object>(count);
    String prior = null;
    for (var index = 0; index < count; ++index) {
      require(
          input.hasRemaining() && Byte.toUnsignedInt(input.get()) == 0x21,
          "map key is not text");
      var key = readText(input);
      require(key.matches("[a-z0-9_]+"), "invalid map key");
      require(prior == null || prior.compareTo(key) < 0, "map keys are not strictly increasing");
      result.put(key, decodeValue(input, depth + 1));
      prior = key;
    }
    return result;
  }

  private static int readBoundedCount(ByteBuffer input) {
    return readBoundedLength(input, MAX_COLLECTION_MEMBERS, "collection");
  }

  private static int readBoundedLength(ByteBuffer input, int maximum, String kind) {
    require(input.remaining() >= Integer.BYTES, "truncated " + kind + " length");
    var length = input.getInt();
    require(length >= 0 && length <= maximum, kind + " length exceeds limit");
    require(length <= input.remaining(), "truncated " + kind);
    return length;
  }

  private static String contentId(byte[] envelope) throws Exception {
    var digest = MessageDigest.getInstance("SHA-256");
    digest.update("deltareduce:003:runtime-descriptor:v1".getBytes(StandardCharsets.US_ASCII));
    digest.update((byte) 0);
    digest.update(envelope);
    return "sha256:" + HexFormat.of().formatHex(digest.digest());
  }

  private static String sha256Hex(byte[] value) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
