package io.deltareduce.node.certificates;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Permissioned, bounded transport for opaque native certificate/share bytes. */
public final class AuthenticatedCertificateTransport {
  private final int capacity;
  private final int maximumBytes;
  private final Set<String> permissionedPeers;
  private final Authenticator authenticator;
  private final List<Delivery> pending = new ArrayList<>();
  private long sequence = 1;
  private long authenticationRejects;
  private long backpressureRejects;
  private long dropped;

  public AuthenticatedCertificateTransport(
      int capacity,
      int maximumBytes,
      Set<String> permissionedPeers,
      Authenticator authenticator) {
    NativeCertificateVerifier.require(capacity > 0, "transport capacity must be positive");
    NativeCertificateVerifier.require(maximumBytes > 0, "transport byte bound must be positive");
    this.capacity = capacity;
    this.maximumBytes = maximumBytes;
    this.permissionedPeers = Set.copyOf(permissionedPeers);
    this.authenticator = Objects.requireNonNull(authenticator, "authenticator");
  }

  public synchronized boolean offer(Envelope envelope, long deliveryTick) {
    Objects.requireNonNull(envelope, "envelope");
    NativeCertificateVerifier.require(deliveryTick >= 0, "delivery tick is negative");
    var bytes = envelope.opaqueBytes();
    NativeCertificateVerifier.require(
        bytes.length > 0 && bytes.length <= maximumBytes, "opaque bytes are outside bounds");
    if (!permissionedPeers.contains(envelope.peerId())
        || !authenticator.authenticate(
            envelope.peerId(), bytes, envelope.authenticationTag())) {
      authenticationRejects++;
      return false;
    }
    if (pending.size() >= capacity) {
      backpressureRejects++;
      return false;
    }
    pending.add(new Delivery(sequence++, deliveryTick, envelope.copy()));
    return true;
  }

  public synchronized int deliverReady(long logicalTick, NativeSink sink) {
    Objects.requireNonNull(sink, "sink");
    pending.sort(
        Comparator.comparingLong(Delivery::deliveryTick).thenComparingLong(Delivery::sequence));
    int count = 0;
    while (!pending.isEmpty() && pending.get(0).deliveryTick() <= logicalTick) {
      var delivery = pending.remove(0);
      sink.accept(delivery.envelope().copy());
      count++;
    }
    return count;
  }

  public synchronized boolean dropNext() {
    if (pending.isEmpty()) {
      return false;
    }
    pending.remove(0);
    dropped++;
    return true;
  }

  public synchronized Telemetry telemetry() {
    return new Telemetry(authenticationRejects, backpressureRejects, dropped, pending.size());
  }

  public record Envelope(
      String peerId,
      NativeCertificateVerifier.Kind kind,
      byte[] opaqueBytes,
      byte[] authenticationTag) {
    public Envelope {
      NativeCertificateVerifier.require(
          peerId != null && peerId.matches("[A-Za-z0-9._:-]{1,128}"), "peer ID is invalid");
      Objects.requireNonNull(kind, "kind");
      Objects.requireNonNull(opaqueBytes, "opaqueBytes");
      Objects.requireNonNull(authenticationTag, "authenticationTag");
      opaqueBytes = Arrays.copyOf(opaqueBytes, opaqueBytes.length);
      authenticationTag = Arrays.copyOf(authenticationTag, authenticationTag.length);
    }

    @Override
    public byte[] opaqueBytes() {
      return Arrays.copyOf(opaqueBytes, opaqueBytes.length);
    }

    @Override
    public byte[] authenticationTag() {
      return Arrays.copyOf(authenticationTag, authenticationTag.length);
    }

    Envelope copy() {
      return new Envelope(peerId, kind, opaqueBytes, authenticationTag);
    }
  }

  public record Telemetry(
      long authenticationRejects, long backpressureRejects, long dropped, int pending) {}

  @FunctionalInterface
  public interface Authenticator {
    boolean authenticate(String peerId, byte[] opaqueBytes, byte[] authenticationTag);
  }

  @FunctionalInterface
  public interface NativeSink {
    void accept(Envelope envelope);
  }

  private record Delivery(long sequence, long deliveryTick, Envelope envelope) {}
}
