package io.deltareduce.node.benchmark;

/** Common embedded/sidecar runner contract with measured crash and replay outcomes. */
public interface ProcessProfileRunner {
  record Request(String requestId, byte[] canonicalBytes) {
    public Request {
      BenchmarkContracts.require(
          requestId != null && requestId.matches("[A-Za-z0-9._-]{1,128}"),
          "invalid request ID");
      BenchmarkContracts.require(canonicalBytes != null, "missing canonical bytes");
      canonicalBytes = canonicalBytes.clone();
    }

    @Override
    public byte[] canonicalBytes() {
      return canonicalBytes.clone();
    }
  }

  record Result(
      String deploymentProfile,
      String responseId,
      long latencyMicros,
      long replayLatencyMicros,
      long restartMicros,
      long requestBytes,
      long responseBytes,
      boolean crashContained,
      boolean replayExact) {
    public Result {
      BenchmarkContracts.require(
          latencyMicros >= 0
              && replayLatencyMicros >= 0
              && restartMicros >= 0
              && requestBytes >= 0
              && responseBytes >= 0,
          "negative process-profile measurement");
      BenchmarkContracts.requireContentId(responseId, "response ID");
    }
  }

  Result run(Request request);
}
