package io.deltareduce.node.qlora;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** Operational byte/cache counters with no semantic decision fields. */
public final class QloraTelemetry {
  private final ConcurrentHashMap<String, LongAdder> counters = new ConcurrentHashMap<>();

  public void add(String metric, long value) {
    QloraContracts.require(metric.matches("[a-z0-9_.-]{1,128}"), "invalid metric name");
    QloraContracts.require(value >= 0, "negative telemetry increment");
    counters.computeIfAbsent(metric, ignored -> new LongAdder()).add(value);
  }

  public Map<String, Long> snapshot() {
    var result = new LinkedHashMap<String, Long>();
    counters.keySet().stream().sorted().forEach(key -> result.put(key, counters.get(key).sum()));
    return Map.copyOf(result);
  }
}
