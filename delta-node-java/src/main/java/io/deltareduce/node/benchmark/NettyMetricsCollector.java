package io.deltareduce.node.benchmark;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** Netty-facing lifetime/backpressure counters; dashboards are not evidence authorities. */
public final class NettyMetricsCollector {
  private final ConcurrentHashMap<String, LongAdder> counters = new ConcurrentHashMap<>();

  public void add(String metric, long value) {
    BenchmarkContracts.require(
        metric != null && metric.matches("[a-z0-9_.-]{1,128}"), "invalid metric");
    BenchmarkContracts.require(value >= 0, "negative metric increment");
    counters.computeIfAbsent(metric, ignored -> new LongAdder()).add(value);
  }

  public Map<String, Long> snapshot() {
    var result = new LinkedHashMap<String, Long>();
    counters.keySet().stream().sorted().forEach(key -> result.put(key, counters.get(key).sum()));
    return Map.copyOf(result);
  }

  public void requireClean(long activeBuffers, long eventLoopBlockMicros, long queueDepth, long queueLimit) {
    BenchmarkContracts.require(activeBuffers == 0, "Netty buffer leak");
    BenchmarkContracts.require(eventLoopBlockMicros == 0, "event loop blocked");
    BenchmarkContracts.require(queueDepth >= 0 && queueDepth <= queueLimit, "backpressure bound exceeded");
  }
}
