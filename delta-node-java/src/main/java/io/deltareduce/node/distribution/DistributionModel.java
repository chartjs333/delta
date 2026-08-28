package io.deltareduce.node.distribution;

import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.regex.Pattern;

/** Immutable feature-005 identities and deterministic piece layout. */
public final class DistributionModel {
  public static final int MAX_MANIFEST_BYTES = 1_048_576;
  public static final int MAX_PIECE_BYTES = 1_048_576;
  public static final int MAX_PIECES = 8_192;
  public static final long MAX_OBJECT_BYTES = 8_589_934_592L;
  public static final int MAX_STREAMS = 8;
  public static final int MAX_TRANSPORT_HEADER_BYTES = 65_536;
  public static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  public static final String PIECE_PROFILE_ID =
      "sha256:de9ca7f1a4e2630f729227e34d51c0c03c565062cc9ba924e465a884acc7987d";
  private static final Pattern CONTENT_ID = Pattern.compile("sha256:[0-9a-f]{64}");
  private static final Pattern PIECE =
      Pattern.compile(
          "\\{\"content_id\":\"(sha256:[0-9a-f]{64})\",\"length\":([0-9]+),"
              + "\"offset\":([0-9]+),\"ordinal\":([0-9]+)\\}");

  private DistributionModel() {}

  public record PieceDescriptor(int ordinal, long offset, int length, String contentId) {
    public PieceDescriptor {
      require(ordinal >= 0 && ordinal < MAX_PIECES, "piece ordinal is outside bounds");
      require(offset >= 0 && offset <= MAX_OBJECT_BYTES, "piece offset is outside bounds");
      require(length > 0 && length <= MAX_PIECE_BYTES, "piece length is outside bounds");
      requireContentId(contentId, "piece content ID");
    }
  }

  public record Manifest(
      byte[] canonicalBytes,
      String manifestId,
      String payloadSha256,
      String pieceTreeRoot,
      long totalLength,
      List<PieceDescriptor> pieces) {
    public Manifest {
      canonicalBytes = canonicalBytes.clone();
      pieces = List.copyOf(pieces);
      require(canonicalBytes.length <= MAX_MANIFEST_BYTES, "manifest exceeds byte limit");
      requireContentId(manifestId, "manifest ID");
      requireContentId(payloadSha256, "payload SHA-256");
      requireContentId(pieceTreeRoot, "piece-tree root");
      require(totalLength >= 0 && totalLength <= MAX_OBJECT_BYTES, "object length is outside bounds");
      require(pieces.size() <= MAX_PIECES, "piece count exceeds limit");
      long cursor = 0;
      for (var index = 0; index < pieces.size(); ++index) {
        var piece = pieces.get(index);
        require(piece.ordinal() == index, "piece ordinals are not canonical");
        require(piece.offset() == cursor, "piece ranges contain a gap or overlap");
        if (index + 1 < pieces.size()) {
          require(piece.length() == MAX_PIECE_BYTES, "non-final piece is short");
        }
        cursor = Math.addExact(cursor, piece.length());
      }
      require(cursor == totalLength, "piece ranges do not cover exact object length");
      require(pieces.isEmpty() == (totalLength == 0), "empty-object layout is noncanonical");
    }

    @Override
    public byte[] canonicalBytes() {
      return canonicalBytes.clone();
    }
  }

  public static Manifest parseManifest(byte[] canonicalBytes) {
    require(canonicalBytes.length <= MAX_MANIFEST_BYTES, "manifest exceeds byte limit");
    var text = new String(canonicalBytes, StandardCharsets.US_ASCII);
    require(text.startsWith("{") && text.endsWith("}"), "manifest is not a JSON object");
    require(extract(text, "type_name").equals("OBJECT_MANIFEST"), "wrong manifest type");
    require(extract(text, "schema_version").equals("1.0.0"), "wrong schema version");
    require(
        extract(text, "formal_semantics_id").equals(FORMAL_SEMANTICS_ID),
        "wrong formal semantics identity");
    require(
        extract(text, "piece_profile_id").equals(PIECE_PROFILE_ID),
        "wrong piece profile identity");
    var piecesMarker = "\"pieces\":[";
    var piecesStart = text.indexOf(piecesMarker);
    require(piecesStart >= 0, "piece table is missing");
    piecesStart += piecesMarker.length();
    var piecesEnd = text.indexOf(']', piecesStart);
    require(piecesEnd >= piecesStart, "piece table is truncated");
    var table = text.substring(piecesStart, piecesEnd);
    var matcher = PIECE.matcher(table);
    var pieces = new ArrayList<PieceDescriptor>();
    var cursor = 0;
    while (matcher.find()) {
      require(matcher.start() == cursor, "piece table contains unknown bytes");
      pieces.add(
          new PieceDescriptor(
              Integer.parseInt(matcher.group(4)),
              Long.parseLong(matcher.group(3)),
              Integer.parseInt(matcher.group(2)),
              matcher.group(1)));
      cursor = matcher.end();
      if (cursor < table.length()) {
        require(table.charAt(cursor) == ',', "piece table separator is malformed");
        ++cursor;
      }
    }
    require(cursor == table.length(), "piece table is malformed");
    return new Manifest(
        canonicalBytes,
        domainId("deltareduce.005.object-manifest.v1", canonicalBytes),
        extract(text, "payload_sha256"),
        extract(text, "piece_tree_root"),
        Long.parseLong(extractUnsigned(text, "total_length")),
        pieces);
  }

  public static List<byte[]> chunk(byte[] payload) {
    require(payload.length <= MAX_OBJECT_BYTES, "payload exceeds object limit");
    var result = new ArrayList<byte[]>();
    for (var offset = 0; offset < payload.length; offset += MAX_PIECE_BYTES) {
      var length = Math.min(MAX_PIECE_BYTES, payload.length - offset);
      result.add(java.util.Arrays.copyOfRange(payload, offset, offset + length));
    }
    return List.copyOf(result);
  }

  public static String pieceId(byte[] piece) {
    require(piece.length > 0 && piece.length <= MAX_PIECE_BYTES, "piece length is outside bounds");
    return domainId("deltareduce.005.piece.v1", piece);
  }

  public static String pieceTreeRoot(List<String> pieceIds) {
    if (pieceIds.isEmpty()) {
      return domainId("deltareduce.005.piece-empty.v1", new byte[0]);
    }
    var nodes = new ArrayList<byte[]>();
    for (var ordinal = 0; ordinal < pieceIds.size(); ++ordinal) {
      var pieceId = pieceIds.get(ordinal);
      requireContentId(pieceId, "piece ID");
      var leafInput = ByteBuffer.allocate(40).order(ByteOrder.BIG_ENDIAN);
      leafInput.putLong(ordinal).put(hexDigest(pieceId));
      nodes.add(domainDigest("deltareduce.005.piece-leaf.v1", leafInput.array()));
    }
    while (nodes.size() > 1) {
      var next = new ArrayList<byte[]>();
      for (var index = 0; index < nodes.size(); index += 2) {
        if (index + 1 == nodes.size()) {
          next.add(nodes.get(index));
        } else {
          var joined = new byte[64];
          System.arraycopy(nodes.get(index), 0, joined, 0, 32);
          System.arraycopy(nodes.get(index + 1), 0, joined, 32, 32);
          next.add(domainDigest("deltareduce.005.piece-node.v1", joined));
        }
      }
      nodes = next;
    }
    return "sha256:" + HexFormat.of().formatHex(nodes.get(0));
  }

  public static String rawSha256(byte[] value) {
    return "sha256:" + HexFormat.of().formatHex(digest(value));
  }

  public static String domainId(String domain, byte[] value) {
    return "sha256:" + HexFormat.of().formatHex(domainDigest(domain, value));
  }

  private static byte[] domainDigest(String domain, byte[] value) {
    var digest = sha256();
    digest.update(domain.getBytes(StandardCharsets.US_ASCII));
    digest.update((byte) 0);
    return digest.digest(value);
  }

  private static byte[] digest(byte[] value) {
    return sha256().digest(value);
  }

  private static MessageDigest sha256() {
    try {
      return MessageDigest.getInstance("SHA-256");
    } catch (java.security.NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  private static byte[] hexDigest(String contentId) {
    return HexFormat.of().parseHex(contentId.substring(7));
  }

  private static String extract(String document, String key) {
    var marker = "\"" + key + "\":\"";
    var offset = document.indexOf(marker);
    require(offset >= 0, key + " is missing");
    require(document.indexOf(marker, offset + marker.length()) < 0, key + " is duplicated");
    offset += marker.length();
    var end = document.indexOf('"', offset);
    require(end >= 0, key + " is truncated");
    return document.substring(offset, end);
  }

  private static String extractUnsigned(String document, String key) {
    var marker = "\"" + key + "\":";
    var offset = document.indexOf(marker);
    require(offset >= 0, key + " is missing");
    require(document.indexOf(marker, offset + marker.length()) < 0, key + " is duplicated");
    offset += marker.length();
    var end = offset;
    while (end < document.length() && Character.isDigit(document.charAt(end))) {
      ++end;
    }
    require(end > offset, key + " is not unsigned");
    return document.substring(offset, end);
  }

  public static void requireContentId(String value, String label) {
    require(value != null && CONTENT_ID.matcher(value).matches(), label + " is malformed");
  }

  public static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
