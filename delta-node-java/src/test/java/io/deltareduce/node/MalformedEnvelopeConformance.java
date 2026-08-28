package io.deltareduce.node;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.Arrays;

/** Bounded malformed-input parity for the opaque Java DRQ1 boundary. */
public final class MalformedEnvelopeConformance {
  private MalformedEnvelopeConformance() {}

  public static void main(String[] arguments) throws Exception {
    FixedPointEnvelopeConformance.require(arguments.length == 1, "expected golden fixture path");
    var valid = FixedPointEnvelopeConformance.loadEnvelopes(Path.of(arguments[0])).get(0);

    expectReject(Arrays.copyOf(valid, valid.length - 1), "truncated shard");
    var trailing = Arrays.copyOf(valid, valid.length + 1);
    expectReject(trailing, "trailing shard byte");

    var oversizedHeader = Arrays.copyOf(valid, 16);
    ByteBuffer.wrap(oversizedHeader).order(ByteOrder.LITTLE_ENDIAN).putInt(8, 65_537);
    expectReject(oversizedHeader, "oversized header");

    var oversizedPayload = Arrays.copyOf(valid, 16);
    ByteBuffer.wrap(oversizedPayload).order(ByteOrder.LITTLE_ENDIAN).putInt(12, 1_048_577);
    expectReject(oversizedPayload, "oversized payload");

    var corrupt = valid.clone();
    corrupt[corrupt.length - 1] ^= 1;
    expectReject(corrupt, "corrupt payload");

    var badMagic = valid.clone();
    badMagic[0] = 'X';
    expectReject(badMagic, "bad magic");

    System.out.println("malformed fixed-point envelope corpus rejected");
  }

  private static void expectReject(byte[] value, String label) throws Exception {
    try {
      FixedPointEnvelopeConformance.validate(value);
    } catch (IllegalArgumentException expected) {
      return;
    }
    throw new IllegalStateException(label + " was accepted");
  }
}
