package io.deltareduce.node.scheduling;

import java.nio.ByteBuffer;
import java.util.Objects;

/** Authenticated-byte collection only; every admission result comes back from native C++. */
public final class CapabilityCollector {
  private final NativeScheduling nativeScheduling;
  private final NativeScheduling.Policy policy;
  private final int maximumProfileBytes;
  private long acceptedProfiles;
  private long rejectedProfiles;

  public CapabilityCollector(
      NativeScheduling nativeScheduling,
      NativeScheduling.Policy policy,
      int maximumProfileBytes) {
    this.nativeScheduling = Objects.requireNonNull(nativeScheduling, "nativeScheduling");
    this.policy = Objects.requireNonNull(policy, "policy");
    NativeScheduling.require(maximumProfileBytes > 0, "profile bound must be positive");
    this.maximumProfileBytes = maximumProfileBytes;
  }

  public synchronized NativeScheduling.Decision collect(
      ByteBuffer authenticatedCanonicalProfile, boolean forceCopy) {
    Objects.requireNonNull(authenticatedCanonicalProfile, "authenticatedCanonicalProfile");
    NativeScheduling.require(
        authenticatedCanonicalProfile.remaining() > 0
            && authenticatedCanonicalProfile.remaining() <= maximumProfileBytes,
        "authenticated profile is outside collection bounds");
    try {
      var decision = nativeScheduling.evaluate(policy, authenticatedCanonicalProfile, forceCopy);
      acceptedProfiles++;
      return decision;
    } catch (IllegalArgumentException error) {
      rejectedProfiles++;
      throw error;
    }
  }

  public synchronized Snapshot telemetry() {
    return new Snapshot(acceptedProfiles, rejectedProfiles);
  }

  public record Snapshot(long acceptedProfiles, long rejectedProfiles) {}
}
