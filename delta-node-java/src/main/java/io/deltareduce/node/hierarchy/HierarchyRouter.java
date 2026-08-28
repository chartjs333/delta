package io.deltareduce.node.hierarchy;

import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Bounded opaque-byte routing only; all arithmetic and quorum decisions remain native. */
public final class HierarchyRouter {
  private final TopologyProjection topology;
  private final int routeCapacity;
  private final int maximumRetries;
  private final Map<TicketShard, Route> ticketRoutes = new HashMap<>();
  private final Map<RouteKey, ArrayDeque<Delivery>> queues = new HashMap<>();
  private final Telemetry telemetry = new Telemetry();
  private long nextSequence = 1;
  private boolean cancelled;
  private boolean hardAborted;

  public HierarchyRouter(
      NativeHierarchy.Validation nativeValidation, TopologyProjection topology,
      int routeCapacity, int maximumRetries) {
    NativeHierarchy.require(nativeValidation.topologyId().equals(topology.topologyId()),
        "Java topology projection is not bound to native validation");
    NativeHierarchy.require(
        nativeValidation.routingProjectionId().equals(topology.routingProjectionId()),
        "Java route table is not bound to the native routing projection");
    NativeHierarchy.require(
        nativeValidation.routingProjectionId().equals(topology.routingProjectionId()),
        "Java routing table differs from the native topology projection");
    NativeHierarchy.require(routeCapacity > 0, "route capacity must be positive");
    NativeHierarchy.require(maximumRetries >= 0, "maximum retries cannot be negative");
    NativeHierarchy.require(topology.softDeadlineTick() < topology.hardDeadlineTick(),
        "routing deadlines are invalid");
    this.topology = topology;
    this.routeCapacity = routeCapacity;
    this.maximumRetries = maximumRetries;
    for (var route : topology.routes()) {
      NativeHierarchy.require(!route.ticketIds().isEmpty(), "route ticket set is empty");
      NativeHierarchy.require(!route.validatorIds().isEmpty(), "route validator set is empty");
      NativeHierarchy.require(queues.put(route.key(), new ArrayDeque<>()) == null,
          "route key is duplicated");
      for (var ticket : route.ticketIds()) {
        var key = new TicketShard(ticket, route.key().shardId());
        NativeHierarchy.require(ticketRoutes.put(key, route) == null,
            "ticket/shard route is duplicated");
      }
    }
  }

  public synchronized boolean offer(OpaqueContribution contribution, long logicalTick) {
    requireActive(logicalTick);
    var route = ticketRoutes.get(new TicketShard(contribution.ticketId(), contribution.shardId()));
    NativeHierarchy.require(route != null, "contribution has no immutable route");
    NativeHierarchy.require(route.key().domainId().equals(contribution.domainId()),
        "contribution domain differs from immutable route");
    var queue = queues.get(route.key());
    if (queue.size() >= routeCapacity) {
      telemetry.backpressureRejects++;
      return false;
    }
    var delivery = new Delivery(
        nextSequence++, route.key(), contribution.copy(), 0, logicalTick);
    queue.addLast(delivery);
    telemetry.accepted++;
    return true;
  }

  public synchronized Delivery poll(RouteKey route, String validatorId, long logicalTick) {
    requireActive(logicalTick);
    var definition = topology.route(route);
    NativeHierarchy.require(definition.validatorIds().contains(validatorId),
        "validator is outside the permissioned regional committee");
    var delivery = queues.get(route).pollFirst();
    if (delivery != null) {
      telemetry.delivered++;
    }
    return delivery;
  }

  public synchronized boolean retry(Delivery prior, long logicalTick) {
    requireActive(logicalTick);
    NativeHierarchy.require(prior.retries() < maximumRetries, "delivery retry budget exhausted");
    var queue = queues.get(prior.route());
    NativeHierarchy.require(queue != null, "delivery route is not active");
    if (queue.size() >= routeCapacity) {
      telemetry.backpressureRejects++;
      return false;
    }
    queue.addLast(new Delivery(
        prior.sequence(), prior.route(), prior.contribution().copy(), prior.retries() + 1,
        logicalTick));
    telemetry.retries++;
    return true;
  }

  public synchronized void acknowledge(Delivery delivery) {
    NativeHierarchy.require(!cancelled && !hardAborted, "router is not active");
    telemetry.acknowledged++;
  }

  public synchronized void cancel() {
    cancelled = true;
    queues.values().forEach(ArrayDeque::clear);
    telemetry.cancellations++;
  }

  public synchronized TelemetrySnapshot telemetry() {
    int queued = queues.values().stream().mapToInt(ArrayDeque::size).sum();
    return new TelemetrySnapshot(
        telemetry.accepted, telemetry.delivered, telemetry.acknowledged, telemetry.retries,
        telemetry.backpressureRejects, telemetry.softDeadlineSignals, telemetry.hardAborts,
        telemetry.cancellations, queued, cancelled, hardAborted);
  }

  private void requireActive(long logicalTick) {
    NativeHierarchy.require(!cancelled, "routing was cancelled");
    if (logicalTick >= topology.hardDeadlineTick()) {
      hardAborted = true;
      queues.values().forEach(ArrayDeque::clear);
      telemetry.hardAborts++;
      throw new IllegalStateException("hard deadline reached: deterministic routing abort");
    }
    if (logicalTick >= topology.softDeadlineTick()) {
      telemetry.softDeadlineSignals++;
    }
    NativeHierarchy.require(!hardAborted, "routing was hard-aborted");
  }

  public record RouteKey(String domainId, String regionId, String shardId) {}

  public record Route(RouteKey key, Set<String> ticketIds, Set<String> validatorIds) {
    public Route {
      ticketIds = Set.copyOf(ticketIds);
      validatorIds = Set.copyOf(validatorIds);
    }
  }

  public record TopologyProjection(
      String topologyId, long softDeadlineTick, long hardDeadlineTick, List<Route> routes) {
    public TopologyProjection {
      routes = List.copyOf(routes);
    }

    Route route(RouteKey key) {
      return routes.stream().filter(route -> route.key().equals(key)).findFirst()
          .orElseThrow(() -> new IllegalArgumentException("route is absent from topology"));
    }

    public String routingProjectionId() {
      try {
        var body = new ByteArrayOutputStream();
        try (var output = new DataOutputStream(body)) {
          output.write(new byte[] {'D', 'R', 'R', 1});
          writeText(output, topologyId);
          output.writeLong(softDeadlineTick);
          output.writeLong(hardDeadlineTick);
          var canonicalRoutes = routes.stream()
              .sorted(Comparator.comparing((Route route) -> route.key().domainId())
                  .thenComparing(route -> route.key().shardId())
                  .thenComparing(route -> route.key().regionId()))
              .toList();
          output.writeInt(canonicalRoutes.size());
          for (var route : canonicalRoutes) {
            writeText(output, route.key().domainId());
            writeText(output, route.key().regionId());
            writeText(output, route.key().shardId());
            var tickets = route.ticketIds().stream().sorted().toList();
            output.writeInt(tickets.size());
            for (var ticket : tickets) {
              writeText(output, ticket);
            }
            var validators = route.validatorIds().stream().sorted().toList();
            output.writeInt(validators.size());
            for (var validator : validators) {
              writeText(output, validator);
            }
          }
        }
        var digest = MessageDigest.getInstance("SHA-256");
        digest.update("deltareduce.006.routing-projection.v1".getBytes(StandardCharsets.US_ASCII));
        digest.update((byte) 0);
        digest.update(body.toByteArray());
        return "sha256:" + HexFormat.of().formatHex(digest.digest());
      } catch (IOException | NoSuchAlgorithmException error) {
        throw new IllegalStateException("cannot canonicalize routing projection", error);
      }
    }
  }

  public record OpaqueContribution(
      String ticketId, String domainId, String shardId, byte[] canonicalBytes) {
    public OpaqueContribution {
      canonicalBytes = Arrays.copyOf(canonicalBytes, canonicalBytes.length);
      NativeHierarchy.require(canonicalBytes.length > 0, "opaque contribution is empty");
    }

    OpaqueContribution copy() {
      return new OpaqueContribution(ticketId, domainId, shardId, canonicalBytes);
    }

    @Override
    public byte[] canonicalBytes() {
      return Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }
  }

  public record Delivery(
      long sequence, RouteKey route, OpaqueContribution contribution, int retries,
      long admittedTick) {}

  public record TelemetrySnapshot(
      long accepted, long delivered, long acknowledged, long retries,
      long backpressureRejects, long softDeadlineSignals, long hardAborts,
      long cancellations, int queued, boolean cancelled, boolean hardAborted) {}

  private record TicketShard(String ticketId, String shardId) {}

  private static final class Telemetry {
    long accepted;
    long delivered;
    long acknowledged;
    long retries;
    long backpressureRejects;
    long softDeadlineSignals;
    long hardAborts;
    long cancellations;
  }

  public static TopologyProjection projection(
      String topologyId, long softDeadlineTick, long hardDeadlineTick, Route... routes) {
    return new TopologyProjection(
        topologyId, softDeadlineTick, hardDeadlineTick, new ArrayList<>(List.of(routes)));
  }

  public static Route route(
      String domainId, String regionId, String shardId,
      Set<String> tickets, Set<String> validators) {
    return new Route(
        new RouteKey(domainId, regionId, shardId), new HashSet<>(tickets),
        new HashSet<>(validators));
  }

  private static void writeText(DataOutputStream output, String value) throws IOException {
    var bytes = value.getBytes(StandardCharsets.US_ASCII);
    NativeHierarchy.require(bytes.length == value.length() && bytes.length > 0,
        "routing projection label is outside non-empty ASCII");
    output.writeInt(bytes.length);
    output.write(bytes);
  }
}
