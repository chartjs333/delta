package io.deltareduce.node.sidecar;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;

/** Self-contained mutation and canonical-byte conformance for sidecar IPC v1. */
public final class SidecarIpcConformance {
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";

  private SidecarIpcConformance() {}

  public static void main(String[] arguments) {
    require(arguments.length == 0, "SidecarIpcConformance takes no arguments");
    var nested = nestedDescriptor();
    var identity = new SidecarIpcV1.DescriptorIdentity(
        id(1), 7, digest(0x42), BUILD_ID, nested);
    var helloPayload = SidecarIpcV1.descriptorPayload(
        SidecarIpcV1.MessageType.CLIENT_HELLO, identity);
    var hello = SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.CLIENT_HELLO,
        identity.sessionId(),
        identity.generation(),
        id(2),
        1,
        helloPayload);
    var canonical = hello.canonicalBytes();
    require(canonical.length == SidecarIpcV1.HEADER_BYTES + helloPayload.canonicalBytes().length,
        "frame length is not header plus logical payload");
    require(new String(canonical, 0, 8, StandardCharsets.US_ASCII).equals("DELTAIPC"),
        "frame magic bytes changed");
    var header = ByteBuffer.wrap(canonical).order(ByteOrder.BIG_ENDIAN);
    require(Short.toUnsignedInt(header.getShort(8)) == 1
            && Short.toUnsignedInt(header.getShort(10)) == 0
            && Short.toUnsignedInt(header.getShort(12)) == 128
            && Short.toUnsignedInt(header.getShort(14)) == 1,
        "frame version/header/opcode offsets changed");
    require(header.getLong(68) == helloPayload.canonicalBytes().length
            && header.getLong(76) == SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES,
        "frame length/capacity offsets changed");
    var decoded = SidecarIpcV1.decodeFrame(canonical);
    require(Arrays.equals(decoded.canonicalBytes(), canonical), "frame round trip changed bytes");
    SidecarIpcV1.requireDescriptor(decoded.payload(), identity);
    var unsignedMaximum = SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.CLIENT_HELLO,
        identity.sessionId(),
        identity.generation(),
        id(3),
        -1L,
        helloPayload);
    require(SidecarIpcV1.decodeFrame(unsignedMaximum.canonicalBytes()).sequence() == -1L,
        "unsigned-max transport sequence was rejected");

    testFrameMutations(canonical);
    testPayloadMutations(identity);
    testNestedDescriptorMutations(nested);
    testRequestDigestAndAdmission();
    testErrorResponseBinding();
    testSharedMemoryDisabled();
    testBounds();
    System.out.println(
        "sidecar IPC v1 compatible on JDK "
            + Runtime.version().feature()
            + ": exact frame/TLV/descriptor/digest/bounds mutations, SHM disabled");
  }

  private static void testFrameMutations(byte[] canonical) {
    expectProtocol(() -> SidecarIpcV1.decodeFrame(Arrays.copyOf(canonical, 127)), "truncated header");
    expectProtocol(
        () -> SidecarIpcV1.decodeFrame(Arrays.copyOf(canonical, canonical.length - 1)),
        "truncated payload");
    expectProtocol(
        () -> SidecarIpcV1.decodeFrame(Arrays.copyOf(canonical, canonical.length + 1)),
        "trailing byte");
    mutateFrame(canonical, 0, (byte) 'X', "bad magic");
    mutateFrame(canonical, 9, (byte) 2, "bad major");
    mutateFrame(canonical, 11, (byte) 1, "bad minor");
    mutateFrame(canonical, 13, (byte) 127, "bad header length");
    mutateFrame(canonical, 15, (byte) 0x7f, "unknown opcode");
    var flags = Arrays.copyOf(canonical, canonical.length);
    ByteBuffer.wrap(flags).order(ByteOrder.BIG_ENDIAN).putInt(16, 0x15);
    expectProtocol(() -> SidecarIpcV1.decodeFrame(flags), "unknown flags");
    mutateFrame(canonical, 67, (byte) 0, "zero sequence");
    var length = Arrays.copyOf(canonical, canonical.length);
    ByteBuffer.wrap(length).order(ByteOrder.BIG_ENDIAN).putLong(68, Long.MAX_VALUE);
    expectProtocol(() -> SidecarIpcV1.decodeFrame(length), "oversize length");
    var capacity = Arrays.copyOf(canonical, canonical.length);
    ByteBuffer.wrap(capacity).order(ByteOrder.BIG_ENDIAN).putLong(76, 0);
    expectProtocol(() -> SidecarIpcV1.decodeFrame(capacity), "wrong response capacity");
    mutateFrame(canonical, 84, (byte) (canonical[84] ^ 1), "bad payload digest");
    mutateFrame(canonical, 116, (byte) 1, "nonzero reserved byte");
  }

  private static void testPayloadMutations(SidecarIpcV1.DescriptorIdentity identity) {
    var payload = SidecarIpcV1.descriptorPayload(
        SidecarIpcV1.MessageType.SERVER_DESCRIPTOR, identity).canonicalBytes();
    mutatePayload(payload, 1, (byte) 3, "schema type mismatch");
    mutatePayload(payload, 3, (byte) 2, "schema major mismatch");
    mutatePayload(payload, 5, (byte) 1, "schema minor mismatch");
    mutatePayload(payload, 7, (byte) 1, "schema reserved byte");
    var declared = Arrays.copyOf(payload, payload.length);
    ByteBuffer.wrap(declared).order(ByteOrder.BIG_ENDIAN).putLong(8, payload.length);
    expectProtocol(
        () -> SidecarIpcV1.decodePayload(
            SidecarIpcV1.MessageType.SERVER_DESCRIPTOR, declared),
        "payload value length mismatch");
    mutatePayload(payload, 17, (byte) 2, "out-of-order first field");
    mutatePayload(payload, 18, (byte) 0xff, "unknown wire type");
    mutatePayload(payload, 19, (byte) 1, "nonzero TLV flags");
    var invalidUtf8 = Arrays.copyOf(payload, payload.length);
    invalidUtf8[24] = (byte) 0xc0;
    expectProtocol(
        () -> SidecarIpcV1.decodePayload(
            SidecarIpcV1.MessageType.SERVER_DESCRIPTOR, invalidUtf8),
        "invalid UTF-8");
    expectProtocol(() -> SidecarIpcV1.text(1, "e\u0301"), "non-NFC text");
    expectProtocol(() -> SidecarIpcV1.text(1, "a\0b"), "NUL text");
  }

  private static void testNestedDescriptorMutations(byte[] nested) {
    var parsed = SidecarIpcV1.parseNestedDescriptor(nested);
    require(parsed.structSize() == 64 && parsed.abiMajor() == 1 && parsed.featureBits() == 7,
        "nested ABI numeric fields changed");
    require(parsed.formalSemanticsId().equals(FORMAL_SEMANTICS_ID)
            && parsed.runtimeProfile().equals("embedded-ffm"),
        "nested ABI text fields changed");
    var magic = Arrays.copyOf(nested, nested.length);
    magic[0] = 'X';
    expectProtocol(() -> SidecarIpcV1.parseNestedDescriptor(magic), "nested magic");
    var length = Arrays.copyOf(nested, nested.length);
    ByteBuffer.wrap(length).order(ByteOrder.BIG_ENDIAN).putInt(8, nested.length + 1);
    expectProtocol(() -> SidecarIpcV1.parseNestedDescriptor(length), "nested length");
    expectProtocol(
        () -> SidecarIpcV1.parseNestedDescriptor(Arrays.copyOf(nested, nested.length + 1)),
        "nested trailing byte");
  }

  private static void testRequestDigestAndAdmission() {
    var request = SidecarIpcV1.requestPayload(
        SidecarIpcV1.MessageType.SUBMIT_REQUEST,
        "request-1".getBytes(StandardCharsets.US_ASCII),
        List.of(SidecarIpcV1.bytes(16, new byte[] {1, 2, 3})));
    SidecarIpcV1.requireRequestDigest(request);
    var changed = request.canonicalBytes();
    changed[changed.length - 1] ^= 1;
    expectProtocol(
        () -> SidecarIpcV1.decodePayload(SidecarIpcV1.MessageType.SUBMIT_REQUEST, changed),
        "changed body with old digest");

    var sentinel = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        new byte[0],
        SidecarIpcV1.emptySha256(),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()),
            SidecarIpcV1.u64(4, 0),
            SidecarIpcV1.u32(5, SidecarIpcV1.NATIVE_STATUS_UNAVAILABLE),
            SidecarIpcV1.u32(16, SidecarIpcV1.LocalError.FRAME_INVALID.code()),
            SidecarIpcV1.u16(17, SidecarIpcV1.MessageType.SUBMIT_REQUEST.code()),
            SidecarIpcV1.u64(18, SidecarIpcV1.MAX_LOGICAL_PAYLOAD_BYTES),
            SidecarIpcV1.text(19, "safe preparse rejection")));
    require(sentinel.bytes(1).length == 0, "safe preparse sentinel request ID is not empty");
    expectProtocol(
        () -> SidecarIpcV1.responsePayload(
            SidecarIpcV1.MessageType.ERROR_RESPONSE,
            new byte[0],
            SidecarIpcV1.emptySha256(),
            List.of(
                SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()),
                SidecarIpcV1.u64(4, 1),
                SidecarIpcV1.u32(5, 0),
                SidecarIpcV1.u32(16, 1),
                SidecarIpcV1.u16(17, SidecarIpcV1.MessageType.SUBMIT_REQUEST.code()),
                SidecarIpcV1.u64(18, 0),
                SidecarIpcV1.text(19, "invalid"))),
        "incoherent admission fields");
  }

  private static void testSharedMemoryDisabled() {
    var request = SidecarIpcV1.requestPayload(
        SidecarIpcV1.MessageType.SUBMIT_REQUEST,
        "shm-disabled".getBytes(StandardCharsets.US_ASCII),
        List.of(SidecarIpcV1.bytes(16, new byte[] {9})));
    var frame = SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.SUBMIT_REQUEST, id(8), 9, id(9), 1, request).canonicalBytes();
    var shared = Arrays.copyOf(frame, frame.length);
    ByteBuffer.wrap(shared).order(ByteOrder.BIG_ENDIAN).putInt(
        16,
        SidecarIpcV1.FLAG_PAYLOAD_SHARED_MEMORY | SidecarIpcV1.FLAG_RESPONSE_EXPECTED);
    expectProtocol(
        () -> SidecarIpcV1.decodeFrame(shared),
        "eligible SHM carrier must be rejected while SHM is disabled");
    var copied = SidecarIpcV1.decodeFrame(frame);
    require(Arrays.equals(copied.payload().canonicalBytes(), request.canonicalBytes()),
        "bounded-copy carrier changed logical bytes");
  }

  private static void testErrorResponseBinding() {
    var session = id(10);
    var correlation = id(11);
    var request = SidecarIpcV1.requestPayload(
        SidecarIpcV1.MessageType.SUBMIT_REQUEST,
        "bound-error".getBytes(StandardCharsets.US_ASCII),
        List.of(SidecarIpcV1.bytes(16, new byte[] {1})));
    var correct = errorResponse(
        request, session, 12, correlation, SidecarIpcV1.MessageType.SUBMIT_REQUEST);
    SidecarIpcV1.requireResponseMatches(
        correct,
        SidecarIpcV1.MessageType.SUBMIT_REQUEST,
        request.bytes(1),
        request.bytes(2),
        session,
        12,
        correlation);

    var wrong = errorResponse(
        request, session, 12, correlation, SidecarIpcV1.MessageType.STATE_REQUEST);
    expectProtocol(
        () -> SidecarIpcV1.requireResponseMatches(
            wrong,
            SidecarIpcV1.MessageType.SUBMIT_REQUEST,
            request.bytes(1),
            request.bytes(2),
            session,
            12,
            correlation),
        "ERROR_RESPONSE offending message type mismatch");
  }

  private static SidecarIpcV1.Frame errorResponse(
      SidecarIpcV1.Payload request,
      SidecarIpcV1.Id128 session,
      long generation,
      SidecarIpcV1.Id128 correlation,
      SidecarIpcV1.MessageType offendingType) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.bytes(1),
        request.bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
            SidecarIpcV1.u64(4, 1),
            SidecarIpcV1.u32(5, 1),
            SidecarIpcV1.u32(16, SidecarIpcV1.LocalError.INTERNAL_TRANSPORT_ERROR.code()),
            SidecarIpcV1.u16(17, offendingType.code()),
            SidecarIpcV1.u64(18, 0),
            SidecarIpcV1.text(19, "bound error")));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        session,
        generation,
        correlation,
        1,
        payload);
  }

  private static void testBounds() {
    var maximumRequestId = new byte[SidecarIpcV1.MAX_REQUEST_ID_BYTES];
    maximumRequestId[0] = 1;
    SidecarIpcV1.requestPayload(
        SidecarIpcV1.MessageType.SUBMIT_REQUEST,
        maximumRequestId,
        List.of(SidecarIpcV1.bytes(16, new byte[] {1})));
    var tooLargeRequestId = Arrays.copyOf(maximumRequestId, maximumRequestId.length + 1);
    expectProtocol(
        () -> SidecarIpcV1.requestPayload(
            SidecarIpcV1.MessageType.SUBMIT_REQUEST,
            tooLargeRequestId,
            List.of(SidecarIpcV1.bytes(16, new byte[] {1}))),
        "request ID +1 bound");
    expectProtocol(
        () -> SidecarIpcV1.requestPayload(
            SidecarIpcV1.MessageType.SUBMIT_REQUEST,
            new byte[] {1},
            List.of(SidecarIpcV1.bytes(
                16, new byte[SidecarIpcV1.MAX_CANONICAL_COMMAND_BYTES + 1]))),
        "command +1 allocation must fail when payload is validated");
    expectProtocol(
        () -> SidecarIpcV1.nextSequence(-1L),
        "unsigned-max is valid but has no representable successor");
  }

  private static byte[] nestedDescriptor() {
    return SidecarIpcV1.encodeNestedDescriptor(
        new SidecarIpcV1.NestedDescriptor(
            64,
            1,
            0,
            7,
            "1.0.0",
            "003.1.0",
            FORMAL_SEMANTICS_ID,
            BUILD_ID,
            SCHEMA_SET_ID,
            "embedded-ffm"));
  }

  private static SidecarIpcV1.Id128 id(int value) {
    var bytes = new byte[16];
    bytes[15] = (byte) value;
    return new SidecarIpcV1.Id128(bytes);
  }

  private static byte[] digest(int value) {
    var bytes = new byte[32];
    Arrays.fill(bytes, (byte) value);
    return bytes;
  }

  private static void mutateFrame(byte[] input, int offset, byte value, String label) {
    var changed = Arrays.copyOf(input, input.length);
    changed[offset] = value;
    expectProtocol(() -> SidecarIpcV1.decodeFrame(changed), label);
  }

  private static void mutatePayload(byte[] input, int offset, byte value, String label) {
    var changed = Arrays.copyOf(input, input.length);
    changed[offset] = value;
    expectProtocol(
        () -> SidecarIpcV1.decodePayload(
            SidecarIpcV1.MessageType.SERVER_DESCRIPTOR, changed),
        label);
  }

  private static void expectProtocol(Runnable operation, String label) {
    try {
      operation.run();
    } catch (SidecarIpcV1.ProtocolException expected) {
      return;
    }
    throw new IllegalStateException("mutation was accepted: " + label);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }
}
