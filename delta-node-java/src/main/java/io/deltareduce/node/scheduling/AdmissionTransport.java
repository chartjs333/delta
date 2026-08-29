package io.deltareduce.node.scheduling;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Objects;

/** Bounded opaque scheduling-byte transport; Java cannot author or repair any artifact. */
public final class AdmissionTransport {
  private final int capacity;
  private final int maximumArtifactBytes;
  private final ArrayDeque<OpaqueArtifact> queue = new ArrayDeque<>();
  private long accepted;
  private long delivered;
  private long backpressureRejects;
  private long cancellations;
  private boolean cancelled;

  public AdmissionTransport(int capacity, int maximumArtifactBytes) {
    NativeScheduling.require(capacity > 0, "transport capacity must be positive");
    NativeScheduling.require(maximumArtifactBytes > 0, "artifact bound must be positive");
    this.capacity = capacity;
    this.maximumArtifactBytes = maximumArtifactBytes;
  }

  public synchronized boolean offer(OpaqueArtifact artifact) {
    Objects.requireNonNull(artifact, "artifact");
    NativeScheduling.require(!cancelled, "transport is cancelled");
    NativeScheduling.require(
        artifact.canonicalBytes().length > 0
            && artifact.canonicalBytes().length <= maximumArtifactBytes,
        "opaque scheduling artifact is outside bounds");
    if (queue.size() >= capacity) {
      backpressureRejects++;
      return false;
    }
    queue.addLast(artifact.copy());
    accepted++;
    return true;
  }

  public synchronized OpaqueArtifact poll() {
    NativeScheduling.require(!cancelled, "transport is cancelled");
    var result = queue.pollFirst();
    if (result != null) {
      delivered++;
    }
    return result;
  }

  public synchronized void cancel() {
    cancelled = true;
    queue.clear();
    cancellations++;
  }

  public synchronized SchedulingTelemetry telemetry() {
    return new SchedulingTelemetry(
        accepted, delivered, backpressureRejects, 0, cancellations, queue.size(), cancelled);
  }

  public enum Kind {
    DECISION,
    PLAN,
    LEASE,
    TIMER_TOKEN
  }

  public record OpaqueArtifact(String contentId, Kind kind, byte[] canonicalBytes) {
    public OpaqueArtifact {
      NativeScheduling.require(
          contentId != null && contentId.matches("sha256:[0-9a-f]{64}"),
          "opaque artifact content ID is invalid");
      Objects.requireNonNull(kind, "kind");
      Objects.requireNonNull(canonicalBytes, "canonicalBytes");
      canonicalBytes = Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    @Override
    public byte[] canonicalBytes() {
      return Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    OpaqueArtifact copy() {
      return new OpaqueArtifact(contentId, kind, canonicalBytes);
    }
  }
}
