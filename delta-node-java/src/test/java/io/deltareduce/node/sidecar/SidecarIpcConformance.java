package io.deltareduce.node.sidecar;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Self-contained mutation and canonical-byte conformance for sidecar IPC v1.1. */
public final class SidecarIpcConformance {
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";

  private SidecarIpcConformance() {}

  public static void main(String[] arguments) throws Exception {
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
            && Short.toUnsignedInt(header.getShort(10)) == 1
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
    testVoteContract();
    testErrorResponseBinding();
    testSharedMemoryDisabled();
    testSharedMemoryCarrier();
    testBounds();
    System.out.println(
        "sidecar IPC v1.1 compatible on JDK "
            + Runtime.version().feature()
            + ": exact frame/TLV/descriptor/digest/bounds mutations and SHM carrier");
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
    mutateFrame(canonical, 11, (byte) 0, "v1.0 downgrade");
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
    require(parsed.structSize() == 64 && parsed.abiMajor() == 1
            && parsed.featureBits() == SidecarIpcV1.NESTED_ABI_FEATURE_BITS,
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

  private static void testVoteContract() {
    require(SidecarIpcV1.MessageType.VOTE_REQUEST.code() == 0x22
            && SidecarIpcV1.MessageType.VOTE_RESPONSE.code() == 0x23
            && SidecarIpcV1.MessageType.VOTE_REQUEST.expectedResponse()
                == SidecarIpcV1.MessageType.VOTE_RESPONSE
            && SidecarIpcV1.MessageType.VOTE_REQUEST.sharedMemoryEligible()
            && SidecarIpcV1.MessageType.VOTE_RESPONSE.sharedMemoryEligible(),
        "vote opcode pair or carrier eligibility changed");

    var vote = new byte[] {9, 8, 7, 6};
    var prepared = LocalSidecarClient.voteRequest(
        "vote-request".getBytes(StandardCharsets.US_ASCII), vote);
    require(prepared.type() == SidecarIpcV1.MessageType.VOTE_REQUEST,
        "vote factory produced the wrong operation");
    var request = SidecarIpcV1.decodePayload(
        SidecarIpcV1.MessageType.VOTE_REQUEST, prepared.canonicalPayload());
    require(Arrays.equals(request.bytes(16), vote), "opaque vote bytes changed");
    SidecarIpcV1.requireRequestDigest(request);
    expectIllegalArgument(
        () -> LocalSidecarClient.voteRequest(new byte[] {1}, new byte[0]),
        "empty opaque vote");

    var receipt = new byte[] {4, 5, 6};
    var response = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.VOTE_RESPONSE,
        request.bytes(1),
        request.bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
            SidecarIpcV1.u64(4, 1),
            SidecarIpcV1.u32(5, 0),
            SidecarIpcV1.bytes(16, receipt),
            SidecarIpcV1.sha256Field(17, SidecarIpcV1.sha256(receipt))));
    require(Arrays.equals(response.bytes(16), receipt), "opaque vote receipt changed");
    var changed = response.canonicalBytes();
    changed[changed.length - 41] ^= 1;
    expectProtocol(
        () -> SidecarIpcV1.decodePayload(SidecarIpcV1.MessageType.VOTE_RESPONSE, changed),
        "changed vote receipt with old digest");

    SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.ERROR_RESPONSE,
        request.bytes(1),
        request.bytes(2),
        List.of(
            SidecarIpcV1.u8(3, SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()),
            SidecarIpcV1.u64(4, 0),
            SidecarIpcV1.u32(5, 2),
            SidecarIpcV1.u32(16, SidecarIpcV1.LocalError.INTERNAL_TRANSPORT_ERROR.code()),
            SidecarIpcV1.u16(17, SidecarIpcV1.MessageType.VOTE_REQUEST.code()),
            SidecarIpcV1.u64(18, 0),
            SidecarIpcV1.text(19, "native vote admission rejected")));

    var policy = new byte[] {1, 3, 3, 7};
    var open = SidecarIpcV1.requestPayload(
        SidecarIpcV1.MessageType.OPEN_REQUEST,
        new byte[] {1},
        List.of(
            SidecarIpcV1.u32(16, SidecarIpcV1.INGRESS_QUEUE_REQUESTS),
            SidecarIpcV1.text(17, "durable"),
            SidecarIpcV1.bytes(18, new byte[] {2}),
            SidecarIpcV1.sha256Field(19, digest(0x19)),
            SidecarIpcV1.bytes(20, policy)));
    require(Arrays.equals(open.bytes(20), policy), "opaque OPEN vote policy changed");
    SidecarIpcV1.requireRequestDigest(open);
    expectProtocol(
        () -> SidecarIpcV1.requestPayload(
            SidecarIpcV1.MessageType.OPEN_REQUEST,
            new byte[] {1},
            List.of(
                SidecarIpcV1.u32(16, SidecarIpcV1.INGRESS_QUEUE_REQUESTS),
                SidecarIpcV1.text(17, "durable"),
                SidecarIpcV1.bytes(18, new byte[] {2}),
                SidecarIpcV1.sha256Field(19, digest(0x19)),
                SidecarIpcV1.bytes(20, new byte[0]))),
        "present empty vote policy");
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

  private static void testSharedMemoryCarrier() throws Exception {
    if (!SidecarSharedMemory.atomicAbiSupported()) {
      return;
    }
    try (var resources = SidecarSharedMemory.GenerationResources.create(19)) {
      var request = SidecarIpcV1.requestPayload(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          "shm-carrier".getBytes(StandardCharsets.US_ASCII),
          List.of(SidecarIpcV1.bytes(16, new byte[] {7, 8, 9})));
      var inline = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST, id(12), 19, id(13), 1, request)
          .canonicalBytes();
      var carrier = SidecarSharedMemory.makeCarrier(
          inline, resources.javaToNative(), null).orElseThrow();
      require(carrier.length == SidecarIpcV1.HEADER_BYTES + 64,
          "shared-memory control carrier has wrong size");
      require(Arrays.equals(
              resources.javaToNative().rawStateBytes(0), new byte[] {0, 0, 0, 2}),
          "published Java atomic state is not raw big-endian U32");

      var staleReference = Arrays.copyOf(carrier, carrier.length);
      ByteBuffer.wrap(staleReference).order(ByteOrder.BIG_ENDIAN)
          .putLong(SidecarIpcV1.HEADER_BYTES + 8, 20);
      expectProtocol(
          () -> SidecarSharedMemory.resolveCarrier(staleReference, resources.javaToNative()),
          "stale shared-memory reference generation");
      var wrongHeaderGeneration = Arrays.copyOf(carrier, carrier.length);
      ByteBuffer.wrap(wrongHeaderGeneration).order(ByteOrder.BIG_ENDIAN).putLong(36, 20);
      expectProtocol(
          () -> SidecarSharedMemory.resolveCarrier(
              wrongHeaderGeneration, resources.javaToNative()),
          "shared-memory header/reference generation mismatch");
      expectProtocol(
          () -> SidecarSharedMemory.resolveCarrier(carrier, resources.nativeToJava()),
          "wrong shared-memory direction");

      var reconstructed = SidecarSharedMemory.resolveCarrier(
          carrier, resources.javaToNative());
      require(Arrays.equals(reconstructed, inline),
          "shared-memory resolution is not byte-identical to inline framing");
      require(Arrays.equals(
              resources.javaToNative().rawStateBytes(0), new byte[] {0, 0, 0, 4}),
          "acknowledged Java atomic state is not raw big-endian U32");

      var delegate = new RecordingTransport();
      var transport = new SidecarSharedMemory.Transport(
          delegate, resources.javaToNative(), resources.nativeToJava());
      var staleNotifications = new ArrayList<SidecarIpcV1.Frame>();
      byte[] referenceBytes = null;
      SidecarSharedMemory.Reference reference = null;
      for (var correlationSeed = 13; correlationSeed <= 20; ++correlationSeed) {
        var trackedInline = SidecarIpcV1.frame(
            SidecarIpcV1.MessageType.SUBMIT_REQUEST,
            id(12),
            19,
            id(correlationSeed),
            correlationSeed - 12L,
            request).canonicalBytes();
        transport.write(trackedInline);
        var publishedCarrier = delegate.written();
        var publishedReferenceBytes = SidecarSharedMemory.referenceBytes(publishedCarrier);
        if (referenceBytes == null) {
          referenceBytes = publishedReferenceBytes;
        } else {
          require(Arrays.equals(referenceBytes, publishedReferenceBytes),
              "byte-identical shared-memory publication did not reuse the exact reference");
        }
        reference = SidecarSharedMemory.Reference.decode(publishedReferenceBytes);
        require(Arrays.equals(
                SidecarSharedMemory.resolveCarrier(
                    publishedCarrier, resources.javaToNative()),
                trackedInline),
            "tracked shared-memory publication changed canonical bytes");
        var notification = sharedMemoryAck(
            request,
            publishedReferenceBytes,
            id(12),
            id(correlationSeed),
            SidecarIpcV1.SharedMemoryDisposition.ACKED);
        if (correlationSeed < 20) {
          staleNotifications.add(notification);
        }
      }
      require(referenceBytes != null && reference != null,
          "tracked shared-memory publication was not created");
      require(resources.javaToNative().classifyTerminalNotification(
                  reference, SidecarIpcV1.SharedMemoryDisposition.ACKED)
                  == SidecarSharedMemory.Region.NotificationMatch.MATCHED
              && resources.javaToNative().classifyTerminalNotification(
                  reference, SidecarIpcV1.SharedMemoryDisposition.REJECTED_DIGEST)
                  == SidecarSharedMemory.Region.NotificationMatch.MISMATCH,
          "terminal ACK disposition did not match control state");
      var rejectedDisposition = sharedMemoryAck(
          request,
          referenceBytes,
          id(12),
          id(20),
          SidecarIpcV1.SharedMemoryDisposition.REJECTED_DIGEST);
      require(!transport.acceptSharedMemoryAck(rejectedDisposition),
          "ACK accepted a disposition that differed from terminal state");
      for (var staleNotification : staleNotifications) {
        require(transport.acceptSharedMemoryAck(staleNotification),
            "delayed stale ACK gained authority after repeated exact-reference reuse");
      }
      var wrongOwner = SidecarIpcV1.requestPayload(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          "wrong-shm-owner".getBytes(StandardCharsets.US_ASCII),
          List.of(SidecarIpcV1.bytes(16, new byte[] {7, 8, 9})));
      var wrongCurrentOwner = sharedMemoryAck(
          wrongOwner,
          referenceBytes,
          id(12),
          id(20),
          SidecarIpcV1.SharedMemoryDisposition.ACKED);
      expectProtocol(
          () -> transport.acceptSharedMemoryAck(wrongCurrentOwner),
          "ACK with current correlation but wrong request owner");
      var notification = sharedMemoryAck(
          request,
          referenceBytes,
          id(12),
          id(20),
          SidecarIpcV1.SharedMemoryDisposition.ACKED);
      require(transport.acceptSharedMemoryAck(notification)
              && transport.acceptSharedMemoryAck(notification),
          "matching or duplicate ACK did not stutter successfully");
      require(!transport.acceptSharedMemoryAck(rejectedDisposition),
          "already-notified current publication accepted a mismatched disposition");

      // Fill two slots, let both consumers finish without delivering either
      // notification, then publish again. The producer reclaims both terminal
      // records but overwrites only one publication entry. A delayed ACK for
      // the other reclaimed slot must still be a stutter.
      var concurrentA = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          id(12),
          19,
          id(21),
          21,
          request).canonicalBytes();
      transport.write(concurrentA);
      var carrierA = delegate.written();
      var concurrentB = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          id(12),
          19,
          id(22),
          22,
          request).canonicalBytes();
      transport.write(concurrentB);
      var carrierB = delegate.written();
      var referenceB = SidecarSharedMemory.referenceBytes(carrierB);
      require(Arrays.equals(
              SidecarSharedMemory.resolveCarrier(carrierA, resources.javaToNative()),
              concurrentA)
              && Arrays.equals(
                  SidecarSharedMemory.resolveCarrier(carrierB, resources.javaToNative()),
                  concurrentB),
          "concurrent shared-memory publications changed canonical bytes");
      var replacement = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          id(12),
          19,
          id(23),
          23,
          request).canonicalBytes();
      transport.write(replacement);
      var replacementCarrier = delegate.written();
      require(transport.acceptSharedMemoryAck(sharedMemoryAck(
              request,
              referenceB,
              id(12),
              id(22),
              SidecarIpcV1.SharedMemoryDisposition.ACKED)),
          "delayed ACK for a reclaimed non-overwritten slot did not stutter");
      require(Arrays.equals(
              SidecarSharedMemory.resolveCarrier(
                  replacementCarrier, resources.javaToNative()),
              replacement),
          "replacement shared-memory publication changed canonical bytes");

      try {
        SidecarSharedMemory.makeCarrier(
            inline,
            resources.javaToNative(),
            () -> { throw new IllegalStateException("publication hook"); });
        throw new IllegalStateException("publication hook did not interrupt publication");
      } catch (IllegalStateException expected) {
        require(expected.getMessage().equals("publication hook"),
            "unexpected shared-memory publication failure");
      }
      require(resources.javaToNative().rawState(0) == SidecarSharedMemory.REJECTED,
          "failed publication stranded a WRITING slot");

      var first = SidecarSharedMemory.makeCarrier(
          inline, resources.javaToNative(), null).orElseThrow();
      var secondInline = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST, id(12), 19, id(14), 2, request)
          .canonicalBytes();
      var second = SidecarSharedMemory.makeCarrier(
          secondInline, resources.javaToNative(), null).orElseThrow();
      var firstReference = SidecarSharedMemory.Reference.decode(
          Arrays.copyOfRange(first, SidecarIpcV1.HEADER_BYTES, first.length));
      var secondReference = SidecarSharedMemory.Reference.decode(
          Arrays.copyOfRange(second, SidecarIpcV1.HEADER_BYTES, second.length));
      require(firstReference.offset() + firstReference.length() <= secondReference.offset()
              || secondReference.offset() + secondReference.length() <= firstReference.offset(),
          "live shared-memory payload ranges overlap");
      require(Arrays.equals(
              SidecarSharedMemory.resolveCarrier(first, resources.javaToNative()), inline)
              && Arrays.equals(
                  SidecarSharedMemory.resolveCarrier(second, resources.javaToNative()),
                  secondInline),
          "multiple live shared-memory slots changed canonical bytes");

      var preparedVote = LocalSidecarClient.voteRequest(
          "shm-vote-request".getBytes(StandardCharsets.US_ASCII),
          new byte[] {9, 8, 7, 6});
      var voteRequestPayload = SidecarIpcV1.decodePayload(
          SidecarIpcV1.MessageType.VOTE_REQUEST, preparedVote.canonicalPayload());
      var voteRequestInline = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.VOTE_REQUEST,
          id(12),
          19,
          id(15),
          3,
          voteRequestPayload).canonicalBytes();
      var voteRequestCarrier = SidecarSharedMemory.makeCarrier(
          voteRequestInline, resources.javaToNative(), null).orElseThrow();
      require(Arrays.equals(
              SidecarSharedMemory.resolveCarrier(
                  voteRequestCarrier, resources.javaToNative()),
              voteRequestInline),
          "opaque VOTE_REQUEST changed across the shared-memory carrier");

      var voteReceipt = new byte[] {4, 5, 6, 7};
      var voteResponsePayload = SidecarIpcV1.responsePayload(
          SidecarIpcV1.MessageType.VOTE_RESPONSE,
          voteRequestPayload.bytes(1),
          voteRequestPayload.bytes(2),
          List.of(
              SidecarIpcV1.u8(
                  3, SidecarIpcV1.AdmissionState.ADMITTED_OUTCOME_AVAILABLE.code()),
              SidecarIpcV1.u64(4, 1),
              SidecarIpcV1.u32(5, 0),
              SidecarIpcV1.bytes(16, voteReceipt),
              SidecarIpcV1.sha256Field(17, SidecarIpcV1.sha256(voteReceipt))));
      var voteResponseInline = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.VOTE_RESPONSE,
          id(12),
          19,
          id(15),
          1,
          voteResponsePayload).canonicalBytes();
      var voteResponseCarrier = SidecarSharedMemory.makeCarrier(
          voteResponseInline, resources.nativeToJava(), null).orElseThrow();
      require(Arrays.equals(
              SidecarSharedMemory.resolveCarrier(
                  voteResponseCarrier, resources.nativeToJava()),
              voteResponseInline),
          "opaque VOTE_RESPONSE changed across the shared-memory carrier");
    }

    var writingPeerRoot = Files.createTempDirectory("delta-sidecar-shm-writing-peer-");
    var writingPeerPath = writingPeerRoot.resolve("region");
    createSparseRegion(writingPeerPath);
    var writingPeerIdentity = SidecarSharedMemory.fileIdentity(writingPeerPath);
    try (var producer = SidecarSharedMemory.Region.open(
             writingPeerPath,
             SidecarSharedMemory.JAVA_TO_NATIVE,
             43,
             writingPeerIdentity);
         var consumer = SidecarSharedMemory.Region.open(
             writingPeerPath,
             SidecarSharedMemory.JAVA_TO_NATIVE,
             43,
             writingPeerIdentity)) {
      var request = SidecarIpcV1.requestPayload(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST,
          "writing-peer".getBytes(StandardCharsets.US_ASCII),
          List.of(SidecarIpcV1.bytes(16, new byte[] {1, 2, 3})));
      var inline = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.SUBMIT_REQUEST, id(12), 43, id(13), 1, request)
          .canonicalBytes();
      var carrier = SidecarSharedMemory.makeCarrier(inline, producer, null).orElseThrow();
      // Slot one is paused after FREE -> WRITING with no valid metadata.
      writeControlRecord(
          writingPeerPath,
          SidecarSharedMemory.WRITING,
          SidecarSharedMemory.JAVA_TO_NATIVE,
          43,
          1,
          0,
          0);
      require(Arrays.equals(SidecarSharedMemory.resolveCarrier(carrier, consumer), inline),
          "consumer read metadata from an unrelated WRITING slot");
    }

    var overlapRoot = Files.createTempDirectory("delta-sidecar-shm-overlap-");
    var overlapPath = overlapRoot.resolve("region");
    createSparseRegion(overlapPath);
    try (var producer = SidecarSharedMemory.Region.open(
        overlapPath,
        SidecarSharedMemory.JAVA_TO_NATIVE,
        47,
        SidecarSharedMemory.fileIdentity(overlapPath))) {
      writeControlRecord(
          overlapPath,
          SidecarSharedMemory.PUBLISHED,
          SidecarSharedMemory.JAVA_TO_NATIVE,
          47,
          0,
          SidecarSharedMemory.CONTROL_PREFIX_BYTES,
          256);
      writeControlRecord(
          overlapPath,
          SidecarSharedMemory.PUBLISHED,
          SidecarSharedMemory.JAVA_TO_NATIVE,
          47,
          1,
          SidecarSharedMemory.CONTROL_PREFIX_BYTES + 64L,
          64);
      expectProtocol(
          () -> producer.publish(new byte[] {1}, null),
          "nested live shared-memory ranges");
    }

    var root = Files.createTempDirectory("delta-sidecar-shm-rebind-");
    var path = root.resolve("region");
    createSparseRegion(path);
    var expectedIdentity = SidecarSharedMemory.fileIdentity(path);
    Files.move(path, root.resolve("original"));
    createSparseRegion(path);
    try {
      SidecarSharedMemory.Region.open(
          path, SidecarSharedMemory.JAVA_TO_NATIVE, 19, expectedIdentity);
      throw new IllegalStateException("replacement shared-memory inode was accepted");
    } catch (java.io.IOException expected) {
      // Expected pinned-identity failure.
    }

    var stale = root.resolve("stale");
    createSparseRegion(stale);
    try (var channel = FileChannel.open(stale, StandardOpenOption.WRITE)) {
      channel.position(31L * SidecarSharedMemory.CONTROL_RECORD_BYTES + 3L);
      channel.write(ByteBuffer.wrap(new byte[] {2}));
    }
    try {
      SidecarSharedMemory.Region.open(
          stale,
          SidecarSharedMemory.JAVA_TO_NATIVE,
          19,
          SidecarSharedMemory.fileIdentity(stale));
      throw new IllegalStateException("nonzero later shared-memory slot was accepted");
    } catch (java.io.IOException expected) {
      // Expected fresh-prefix failure.
    }
  }

  private static void createSparseRegion(java.nio.file.Path path) throws java.io.IOException {
    try (var channel = FileChannel.open(
        path,
        StandardOpenOption.CREATE_NEW,
        StandardOpenOption.READ,
        StandardOpenOption.WRITE)) {
      channel.position(SidecarSharedMemory.REGION_BYTES - 1);
      channel.write(ByteBuffer.wrap(new byte[] {0}));
    }
  }

  private static void writeControlRecord(
      Path path,
      int state,
      int region,
      long generation,
      int slot,
      long offset,
      long length) throws IOException {
    var record = ByteBuffer.allocate(SidecarSharedMemory.CONTROL_RECORD_BYTES)
        .order(ByteOrder.BIG_ENDIAN);
    record.putInt(state);
    record.putInt(region);
    record.putLong(generation);
    record.putInt(slot);
    record.putInt(0);
    record.putLong(offset);
    record.putLong(length);
    record.position(0);
    try (var channel = FileChannel.open(path, StandardOpenOption.WRITE)) {
      channel.position(Math.multiplyExact((long) slot, SidecarSharedMemory.CONTROL_RECORD_BYTES));
      while (record.hasRemaining()) {
        channel.write(record);
      }
      channel.force(true);
    }
  }

  private static SidecarIpcV1.Frame sharedMemoryAck(
      SidecarIpcV1.Payload request,
      byte[] reference,
      SidecarIpcV1.Id128 session,
      SidecarIpcV1.Id128 correlation,
      SidecarIpcV1.SharedMemoryDisposition disposition) {
    var payload = SidecarIpcV1.responsePayload(
        SidecarIpcV1.MessageType.SHARED_MEMORY_ACK,
        request.bytes(1),
        request.bytes(2),
        List.of(
            SidecarIpcV1.sharedMemoryReference(16, reference),
            SidecarIpcV1.u8(17, disposition.code())));
    return SidecarIpcV1.frame(
        SidecarIpcV1.MessageType.SHARED_MEMORY_ACK,
        session,
        19,
        correlation,
        2,
        payload);
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
            SidecarIpcV1.NESTED_ABI_FEATURE_BITS,
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

  private static void expectIllegalArgument(Runnable operation, String label) {
    try {
      operation.run();
    } catch (IllegalArgumentException expected) {
      return;
    }
    throw new IllegalStateException("invalid argument was accepted: " + label);
  }

  private static final class RecordingTransport implements LocalSidecarClient.Transport {
    private byte[] written;
    private boolean open = true;

    @Override
    public void write(byte[] canonicalFrame) {
      written = Arrays.copyOf(canonicalFrame, canonicalFrame.length);
    }

    private byte[] written() {
      require(written != null, "transport did not record a frame");
      return Arrays.copyOf(written, written.length);
    }

    @Override
    public byte[] read() {
      throw new IllegalStateException("recording transport is write-only");
    }

    @Override
    public boolean isOpen() {
      return open;
    }

    @Override
    public void close() {
      open = false;
    }
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }
}
