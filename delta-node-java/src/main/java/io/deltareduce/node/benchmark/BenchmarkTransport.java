package io.deltareduce.node.benchmark;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;

/** Bounded opaque local benchmark transport with idempotent duplicate delivery. */
public final class BenchmarkTransport {
  private final int maximumMessageBytes;
  private final int maximumEntries;
  private final LinkedHashMap<String, byte[]> delivered = new LinkedHashMap<>();

  public BenchmarkTransport(int maximumMessageBytes, int maximumEntries) {
    BenchmarkContracts.require(
        maximumMessageBytes > 0 && maximumEntries > 0, "invalid transport bounds");
    this.maximumMessageBytes = maximumMessageBytes;
    this.maximumEntries = maximumEntries;
  }

  public synchronized byte[] deliver(String messageId, byte[] bytes) {
    BenchmarkContracts.requireContentId(messageId, "message ID");
    BenchmarkContracts.require(bytes != null && bytes.length <= maximumMessageBytes, "message too large");
    byte[] prior = delivered.get(messageId);
    if (prior != null) {
      BenchmarkContracts.require(Arrays.equals(prior, bytes), "conflicting duplicate message");
      return prior.clone();
    }
    BenchmarkContracts.require(delivered.size() < maximumEntries, "transport queue full");
    byte[] copy = bytes.clone();
    delivered.put(messageId, copy);
    return copy.clone();
  }

  public synchronized Map<String, Integer> snapshotSizes() {
    var result = new LinkedHashMap<String, Integer>();
    delivered.forEach((key, value) -> result.put(key, value.length));
    return Map.copyOf(result);
  }
}
