package io.deltareduce.node.certificates;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;

/** Opaque logical-tick delivery only; native state decides whether a token is stale. */
public final class CertificateTimerService {
  private final int capacity;
  private final int maximumTokenBytes;
  private final List<Timer> timers = new ArrayList<>();
  private long sequence = 1;

  public CertificateTimerService(int capacity, int maximumTokenBytes) {
    NativeCertificateVerifier.require(capacity > 0, "timer capacity must be positive");
    NativeCertificateVerifier.require(maximumTokenBytes > 0, "timer bound must be positive");
    this.capacity = capacity;
    this.maximumTokenBytes = maximumTokenBytes;
  }

  public synchronized boolean schedule(byte[] opaqueNativeToken, long deliveryTick) {
    Objects.requireNonNull(opaqueNativeToken, "opaqueNativeToken");
    NativeCertificateVerifier.require(deliveryTick >= 0, "timer tick is negative");
    NativeCertificateVerifier.require(
        opaqueNativeToken.length > 0 && opaqueNativeToken.length <= maximumTokenBytes,
        "timer token is outside bounds");
    if (timers.size() >= capacity) {
      return false;
    }
    timers.add(
        new Timer(
            sequence++, deliveryTick, Arrays.copyOf(opaqueNativeToken, opaqueNativeToken.length)));
    return true;
  }

  public synchronized int deliverReady(long logicalTick, NativeTimerSink sink) {
    Objects.requireNonNull(sink, "sink");
    timers.sort(Comparator.comparingLong(Timer::deliveryTick).thenComparingLong(Timer::sequence));
    int count = 0;
    while (!timers.isEmpty() && timers.get(0).deliveryTick() <= logicalTick) {
      var timer = timers.remove(0);
      sink.accept(Arrays.copyOf(timer.token(), timer.token().length), logicalTick);
      count++;
    }
    return count;
  }

  @FunctionalInterface
  public interface NativeTimerSink {
    void accept(byte[] opaqueNativeToken, long observedLogicalTick);
  }

  private record Timer(long sequence, long deliveryTick, byte[] token) {}
}
