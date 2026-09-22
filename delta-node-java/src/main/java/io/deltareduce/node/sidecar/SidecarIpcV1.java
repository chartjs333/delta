package io.deltareduce.node.sidecar;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Strict bounded-copy codec for {@code delta-local-sidecar-ipc/1.0}. */
public final class SidecarIpcV1 {
  public static final int IPC_MAJOR = 1;
  public static final int IPC_MINOR = 0;
  public static final int HEADER_BYTES = 128;
  public static final int MAX_LOGICAL_PAYLOAD_BYTES = 16_785_408;
  public static final int MAX_CONTROL_ENVELOPE_BYTES = 16_785_536;
  public static final int MAX_CANONICAL_COMMAND_BYTES = 16_777_216;
  public static final int MAX_CANONICAL_EFFECT_BYTES = 16_777_216;
  public static final int MAX_REQUEST_ID_BYTES = 256;
  public static final int MAX_IDENTITY_TEXT_BYTES = 256;
  public static final int MAX_OPEN_DIRECTORY_UTF8_BYTES = 4_096;
  public static final int MAX_NESTED_DESCRIPTOR_BYTES = 2_048;
  public static final int MAX_ERROR_DETAIL_BYTES = 512;
  public static final int INGRESS_QUEUE_REQUESTS = 64;
  public static final int IN_FLIGHT_CORRELATIONS = 64;
  public static final int TRACKED_TIMERS = 65_536;
  public static final long NATIVE_STATUS_UNAVAILABLE = 4_294_967_295L;

  public static final int FLAG_PAYLOAD_INLINE = 0x01;
  public static final int FLAG_PAYLOAD_SHARED_MEMORY = 0x02;
  public static final int FLAG_RESPONSE_EXPECTED = 0x04;
  public static final int FLAG_READ_ONLY = 0x08;

  public static final String CONTRACT_NAME = "delta-local-sidecar-ipc";
  public static final String CANONICAL_ENCODING_ID =
      "sha256:393cd207a2cd3fd4da366be56095a3467e3184c2c5db1d300d1c07d49cdd7aff";
  public static final String FRAME_LAYOUT_SHA256 =
      "sha256:46fcc91280fc2c878cb176bf6e9d855f8e39ac9fffcf18709b1a6b80a30ce18e";
  public static final String PAYLOAD_SCHEMA_SHA256 =
      "sha256:31edfa48d707fb06cd24624d1790946981294bb093d74d44c202a5d15c5376c5";
  public static final String MESSAGE_TYPE_TABLE_SHA256 =
      "sha256:dfa3fe65b946e6527b317168ef0ea000a4610bba1e9c1ed9ebd099adff71e64e";
  public static final String FLAG_TABLE_SHA256 =
      "sha256:6aa94eb75b5b6af99132f71b2753d56988454be86a371b46f46241cf7a8e33d5";
  public static final String BOUNDS_SHA256 =
      "sha256:32d9e791ac35dc6bb061aaedb0a67ee28ad1a2662bbb0ffd1bfc9177b055d0f8";
  public static final String SHARED_MEMORY_LAYOUT_SHA256 =
      "sha256:0a48282fddae72060e9b93c02f97f174b56f8a20b07aabb88ee51f7ef03f5aa4";

  private static final byte[] MAGIC = "DELTAIPC".getBytes(StandardCharsets.US_ASCII);
  private static final byte[] ABI_MAGIC = "DELTABI1".getBytes(StandardCharsets.US_ASCII);
  private static final byte[] REQUEST_DOMAIN =
      "DELTAIPCREQUEST1".getBytes(StandardCharsets.US_ASCII);
  private static final byte[] EMPTY_SHA256 = sha256(new byte[0]);
  private static final int KNOWN_FLAGS =
      FLAG_PAYLOAD_INLINE
          | FLAG_PAYLOAD_SHARED_MEMORY
          | FLAG_RESPONSE_EXPECTED
          | FLAG_READ_ONLY;
  private static final Map<MessageType, List<FieldRule>> SCHEMAS = schemas();

  private SidecarIpcV1() {}

  public enum MessageType {
    CLIENT_HELLO(0x01, true, false, false),
    SERVER_DESCRIPTOR(0x02, false, false, false),
    OPEN_REQUEST(0x10, true, false, true),
    OPEN_RESPONSE(0x11, false, false, false),
    SUBMIT_REQUEST(0x20, true, false, true),
    SUBMIT_RESPONSE(0x21, false, false, true),
    STATE_REQUEST(0x30, true, true, false),
    STATE_RESPONSE(0x31, false, false, true),
    SNAPSHOT_REQUEST(0x40, true, false, false),
    SNAPSHOT_RESPONSE(0x41, false, false, true),
    CLOSE_REQUEST(0x50, true, false, false),
    CLOSE_RESPONSE(0x51, false, false, false),
    HEALTH_REQUEST(0x60, true, true, false),
    HEALTH_RESPONSE(0x61, false, false, false),
    SHARED_MEMORY_ACK(0x70, false, false, false),
    ERROR_RESPONSE(0xff, false, false, false);

    private final int code;
    private final boolean responseExpected;
    private final boolean readOnly;
    private final boolean sharedMemoryEligible;

    MessageType(
        int code, boolean responseExpected, boolean readOnly, boolean sharedMemoryEligible) {
      this.code = code;
      this.responseExpected = responseExpected;
      this.readOnly = readOnly;
      this.sharedMemoryEligible = sharedMemoryEligible;
    }

    public int code() {
      return code;
    }

    public boolean responseExpected() {
      return responseExpected;
    }

    public boolean readOnly() {
      return readOnly;
    }

    public boolean sharedMemoryEligible() {
      return sharedMemoryEligible;
    }

    public boolean isRequest() {
      return responseExpected;
    }

    public static MessageType fromCode(int code) {
      for (var value : values()) {
        if (value.code == code) {
          return value;
        }
      }
      throw invalid("unknown message type: " + code);
    }

    public MessageType expectedResponse() {
      return switch (this) {
        case CLIENT_HELLO -> SERVER_DESCRIPTOR;
        case OPEN_REQUEST -> OPEN_RESPONSE;
        case SUBMIT_REQUEST -> SUBMIT_RESPONSE;
        case STATE_REQUEST -> STATE_RESPONSE;
        case SNAPSHOT_REQUEST -> SNAPSHOT_RESPONSE;
        case CLOSE_REQUEST -> CLOSE_RESPONSE;
        case HEALTH_REQUEST -> HEALTH_RESPONSE;
        default -> throw invalid("message does not expect a response: " + this);
      };
    }
  }

  public enum WireType {
    U8(1, 1),
    U16_BE(2, 2),
    U32_BE(3, 4),
    U64_BE(4, 8),
    ID128(5, 16),
    SHA256(6, 32),
    BYTES(7, -1),
    CANONICAL_UTF8(8, -1),
    SHM_REFERENCE_64(9, 64);

    private final int code;
    private final int exactLength;

    WireType(int code, int exactLength) {
      this.code = code;
      this.exactLength = exactLength;
    }

    public int code() {
      return code;
    }

    static WireType fromCode(int code) {
      for (var value : values()) {
        if (value.code == code) {
          return value;
        }
      }
      throw invalid("unknown wire type: " + code);
    }
  }

  public enum AdmissionState {
    NOT_APPLICABLE(0),
    NOT_ADMITTED_PROVEN(1),
    ADMITTED_OUTCOME_AVAILABLE(2),
    OUTCOME_UNKNOWN(3);

    private final int code;

    AdmissionState(int code) {
      this.code = code;
    }

    public int code() {
      return code;
    }

    static AdmissionState fromCode(int code) {
      for (var value : values()) {
        if (value.code == code) {
          return value;
        }
      }
      throw invalid("unknown admission state: " + code);
    }
  }

  public enum HealthState {
    DESCRIBE_ONLY(0),
    RECOVERING(1),
    READY(2),
    SUSPECTED_FENCED(3),
    UNREADY(4);

    private final int code;

    HealthState(int code) {
      this.code = code;
    }

    public int code() {
      return code;
    }

    static HealthState fromCode(int code) {
      for (var value : values()) {
        if (value.code == code) {
          return value;
        }
      }
      throw invalid("unknown health state: " + code);
    }
  }

  public enum CloseMode {
    DRAINED_TERMINAL_ONLY(1),
    TERMINATE_AND_FENCE(2);

    private final int code;

    CloseMode(int code) {
      this.code = code;
    }

    public int code() {
      return code;
    }
  }

  public enum LocalError {
    FRAME_INVALID(1),
    IDENTITY_MISMATCH(2),
    STALE_GENERATION(3),
    BACKPRESSURE(4),
    OUTCOME_UNKNOWN(5),
    INTERNAL_TRANSPORT_ERROR(6);

    private final int code;

    LocalError(int code) {
      this.code = code;
    }

    public int code() {
      return code;
    }
  }

  /** Per-direction strict-u64 sequence state. Unsigned max is claimable once, then exhausted. */
  public static final class SequenceCursor {
    private long next;
    private boolean exhausted;

    public SequenceCursor(long first) {
      require(first != 0, "transport sequence zero is reserved");
      next = first;
    }

    public synchronized long claim() {
      require(!exhausted, "transport sequence was exhausted after unsigned max");
      var result = next;
      advance();
      return result;
    }

    public synchronized void accept(long actual) {
      require(!exhausted, "transport sequence continued after unsigned max");
      require(actual == next, "non-monotonic transport sequence");
      advance();
    }

    public synchronized long nextValue() {
      require(!exhausted, "transport sequence has no successor after unsigned max");
      return next;
    }

    public synchronized boolean exhausted() {
      return exhausted;
    }

    private void advance() {
      if (next == -1L) {
        exhausted = true;
      } else {
        next += 1;
      }
    }
  }

  /** Immutable 128-bit transport identity. */
  public static final class Id128 {
    private final byte[] bytes;

    public Id128(byte[] bytes) {
      Objects.requireNonNull(bytes, "bytes");
      require(bytes.length == 16, "ID128 must contain exactly 16 bytes");
      this.bytes = Arrays.copyOf(bytes, bytes.length);
    }

    public byte[] bytes() {
      return Arrays.copyOf(bytes, bytes.length);
    }

    public String hex() {
      return HexFormat.of().formatHex(bytes);
    }

    @Override
    public boolean equals(Object other) {
      return other instanceof Id128 value && Arrays.equals(bytes, value.bytes);
    }

    @Override
    public int hashCode() {
      return Arrays.hashCode(bytes);
    }

    @Override
    public String toString() {
      return hex();
    }
  }

  /** Immutable TLV field. */
  public static final class Field {
    private final int id;
    private final WireType type;
    private final byte[] value;

    public Field(int id, WireType type, byte[] value) {
      require(id > 0 && id <= 0xffff, "field ID is outside u16");
      this.id = id;
      this.type = Objects.requireNonNull(type, "type");
      this.value = Arrays.copyOf(Objects.requireNonNull(value, "value"), value.length);
    }

    public int id() {
      return id;
    }

    public WireType type() {
      return type;
    }

    public byte[] value() {
      return Arrays.copyOf(value, value.length);
    }

    int length() {
      return value.length;
    }
  }

  /** Fully validated logical payload. */
  public static final class Payload {
    private final MessageType type;
    private final List<Field> fields;
    private final Map<Integer, Field> byId;
    private final byte[] canonicalBytes;

    private Payload(MessageType type, List<Field> fields, byte[] canonicalBytes) {
      this.type = type;
      this.fields = List.copyOf(fields);
      var index = new LinkedHashMap<Integer, Field>();
      for (var field : fields) {
        index.put(field.id(), field);
      }
      byId = Collections.unmodifiableMap(index);
      this.canonicalBytes = Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    public MessageType type() {
      return type;
    }

    public List<Field> fields() {
      return fields;
    }

    public Field field(int id) {
      var result = byId.get(id);
      if (result == null) {
        throw invalid("payload lacks required field " + id);
      }
      return result;
    }

    public byte[] bytes(int id) {
      return field(id).value();
    }

    public int u8(int id) {
      var value = field(id);
      require(value.type == WireType.U8, "field is not U8: " + id);
      return Byte.toUnsignedInt(value.value[0]);
    }

    public int u16(int id) {
      var value = field(id);
      require(value.type == WireType.U16_BE, "field is not U16: " + id);
      return Short.toUnsignedInt(ByteBuffer.wrap(value.value).order(ByteOrder.BIG_ENDIAN).getShort());
    }

    public long u32(int id) {
      var value = field(id);
      require(value.type == WireType.U32_BE, "field is not U32: " + id);
      return Integer.toUnsignedLong(ByteBuffer.wrap(value.value).order(ByteOrder.BIG_ENDIAN).getInt());
    }

    public long u64Bits(int id) {
      var value = field(id);
      require(value.type == WireType.U64_BE, "field is not U64: " + id);
      return ByteBuffer.wrap(value.value).order(ByteOrder.BIG_ENDIAN).getLong();
    }

    public String text(int id) {
      var value = field(id);
      require(value.type == WireType.CANONICAL_UTF8, "field is not canonical UTF-8: " + id);
      return decodeCanonicalUtf8(value.value, Integer.MAX_VALUE, "field " + id);
    }

    public Id128 id128(int id) {
      var value = field(id);
      require(value.type == WireType.ID128, "field is not ID128: " + id);
      return new Id128(value.value);
    }

    public byte[] canonicalBytes() {
      return Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    public int canonicalLength() {
      return canonicalBytes.length;
    }
  }

  /** Fully validated inline frame. */
  public static final class Frame {
    private final MessageType messageType;
    private final int flags;
    private final Id128 sessionId;
    private final long generation;
    private final Id128 correlationId;
    private final long sequence;
    private final long responseCapacity;
    private final Payload payload;
    private final byte[] payloadSha256;
    private final byte[] canonicalBytes;

    private Frame(
        MessageType messageType,
        int flags,
        Id128 sessionId,
        long generation,
        Id128 correlationId,
        long sequence,
        long responseCapacity,
        Payload payload,
        byte[] payloadSha256,
        byte[] canonicalBytes) {
      this.messageType = messageType;
      this.flags = flags;
      this.sessionId = sessionId;
      this.generation = generation;
      this.correlationId = correlationId;
      this.sequence = sequence;
      this.responseCapacity = responseCapacity;
      this.payload = payload;
      this.payloadSha256 = Arrays.copyOf(payloadSha256, payloadSha256.length);
      this.canonicalBytes = Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    public MessageType messageType() {
      return messageType;
    }

    public int flags() {
      return flags;
    }

    public Id128 sessionId() {
      return sessionId;
    }

    public long generation() {
      return generation;
    }

    public Id128 correlationId() {
      return correlationId;
    }

    public long sequence() {
      return sequence;
    }

    public long responseCapacity() {
      return responseCapacity;
    }

    public Payload payload() {
      return payload;
    }

    public int payloadLength() {
      return payload.canonicalLength();
    }

    public byte[] payloadSha256() {
      return Arrays.copyOf(payloadSha256, payloadSha256.length);
    }

    public byte[] canonicalBytes() {
      return Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }
  }

  /** Canonical nested C-ABI identity carried by the descriptor handshake. */
  public record NestedDescriptor(
      long structSize,
      int abiMajor,
      int abiMinor,
      long featureBits,
      String schemaVersion,
      String protocolVersion,
      String formalSemanticsId,
      String buildId,
      String schemaSetId,
      String runtimeProfile) {
    public NestedDescriptor {
      require(structSize > 0 && structSize <= 0xffff_ffffL, "invalid nested struct size");
      require(abiMajor >= 0 && abiMajor <= 0xffff, "invalid nested ABI major");
      require(abiMinor >= 0 && abiMinor <= 0xffff, "invalid nested ABI minor");
      validateIdentityText(schemaVersion, "schema version");
      validateIdentityText(protocolVersion, "protocol version");
      validateIdentityText(formalSemanticsId, "formal semantics ID");
      validateIdentityText(buildId, "build ID");
      validateIdentityText(schemaSetId, "schema-set ID");
      validateIdentityText(runtimeProfile, "runtime profile");
    }
  }

  /** Expected exact identity for CLIENT_HELLO/SERVER_DESCRIPTOR. */
  public static final class DescriptorIdentity {
    private final Id128 sessionId;
    private final long generation;
    private final byte[] executableSha256;
    private final String sidecarBuildId;
    private final byte[] nestedDescriptor;

    public DescriptorIdentity(
        Id128 sessionId,
        long generation,
        byte[] executableSha256,
        String sidecarBuildId,
        byte[] nestedDescriptor) {
      this.sessionId = Objects.requireNonNull(sessionId, "sessionId");
      require(generation != 0, "generation zero is reserved");
      this.generation = generation;
      this.executableSha256 = digest(executableSha256, "sidecar executable SHA-256");
      validateIdentityText(sidecarBuildId, "sidecar build ID");
      this.sidecarBuildId = sidecarBuildId;
      this.nestedDescriptor =
          Arrays.copyOf(Objects.requireNonNull(nestedDescriptor, "nestedDescriptor"),
              nestedDescriptor.length);
      require(
          this.nestedDescriptor.length > 0
              && this.nestedDescriptor.length <= MAX_NESTED_DESCRIPTOR_BYTES,
          "nested descriptor is outside bounds");
      parseNestedDescriptor(this.nestedDescriptor);
    }

    public Id128 sessionId() {
      return sessionId;
    }

    public long generation() {
      return generation;
    }

    public byte[] executableSha256() {
      return Arrays.copyOf(executableSha256, executableSha256.length);
    }

    public String sidecarBuildId() {
      return sidecarBuildId;
    }

    public byte[] nestedDescriptor() {
      return Arrays.copyOf(nestedDescriptor, nestedDescriptor.length);
    }

    public byte[] nestedDescriptorSha256() {
      return sha256(nestedDescriptor);
    }
  }

  public static Field u8(int id, int value) {
    require(value >= 0 && value <= 0xff, "U8 value is outside bounds");
    return new Field(id, WireType.U8, new byte[] {(byte) value});
  }

  public static Field u16(int id, int value) {
    require(value >= 0 && value <= 0xffff, "U16 value is outside bounds");
    return new Field(
        id, WireType.U16_BE, ByteBuffer.allocate(2).order(ByteOrder.BIG_ENDIAN).putShort((short) value).array());
  }

  public static Field u32(int id, long value) {
    require(value >= 0 && value <= 0xffff_ffffL, "U32 value is outside bounds");
    return new Field(
        id, WireType.U32_BE, ByteBuffer.allocate(4).order(ByteOrder.BIG_ENDIAN).putInt((int) value).array());
  }

  public static Field u64(int id, long unsignedBits) {
    return new Field(
        id, WireType.U64_BE, ByteBuffer.allocate(8).order(ByteOrder.BIG_ENDIAN).putLong(unsignedBits).array());
  }

  public static Field id128(int id, Id128 value) {
    return new Field(id, WireType.ID128, Objects.requireNonNull(value, "value").bytes());
  }

  public static Field sha256Field(int id, byte[] value) {
    return new Field(id, WireType.SHA256, digest(value, "SHA-256 field"));
  }

  public static Field sha256Identity(int id, String value) {
    Objects.requireNonNull(value, "value");
    require(value.matches("sha256:[0-9a-f]{64}"), "invalid textual SHA-256 identity");
    return sha256Field(id, HexFormat.of().parseHex(value.substring(7)));
  }

  public static Field bytes(int id, byte[] value) {
    return new Field(id, WireType.BYTES, value);
  }

  public static Field text(int id, String value) {
    return new Field(id, WireType.CANONICAL_UTF8, encodeCanonicalUtf8(value, Integer.MAX_VALUE, "text"));
  }

  public static Field sharedMemoryReference(int id, byte[] value) {
    return new Field(id, WireType.SHM_REFERENCE_64, value);
  }

  public static Payload descriptorPayload(MessageType type, DescriptorIdentity identity) {
    require(
        type == MessageType.CLIENT_HELLO || type == MessageType.SERVER_DESCRIPTOR,
        "descriptor payload has the wrong message type");
    Objects.requireNonNull(identity, "identity");
    return payload(
        type,
        List.of(
            text(1, CONTRACT_NAME),
            u16(2, IPC_MAJOR),
            u16(3, IPC_MINOR),
            sha256Identity(4, CANONICAL_ENCODING_ID),
            sha256Identity(5, FRAME_LAYOUT_SHA256),
            sha256Identity(6, PAYLOAD_SCHEMA_SHA256),
            sha256Identity(7, MESSAGE_TYPE_TABLE_SHA256),
            sha256Identity(8, FLAG_TABLE_SHA256),
            sha256Identity(9, BOUNDS_SHA256),
            sha256Identity(10, SHARED_MEMORY_LAYOUT_SHA256),
            id128(11, identity.sessionId),
            u64(12, identity.generation),
            sha256Field(13, identity.executableSha256),
            text(14, identity.sidecarBuildId),
            u16(15, 1),
            bytes(16, identity.nestedDescriptor),
            sha256Field(17, identity.nestedDescriptorSha256())));
  }

  public static Payload requestPayload(
      MessageType type, byte[] canonicalRequestId, List<Field> operationFields) {
    require(type.isRequest() && type != MessageType.CLIENT_HELLO, "not an operation request");
    var requestId = Arrays.copyOf(
        Objects.requireNonNull(canonicalRequestId, "canonicalRequestId"),
        canonicalRequestId.length);
    require(requestId.length > 0 && requestId.length <= MAX_REQUEST_ID_BYTES,
        "canonical request ID is outside bounds");
    var operations = List.copyOf(Objects.requireNonNull(operationFields, "operationFields"));
    for (var field : operations) {
      require(field.id >= 16, "operation fields must start at ID 16");
    }
    var digest = requestDigest(type, operations);
    var fields = new ArrayList<Field>(operations.size() + 2);
    fields.add(bytes(1, requestId));
    fields.add(sha256Field(2, digest));
    fields.addAll(operations);
    return payload(type, fields);
  }

  public static Payload responsePayload(
      MessageType type,
      byte[] canonicalRequestId,
      byte[] requestDigest,
      List<Field> responseFields) {
    require(!type.isRequest() && type != MessageType.SERVER_DESCRIPTOR,
        "not an operation response");
    var fields = new ArrayList<Field>(responseFields.size() + 2);
    fields.add(bytes(1, canonicalRequestId));
    fields.add(sha256Field(2, requestDigest));
    fields.addAll(responseFields);
    return payload(type, fields);
  }

  public static Payload payload(MessageType type, List<Field> fields) {
    Objects.requireNonNull(type, "type");
    var immutable = List.copyOf(Objects.requireNonNull(fields, "fields"));
    validateFields(type, immutable);
    var value = encodeFields(immutable);
    require(value.length <= MAX_LOGICAL_PAYLOAD_BYTES - 16, "payload metadata exceeds bound");
    var output = ByteBuffer.allocate(16 + value.length).order(ByteOrder.BIG_ENDIAN);
    output.putShort((short) type.code);
    output.putShort((short) 1);
    output.putShort((short) 0);
    output.putShort((short) 0);
    output.putLong(value.length);
    output.put(value);
    var canonical = output.array();
    validatePayloadSemantics(type, immutable);
    return new Payload(type, immutable, canonical);
  }

  public static Payload decodePayload(MessageType expectedType, byte[] canonicalBytes) {
    Objects.requireNonNull(expectedType, "expectedType");
    var bytes = Arrays.copyOf(Objects.requireNonNull(canonicalBytes, "canonicalBytes"),
        canonicalBytes.length);
    require(bytes.length >= 16 && bytes.length <= MAX_LOGICAL_PAYLOAD_BYTES,
        "logical payload is outside bounds");
    var input = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN);
    require(Short.toUnsignedInt(input.getShort()) == expectedType.code,
        "payload schema type differs from message type");
    require(Short.toUnsignedInt(input.getShort()) == 1, "payload schema major mismatch");
    require(Short.toUnsignedInt(input.getShort()) == 0, "payload schema minor mismatch");
    require(input.getShort() == 0, "payload prefix reserved bytes are nonzero");
    var declared = input.getLong();
    require(declared >= 0 && declared == input.remaining(), "payload value length mismatch");
    var rules = SCHEMAS.get(expectedType);
    require(rules != null, "missing schema for " + expectedType);
    var fields = new ArrayList<Field>(rules.size());
    for (var rule : rules) {
      require(input.remaining() >= 8, "truncated TLV header");
      var id = Short.toUnsignedInt(input.getShort());
      var wire = WireType.fromCode(Byte.toUnsignedInt(input.get()));
      require(input.get() == 0, "TLV flags are nonzero");
      var length = Integer.toUnsignedLong(input.getInt());
      require(length <= Integer.MAX_VALUE && length <= input.remaining(), "truncated TLV value");
      require(id == rule.id && wire == rule.type, "unexpected TLV field or wire type");
      var value = new byte[(int) length];
      input.get(value);
      validateField(rule, value);
      fields.add(new Field(id, wire, value));
    }
    require(!input.hasRemaining(), "payload has unknown or trailing fields");
    validatePayloadSemantics(expectedType, fields);
    return new Payload(expectedType, fields, bytes);
  }

  public static Frame frame(
      MessageType type,
      Id128 sessionId,
      long generation,
      Id128 correlationId,
      long sequence,
      Payload payload) {
    Objects.requireNonNull(type, "type");
    Objects.requireNonNull(payload, "payload");
    require(type == payload.type, "frame and payload types differ");
    require(generation != 0, "generation zero is reserved");
    require(sequence != 0, "transport sequence zero is reserved");
    var flags = inlineFlags(type);
    var responseCapacity = type.responseExpected ? MAX_LOGICAL_PAYLOAD_BYTES : 0L;
    var logical = payload.canonicalBytes;
    var logicalDigest = sha256(logical);
    require(logical.length <= MAX_LOGICAL_PAYLOAD_BYTES, "logical payload exceeds bound");
    var output = ByteBuffer.allocate(HEADER_BYTES + logical.length).order(ByteOrder.BIG_ENDIAN);
    output.put(MAGIC);
    output.putShort((short) IPC_MAJOR);
    output.putShort((short) IPC_MINOR);
    output.putShort((short) HEADER_BYTES);
    output.putShort((short) type.code);
    output.putInt(flags);
    output.put(Objects.requireNonNull(sessionId, "sessionId").bytes);
    output.putLong(generation);
    output.put(Objects.requireNonNull(correlationId, "correlationId").bytes);
    output.putLong(sequence);
    output.putLong(logical.length);
    output.putLong(responseCapacity);
    output.put(logicalDigest);
    output.put(new byte[12]);
    output.put(logical);
    var canonical = output.array();
    require(canonical.length <= MAX_CONTROL_ENVELOPE_BYTES, "control envelope exceeds bound");
    return new Frame(
        type,
        flags,
        sessionId,
        generation,
        correlationId,
        sequence,
        responseCapacity,
        payload,
        logicalDigest,
        canonical);
  }

  public static Frame decodeFrame(byte[] canonicalBytes) {
    var bytes = Arrays.copyOf(Objects.requireNonNull(canonicalBytes, "canonicalBytes"),
        canonicalBytes.length);
    require(bytes.length >= HEADER_BYTES && bytes.length <= MAX_CONTROL_ENVELOPE_BYTES,
        "control envelope is outside bounds");
    var input = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN);
    var magic = new byte[MAGIC.length];
    input.get(magic);
    require(Arrays.equals(magic, MAGIC), "frame magic mismatch");
    require(Short.toUnsignedInt(input.getShort()) == IPC_MAJOR, "IPC major mismatch");
    require(Short.toUnsignedInt(input.getShort()) == IPC_MINOR, "IPC minor mismatch");
    require(Short.toUnsignedInt(input.getShort()) == HEADER_BYTES, "header length mismatch");
    var type = MessageType.fromCode(Short.toUnsignedInt(input.getShort()));
    var flags = input.getInt();
    validateInlineFlags(type, flags);
    var session = new byte[16];
    input.get(session);
    var generation = input.getLong();
    require(generation != 0, "generation zero is reserved");
    var correlation = new byte[16];
    input.get(correlation);
    var sequence = input.getLong();
    require(sequence != 0, "transport sequence zero is reserved");
    var payloadLength = input.getLong();
    require(payloadLength >= 0 && payloadLength <= MAX_LOGICAL_PAYLOAD_BYTES,
        "payload length is outside bounds");
    var responseCapacity = input.getLong();
    var expectedCapacity = type.responseExpected ? MAX_LOGICAL_PAYLOAD_BYTES : 0L;
    require(responseCapacity == expectedCapacity, "response capacity violates frozen rule");
    var expectedDigest = new byte[32];
    input.get(expectedDigest);
    var reserved = new byte[12];
    input.get(reserved);
    require(allZero(reserved), "frame reserved bytes are nonzero");
    require(payloadLength == input.remaining(), "inline payload length or trailing bytes mismatch");
    var logical = new byte[(int) payloadLength];
    input.get(logical);
    require(Arrays.equals(expectedDigest, sha256(logical)), "payload SHA-256 mismatch");
    var payload = decodePayload(type, logical);
    return new Frame(
        type,
        flags,
        new Id128(session),
        generation,
        new Id128(correlation),
        sequence,
        responseCapacity,
        payload,
        expectedDigest,
        bytes);
  }

  public static void requireDescriptor(Payload payload, DescriptorIdentity expected) {
    Objects.requireNonNull(payload, "payload");
    Objects.requireNonNull(expected, "expected");
    require(
        payload.type == MessageType.CLIENT_HELLO
            || payload.type == MessageType.SERVER_DESCRIPTOR,
        "not a descriptor payload");
    require(payload.text(1).equals(CONTRACT_NAME), "IPC contract name mismatch");
    require(payload.u16(2) == IPC_MAJOR && payload.u16(3) == IPC_MINOR,
        "IPC contract version mismatch");
    requireDigestIdentity(payload.bytes(4), CANONICAL_ENCODING_ID, "canonical encoding");
    requireDigestIdentity(payload.bytes(5), FRAME_LAYOUT_SHA256, "frame layout");
    requireDigestIdentity(payload.bytes(6), PAYLOAD_SCHEMA_SHA256, "payload schema");
    requireDigestIdentity(payload.bytes(7), MESSAGE_TYPE_TABLE_SHA256, "message table");
    requireDigestIdentity(payload.bytes(8), FLAG_TABLE_SHA256, "flag table");
    requireDigestIdentity(payload.bytes(9), BOUNDS_SHA256, "bounds");
    requireDigestIdentity(payload.bytes(10), SHARED_MEMORY_LAYOUT_SHA256, "shared-memory layout");
    require(payload.id128(11).equals(expected.sessionId), "descriptor session mismatch");
    require(payload.u64Bits(12) == expected.generation, "descriptor generation mismatch");
    require(Arrays.equals(payload.bytes(13), expected.executableSha256),
        "sidecar executable identity mismatch");
    require(payload.text(14).equals(expected.sidecarBuildId), "sidecar build ID mismatch");
    require(payload.u16(15) == 1, "outer deployment profile is not ISOLATED_SIDECAR");
    require(Arrays.equals(payload.bytes(16), expected.nestedDescriptor),
        "nested C ABI descriptor mismatch");
    require(Arrays.equals(payload.bytes(17), expected.nestedDescriptorSha256()),
        "nested descriptor digest mismatch");
    parseNestedDescriptor(payload.bytes(16));
  }

  public static NestedDescriptor parseNestedDescriptor(byte[] canonicalBytes) {
    var bytes = Arrays.copyOf(Objects.requireNonNull(canonicalBytes, "canonicalBytes"),
        canonicalBytes.length);
    require(bytes.length >= 28 && bytes.length <= MAX_NESTED_DESCRIPTOR_BYTES,
        "nested C ABI descriptor is outside bounds");
    var input = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN);
    var magic = new byte[8];
    input.get(magic);
    require(Arrays.equals(magic, ABI_MAGIC), "nested C ABI magic mismatch");
    var encodedLength = Integer.toUnsignedLong(input.getInt());
    require(encodedLength == bytes.length, "nested C ABI encoded length mismatch");
    var structSize = Integer.toUnsignedLong(input.getInt());
    var abiMajor = Short.toUnsignedInt(input.getShort());
    var abiMinor = Short.toUnsignedInt(input.getShort());
    var featureBits = input.getLong();
    var values = new String[6];
    for (var index = 0; index < values.length; ++index) {
      require(input.remaining() >= 4, "truncated nested C ABI text length");
      var length = Integer.toUnsignedLong(input.getInt());
      require(length <= MAX_IDENTITY_TEXT_BYTES && length <= input.remaining(),
          "nested C ABI text is outside bounds");
      var value = new byte[(int) length];
      input.get(value);
      values[index] = decodeCanonicalUtf8(value, MAX_IDENTITY_TEXT_BYTES, "nested descriptor text");
    }
    require(!input.hasRemaining(), "nested C ABI descriptor has trailing bytes");
    return new NestedDescriptor(
        structSize,
        abiMajor,
        abiMinor,
        featureBits,
        values[0],
        values[1],
        values[2],
        values[3],
        values[4],
        values[5]);
  }

  public static byte[] encodeNestedDescriptor(NestedDescriptor descriptor) {
    Objects.requireNonNull(descriptor, "descriptor");
    var texts = List.of(
        descriptor.schemaVersion,
        descriptor.protocolVersion,
        descriptor.formalSemanticsId,
        descriptor.buildId,
        descriptor.schemaSetId,
        descriptor.runtimeProfile);
    var encoded = new ArrayList<byte[]>(texts.size());
    var total = 28;
    for (var text : texts) {
      var value = encodeCanonicalUtf8(text, MAX_IDENTITY_TEXT_BYTES, "nested descriptor text");
      encoded.add(value);
      total = Math.addExact(total, Math.addExact(4, value.length));
    }
    require(total <= MAX_NESTED_DESCRIPTOR_BYTES, "nested descriptor exceeds bound");
    var output = ByteBuffer.allocate(total).order(ByteOrder.BIG_ENDIAN);
    output.put(ABI_MAGIC);
    output.putInt(total);
    output.putInt((int) descriptor.structSize);
    output.putShort((short) descriptor.abiMajor);
    output.putShort((short) descriptor.abiMinor);
    output.putLong(descriptor.featureBits);
    for (var value : encoded) {
      output.putInt(value.length);
      output.put(value);
    }
    return output.array();
  }

  public static void requireRequestDigest(Payload request) {
    require(request.type.isRequest() && request.type != MessageType.CLIENT_HELLO,
        "not a digest-bearing request");
    var operations = request.fields.stream().filter(field -> field.id >= 16).toList();
    require(Arrays.equals(request.bytes(2), requestDigest(request.type, operations)),
        "request digest mismatch");
  }

  public static void requireResponseMatches(
      Frame response,
      MessageType requestType,
      byte[] requestId,
      byte[] requestDigest,
      Id128 session,
      long generation,
      Id128 correlation) {
    Objects.requireNonNull(response, "response");
    var expectedType = requestType.expectedResponse();
    require(
        response.messageType == expectedType || response.messageType == MessageType.ERROR_RESPONSE,
        "response operation mismatch");
    if (response.messageType == MessageType.ERROR_RESPONSE) {
      require(
          response.payload.u16(17) == requestType.code(),
          "error response offending message type mismatch");
    }
    require(response.sessionId.equals(session), "response session mismatch");
    require(response.generation == generation, "response generation mismatch");
    require(response.correlationId.equals(correlation), "response correlation mismatch");
    require(Arrays.equals(response.payload.bytes(1), requestId), "response request ID mismatch");
    require(Arrays.equals(response.payload.bytes(2), requestDigest), "response request digest mismatch");
  }

  public static int inlineFlags(MessageType type) {
    var flags = FLAG_PAYLOAD_INLINE;
    if (type.responseExpected) {
      flags |= FLAG_RESPONSE_EXPECTED;
    }
    if (type.readOnly) {
      flags |= FLAG_READ_ONLY;
    }
    return flags;
  }

  /**
   * Returns the strict unsigned successor. {@code 0xffffffffffffffff} is itself a valid frame
   * sequence, but asking for a successor after that frame permanently fences the generation.
   */
  public static long nextSequence(long current) {
    require(current != 0, "sequence zero is reserved");
    require(current != -1L, "sequence overflow permanently fences the generation");
    return current + 1;
  }

  public static byte[] sha256(byte[] value) {
    try {
      return MessageDigest.getInstance("SHA-256").digest(
          Arrays.copyOf(Objects.requireNonNull(value, "value"), value.length));
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  public static byte[] emptySha256() {
    return Arrays.copyOf(EMPTY_SHA256, EMPTY_SHA256.length);
  }

  private static byte[] requestDigest(MessageType type, List<Field> operationFields) {
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      digest.update(REQUEST_DOMAIN);
      var prefix = ByteBuffer.allocate(6).order(ByteOrder.BIG_ENDIAN);
      prefix.putShort((short) type.code).putShort((short) 1).putShort((short) 0);
      digest.update(prefix.array());
      digest.update(encodeFields(operationFields));
      return digest.digest();
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException("SHA-256 is unavailable", error);
    }
  }

  private static byte[] encodeFields(List<Field> fields) {
    var output = new ByteArrayOutputStream();
    var previous = 0;
    for (var field : fields) {
      require(field.id > previous, "field IDs are not strictly increasing");
      var header = ByteBuffer.allocate(8).order(ByteOrder.BIG_ENDIAN);
      header.putShort((short) field.id);
      header.put((byte) field.type.code);
      header.put((byte) 0);
      header.putInt(field.value.length);
      output.writeBytes(header.array());
      output.writeBytes(field.value);
      require(output.size() <= MAX_LOGICAL_PAYLOAD_BYTES, "encoded fields exceed bound");
      previous = field.id;
    }
    return output.toByteArray();
  }

  private static void validateFields(MessageType type, List<Field> fields) {
    var rules = SCHEMAS.get(type);
    require(rules != null, "missing payload schema for " + type);
    require(fields.size() == rules.size(), "payload field count mismatch for " + type);
    for (var index = 0; index < rules.size(); ++index) {
      var field = fields.get(index);
      var rule = rules.get(index);
      require(field.id == rule.id && field.type == rule.type,
          "payload field order/type mismatch for " + type);
      validateField(rule, field.value);
    }
  }

  private static void validateField(FieldRule rule, byte[] value) {
    if (rule.type.exactLength >= 0) {
      require(value.length == rule.type.exactLength, "field " + rule.id + " has the wrong width");
    } else {
      require(value.length <= rule.maximumLength, "field " + rule.id + " exceeds its bound");
    }
    if (rule.type == WireType.CANONICAL_UTF8) {
      decodeCanonicalUtf8(value, rule.maximumLength, "field " + rule.id);
    }
  }

  private static void validatePayloadSemantics(MessageType type, List<Field> fields) {
    var map = new LinkedHashMap<Integer, Field>();
    for (var field : fields) {
      map.put(field.id, field);
    }
    if (type.isRequest() && type != MessageType.CLIENT_HELLO) {
      require(map.get(1).value.length > 0, "request ID is empty");
      var operations = fields.stream().filter(field -> field.id >= 16).toList();
      require(Arrays.equals(map.get(2).value, requestDigest(type, operations)),
          "request digest mismatch");
    }
    if (type == MessageType.CLIENT_HELLO || type == MessageType.SERVER_DESCRIPTOR) {
      require(textValue(map.get(1)).equals(CONTRACT_NAME), "contract name mismatch");
      require(u16Value(map.get(2)) == IPC_MAJOR && u16Value(map.get(3)) == IPC_MINOR,
          "descriptor version mismatch");
      requireDigestIdentity(map.get(4).value, CANONICAL_ENCODING_ID, "canonical encoding");
      requireDigestIdentity(map.get(5).value, FRAME_LAYOUT_SHA256, "frame layout");
      requireDigestIdentity(map.get(6).value, PAYLOAD_SCHEMA_SHA256, "payload schema");
      requireDigestIdentity(map.get(7).value, MESSAGE_TYPE_TABLE_SHA256, "message table");
      requireDigestIdentity(map.get(8).value, FLAG_TABLE_SHA256, "flag table");
      requireDigestIdentity(map.get(9).value, BOUNDS_SHA256, "bounds");
      requireDigestIdentity(map.get(10).value, SHARED_MEMORY_LAYOUT_SHA256, "SHM layout");
      require(u64Value(map.get(12)) != 0, "descriptor generation is zero");
      require(u16Value(map.get(15)) == 1, "outer deployment profile mismatch");
      parseNestedDescriptor(map.get(16).value);
      require(Arrays.equals(map.get(17).value, sha256(map.get(16).value)),
          "nested descriptor digest mismatch");
    }
    switch (type) {
      case OPEN_REQUEST -> require(
          u32Value(map.get(16)) == INGRESS_QUEUE_REQUESTS,
          "submission capacity differs from frozen bound");
      case OPEN_RESPONSE -> requireBoolean(map.get(19), "ready");
      case SUBMIT_RESPONSE -> require(
          Arrays.equals(map.get(18).value, sha256(map.get(17).value)),
          "effect digest mismatch");
      case STATE_RESPONSE -> require(
          Arrays.equals(map.get(18).value, sha256(map.get(19).value)),
          "state digest mismatch");
      case SNAPSHOT_RESPONSE -> require(
          Arrays.equals(map.get(18).value, sha256(map.get(19).value)),
          "snapshot receipt digest mismatch");
      case CLOSE_REQUEST -> requireRange(u8Value(map.get(17)), 1, 2, "close mode");
      case CLOSE_RESPONSE -> requireBoolean(map.get(18), "closed");
      case HEALTH_RESPONSE -> {
        requireRange(u8Value(map.get(16)), 0, 4, "health state");
        require(u64Value(map.get(17)) != 0, "health generation is zero");
        requireBoolean(map.get(20), "durable lock held");
        requireBoolean(map.get(21), "ready");
      }
      case SHARED_MEMORY_ACK -> requireRange(u8Value(map.get(17)), 1, 4, "SHM disposition");
      case ERROR_RESPONSE -> {
        requireRange(u32Value(map.get(16)), 1, 6, "local error");
        MessageType.fromCode(u16Value(map.get(17)));
        require(u64Value(map.get(18)) == 0
                || Long.compareUnsigned(u64Value(map.get(18)), MAX_LOGICAL_PAYLOAD_BYTES) <= 0,
            "required response capacity exceeds bound");
      }
      default -> {
        // Field-level validation is complete for the remaining schemas.
      }
    }
    if (!type.isRequest()
        && type != MessageType.SERVER_DESCRIPTOR
        && type != MessageType.SHARED_MEMORY_ACK) {
      validateAdmission(type, map);
    }
  }

  private static void validateAdmission(MessageType type, Map<Integer, Field> fields) {
    var admission = AdmissionState.fromCode(u8Value(fields.get(3)));
    var sequence = u64Value(fields.get(4));
    var nativeStatus = u32Value(fields.get(5));
    switch (admission) {
      case NOT_APPLICABLE -> {
        require(sequence == 0 && nativeStatus == 0, "NOT_APPLICABLE fields are incoherent");
        require(type == MessageType.HEALTH_RESPONSE,
            "NOT_APPLICABLE cannot carry an operation result");
      }
      case NOT_ADMITTED_PROVEN -> {
        require(sequence == 0 && nativeStatus == NATIVE_STATUS_UNAVAILABLE,
            "NOT_ADMITTED_PROVEN fields are incoherent");
        require(type == MessageType.ERROR_RESPONSE,
            "NOT_ADMITTED_PROVEN must use ERROR_RESPONSE");
      }
      case ADMITTED_OUTCOME_AVAILABLE -> {
        require(sequence != 0, "admitted sequence is zero");
        if (type == MessageType.ERROR_RESPONSE) {
          require(nativeStatus != 0, "admitted native failure lacks status");
        } else {
          require(nativeStatus == 0, "successful operation response has nonzero status");
        }
      }
      case OUTCOME_UNKNOWN -> {
        require(sequence != 0, "unknown outcome lacks admitted sequence");
        require(type == MessageType.ERROR_RESPONSE, "OUTCOME_UNKNOWN must use ERROR_RESPONSE");
        require(nativeStatus != 0, "OUTCOME_UNKNOWN has a successful native status");
      }
    }
  }

  private static Map<MessageType, List<FieldRule>> schemas() {
    var result = new EnumMap<MessageType, List<FieldRule>>(MessageType.class);
    var descriptor = List.of(
        textRule(1, 64),
        fixed(2, WireType.U16_BE),
        fixed(3, WireType.U16_BE),
        fixed(4, WireType.SHA256),
        fixed(5, WireType.SHA256),
        fixed(6, WireType.SHA256),
        fixed(7, WireType.SHA256),
        fixed(8, WireType.SHA256),
        fixed(9, WireType.SHA256),
        fixed(10, WireType.SHA256),
        fixed(11, WireType.ID128),
        fixed(12, WireType.U64_BE),
        fixed(13, WireType.SHA256),
        textRule(14, MAX_IDENTITY_TEXT_BYTES),
        fixed(15, WireType.U16_BE),
        bytesRule(16, MAX_NESTED_DESCRIPTOR_BYTES),
        fixed(17, WireType.SHA256));
    result.put(MessageType.CLIENT_HELLO, descriptor);
    result.put(MessageType.SERVER_DESCRIPTOR, descriptor);
    result.put(MessageType.OPEN_REQUEST, List.of(
        bytesRule(1, MAX_REQUEST_ID_BYTES), fixed(2, WireType.SHA256),
        fixed(16, WireType.U32_BE), textRule(17, MAX_OPEN_DIRECTORY_UTF8_BYTES),
        bytesRule(18, MAX_CANONICAL_COMMAND_BYTES), fixed(19, WireType.SHA256)));
    result.put(MessageType.OPEN_RESPONSE, responseRules(
        fixed(16, WireType.ID128), fixed(17, WireType.U64_BE),
        fixed(18, WireType.SHA256), fixed(19, WireType.U8)));
    result.put(MessageType.SUBMIT_REQUEST, List.of(
        bytesRule(1, MAX_REQUEST_ID_BYTES), fixed(2, WireType.SHA256),
        bytesRule(16, MAX_CANONICAL_COMMAND_BYTES)));
    result.put(MessageType.SUBMIT_RESPONSE, responseRules(
        bytesRule(16, MAX_REQUEST_ID_BYTES), bytesRule(17, MAX_CANONICAL_EFFECT_BYTES),
        fixed(18, WireType.SHA256), fixed(19, WireType.U64_BE),
        fixed(20, WireType.SHA256), fixed(21, WireType.SHA256)));
    result.put(MessageType.STATE_REQUEST, simpleRuntimeRequest());
    result.put(MessageType.SNAPSHOT_REQUEST, simpleRuntimeRequest());
    result.put(MessageType.STATE_RESPONSE, responseRules(
        fixed(16, WireType.U64_BE), fixed(17, WireType.SHA256),
        fixed(18, WireType.SHA256), bytesRule(19, MAX_CANONICAL_EFFECT_BYTES)));
    result.put(MessageType.SNAPSHOT_RESPONSE, responseRules(
        fixed(16, WireType.U64_BE), fixed(17, WireType.SHA256),
        fixed(18, WireType.SHA256), bytesRule(19, MAX_CANONICAL_EFFECT_BYTES)));
    result.put(MessageType.CLOSE_REQUEST, List.of(
        bytesRule(1, MAX_REQUEST_ID_BYTES), fixed(2, WireType.SHA256),
        fixed(16, WireType.ID128), fixed(17, WireType.U8)));
    result.put(MessageType.CLOSE_RESPONSE, responseRules(
        fixed(16, WireType.U64_BE), fixed(17, WireType.SHA256),
        fixed(18, WireType.U8)));
    result.put(MessageType.HEALTH_REQUEST, simpleRuntimeRequest());
    result.put(MessageType.HEALTH_RESPONSE, responseRules(
        fixed(16, WireType.U8), fixed(17, WireType.U64_BE),
        fixed(18, WireType.U64_BE), fixed(19, WireType.U32_BE),
        fixed(20, WireType.U8), fixed(21, WireType.U8)));
    result.put(MessageType.SHARED_MEMORY_ACK, List.of(
        bytesRule(1, MAX_REQUEST_ID_BYTES), fixed(2, WireType.SHA256),
        fixed(16, WireType.SHM_REFERENCE_64), fixed(17, WireType.U8)));
    result.put(MessageType.ERROR_RESPONSE, responseRules(
        fixed(16, WireType.U32_BE), fixed(17, WireType.U16_BE),
        fixed(18, WireType.U64_BE), textRule(19, MAX_ERROR_DETAIL_BYTES)));
    return Collections.unmodifiableMap(result);
  }

  private static List<FieldRule> simpleRuntimeRequest() {
    return List.of(
        bytesRule(1, MAX_REQUEST_ID_BYTES),
        fixed(2, WireType.SHA256),
        fixed(16, WireType.ID128));
  }

  private static List<FieldRule> responseRules(FieldRule... operationFields) {
    var result = new ArrayList<FieldRule>(operationFields.length + 5);
    result.add(bytesRule(1, MAX_REQUEST_ID_BYTES));
    result.add(fixed(2, WireType.SHA256));
    result.add(fixed(3, WireType.U8));
    result.add(fixed(4, WireType.U64_BE));
    result.add(fixed(5, WireType.U32_BE));
    result.addAll(Arrays.asList(operationFields));
    return List.copyOf(result);
  }

  private static FieldRule fixed(int id, WireType type) {
    return new FieldRule(id, type, type.exactLength);
  }

  private static FieldRule bytesRule(int id, int maximum) {
    return new FieldRule(id, WireType.BYTES, maximum);
  }

  private static FieldRule textRule(int id, int maximum) {
    return new FieldRule(id, WireType.CANONICAL_UTF8, maximum);
  }

  private static int inlineFlags(MessageType type, boolean ignored) {
    return inlineFlags(type);
  }

  private static void validateInlineFlags(MessageType type, int flags) {
    require((flags & ~KNOWN_FLAGS) == 0, "unknown frame flag bit");
    require((flags & FLAG_PAYLOAD_SHARED_MEMORY) == 0,
        "shared-memory carrier is disabled in bounded-copy implementation");
    require(flags == inlineFlags(type, true), "opcode flag set violates frozen table");
  }

  private static byte[] encodeCanonicalUtf8(String value, int maximum, String label) {
    Objects.requireNonNull(value, label);
    require(value.indexOf('\0') < 0, label + " contains NUL");
    require(Normalizer.isNormalized(value, Normalizer.Form.NFC), label + " is not NFC");
    try {
      var output = StandardCharsets.UTF_8.newEncoder()
          .onMalformedInput(CodingErrorAction.REPORT)
          .onUnmappableCharacter(CodingErrorAction.REPORT)
          .encode(java.nio.CharBuffer.wrap(value));
      var bytes = new byte[output.remaining()];
      output.get(bytes);
      require(bytes.length <= maximum, label + " exceeds UTF-8 bound");
      return bytes;
    } catch (CharacterCodingException error) {
      throw invalid(label + " is not canonical UTF-8", error);
    }
  }

  private static String decodeCanonicalUtf8(byte[] value, int maximum, String label) {
    require(value.length <= maximum, label + " exceeds UTF-8 bound");
    try {
      var text = StandardCharsets.UTF_8.newDecoder()
          .onMalformedInput(CodingErrorAction.REPORT)
          .onUnmappableCharacter(CodingErrorAction.REPORT)
          .decode(ByteBuffer.wrap(value))
          .toString();
      require(text.indexOf('\0') < 0, label + " contains NUL");
      require(Normalizer.isNormalized(text, Normalizer.Form.NFC), label + " is not NFC");
      require(Arrays.equals(value, text.getBytes(StandardCharsets.UTF_8)),
          label + " is not minimally encoded UTF-8");
      return text;
    } catch (CharacterCodingException error) {
      throw invalid(label + " is not canonical UTF-8", error);
    }
  }

  private static void validateIdentityText(String value, String label) {
    var bytes = encodeCanonicalUtf8(value, MAX_IDENTITY_TEXT_BYTES, label);
    require(bytes.length > 0, label + " is empty");
  }

  private static byte[] digest(byte[] value, String label) {
    Objects.requireNonNull(value, label);
    require(value.length == 32, label + " must contain exactly 32 bytes");
    return Arrays.copyOf(value, value.length);
  }

  private static void requireDigestIdentity(byte[] actual, String expected, String label) {
    var bytes = HexFormat.of().parseHex(expected.substring(7));
    require(Arrays.equals(actual, bytes), label + " digest identity mismatch");
  }

  private static boolean allZero(byte[] value) {
    var aggregate = 0;
    for (var item : value) {
      aggregate |= item;
    }
    return aggregate == 0;
  }

  private static int u8Value(Field value) {
    return Byte.toUnsignedInt(value.value[0]);
  }

  private static int u16Value(Field value) {
    return Short.toUnsignedInt(ByteBuffer.wrap(value.value).order(ByteOrder.BIG_ENDIAN).getShort());
  }

  private static long u32Value(Field value) {
    return Integer.toUnsignedLong(ByteBuffer.wrap(value.value).order(ByteOrder.BIG_ENDIAN).getInt());
  }

  private static long u64Value(Field value) {
    return ByteBuffer.wrap(value.value).order(ByteOrder.BIG_ENDIAN).getLong();
  }

  private static String textValue(Field value) {
    return decodeCanonicalUtf8(value.value, Integer.MAX_VALUE, "text field");
  }

  private static void requireBoolean(Field field, String label) {
    requireRange(u8Value(field), 0, 1, label);
  }

  private static void requireRange(long value, long minimum, long maximum, String label) {
    require(value >= minimum && value <= maximum, label + " is outside enum range");
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw invalid(message);
    }
  }

  private static ProtocolException invalid(String message) {
    return new ProtocolException(message);
  }

  private static ProtocolException invalid(String message, Throwable cause) {
    return new ProtocolException(message, cause);
  }

  private record FieldRule(int id, WireType type, int maximumLength) {}

  /** Fail-closed codec violation. */
  public static final class ProtocolException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;

    public ProtocolException(String message) {
      super(message);
    }

    public ProtocolException(String message, Throwable cause) {
      super(message, cause);
    }
  }
}
