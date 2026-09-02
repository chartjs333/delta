package io.deltareduce.node.benchmark;

import java.util.Objects;

/** Synchronous borrowed-memory benchmark path; native failures share Java process blast radius. */
public final class EmbeddedFfmRunner implements ProcessProfileRunner {
  @FunctionalInterface
  public interface NativeEndpoint {
    byte[] execute(byte[] canonicalBytes);
  }

  private final NativeEndpoint endpoint;

  public EmbeddedFfmRunner(NativeEndpoint endpoint) {
    this.endpoint = Objects.requireNonNull(endpoint, "endpoint");
  }

  @Override
  public Result run(Request request) {
    byte[] input = request.canonicalBytes();
    long firstStart = System.nanoTime();
    byte[] output = Objects.requireNonNull(endpoint.execute(input.clone()), "native response");
    long firstMicros = elapsedMicros(firstStart);
    long replayStart = System.nanoTime();
    byte[] replay = Objects.requireNonNull(endpoint.execute(input.clone()), "native replay response");
    long replayMicros = elapsedMicros(replayStart);
    return new Result(
        "EMBEDDED_FFM",
        BenchmarkContracts.sha256(output),
        firstMicros,
        replayMicros,
        0,
        input.length,
        output.length,
        false,
        java.util.Arrays.equals(output, replay));
  }

  private static long elapsedMicros(long startNanos) {
    return Math.max(1, (System.nanoTime() - startNanos + 999) / 1_000);
  }
}
