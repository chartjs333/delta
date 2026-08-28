package io.deltareduce.node.distribution;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** Structured, non-authoritative distribution telemetry. */
public final class Telemetry {
  private final ConcurrentHashMap<String, LongAdder> counters = new ConcurrentHashMap<>();

  public void add(String metric, long value) {
    DistributionModel.require(metric.matches("[a-z0-9_.-]{1,128}"), "invalid metric name");
    DistributionModel.require(value >= 0, "negative metric increment");
    counters.computeIfAbsent(metric, ignored -> new LongAdder()).add(value);
  }

  public void increment(String metric) {
    add(metric, 1);
  }

  public Map<String, Long> snapshot() {
    var result = new LinkedHashMap<String, Long>();
    counters.keySet().stream().sorted().forEach(key -> result.put(key, counters.get(key).sum()));
    return Map.copyOf(result);
  }
}
