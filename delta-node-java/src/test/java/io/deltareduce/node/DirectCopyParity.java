package io.deltareduce.node;

import java.nio.ByteBuffer;
import java.nio.file.Path;
import java.util.Arrays;

/** Proves heap/direct copies preserve DRQ1 envelopes byte-for-byte without q decoding. */
public final class DirectCopyParity {
  private DirectCopyParity() {}

  public static void main(String[] arguments) throws Exception {
    FixedPointEnvelopeConformance.require(arguments.length == 1, "expected golden fixture path");
    var envelopes = FixedPointEnvelopeConformance.loadEnvelopes(Path.of(arguments[0]));
    for (var envelope : envelopes) {
      FixedPointEnvelopeConformance.require(
          Arrays.equals(envelope, directRoundTrip(envelope)), "direct byte parity failed");
      FixedPointEnvelopeConformance.require(
          Arrays.equals(envelope, heapRoundTrip(envelope)), "heap byte parity failed");
    }
    System.out.println("direct/copy fixed-point parity passed: " + envelopes.size());
  }

  static byte[] directRoundTrip(byte[] source) {
    var direct = ByteBuffer.allocateDirect(source.length);
    direct.put(source).flip();
    var result = new byte[source.length];
    direct.get(result);
    return result;
  }

  static byte[] heapRoundTrip(byte[] source) {
    var heap = ByteBuffer.allocate(source.length);
    heap.put(source).flip();
    var result = new byte[source.length];
    heap.get(result);
    return result;
  }
}
