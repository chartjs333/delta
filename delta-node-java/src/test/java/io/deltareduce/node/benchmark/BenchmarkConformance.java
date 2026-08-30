package io.deltareduce.node.benchmark;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.regex.Pattern;

public final class BenchmarkConformance {
  private BenchmarkConformance() {}

  public static void main(String[] args) {
    runtimeIdentitiesAreExact();
    networkAndTransportAreDeterministic();
    embeddedAndSidecarAreSeparated();
    if (args.length == 2 || args.length == 3) {
      externalSidecarSurvivesRestart(
          Path.of(args[0]), Path.of(args[1]), args.length == 3 ? Path.of(args[2]) : null);
    } else if (args.length != 0) {
      throw new IllegalArgumentException("expected SIDECAR JOURNAL arguments");
    }
    metricsFailClosed();
  }

  private static void externalSidecarSurvivesRestart(
      Path executable, Path journal, Path crossLanguageFixture) {
    byte[] request = "external-sidecar".getBytes(StandardCharsets.US_ASCII);
    try (var endpoint = new SidecarRunner.ExternalEndpoint(executable, journal, 8192)) {
      var runner = new SidecarRunner(endpoint, 8192);
      var result = runner.run(new ProcessProfileRunner.Request("external", request));
      require(result.crashContained() && result.replayExact());
      require(result.responseId().equals(BenchmarkContracts.sha256(request)));
      require(result.requestBytes() == request.length && result.responseBytes() == request.length);
      require(
          result.latencyMicros() > 0
              && result.replayLatencyMicros() > 0
              && result.restartMicros() > 0);
      System.out.println(
          "PROCESS_PROFILE ISOLATED_SIDECAR "
              + result.requestBytes()
              + " "
              + result.responseBytes()
              + " "
              + result.latencyMicros()
              + " "
              + result.replayLatencyMicros()
              + " "
              + result.restartMicros());
      if (crossLanguageFixture != null) {
        verifyCrossLanguageFixture(runner, crossLanguageFixture);
      }
    }
  }

  private static void verifyCrossLanguageFixture(ProcessProfileRunner runner, Path fixture) {
    var bytesHex = Pattern.compile("\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\"");
    var hashes = new ArrayList<String>();
    try {
      var matcher = bytesHex.matcher(Files.readString(fixture, StandardCharsets.UTF_8));
      while (matcher.find()) {
        byte[] canonicalBytes = HexFormat.of().parseHex(matcher.group(1));
        String requestId = "fixture-" + hashes.size();
        var result = runner.run(new ProcessProfileRunner.Request(requestId, canonicalBytes));
        String expected = BenchmarkContracts.sha256(canonicalBytes);
        require(result.replayExact() && result.responseId().equals(expected));
        hashes.add(expected);
      }
    } catch (IOException error) {
      throw new IllegalStateException("cross-language fixture read failed", error);
    }
    require(hashes.size() >= 14);
    String aggregate =
        BenchmarkContracts.sha256(String.join("\n", hashes).getBytes(StandardCharsets.US_ASCII));
    System.out.println("CROSS_LANGUAGE " + hashes.size() + " " + aggregate);
  }

  private static void runtimeIdentitiesAreExact() {
    String id = "sha256:" + "1".repeat(64);
    var identities = new RuntimeIdentityCollector().collect(id, id, id, id, id, "EMBEDDED_FFM");
    require(identities.get("formal_semantics_id").equals(BenchmarkContracts.FORMAL_SEMANTICS_ID));
    require(identities.get("deployment_profile").equals("EMBEDDED_FFM"));
    expectRejected(
        () -> new RuntimeIdentityCollector().collect("sha256:" + "0".repeat(63), id, id, id, id,
            "EMBEDDED_FFM"));
    expectRejected(
        () -> new RuntimeIdentityCollector().collect(id, id, id, id, id, "UNREGISTERED"));
  }

  private static void networkAndTransportAreDeterministic() {
    var faults = new NetworkFaultController(17, 80, 5, 10_000, 1_000, 5_000);
    require(faults.decision(42).equals(faults.decision(42)));
    var transport = new BenchmarkTransport(64, 2);
    byte[] message = "canonical".getBytes(StandardCharsets.US_ASCII);
    String id = BenchmarkContracts.sha256(message);
    require(Arrays.equals(message, transport.deliver(id, message)));
    require(Arrays.equals(message, transport.deliver(id, message)));
  }

  private static void embeddedAndSidecarAreSeparated() {
    byte[] request = "request".getBytes(StandardCharsets.US_ASCII);
    var embedded = new EmbeddedFfmRunner(bytes -> bytes.clone());
    var embeddedResult = embedded.run(new ProcessProfileRunner.Request("embedded", request));
    require(!embeddedResult.crashContained() && embeddedResult.replayExact());

    final class Endpoint implements SidecarRunner.SidecarEndpoint {
      private final LinkedHashMap<String, byte[]> responses = new LinkedHashMap<>();

      @Override
      public byte[] execute(String requestId, byte[] bytes) {
        return responses.computeIfAbsent(requestId, ignored -> bytes.clone()).clone();
      }

      @Override
      public void crash() {}

      @Override
      public void restart() {}
    }
    var sidecar = new SidecarRunner(new Endpoint(), 64);
    var sidecarResult = sidecar.run(new ProcessProfileRunner.Request("sidecar", request));
    require(sidecarResult.crashContained() && sidecarResult.replayExact());
    require(sidecarResult.responseId().equals(embeddedResult.responseId()));
  }

  private static void metricsFailClosed() {
    var metrics = new NettyMetricsCollector();
    metrics.add("queue.bytes", 16);
    require(metrics.snapshot().get("queue.bytes") == 16L);
    metrics.requireClean(0, 0, 2, 2);
    expectRejected(() -> metrics.requireClean(1, 0, 0, 2));
    expectRejected(() -> metrics.requireClean(0, 1, 0, 2));
    expectRejected(() -> metrics.requireClean(0, 0, 3, 2));
    expectRejected(() -> metrics.requireClean(0, 0, -1, 2));
    expectRejected(() -> metrics.add("UPPERCASE", 1));
    expectRejected(() -> metrics.add("queue.bytes", -1));

    var transport = new BenchmarkTransport(4, 1);
    byte[] first = {1};
    String firstId = BenchmarkContracts.sha256(first);
    byte[] delivered = transport.deliver(firstId, first);
    delivered[0] = 9;
    require(transport.deliver(firstId, first)[0] == 1);
    expectRejected(() -> transport.deliver(firstId, new byte[] {2}));
    expectRejected(() -> transport.deliver(BenchmarkContracts.sha256(new byte[] {3}), new byte[] {3}));
    expectRejected(
        () -> new BenchmarkTransport(1, 1).deliver(
            BenchmarkContracts.sha256(new byte[] {1, 2}), new byte[] {1, 2}));
    expectRejected(() -> new BenchmarkTransport(1, 1).deliver("not-an-id", new byte[0]));
  }

  private static void expectRejected(Runnable operation) {
    try {
      operation.run();
      throw new AssertionError("expected rejection");
    } catch (IllegalArgumentException expected) {
      // Expected fail-closed boundary.
    }
  }

  private static void require(boolean condition) {
    if (!condition) {
      throw new AssertionError("benchmark conformance failed");
    }
  }
}
