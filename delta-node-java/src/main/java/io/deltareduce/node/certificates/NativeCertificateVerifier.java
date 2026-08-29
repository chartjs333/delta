package io.deltareduce.node.certificates;

import static java.lang.foreign.ValueLayout.ADDRESS;
import static java.lang.foreign.ValueLayout.JAVA_BYTE;
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
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;

/** Synchronous native-only certificate inspection boundary. Java never reconstructs a QC. */
@SuppressWarnings("restricted")
public final class NativeCertificateVerifier implements AutoCloseable {
  public static final String FORMAL_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final int OK = 0;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final int CONTEXT_SIZE = 40;
  private static final int MAX_CERTIFICATE_BYTES = 4 * 1024 * 1024;
  private static final int MAX_EFFECT_BYTES = 4096;
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);

  private final Arena libraryArena;
  private final MethodHandle borrowed;
  private final MethodHandle copied;

  public NativeCertificateVerifier(Path nativeLibrary) {
    libraryArena = Arena.ofShared();
    var linker = Linker.nativeLinker();
    var lookup = SymbolLookup.libraryLookup(nativeLibrary.toAbsolutePath(), libraryArena);
    var descriptor = FunctionDescriptor.of(JAVA_INT, ADDRESS, VIEW, ADDRESS);
    borrowed = downcall(linker, lookup, "delta_certificate_inspect_borrowed", descriptor);
    copied = downcall(linker, lookup, "delta_certificate_inspect_copy", descriptor);
  }

  public Inspection inspect(
      Kind kind, String expectedContentId, ByteBuffer canonicalBytes, boolean forceCopy) {
    Objects.requireNonNull(kind, "kind");
    requireContentId(expectedContentId, "expected content ID");
    Objects.requireNonNull(canonicalBytes, "canonicalBytes");
    require(
        canonicalBytes.remaining() > 0 && canonicalBytes.remaining() <= MAX_CERTIFICATE_BYTES,
        "certificate bytes are outside bounds");
    boolean direct = !forceCopy && canonicalBytes.isDirect();
    try (var arena = Arena.ofConfined()) {
      var context = arena.allocate(CONTEXT_SIZE, 8);
      context.set(JAVA_INT, 0, CONTEXT_SIZE);
      context.set(JAVA_INT, 4, kind.code());
      setView(context, 8, ascii(arena, expectedContentId));
      setView(context, 24, ascii(arena, FORMAL_ID));
      var source = memory(arena, canonicalBytes, direct);
      var sourceView = arena.allocate(VIEW);
      setView(sourceView, 0, source);
      var output = arena.allocate(OUTPUT);
      reset(output);
      var function = direct ? borrowed : copied;
      int first = invoke(function, context, sourceView, output);
      require(first == BUFFER_TOO_SMALL, "native certificate sizing failed");
      long required = output.get(JAVA_LONG, 16);
      require(required > 0 && required <= MAX_EFFECT_BYTES, "native effect is outside bounds");
      var destination = arena.allocate(required);
      output.set(ADDRESS, 0, destination);
      output.set(JAVA_LONG, 8, required);
      output.set(JAVA_LONG, 16, 0);
      output.set(JAVA_LONG, 24, 0);
      int second = invoke(function, context, sourceView, output);
      require(
          second == OK && output.get(JAVA_LONG, 16) == required
              && output.get(JAVA_LONG, 24) == required,
          "native certificate verification failed");
      var effect = destination.toArray(JAVA_BYTE);
      var json = new String(effect, StandardCharsets.US_ASCII);
      require(
          json.contains("\"content_id\":\"" + expectedContentId + "\"")
              && json.contains("\"status\":\"ACCEPT\"")
              && json.contains("\"type_name\":\"" + kind.typeName() + "\""),
          "native certificate effect is malformed");
      return new Inspection(effect, direct);
    }
  }

  @Override
  public void close() {
    libraryArena.close();
  }

  public enum Kind {
    INPUT_SET(1, "INPUT_SET_CERTIFICATE"),
    SEED_TRANSCRIPT(2, "SEED_TRANSCRIPT"),
    NORM_EVIDENCE(3, "NORM_EVIDENCE"),
    ELIGIBILITY(4, "ELIGIBILITY_CERTIFICATE"),
    AGGREGATION_PLAN(5, "AGGREGATION_PLAN_CERTIFICATE"),
    PARAMETER_SHARD_QC(6, "PARAMETER_SHARD_QC"),
    AGGREGATE_ROOT_QC(7, "AGGREGATE_ROOT_QC"),
    APPLY_PROFILE(8, "APPLY_ARITHMETIC_PROFILE"),
    APPLY_CANDIDATE(9, "APPLY_CANDIDATE"),
    APPLY_QC(10, "APPLY_QC"),
    CURRENT_POINTER_COMMAND(11, "CURRENT_POINTER_COMMAND");

    private final int code;
    private final String typeName;

    Kind(int code, String typeName) {
      this.code = code;
      this.typeName = typeName;
    }

    int code() {
      return code;
    }

    String typeName() {
      return typeName;
    }
  }

  public record Inspection(byte[] nativeEffect, boolean borrowedDirect) {
    public Inspection {
      nativeEffect = Arrays.copyOf(nativeEffect, nativeEffect.length);
    }

    @Override
    public byte[] nativeEffect() {
      return Arrays.copyOf(nativeEffect, nativeEffect.length);
    }
  }

  private static MemorySegment ascii(Arena arena, String value) {
    var bytes = value.getBytes(StandardCharsets.US_ASCII);
    var segment = arena.allocate(bytes.length, 1);
    segment.copyFrom(MemorySegment.ofArray(bytes));
    return segment;
  }

  private static MemorySegment memory(Arena arena, ByteBuffer value, boolean direct) {
    var source = value.duplicate();
    if (direct) {
      return MemorySegment.ofBuffer(source);
    }
    var bytes = new byte[source.remaining()];
    source.get(bytes);
    var result = arena.allocate(bytes.length, 1);
    result.copyFrom(MemorySegment.ofArray(bytes));
    return result;
  }

  private static void setView(MemorySegment container, long offset, MemorySegment value) {
    container.set(ADDRESS, offset, value);
    container.set(JAVA_LONG, offset + 8, value.byteSize());
  }

  private static void reset(MemorySegment output) {
    output.set(ADDRESS, 0, MemorySegment.NULL);
    output.set(JAVA_LONG, 8, 0);
    output.set(JAVA_LONG, 16, 0);
    output.set(JAVA_LONG, 24, 0);
  }

  private static MethodHandle downcall(
      Linker linker, SymbolLookup lookup, String name, FunctionDescriptor descriptor) {
    return linker.downcallHandle(
        lookup.find(name).orElseThrow(() -> new IllegalArgumentException("missing symbol " + name)),
        descriptor);
  }

  private static int invoke(
      MethodHandle function, MemorySegment context, MemorySegment source, MemorySegment output) {
    try {
      return (int) function.invoke(context, source, output);
    } catch (Throwable error) {
      throw new IllegalStateException("native certificate invocation failed", error);
    }
  }

  public static void requireContentId(String value, String label) {
    require(value != null && value.matches("sha256:[0-9a-f]{64}"), label + " is invalid");
  }

  public static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
