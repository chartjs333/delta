package io.deltareduce.node.scheduling;

import io.deltareduce.node.scheduling.AdmissionTransport.Kind;
import io.deltareduce.node.scheduling.AdmissionTransport.OpaqueArtifact;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.regex.Pattern;

/** JDK 25/26 FFM and transport-only scheduling conformance matrix. */
public final class SchedulingConformance {
  private SchedulingConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 2, "usage: SchedulingConformance <native-library> <fixture>");
    var fixture = Fixture.read(Path.of(arguments[1]));
    NativeScheduling.Decision direct;
    NativeScheduling.Decision copied;
    NativeScheduling.Decision collected;
    try (var nativeScheduling = new NativeScheduling(Path.of(arguments[0]))) {
      var profileDirect = direct(fixture.profile().bytes());
      direct = nativeScheduling.evaluate(policy(), profileDirect, false);
      copied = nativeScheduling.evaluate(
          policy(), ByteBuffer.wrap(fixture.profile().bytes()), true);
      profileDirect.put(0, (byte) 0);
      var collector = new CapabilityCollector(nativeScheduling, policy(), 256 * 1024);
      collected = collector.collect(ByteBuffer.wrap(fixture.profile().bytes()), true);
      require(
          collector.telemetry().acceptedProfiles() == 1
              && collector.telemetry().rejectedProfiles() == 0,
          "capability collector telemetry changed");
    }
    require(direct.borrowedDirect(), "direct profile did not use borrowed synchronous ABI");
    require(!copied.borrowedDirect(), "heap profile did not use owned-copy ABI");
    require(
        Arrays.equals(direct.canonicalBytes(), fixture.decision().bytes())
            && Arrays.equals(copied.canonicalBytes(), fixture.decision().bytes())
            && Arrays.equals(collected.canonicalBytes(), fixture.decision().bytes()),
        "native scheduling FFM decisions differ from frozen bytes");
    testBoundedOpaqueTransport(fixture);
    testOpaqueTimerCallbacks(fixture);
    System.out.println(
        "native scheduling adapter compatible on JDK " + Runtime.version().feature()
            + ": borrowed/copy parity, bounded opaque transport, no Java lease/math authority");
  }

  private static void testBoundedOpaqueTransport(Fixture fixture) {
    var transport = new AdmissionTransport(2, 1024 * 1024);
    var planBytes = fixture.plan().bytes();
    require(
        transport.offer(new OpaqueArtifact(fixture.plan().contentId(), Kind.PLAN, planBytes)),
        "plan transport was rejected");
    Arrays.fill(planBytes, (byte) 0);
    require(
        transport.offer(
            new OpaqueArtifact(fixture.lease().contentId(), Kind.LEASE, fixture.lease().bytes())),
        "lease transport was rejected");
    require(
        !transport.offer(
            new OpaqueArtifact(
                fixture.timer().contentId(), Kind.TIMER_TOKEN, fixture.timer().bytes())),
        "transport accepted bytes beyond bounded capacity");
    var deliveredPlan = transport.poll();
    var deliveredLease = transport.poll();
    require(
        deliveredPlan.kind() == Kind.PLAN
            && Arrays.equals(deliveredPlan.canonicalBytes(), fixture.plan().bytes())
            && deliveredLease.kind() == Kind.LEASE
            && Arrays.equals(deliveredLease.canonicalBytes(), fixture.lease().bytes()),
        "Java transport changed opaque native bytes or FIFO order");
    var beforeCancel = transport.telemetry();
    require(
        beforeCancel.accepted() == 2 && beforeCancel.delivered() == 2
            && beforeCancel.backpressureRejects() == 1 && beforeCancel.queued() == 0,
        "bounded admission transport telemetry is incomplete");
    transport.cancel();
    require(transport.telemetry().cancelled(), "transport cancellation was not recorded");
    expectFailure(
        () -> transport.offer(
            new OpaqueArtifact(fixture.plan().contentId(), Kind.PLAN, fixture.plan().bytes())),
        "cancelled transport accepted native bytes");
  }

  private static void testOpaqueTimerCallbacks(Fixture fixture) {
    var router = new LeaseTimerRouter(2, 4096);
    var original = fixture.timer().bytes();
    require(router.schedule(original, 9), "first timer delivery was rejected");
    require(router.schedule(original, 8), "reordered duplicate timer delivery was rejected");
    Arrays.fill(original, (byte) 0);
    require(!router.schedule(fixture.timer().bytes(), 10), "timer router exceeded capacity");
    var callbacks = new ArrayList<byte[]>();
    require(router.deliverReady(7, (bytes, tick) -> callbacks.add(bytes)) == 0,
        "timer callback fired before its delivery tick");
    require(router.deliverReady(8, (bytes, tick) -> callbacks.add(bytes)) == 1,
        "reordered timer callback was not delivered");
    require(router.deliverReady(9, (bytes, tick) -> callbacks.add(bytes)) == 1,
        "duplicate timer callback was not forwarded to native state");
    require(
        callbacks.size() == 2
            && Arrays.equals(callbacks.get(0), fixture.timer().bytes())
            && Arrays.equals(callbacks.get(1), fixture.timer().bytes()),
        "Java timer routing changed opaque native token bytes");
    var telemetry = router.telemetry();
    require(
        telemetry.timerCallbacks() == 2 && telemetry.backpressureRejects() == 1
            && telemetry.queued() == 0,
        "opaque timer telemetry is incomplete");
    router.cancel();
    require(router.telemetry().cancelled(), "timer cancellation was not recorded");
  }

  private static NativeScheduling.Policy policy() {
    return new NativeScheduling.Policy(
        "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        "QLORA-8GB",
        List.of("code", "text"),
        List.of("eu", "us"),
        List.of(
            "sha256:3333333333333333333333333333333333333333333333333333333333333333"),
        List.of(
            "sha256:8888888888888888888888888888888888888888888888888888888888888888",
            "sha256:9999999999999999999999999999999999999999999999999999999999999999"),
        12,
        7,
        8_589_934_592L,
        8);
  }

  private static ByteBuffer direct(byte[] input) {
    var result = ByteBuffer.allocateDirect(input.length);
    result.put(input).flip();
    return result;
  }

  private static void expectFailure(Runnable operation, String message) {
    try {
      operation.run();
    } catch (IllegalArgumentException expected) {
      return;
    }
    throw new IllegalStateException(message);
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

  private record Fixture(
      Artifact profile, Artifact decision, Artifact plan, Artifact lease, Artifact timer) {
    private static final Pattern PROFILE = Pattern.compile(
        "\\\"capability_profiles\\\":\\[\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"content_id\\\":\\\"(sha256:[0-9a-f]{64})\\\"");
    private static final Pattern DECISION = Pattern.compile(
        "\\\"eligibility_decisions\\\":\\[\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"content_id\\\":\\\"(sha256:[0-9a-f]{64})\\\"");
    private static final Pattern PLAN = Pattern.compile(
        "\\\"plan\\\":\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"content_id\\\":\\\"(sha256:[0-9a-f]{64})\\\"");
    private static final Pattern LEASE = Pattern.compile(
        "\\\"ticket_leases\\\":\\[\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"content_id\\\":\\\"(sha256:[0-9a-f]{64})\\\"");
    private static final Pattern TIMER = Pattern.compile(
        "\\\"lease_timer_tokens\\\":\\[\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\","
            + "\\\"content_id\\\":\\\"(sha256:[0-9a-f]{64})\\\"");

    static Fixture read(Path path) throws Exception {
      var document = Files.readString(path);
      return new Fixture(
          artifact(PROFILE, document, "capability"),
          artifact(DECISION, document, "decision"),
          artifact(PLAN, document, "plan"),
          artifact(LEASE, document, "lease"),
          artifact(TIMER, document, "timer"));
    }

    private static Artifact artifact(Pattern pattern, String document, String label) {
      var matcher = pattern.matcher(document);
      require(matcher.find(), "scheduling Java fixture lacks " + label);
      return new Artifact(HexFormat.of().parseHex(matcher.group(1)), matcher.group(2));
    }
  }
}
