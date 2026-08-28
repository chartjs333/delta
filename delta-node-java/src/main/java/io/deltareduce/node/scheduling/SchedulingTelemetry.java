package io.deltareduce.node.scheduling;

/** Operational counters only; this type has no admission or lease-state authority. */
public record SchedulingTelemetry(
    long accepted,
    long delivered,
    long backpressureRejects,
    long timerCallbacks,
    long cancellations,
    int queued,
    boolean cancelled) {}
