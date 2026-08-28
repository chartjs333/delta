package io.deltareduce.node.hierarchy;

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
import java.util.Objects;
import java.util.regex.Pattern;

/** Synchronous, bounded FFM boundary for the native hierarchy contract authority. */
@SuppressWarnings("restricted")
public final class NativeHierarchy implements AutoCloseable {
  private static final int OK = 0;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final int CONTEXT_SIZE = 168;
  private static final int MAX_TOPOLOGY_BYTES = 1_048_576;
  private static final int MAX_PROOF_BYTES = 262_144;
  private static final int MAX_EFFECT_BYTES = 512;
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);
  private static final Pattern EFFECT =
      Pattern.compile(
          "\\{\"hierarchy_proof_instance_id\":\"(sha256:[0-9a-f]{64})\","
              + "\"routing_projection_id\":\"(sha256:[0-9a-f]{64})\","
              + "\"status\":\"ACCEPT\",\"topology_id\":\"(sha256:[0-9a-f]{64})\"\\}");

  private final Arena libraryArena;
  private final MethodHandle borrowed;
  private final MethodHandle copied;

  public NativeHierarchy(Path nativeLibrary) {
    libraryArena = Arena.ofShared();
    var linker = Linker.nativeLinker();
    var lookup = SymbolLookup.libraryLookup(nativeLibrary.toAbsolutePath(), libraryArena);
    var descriptor = FunctionDescriptor.of(JAVA_INT, ADDRESS, VIEW, VIEW, ADDRESS);
    borrowed = downcall(linker, lookup, "delta_hierarchy_contract_validate_borrowed", descriptor);
    copied = downcall(linker, lookup, "delta_hierarchy_contract_validate_copy", descriptor);
  }

  public Validation validate(
      Context expectedContext, ByteBuffer canonicalTopology, ByteBuffer canonicalProof,
      boolean forceCopy) {
    Objects.requireNonNull(expectedContext, "expectedContext");
    Objects.requireNonNull(canonicalTopology, "canonicalTopology");
    Objects.requireNonNull(canonicalProof, "canonicalProof");
    require(canonicalTopology.remaining() <= MAX_TOPOLOGY_BYTES, "topology exceeds staging bound");
    require(canonicalProof.remaining() <= MAX_PROOF_BYTES, "proof exceeds staging bound");
    boolean direct = !forceCopy && canonicalTopology.isDirect() && canonicalProof.isDirect();
    try (var arena = Arena.ofConfined()) {
      var context = nativeContext(arena, expectedContext);
      var topology = memory(arena, canonicalTopology, direct);
      var proof = memory(arena, canonicalProof, direct);
      var topologyView = arena.allocate(VIEW);
      var proofView = arena.allocate(VIEW);
      setView(topologyView, topology);
      setView(proofView, proof);
      var function = direct ? borrowed : copied;
      var output = arena.allocate(OUTPUT);
      resetOutput(output);
      int first = invoke(function, context, topologyView, proofView, output);
      require(first == BUFFER_TOO_SMALL, "native hierarchy effect sizing failed");
      long required = output.get(JAVA_LONG, 16);
      require(
          required > 0 && required <= MAX_EFFECT_BYTES && output.get(JAVA_LONG, 24) == 0,
          "native hierarchy effect length is outside bounds");
      var destination = arena.allocate(required);
      output.set(ADDRESS, 0, destination);
      output.set(JAVA_LONG, 8, required);
      output.set(JAVA_LONG, 16, 0);
      output.set(JAVA_LONG, 24, 0);
      int second = invoke(function, context, topologyView, proofView, output);
      require(
          second == OK && output.get(JAVA_LONG, 16) == required
              && output.get(JAVA_LONG, 24) == required,
          "native hierarchy bounded retry failed");
      var effect = new String(destination.toArray(JAVA_BYTE), StandardCharsets.US_ASCII);
      var matcher = EFFECT.matcher(effect);
      require(matcher.matches(), "native hierarchy effect is not canonical");
      return new Validation(matcher.group(3), matcher.group(1), matcher.group(2), effect, direct);
    }
  }

  @Override
  public void close() {
    libraryArena.close();
  }

  public record Context(
      String accumulatorProofInstanceId,
      String coefficientPlanRoot,
      String fixedpointConfigId,
      String formalSemanticsId,
      String frozenInputRoot,
      String parentCheckpointId,
      String profileId,
      String roundConfigId,
      String scaleTableId,
      String shardPlanId) {
    public Context {
      for (var value : values(
          accumulatorProofInstanceId, coefficientPlanRoot, fixedpointConfigId,
          formalSemanticsId, frozenInputRoot, parentCheckpointId, profileId, roundConfigId,
          scaleTableId, shardPlanId)) {
        requireContentId(value, "hierarchy context ID");
      }
    }
  }

  public record Validation(
      String topologyId, String hierarchyProofInstanceId, String routingProjectionId,
      String canonicalEffect,
      boolean borrowedDirect) {}

  private static MemorySegment nativeContext(Arena arena, Context value) {
    var result = arena.allocate(CONTEXT_SIZE, 8);
    result.set(JAVA_INT, 0, CONTEXT_SIZE);
    result.set(JAVA_INT, 4, 0);
    int index = 0;
    for (var text : values(
        value.accumulatorProofInstanceId(), value.coefficientPlanRoot(),
        value.fixedpointConfigId(), value.formalSemanticsId(), value.frozenInputRoot(),
        value.parentCheckpointId(), value.profileId(), value.roundConfigId(), value.scaleTableId(),
        value.shardPlanId())) {
      var bytes = text.getBytes(StandardCharsets.US_ASCII);
      var segment = arena.allocate(bytes.length, 1);
      segment.copyFrom(MemorySegment.ofArray(bytes));
      long offset = 8L + 16L * index++;
      result.set(ADDRESS, offset, segment);
      result.set(JAVA_LONG, offset + 8L, bytes.length);
    }
    return result;
  }

  private static MemorySegment memory(Arena arena, ByteBuffer input, boolean direct) {
    var source = input.duplicate();
    if (direct) {
      return MemorySegment.ofBuffer(source);
    }
    var output = arena.allocate(Math.max(1, source.remaining()), 1);
    if (source.hasRemaining()) {
      var bytes = new byte[source.remaining()];
      source.get(bytes);
      output.asSlice(0, bytes.length).copyFrom(MemorySegment.ofArray(bytes));
      return output.asSlice(0, bytes.length);
    }
    return output.asSlice(0, 0);
  }

  private static int invoke(
      MethodHandle function, MemorySegment context, MemorySegment topology,
      MemorySegment proof, MemorySegment output) {
    try {
      return (int) function.invoke(context, topology, proof, output);
    } catch (Throwable error) {
      throw new IllegalStateException("native hierarchy invocation failed", error);
    }
  }

  private static void setView(MemorySegment view, MemorySegment value) {
    view.set(ADDRESS, 0, value);
    view.set(JAVA_LONG, 8, value.byteSize());
  }

  private static void resetOutput(MemorySegment output) {
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

  private static String[] values(String... values) {
    return values;
  }

  private static void requireContentId(String value, String label) {
    require(value != null && value.matches("sha256:[0-9a-f]{64}"), label + " is invalid");
  }

  static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
