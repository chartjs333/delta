package io.deltareduce.node.certificates;

import io.deltareduce.node.apply.ArtifactEffectAdapter;
import io.deltareduce.node.apply.CurrentCheckpointPublisher;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Pattern;

/** JDK 25/26 native-inspection and opaque-adapter conformance. */
public final class CertificatesConformance {
  private CertificatesConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 2, "usage: CertificatesConformance <native-library> <fixture>");
    var artifact = fixture(Path.of(arguments[1]));
    try (var verifier = new NativeCertificateVerifier(Path.of(arguments[0]))) {
      var directBytes = ByteBuffer.allocateDirect(artifact.bytes().length);
      directBytes.put(artifact.bytes()).flip();
      var direct = verifier.inspect(
          NativeCertificateVerifier.Kind.INPUT_SET, artifact.contentId(), directBytes, false);
      var copied = verifier.inspect(
          NativeCertificateVerifier.Kind.INPUT_SET,
          artifact.contentId(),
          ByteBuffer.wrap(artifact.bytes()),
          true);
      directBytes.put(0, (byte) 0);
      require(
          direct.borrowedDirect() && !copied.borrowedDirect()
              && Arrays.equals(direct.nativeEffect(), copied.nativeEffect()),
          "native borrowed/copy inspection parity failed");
    }
    testTransport(artifact);
    testTimers(artifact);
    testEffects(artifact);
    System.out.println(
        "certificate adapters compatible on JDK " + Runtime.version().feature()
            + ": native-only verification, opaque delivery/timers, bounded effects");
  }

  private static void testTransport(Artifact artifact) {
    var transport = new AuthenticatedCertificateTransport(
        2, 4 * 1024 * 1024, Set.of("validator-0"),
        (peer, bytes, tag) -> tag.length == 1 && tag[0] == 7);
    var envelope = new AuthenticatedCertificateTransport.Envelope(
        "validator-0", NativeCertificateVerifier.Kind.INPUT_SET, artifact.bytes(), new byte[] {7});
    require(transport.offer(envelope, 10), "authenticated certificate was rejected");
    require(transport.offer(envelope, 9), "duplicate/reordered certificate was rejected");
    require(!transport.offer(envelope, 11), "transport exceeded bounded capacity");
    var delivered = new ArrayList<byte[]>();
    require(
        transport.deliverReady(9, value -> delivered.add(value.opaqueBytes())) == 1,
        "reordered delivery failed");
    require(transport.dropNext(), "network drop injection failed");
    var bad = new AuthenticatedCertificateTransport.Envelope(
        "validator-0", NativeCertificateVerifier.Kind.INPUT_SET, artifact.bytes(), new byte[] {0});
    require(!transport.offer(bad, 12), "unauthenticated bytes were accepted");
    require(
        delivered.size() == 1 && Arrays.equals(delivered.get(0), artifact.bytes())
            && transport.telemetry().backpressureRejects() == 1
            && transport.telemetry().authenticationRejects() == 1
            && transport.telemetry().dropped() == 1,
        "transport telemetry or opaque bytes changed");
  }

  private static void testTimers(Artifact artifact) {
    var timers = new CertificateTimerService(2, 4 * 1024 * 1024);
    require(timers.schedule(artifact.bytes(), 4), "first timer was rejected");
    require(timers.schedule(artifact.bytes(), 3), "duplicate timer was rejected");
    require(!timers.schedule(artifact.bytes(), 5), "timer service exceeded capacity");
    var delivered = new ArrayList<byte[]>();
    require(
        timers.deliverReady(3, (bytes, tick) -> delivered.add(bytes)) == 1
            && timers.deliverReady(4, (bytes, tick) -> delivered.add(bytes)) == 1
            && Arrays.equals(delivered.get(0), artifact.bytes())
            && Arrays.equals(delivered.get(1), artifact.bytes()),
        "opaque timer delivery changed bytes/order");
  }

  private static void testEffects(Artifact artifact) throws Exception {
    var root = Files.createTempDirectory("delta-008-artifacts");
    var adapter = new ArtifactEffectAdapter(root, 4 * 1024 * 1024);
    var target = adapter.execute(new ArtifactEffectAdapter.NativeEffect(
        ArtifactEffectAdapter.Action.WRITE,
        artifact.contentId(),
        "objects/input-set.json",
        artifact.bytes(),
        new byte[] {1}));
    require(Arrays.equals(Files.readAllBytes(target), artifact.bytes()), "artifact effect changed bytes");
    var published = new AtomicReference<CurrentCheckpointPublisher.NativeAdvanceCurrent>();
    var publisher = new CurrentCheckpointPublisher(published::set);
    var current = new CurrentCheckpointPublisher.NativeAdvanceCurrent(
        artifact.contentId(), id('b'), id('7'), new byte[] {2});
    publisher.publish(current);
    require(
        published.get().applyQcId().equals(current.applyQcId())
            && published.get().checkpointId().equals(current.checkpointId())
            && published.get().optimizerId().equals(current.optimizerId())
            && Arrays.equals(published.get().authorization(), current.authorization()),
        "native current effect was not published exactly");
  }

  private static Artifact fixture(Path path) throws Exception {
    var document = Files.readString(path);
    var pattern = Pattern.compile(
        "\\\"input_set_certificate\\\":\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"content_id\\\":\\\"(sha256:[0-9a-f]{64})\\\"");
    var match = pattern.matcher(document);
    require(match.find(), "certificate Java fixture lacks input set");
    return new Artifact(HexFormat.of().parseHex(match.group(1)), match.group(2));
  }

  private static String id(char digit) {
    return "sha256:" + String.valueOf(digit).repeat(64);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }

  private record Artifact(byte[] bytes, String contentId) {
    private Artifact {
      bytes = Arrays.copyOf(bytes, bytes.length);
    }

    @Override
    public byte[] bytes() {
      return Arrays.copyOf(bytes, bytes.length);
    }
  }
}
