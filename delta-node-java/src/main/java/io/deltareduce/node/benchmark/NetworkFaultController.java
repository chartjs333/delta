package io.deltareduce.node.benchmark;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/** Deterministic unprivileged network decisions; no sockets or wall-clock access. */
public final class NetworkFaultController {
  public record Decision(long delayMillis, boolean dropped, boolean duplicated, boolean reordered) {}

  private final long seed;
  private final long halfRttMillis;
  private final long jitterMillis;
  private final long lossPpm;
  private final long duplicationPpm;
  private final long reorderingPpm;

  public NetworkFaultController(
      long seed,
      long rttMillis,
      long jitterMillis,
      long lossPpm,
      long duplicationPpm,
      long reorderingPpm) {
    BenchmarkContracts.require(
        seed >= 0
            && rttMillis >= 0
            && jitterMillis >= 0
            && inPpm(lossPpm)
            && inPpm(duplicationPpm)
            && inPpm(reorderingPpm),
        "invalid network profile");
    this.seed = seed;
    this.halfRttMillis = rttMillis / 2;
    this.jitterMillis = jitterMillis;
    this.lossPpm = lossPpm;
    this.duplicationPpm = duplicationPpm;
    this.reorderingPpm = reorderingPpm;
  }

  public Decision decision(long packetIndex) {
    BenchmarkContracts.require(packetIndex >= 0, "negative packet index");
    byte[] digest = digest(seed, packetIndex);
    long loss = unsignedInt(digest, 0) % 1_000_000L;
    long duplicate = unsignedInt(digest, 4) % 1_000_000L;
    long reorder = unsignedInt(digest, 8) % 1_000_000L;
    long span = 2 * jitterMillis + 1;
    long jitter = unsignedInt(digest, 12) % span - jitterMillis;
    return new Decision(
        Math.max(0, halfRttMillis + jitter),
        loss < lossPpm,
        duplicate < duplicationPpm,
        reorder < reorderingPpm);
  }

  private static boolean inPpm(long value) {
    return value >= 0 && value <= 1_000_000L;
  }

  private static long unsignedInt(byte[] value, int offset) {
    return Integer.toUnsignedLong(ByteBuffer.wrap(value, offset, 4).getInt());
  }

  private static byte[] digest(long seed, long packetIndex) {
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      return digest.digest((seed + ":" + packetIndex).getBytes(StandardCharsets.US_ASCII));
    } catch (NoSuchAlgorithmException error) {
      throw new IllegalStateException(error);
    }
  }
}
