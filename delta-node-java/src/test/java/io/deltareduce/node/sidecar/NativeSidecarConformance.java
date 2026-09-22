package io.deltareduce.node.sidecar;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

/** Real-process bounded-copy conformance for the isolated native sidecar. */
public final class NativeSidecarConformance {
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";

  private NativeSidecarConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(
        arguments.length == 3,
        "usage: NativeSidecarConformance <sidecar-executable> <golden-fixture> <durable-directory>");
    var executable = Path.of(arguments[0]).toAbsolutePath();
    var fixture = Files.readString(Path.of(arguments[1]), StandardCharsets.US_ASCII);
    var durableDirectory = Path.of(arguments[2]).toAbsolutePath();
    Files.createDirectories(durableDirectory);
    var initialState = golden(fixture, 5);
    var command = golden(fixture, 6);
    var nestedDescriptor = SidecarIpcV1.encodeNestedDescriptor(
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
    var executableSha = SidecarSupervisor.PipeProcessConnector.executableSha256(executable);
    // The IPC request ID is the exact canonical Command.request_id from golden type 6.
    var exactSubmit = LocalSidecarClient.submitRequest(ascii("request-001"), command);
    byte[] firstSubmitRecoveryProof;
    long firstAdmissionSequence;
    long durableSequence;
    byte[] effectIdentity;

    var firstIdentity = identity(
        "00112233445566778899aabbccddeeff", 1, executableSha, nestedDescriptor);
    try (var first = startPeer(executable, firstIdentity)) {
      first.handshake();
      var firstRuntimeId = first.open(durableDirectory, initialState);
      var mismatch = first.operationAllowError(
          LocalSidecarClient.submitRequest(ascii("wrong-command-request-id"), command));
      require(mismatch.messageType() == SidecarIpcV1.MessageType.ERROR_RESPONSE
              && mismatch.payload().u8(3)
                  == SidecarIpcV1.AdmissionState.NOT_ADMITTED_PROVEN.code()
              && mismatch.payload().u64Bits(4) == 0
              && mismatch.payload().u32(5) == SidecarIpcV1.NATIVE_STATUS_UNAVAILABLE
              && mismatch.payload().text(19).contains("request ID"),
          "native sidecar did not fail closed on IPC/Command request-ID mismatch");
      var admittedState = first.operation(
          LocalSidecarClient.stateRequest(requestId("state-before-submit"), firstRuntimeId));
      require(admittedState.messageType() == SidecarIpcV1.MessageType.STATE_RESPONSE,
          "admitted STATE before first SUBMIT failed");
      var submit = first.operation(exactSubmit);
      require(submit.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
          "SUBMIT did not return SUBMIT_RESPONSE");
      require(submit.payload().u32(5) == 0, "SUBMIT returned a native failure");
      firstSubmitRecoveryProof = LocalSidecarClient.submitRecoveryProofSha256(submit);
      firstAdmissionSequence = submit.payload().u64Bits(4);
      effectIdentity = submit.payload().bytes(16);
      durableSequence = submit.payload().u64Bits(19);
      require(effectIdentity.length > 0 && durableSequence == 1,
          "SUBMIT omitted its effect identity or mismatch consumed a durable sequence");
      first.abortAndWait();
    }

    var secondIdentity = identity(
        "ffeeddccbbaa99887766554433221100", 2, executableSha, nestedDescriptor);
    try (var second = startPeer(executable, secondIdentity)) {
      second.handshake();
      var runtimeId = second.open(durableDirectory, initialState);
      var replay = second.operation(exactSubmit);
      require(replay.messageType() == SidecarIpcV1.MessageType.SUBMIT_RESPONSE,
          "recovery retry did not return SUBMIT_RESPONSE");
      require(replay.payload().u64Bits(4) != firstAdmissionSequence,
          "qualification did not exercise a per-generation admission-sequence change");
      require(Arrays.equals(
              LocalSidecarClient.submitRecoveryProofSha256(replay),
              firstSubmitRecoveryProof),
          "recovery retry changed the durable SUBMIT recovery proof");
      require(Arrays.equals(replay.payload().bytes(16), effectIdentity)
              && replay.payload().u64Bits(19) == durableSequence,
          "recovery retry changed effect identity or durable sequence");

      var state = second.operation(LocalSidecarClient.stateRequest(requestId("state"), runtimeId));
      require(state.messageType() == SidecarIpcV1.MessageType.STATE_RESPONSE,
          "STATE did not return STATE_RESPONSE");
      require(state.payload().u64Bits(16) == durableSequence,
          "STATE durable sequence differs from SUBMIT");

      var snapshot = second.operation(
          LocalSidecarClient.snapshotRequest(requestId("snapshot"), runtimeId));
      require(snapshot.messageType() == SidecarIpcV1.MessageType.SNAPSHOT_RESPONSE,
          "SNAPSHOT did not return SNAPSHOT_RESPONSE");
      require(snapshot.payload().u64Bits(16) == durableSequence,
          "SNAPSHOT changed the durable sequence");

      var health = second.operation(LocalSidecarClient.healthRequest(requestId("health"), runtimeId));
      require(health.messageType() == SidecarIpcV1.MessageType.HEALTH_RESPONSE,
          "HEALTH did not return HEALTH_RESPONSE");
      require(health.payload().u8(16) == SidecarIpcV1.HealthState.READY.code()
              && health.payload().u64Bits(17) == secondIdentity.generation()
              && health.payload().u8(20) == 1
              && health.payload().u8(21) == 1,
          "HEALTH lacks generation/lock/READY evidence");

      var close = second.operation(
          LocalSidecarClient.closeRequest(
              requestId("close"), runtimeId, SidecarIpcV1.CloseMode.TERMINATE_AND_FENCE));
      require(close.messageType() == SidecarIpcV1.MessageType.CLOSE_RESPONSE,
          "CLOSE did not return CLOSE_RESPONSE");
      require(close.payload().u8(18) == 1, "native runtime did not close");
      second.awaitCleanExit();
    }
    System.out.println(
        "isolated sidecar compatible on JDK "
            + Runtime.version().feature()
            + ": descriptor/open/submit/crash/recover/retry/state/snapshot/health/close exact");
  }

  private static SidecarIpcV1.DescriptorIdentity identity(
      String sessionHex, long generation, byte[] executableSha, byte[] nestedDescriptor) {
    return new SidecarIpcV1.DescriptorIdentity(
        new SidecarIpcV1.Id128(HexFormat.of().parseHex(sessionHex)),
        generation,
        executableSha,
        BUILD_ID,
        nestedDescriptor);
  }

  private static Peer startPeer(
      Path executable, SidecarIpcV1.DescriptorIdentity identity) throws IOException {
    var process = new ProcessBuilder(
            executable.toString(),
            "--session",
            identity.sessionId().hex(),
            "--generation",
            Long.toUnsignedString(identity.generation()))
        .redirectError(ProcessBuilder.Redirect.INHERIT)
        .start();
    return new Peer(
        process,
        new LocalSidecarClient.StreamTransport(
            process.getInputStream(), process.getOutputStream()),
        identity);
  }

  private static byte[] requestId(String operation) {
    return ("java-sidecar-conformance-" + operation).getBytes(StandardCharsets.US_ASCII);
  }

  private static byte[] ascii(String value) {
    return value.getBytes(StandardCharsets.US_ASCII);
  }

  private static byte[] golden(String fixture, int typeCode) {
    var pattern = Pattern.compile(
        "\\\"envelope_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"envelope_sha256\\\":\\\"[0-9a-f]+\\\","
            + "\\\"type_code\\\":"
            + typeCode);
    var matcher = pattern.matcher(fixture);
    require(matcher.find(), "golden type " + typeCode + " is missing");
    var result = HexFormat.of().parseHex(matcher.group(1));
    require(!matcher.find(), "golden type " + typeCode + " is duplicated");
    return result;
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }

  private static final class Peer implements AutoCloseable {
    private final Process process;
    private final LocalSidecarClient.StreamTransport transport;
    private final SidecarIpcV1.DescriptorIdentity identity;
    private final SidecarIpcV1.SequenceCursor sendSequences =
        new SidecarIpcV1.SequenceCursor(1);
    private final SidecarIpcV1.SequenceCursor receiveSequences =
        new SidecarIpcV1.SequenceCursor(1);
    private int correlationCounter = 1;

    private Peer(
        Process process,
        LocalSidecarClient.StreamTransport transport,
        SidecarIpcV1.DescriptorIdentity identity) {
      this.process = process;
      this.transport = transport;
      this.identity = identity;
    }

    private void handshake() throws IOException {
      var correlation = correlation();
      var request = SidecarIpcV1.frame(
          SidecarIpcV1.MessageType.CLIENT_HELLO,
          identity.sessionId(),
          identity.generation(),
          correlation,
          sendSequences.claim(),
          SidecarIpcV1.descriptorPayload(SidecarIpcV1.MessageType.CLIENT_HELLO, identity));
      transport.write(request.canonicalBytes());
      var response = receive();
      require(response.messageType() == SidecarIpcV1.MessageType.SERVER_DESCRIPTOR,
          "sidecar handshake returned the wrong message");
      require(response.correlationId().equals(correlation), "descriptor correlation mismatch");
      SidecarIpcV1.requireDescriptor(response.payload(), identity);
    }

    private SidecarIpcV1.Id128 open(Path directory, byte[] initialState) throws IOException {
      var request = SidecarIpcV1.requestPayload(
          SidecarIpcV1.MessageType.OPEN_REQUEST,
          requestId("open"),
          List.of(
              SidecarIpcV1.u32(16, SidecarIpcV1.INGRESS_QUEUE_REQUESTS),
              SidecarIpcV1.text(17, directory.toString()),
              SidecarIpcV1.bytes(18, initialState),
              SidecarIpcV1.sha256Field(19, identity.nestedDescriptorSha256())));
      var response = operation(request);
      require(response.messageType() == SidecarIpcV1.MessageType.OPEN_RESPONSE,
          "OPEN did not return OPEN_RESPONSE");
      require(response.payload().u32(5) == 0 && response.payload().u8(19) == 1,
          "OPEN did not complete recovery before READY");
      return response.payload().id128(16);
    }

    private SidecarIpcV1.Frame operation(LocalSidecarClient.PreparedRequest request)
        throws IOException {
      return operation(SidecarIpcV1.decodePayload(request.type(), request.canonicalPayload()));
    }

    private SidecarIpcV1.Frame operationAllowError(LocalSidecarClient.PreparedRequest request)
        throws IOException {
      return operationAllowError(
          SidecarIpcV1.decodePayload(request.type(), request.canonicalPayload()));
    }

    private SidecarIpcV1.Frame operation(SidecarIpcV1.Payload request) throws IOException {
      var response = operationAllowError(request);
      if (response.messageType() == SidecarIpcV1.MessageType.ERROR_RESPONSE) {
        throw new IllegalStateException(
            "native sidecar returned ERROR_RESPONSE: " + response.payload().text(19));
      }
      return response;
    }

    private SidecarIpcV1.Frame operationAllowError(SidecarIpcV1.Payload request)
        throws IOException {
      var correlation = correlation();
      var frame = SidecarIpcV1.frame(
          request.type(),
          identity.sessionId(),
          identity.generation(),
          correlation,
          sendSequences.claim(),
          request);
      transport.write(frame.canonicalBytes());
      var response = receive();
      SidecarIpcV1.requireResponseMatches(
          response,
          request.type(),
          request.bytes(1),
          request.bytes(2),
          identity.sessionId(),
          identity.generation(),
          correlation);
      return response;
    }

    private SidecarIpcV1.Frame receive() throws IOException {
      var response = SidecarIpcV1.decodeFrame(transport.read());
      require(response.sessionId().equals(identity.sessionId()), "response session mismatch");
      require(response.generation() == identity.generation(), "response generation mismatch");
      receiveSequences.accept(response.sequence());
      return response;
    }

    private void abortAndWait() throws Exception {
      process.destroyForcibly();
      require(process.waitFor(10, TimeUnit.SECONDS), "sidecar did not exit after crash injection");
      transport.close();
    }

    private void awaitCleanExit() throws InterruptedException {
      require(process.waitFor(10, TimeUnit.SECONDS), "sidecar did not exit after CLOSE");
      require(process.exitValue() == 0, "sidecar exited unsuccessfully: " + process.exitValue());
    }

    private SidecarIpcV1.Id128 correlation() {
      var value = new byte[16];
      value[12] = (byte) (correlationCounter >>> 24);
      value[13] = (byte) (correlationCounter >>> 16);
      value[14] = (byte) (correlationCounter >>> 8);
      value[15] = (byte) correlationCounter;
      correlationCounter++;
      return new SidecarIpcV1.Id128(value);
    }

    @Override
    public void close() throws IOException {
      transport.close();
      if (process.isAlive()) {
        process.destroyForcibly();
      }
    }
  }
}
