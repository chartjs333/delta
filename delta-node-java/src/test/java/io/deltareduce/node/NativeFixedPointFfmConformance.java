package io.deltareduce.node;

import static java.lang.foreign.ValueLayout.ADDRESS;
import static java.lang.foreign.ValueLayout.JAVA_INT;
import static java.lang.foreign.ValueLayout.JAVA_LONG;

import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemoryLayout;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.invoke.MethodHandle;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.Arrays;

/** JDK 25/26 FFM parity against the production C++ bounded DRQ1 parser. */
public final class NativeFixedPointFfmConformance {
  private static final int OK = 0;
  private static final int INVALID_ARGUMENT = 1;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);

  private NativeFixedPointFfmConformance() {}

  public static void main(String[] arguments) throws Throwable {
    FixedPointEnvelopeConformance.require(
        arguments.length == 2, "expected native library and feature-004 golden fixture");
    var linker = Linker.nativeLinker();
    try (var arena = Arena.ofConfined()) {
      var lookup = SymbolLookup.libraryLookup(Path.of(arguments[0]).toAbsolutePath(), arena);
      var descriptor = FunctionDescriptor.of(JAVA_INT, VIEW, ADDRESS);
      var borrowed = downcall(linker, lookup, "delta_fixedpoint_shard_validate_borrowed", descriptor);
      var copied = downcall(linker, lookup, "delta_fixedpoint_shard_validate_copy", descriptor);
      var envelopes = FixedPointEnvelopeConformance.loadEnvelopes(Path.of(arguments[1]));
      FixedPointEnvelopeConformance.require(envelopes.size() == 5, "expected five envelopes");
      for (var envelope : envelopes) {
        FixedPointEnvelopeConformance.require(
            Arrays.equals(envelope, validate(arena, borrowed, envelope)),
            "native borrowed boundary changed bytes");
        FixedPointEnvelopeConformance.require(
            Arrays.equals(envelope, validate(arena, copied, envelope)),
            "native copy boundary changed bytes");
      }
      var valid = envelopes.get(0);
      reject(arena, borrowed, Arrays.copyOf(valid, valid.length - 1), "truncated");
      reject(arena, copied, Arrays.copyOf(valid, valid.length + 1), "trailing");
      var corrupt = valid.clone();
      corrupt[corrupt.length - 1] ^= 1;
      reject(arena, borrowed, corrupt, "payload hash mismatch");
      var oversized = Arrays.copyOf(valid, 16);
      ByteBuffer.wrap(oversized).order(ByteOrder.LITTLE_ENDIAN).putInt(8, 65_537);
      reject(arena, copied, oversized, "oversized header");
    }
    System.out.println(
        "native fixed-point FFM compatible on JDK "
            + Runtime.version().feature()
            + ": borrowed/copy/malformed parity");
  }

  private static byte[] validate(Arena arena, MethodHandle function, byte[] source) throws Throwable {
    var input = bytes(arena, source);
    var view = arena.allocate(VIEW);
    setView(view, input);
    var output = arena.allocate(OUTPUT);
    output.set(ADDRESS, 0, MemorySegment.NULL);
    output.set(JAVA_LONG, 8, 0);
    output.set(JAVA_LONG, 16, 0);
    output.set(JAVA_LONG, 24, 0);
    FixedPointEnvelopeConformance.require(
        (int) function.invoke(view, output) == BUFFER_TOO_SMALL,
        "native fixed-point sizing did not request retry");
    var required = output.get(JAVA_LONG, 16);
    FixedPointEnvelopeConformance.require(
        required == source.length && output.get(JAVA_LONG, 24) == 0,
        "native fixed-point sizing metadata mismatch");
    var destination = arena.allocate(required);
    output.set(ADDRESS, 0, destination);
    output.set(JAVA_LONG, 8, required);
    output.set(JAVA_LONG, 16, 0);
    output.set(JAVA_LONG, 24, 0);
    FixedPointEnvelopeConformance.require(
        (int) function.invoke(view, output) == OK, "native fixed-point validation failed");
    return destination.toArray(java.lang.foreign.ValueLayout.JAVA_BYTE);
  }

  private static void reject(
      Arena arena, MethodHandle function, byte[] source, String label) throws Throwable {
    var input = bytes(arena, source);
    var view = arena.allocate(VIEW);
    setView(view, input);
    var output = arena.allocate(OUTPUT);
    output.set(ADDRESS, 0, MemorySegment.NULL);
    output.set(JAVA_LONG, 8, 0);
    output.set(JAVA_LONG, 16, 99);
    output.set(JAVA_LONG, 24, 99);
    FixedPointEnvelopeConformance.require(
        (int) function.invoke(view, output) == INVALID_ARGUMENT,
        "native boundary accepted " + label);
    FixedPointEnvelopeConformance.require(
        output.get(JAVA_LONG, 16) == 0 && output.get(JAVA_LONG, 24) == 0,
        "native rejection exposed partial output");
  }

  private static MemorySegment bytes(Arena arena, byte[] value) {
    var result = arena.allocate(value.length == 0 ? 1 : value.length);
    if (value.length != 0) {
      result.copyFrom(MemorySegment.ofArray(value));
    }
    return value.length == 0 ? result.asSlice(0, 0) : result;
  }

  private static void setView(MemorySegment view, MemorySegment value) {
    view.set(ADDRESS, 0, value);
    view.set(JAVA_LONG, 8, value.byteSize());
  }

  private static MethodHandle downcall(
      Linker linker, SymbolLookup lookup, String name, FunctionDescriptor descriptor) {
    return linker.downcallHandle(
        lookup.find(name).orElseThrow(() -> new IllegalArgumentException("missing symbol " + name)),
        descriptor);
  }
}
