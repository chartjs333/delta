package io.deltareduce.node.distribution;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicBoolean;

/** Permissioned, bounded, non-authoritative peer discovery and piece streaming. */
public final class PeerPlane {
  private PeerPlane() {}

  public record Advertisement(
      String projectId,
      String manifestId,
      String peerId,
      String endpoint,
      long leaseEpoch,
      long leaseExpiresAtTick,
      int maxStreams,
      Set<Integer> availableOrdinals,
      String requestId) {
    public Advertisement {
      DistributionModel.requireContentId(manifestId, "advertised manifest ID");
      DistributionModel.require(projectId.matches("[a-zA-Z0-9._-]{1,128}"), "invalid project ID");
      DistributionModel.require(peerId.matches("[a-zA-Z0-9._-]{1,128}"), "invalid peer ID");
      DistributionModel.require(endpoint.startsWith("loopback://"), "v1 endpoint is not permissioned");
      DistributionModel.require(leaseEpoch >= 0, "negative lease epoch");
      DistributionModel.require(maxStreams > 0 && maxStreams <= DistributionModel.MAX_STREAMS,
          "advertised stream limit is outside bounds");
      availableOrdinals = Set.copyOf(availableOrdinals);
    }
  }

  public static final class DiscoveryRegistry {
    private final Set<String> permissionedPeers;
    private final Map<String, Advertisement> latest = new HashMap<>();
    private final Set<String> requests = new HashSet<>();
    private boolean available = true;

    public DiscoveryRegistry(Set<String> permissionedPeers) {
      this.permissionedPeers = Set.copyOf(permissionedPeers);
    }

    public synchronized void publish(Advertisement advertisement, long nowTick) {
      DistributionModel.require(available, "REGISTRY_UNAVAILABLE");
      DistributionModel.require(permissionedPeers.contains(advertisement.peerId()), "PEER_UNAUTHORIZED");
      DistributionModel.require(advertisement.leaseExpiresAtTick() > nowTick, "LEASE_EXPIRED");
      DistributionModel.require(requests.add(advertisement.requestId()), "ADVERTISEMENT_REPLAY");
      var prior = latest.get(advertisement.peerId());
      DistributionModel.require(
          prior == null || advertisement.leaseEpoch() > prior.leaseEpoch(), "LEASE_EPOCH_REPLAY");
      latest.put(advertisement.peerId(), advertisement);
    }

    public synchronized List<Advertisement> snapshot(
        String projectId, String manifestId, long nowTick) {
      DistributionModel.require(available, "REGISTRY_UNAVAILABLE");
      return latest.values().stream()
          .filter(item -> item.projectId().equals(projectId))
          .filter(item -> item.manifestId().equals(manifestId))
          .filter(item -> item.leaseExpiresAtTick() > nowTick)
          .sorted(Comparator.comparing(Advertisement::peerId))
          .toList();
    }

    public synchronized void setAvailable(boolean value) {
      available = value;
    }
  }

  public record TransportEnvelope(
      String projectId,
      String manifestId,
      int ordinal,
      int declaredPayloadBytes,
      String requestId,
      String authorization,
      long deadlineTick) {
    public TransportEnvelope {
      DistributionModel.require(projectId.matches("[a-zA-Z0-9._-]{1,128}"), "invalid project ID");
      DistributionModel.requireContentId(manifestId, "transport manifest ID");
      DistributionModel.require(ordinal >= 0 && ordinal < DistributionModel.MAX_PIECES,
          "transport ordinal is outside bounds");
      DistributionModel.require(
          declaredPayloadBytes > 0 && declaredPayloadBytes <= DistributionModel.MAX_PIECE_BYTES,
          "TRANSPORT_PAYLOAD_TOO_LARGE");
      DistributionModel.require(requestId.matches("[a-zA-Z0-9._-]{1,128}"), "invalid request ID");
      DistributionModel.require(authorization.length() <= DistributionModel.MAX_TRANSPORT_HEADER_BYTES,
          "TRANSPORT_HEADER_TOO_LARGE");
    }
  }

  public static final class Cancellation {
    private final AtomicBoolean cancelled = new AtomicBoolean();

    public void cancel() {
      cancelled.set(true);
    }

    public boolean cancelled() {
      return cancelled.get();
    }
  }

  public enum Fault {
    NONE,
    CORRUPT,
    TRUNCATE,
    OVERSIZE,
    SLOW
  }

  public static final class PeerService {
    private final String projectId;
    private final String peerId;
    private final DistributionModel.Manifest manifest;
    private final CasStore cas;
    private final Telemetry telemetry;
    private final Semaphore streams;
    private final Fault fault;
    private final int faultOrdinal;

    public PeerService(
        String projectId,
        String peerId,
        DistributionModel.Manifest manifest,
        CasStore cas,
        Telemetry telemetry,
        int maxStreams,
        Fault fault,
        int faultOrdinal) {
      DistributionModel.require(maxStreams > 0 && maxStreams <= DistributionModel.MAX_STREAMS,
          "peer stream limit is outside bounds");
      this.projectId = projectId;
      this.peerId = peerId;
      this.manifest = manifest;
      this.cas = cas;
      this.telemetry = telemetry;
      streams = new Semaphore(maxStreams, true);
      this.fault = fault;
      this.faultOrdinal = faultOrdinal;
    }

    public Advertisement advertisement(
        String requestId, long leaseEpoch, long expiresAtTick) throws IOException {
      var available = new HashSet<Integer>();
      for (var piece : manifest.pieces()) {
        if (cas.hasVerifiedPiece(piece)) {
          available.add(piece.ordinal());
        }
      }
      return new Advertisement(
          projectId,
          manifest.manifestId(),
          peerId,
          "loopback://" + peerId,
          leaseEpoch,
          expiresAtTick,
          streams.availablePermits(),
          available,
          requestId);
    }

    public ByteBuf fetch(TransportEnvelope envelope, long nowTick, Cancellation cancellation)
        throws IOException {
      DistributionModel.require(
          !Thread.currentThread().getName().toLowerCase().contains("eventloop"),
          "EVENT_LOOP_BLOCKING_GUARD");
      DistributionModel.require(!cancellation.cancelled(), "CANCELLED");
      DistributionModel.require(envelope.deadlineTick() >= nowTick, "PEER_DEADLINE");
      DistributionModel.require(envelope.projectId().equals(projectId), "PROJECT_MISMATCH");
      DistributionModel.require(envelope.manifestId().equals(manifest.manifestId()),
          "MANIFEST_MISMATCH");
      DistributionModel.require(envelope.authorization().equals("permission:" + peerId),
          "PEER_UNAUTHORIZED");
      DistributionModel.require(envelope.ordinal() < manifest.pieces().size(), "ORDINAL_UNKNOWN");
      var descriptor = manifest.pieces().get(envelope.ordinal());
      DistributionModel.require(envelope.declaredPayloadBytes() == descriptor.length(),
          "DECLARED_LENGTH_MISMATCH");
      DistributionModel.require(streams.tryAcquire(), "BACKPRESSURE");
      try {
        if (fault == Fault.SLOW && descriptor.ordinal() == faultOrdinal) {
          throw new IllegalArgumentException("PEER_DEADLINE");
        }
        var bytes = cas.readVerifiedPiece(descriptor);
        if (descriptor.ordinal() == faultOrdinal) {
          switch (fault) {
            case CORRUPT -> bytes[0] ^= 1;
            case TRUNCATE -> bytes = java.util.Arrays.copyOf(bytes, bytes.length - 1);
            case OVERSIZE -> bytes = java.util.Arrays.copyOf(bytes, bytes.length + 1);
            default -> {
              // NONE/SLOW are handled elsewhere.
            }
          }
        }
        DistributionModel.require(bytes.length <= DistributionModel.MAX_PIECE_BYTES,
            "TRANSPORT_PAYLOAD_TOO_LARGE");
        var output = Unpooled.directBuffer(bytes.length).writeBytes(bytes);
        telemetry.add("peer." + peerId + ".bytes", bytes.length);
        return output;
      } finally {
        streams.release();
      }
    }

    public String peerId() {
      return peerId;
    }
  }

  public static List<PeerService> servicesFor(
      List<Advertisement> snapshot, Map<String, PeerService> services) {
    var result = new ArrayList<PeerService>();
    for (var advertisement : snapshot) {
      var service = services.get(advertisement.peerId());
      if (service != null) {
        result.add(service);
      }
    }
    return List.copyOf(result);
  }
}
