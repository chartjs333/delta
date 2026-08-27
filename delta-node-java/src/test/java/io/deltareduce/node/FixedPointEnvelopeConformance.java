package io.deltareduce.node;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.regex.Pattern;

/** Opaque-byte validation for bounded DRQ1 fixed-point shard envelopes. */
public final class FixedPointEnvelopeConformance {
  static final int MAX_HEADER_BYTES = 65_536;
  static final int MAX_PAYLOAD_BYTES = 1_048_576;
  static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  static final String PROFILE_ID =
      "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61";
  private static final Pattern ENVELOPE =
      Pattern.compile("\\\"envelope_hex\\\":\\\"([0-9a-f]+)\\\"");
  private static final Pattern PAYLOAD_HASH =
      Pattern.compile("\\\"payload_sha256\\\":\\\"sha256:([0-9a-f]{64})\\\"");

  private FixedPointEnvelopeConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 1, "expected feature-004 golden fixture path");
    var envelopes = loadEnvelopes(Path.of(arguments[0]));
    require(envelopes.size() == 5, "expected five golden shard envelopes");
    for (var envelope : envelopes) {
      validate(envelope);
      require(
          java.util.Arrays.equals(envelope, DirectCopyParity.directRoundTrip(envelope)),
          "direct buffer changed opaque bytes");
      require(
          java.util.Arrays.equals(envelope, DirectCopyParity.heapRoundTrip(envelope)),
          "heap buffer changed opaque bytes");
    }
    System.out.println(
        "fixed-point envelopes compatible on JDK "
            + Runtime.version().feature()
            + ": "
            + envelopes.size());
  }

  static List<byte[]> loadEnvelopes(Path fixturePath) throws Exception {
    var fixture = Files.readString(fixturePath, StandardCharsets.US_ASCII);
    var matcher = ENVELOPE.matcher(fixture);
    var result = new ArrayList<byte[]>();
    while (matcher.find()) {
      result.add(HexFormat.of().parseHex(matcher.group(1)));
    }
    return List.copyOf(result);
  }

  static void validate(byte[] envelope) throws Exception {
    require(envelope.length >= 16, "truncated DRQ1 prefix");
    var input = ByteBuffer.wrap(envelope).order(ByteOrder.LITTLE_ENDIAN);
    var magic = new byte[4];
    input.get(magic);
    require(new String(magic, StandardCharsets.US_ASCII).equals("DRQ1"), "bad DRQ1 magic");
    require(Short.toUnsignedInt(input.getShort()) == 1, "unsupported DRQ1 major");
    require(Short.toUnsignedInt(input.getShort()) == 0, "unsupported DRQ1 minor");
    var headerLength = input.getInt();
    var payloadLength = input.getInt();
    require(headerLength >= 0 && headerLength <= MAX_HEADER_BYTES, "header limit exceeded");
    require(payloadLength >= 0 && payloadLength <= MAX_PAYLOAD_BYTES, "payload limit exceeded");
    var declaredLength = 16L + headerLength + payloadLength;
    require(declaredLength == envelope.length, "truncated or trailing DRQ1 bytes");
    var headerBytes = new byte[headerLength];
    input.get(headerBytes);
    var header = new String(headerBytes, StandardCharsets.US_ASCII);
    require(header.startsWith("{\"element_count\":"), "header is not canonical JSON");
    require(header.contains(FORMAL_SEMANTICS_ID), "formal semantics ID mismatch");
    require(header.contains(PROFILE_ID), "fixed-point profile ID mismatch");
    require(header.endsWith("\"type_name\":\"ENCODED_INT16_SHARD\"}"), "type mismatch");
    var payloadHash = PAYLOAD_HASH.matcher(header);
    require(payloadHash.find(), "payload hash field is missing");
    var expectedPayloadHash = payloadHash.group(1);
    require(!payloadHash.find(), "payload hash field is duplicated");
    var payload = new byte[payloadLength];
    input.get(payload);
    require(payloadLength % 2 == 0, "INT16 payload length is odd");
    require(
        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload))
            .equals(expectedPayloadHash),
        "payload SHA-256 mismatch");
    require(!input.hasRemaining(), "trailing bytes");
  }

  static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
