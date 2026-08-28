package io.deltareduce.node.hierarchy;

import io.deltareduce.node.hierarchy.HierarchyRouter.OpaqueContribution;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Pattern;

/** JDK 25/26 native-contract and bounded routing-only conformance matrix. */
public final class HierarchyConformance {
  private static final String TOPOLOGY_ID =
      "sha256:99b0c5ce4fe5c850e95750d39c8a9844148adc8b0f00353da02f2f1ad00da157";
  private static final String ROUTING_PROJECTION_ID =
      "sha256:22caad4705d05abcdb56958095bacd1686dc37d9d1b8996f3bf2f312f79a3472";

  private HierarchyConformance() {}

  public static void main(String[] arguments) throws Exception {
    require(arguments.length == 2, "usage: HierarchyConformance <native-library> <fixture>");
    var fixture = Fixture.read(Path.of(arguments[1]));
    NativeHierarchy.Validation direct;
    NativeHierarchy.Validation copied;
    try (var nativeHierarchy = new NativeHierarchy(Path.of(arguments[0]))) {
      var topologyDirect = direct(fixture.topology());
      var proofDirect = direct(fixture.proof());
      direct = nativeHierarchy.validate(context(), topologyDirect, proofDirect, false);
      copied = nativeHierarchy.validate(
          context(), ByteBuffer.wrap(fixture.topology()), ByteBuffer.wrap(fixture.proof()), true);
      topologyDirect.put(0, (byte) 0);
      proofDirect.put(0, (byte) 0);
    }
    require(direct.borrowedDirect(), "direct topology did not use borrowed synchronous ABI");
    require(!copied.borrowedDirect(), "heap topology did not use owned-copy ABI");
    require(direct.canonicalEffect().equals(copied.canonicalEffect()),
        "borrowed/copy native hierarchy effects differ");
    require(direct.topologyId().equals(TOPOLOGY_ID), "native topology identity changed");
    require(direct.routingProjectionId().equals(ROUTING_PROJECTION_ID),
        "native routing projection identity changed");
    testRoutingOnly(direct);
    System.out.println(
        "native hierarchy/routing compatible on JDK " + Runtime.version().feature()
            + ": exact IDs, bounded opaque routing, no Java math/QC authority, "
            + "routing_projection_id=" + direct.routingProjectionId());
  }

  private static void testRoutingOnly(NativeHierarchy.Validation validation) {
    var projection = HierarchyRouter.projection(
        TOPOLOGY_ID,
        50,
        100,
        route("eu", "parameter-000", Set.of("c-ticket-01")),
        route("us", "parameter-000", Set.of("c-ticket-02", "c-ticket-03")),
        route("ap", "parameter-000", Set.of("c-ticket-04", "c-ticket-05", "c-ticket-06")),
        route("eu", "parameter-001", Set.of("c-ticket-01")),
        route("us", "parameter-001", Set.of("c-ticket-02", "c-ticket-03")),
        route("ap", "parameter-001", Set.of("c-ticket-04", "c-ticket-05", "c-ticket-06")),
        route("text", "eu", "parameter-000", Set.of("t-ticket-01")),
        route("text", "us", "parameter-000", Set.of("t-ticket-02")),
        route("text", "ap", "parameter-000", Set.of("t-ticket-03", "t-ticket-04", "t-ticket-05")),
        route("text", "eu", "parameter-001", Set.of("t-ticket-01")),
        route("text", "us", "parameter-001", Set.of("t-ticket-02")),
        route("text", "ap", "parameter-001", Set.of("t-ticket-03", "t-ticket-04", "t-ticket-05")));
    testParallelShuffleAndRestart(validation, projection);
    var router = new HierarchyRouter(validation, projection, 1, 2);
    var incompleteProjection = HierarchyRouter.projection(
        TOPOLOGY_ID, 50, 100, route("eu", "parameter-000", Set.of("c-ticket-01")));
    expectFailure(() -> new HierarchyRouter(validation, incompleteProjection, 1, 1),
        "Java accepted a routing table that differs from the native topology");
    var first = contribution("c-ticket-02", "parameter-000", 1);
    var second = contribution("c-ticket-03", "parameter-000", 2);
    require(router.offer(first, 1), "first bounded route delivery was rejected");
    require(!router.offer(second, 2), "route accepted input beyond bounded capacity");
    var route = new HierarchyRouter.RouteKey("code", "us", "parameter-000");
    expectFailure(() -> router.poll(route, "c-eu-v1", 3),
        "non-member validator received regional bytes");
    var delivered = router.poll(route, "c-us-v1", 3);
    require(delivered != null && Arrays.equals(
            delivered.contribution().canonicalBytes(), first.canonicalBytes()),
        "opaque contribution bytes changed during Java routing");
    require(router.retry(delivered, 50), "soft-deadline retry was rejected");
    var retried = router.poll(route, "c-us-v2", 51);
    require(retried != null && retried.retries() == 1, "retry metadata or order changed");
    router.acknowledge(retried);
    var beforeAbort = router.telemetry();
    require(beforeAbort.accepted() == 1 && beforeAbort.delivered() == 2
            && beforeAbort.acknowledged() == 1 && beforeAbort.retries() == 1
            && beforeAbort.backpressureRejects() == 1
            && beforeAbort.softDeadlineSignals() >= 2,
        "bounded routing telemetry is incomplete");
    expectStateFailure(() -> router.offer(contribution("c-ticket-04", "parameter-001", 4), 100),
        "hard deadline did not deterministically abort routing");
    require(router.telemetry().hardAborted() && router.telemetry().queued() == 0,
        "hard abort retained queued opaque bytes");

    var cancellable = new HierarchyRouter(validation, projection, 2, 1);
    require(cancellable.offer(contribution("c-ticket-01", "parameter-001", 9), 1),
        "cancellation fixture admission failed");
    cancellable.cancel();
    require(cancellable.telemetry().cancelled() && cancellable.telemetry().queued() == 0,
        "cancellation did not release bounded routing queue");
    expectFailure(() -> cancellable.offer(contribution("c-ticket-01", "parameter-001", 10), 2),
        "cancelled router accepted new bytes");
  }

  private static void testParallelShuffleAndRestart(
      NativeHierarchy.Validation validation, HierarchyRouter.TopologyProjection projection) {
    var router = new HierarchyRouter(validation, projection, 8, 2);
    var accepted = new AtomicInteger();
    var failure = new AtomicReference<Throwable>();
    var inputs = new OpaqueContribution[] {
        contribution("code", "c-ticket-01", "parameter-000", 11),
        contribution("text", "t-ticket-02", "parameter-001", 12),
        contribution("code", "c-ticket-05", "parameter-001", 13),
        contribution("text", "t-ticket-04", "parameter-000", 14),
    };
    var threads = new Thread[inputs.length];
    for (int index = inputs.length - 1; index >= 0; --index) {
      var contribution = inputs[index];
      threads[index] = Thread.ofVirtual().unstarted(() -> {
        try {
          if (router.offer(contribution, 7)) {
            accepted.incrementAndGet();
          }
        } catch (Throwable error) {
          failure.compareAndSet(null, error);
        }
      });
      threads[index].start();
    }
    for (var thread : threads) {
      try {
        thread.join();
      } catch (InterruptedException error) {
        Thread.currentThread().interrupt();
        throw new IllegalStateException("parallel routing test interrupted", error);
      }
    }
    require(failure.get() == null && accepted.get() == inputs.length,
        "parallel shuffled ingress lost a bounded contribution");
    for (var input : inputs) {
      var region = input.ticketId().contains("01") ? "eu"
          : input.ticketId().contains("02") ? "us" : "ap";
      var prefix = input.domainId().substring(0, 1);
      var key = new HierarchyRouter.RouteKey(input.domainId(), region, input.shardId());
      var delivery = router.poll(key, prefix + "-" + region + "-v1", 8);
      require(delivery != null
              && Arrays.equals(delivery.contribution().canonicalBytes(), input.canonicalBytes()),
          "parallel/shuffled routing changed opaque canonical bytes");
    }

    var beforeRestart = new HierarchyRouter(validation, projection, 2, 1);
    var replay = contribution("text", "t-ticket-01", "parameter-001", 21);
    require(beforeRestart.offer(replay, 50), "soft-view retry fixture was rejected");
    var afterRestart = new HierarchyRouter(validation, projection, 2, 1);
    require(afterRestart.telemetry().queued() == 0 && afterRestart.offer(replay, 51),
        "Java transport restart retained stale queue state or changed exact replay admission");
    var delivery = afterRestart.poll(
        new HierarchyRouter.RouteKey("text", "eu", "parameter-001"), "t-eu-v2", 52);
    require(delivery != null && Arrays.equals(
            delivery.contribution().canonicalBytes(), replay.canonicalBytes()),
        "restart/retry changed opaque contribution identity");
  }

  private static HierarchyRouter.Route route(
      String region, String shard, Set<String> tickets) {
    return route("code", region, shard, tickets);
  }

  private static HierarchyRouter.Route route(
      String domain, String region, String shard, Set<String> tickets) {
    var prefix = domain.substring(0, 1);
    return HierarchyRouter.route(
        domain, region, shard, tickets,
        Set.of(prefix + "-" + region + "-v1", prefix + "-" + region + "-v2",
            prefix + "-" + region + "-v3", prefix + "-" + region + "-v4"));
  }

  private static OpaqueContribution contribution(String ticket, String shard, int marker) {
    return contribution("code", ticket, shard, marker);
  }

  private static OpaqueContribution contribution(
      String domain, String ticket, String shard, int marker) {
    return new OpaqueContribution(ticket, domain, shard, new byte[] {(byte) marker, 2, 3, 4});
  }

  private static NativeHierarchy.Context context() {
    return new NativeHierarchy.Context(
        "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
        "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
        "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
        "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1");
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

  private static void expectStateFailure(Runnable operation, String message) {
    try {
      operation.run();
    } catch (IllegalStateException expected) {
      return;
    }
    throw new IllegalStateException(message);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }

  private record Fixture(byte[] topology, byte[] proof) {
    private static final Pattern TOPOLOGY =
        Pattern.compile("\\\"topology\\\":\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\"");
    private static final Pattern PROOF =
        Pattern.compile(
            "\\\"hierarchy_proof_instance\\\":\\{\\\"bytes_hex\\\":\\\"([0-9a-f]+)\\\"");

    static Fixture read(Path path) throws Exception {
      var document = Files.readString(path);
      var topology = TOPOLOGY.matcher(document);
      var proof = PROOF.matcher(document);
      require(topology.find() && proof.find(), "hierarchy Java fixture is incomplete");
      return new Fixture(java.util.HexFormat.of().parseHex(topology.group(1)),
          java.util.HexFormat.of().parseHex(proof.group(1)));
    }
  }
}
