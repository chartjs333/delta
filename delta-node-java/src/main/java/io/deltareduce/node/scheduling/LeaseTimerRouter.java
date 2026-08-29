package io.deltareduce.node.scheduling;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;

/** Delivers native-issued opaque timer bytes; native state decides stale/early/committed outcomes. */
public final class LeaseTimerRouter {
  private final int capacity;
  private final int maximumTokenBytes;
  private final List<Delivery> pending = new ArrayList<>();
  private long nextSequence = 1;
  private long callbacks;
  private long backpressureRejects;
  private boolean cancelled;

  public LeaseTimerRouter(int capacity, int maximumTokenBytes) {
    NativeScheduling.require(capacity > 0, "timer capacity must be positive");
    NativeScheduling.require(maximumTokenBytes > 0, "timer token bound must be positive");
    this.capacity = capacity;
    this.maximumTokenBytes = maximumTokenBytes;
  }

  public synchronized boolean schedule(byte[] opaqueNativeToken, long deliveryTick) {
    Objects.requireNonNull(opaqueNativeToken, "opaqueNativeToken");
    NativeScheduling.require(!cancelled, "timer router is cancelled");
    NativeScheduling.require(deliveryTick >= 0, "timer delivery tick is negative");
    NativeScheduling.require(
        opaqueNativeToken.length > 0 && opaqueNativeToken.length <= maximumTokenBytes,
        "opaque timer token is outside bounds");
    if (pending.size() >= capacity) {
      backpressureRejects++;
      return false;
    }
    pending.add(new Delivery(
        nextSequence++, deliveryTick, Arrays.copyOf(opaqueNativeToken, opaqueNativeToken.length)));
    return true;
  }

  public synchronized int deliverReady(long logicalTick, NativeTimerSink nativeSink) {
    Objects.requireNonNull(nativeSink, "nativeSink");
    NativeScheduling.require(!cancelled, "timer router is cancelled");
    pending.sort(Comparator.comparingLong(Delivery::deliveryTick)
        .thenComparingLong(Delivery::sequence));
    int delivered = 0;
    while (!pending.isEmpty() && pending.get(0).deliveryTick() <= logicalTick) {
      var item = pending.remove(0);
      nativeSink.accept(Arrays.copyOf(item.opaqueToken(), item.opaqueToken().length), logicalTick);
      callbacks++;
      delivered++;
    }
    return delivered;
  }

  public synchronized void cancel() {
    cancelled = true;
    pending.clear();
  }

  public synchronized SchedulingTelemetry telemetry() {
    return new SchedulingTelemetry(
        0, 0, backpressureRejects, callbacks, cancelled ? 1 : 0, pending.size(), cancelled);
  }

  @FunctionalInterface
  public interface NativeTimerSink {
    void accept(byte[] opaqueNativeToken, long observedLogicalTick);
  }

  private record Delivery(long sequence, long deliveryTick, byte[] opaqueToken) {}
}
