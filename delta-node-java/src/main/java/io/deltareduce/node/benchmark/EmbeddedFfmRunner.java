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
    byte[] output = Objects.requireNonNull(endpoint.execute(input.clone()), "native response");
    return new Result(
        "EMBEDDED_FFM",
        BenchmarkContracts.sha256(output),
        input.length + output.length,
        0,
        false,
        java.util.Arrays.equals(output, endpoint.execute(input.clone())));
  }
}
