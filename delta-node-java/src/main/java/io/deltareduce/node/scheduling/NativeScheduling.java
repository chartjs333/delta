package io.deltareduce.node.scheduling;

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
import java.util.List;
import java.util.Objects;
import java.util.regex.Pattern;

/** Synchronous bounded FFM boundary; the capability decision is authored only by native C++. */
@SuppressWarnings("restricted")
public final class NativeScheduling implements AutoCloseable {
  private static final int OK = 0;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final int POLICY_SIZE = 184;
  private static final int MAX_PROFILE_BYTES = 256 * 1024;
  private static final int MAX_DECISION_BYTES = 4096;
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);
  private static final Pattern DECISION =
      Pattern.compile(
          "\\{\"allowed_domain_ids\":\\[[^]]*],"
              + "\"capability_profile_id\":\"sha256:[0-9a-f]{64}\","
              + "\"decision_tick\":[0-9]+,\"eligibility_policy_id\":"
              + "\"sha256:[0-9a-f]{64}\",\"eligible\":(?:true|false),"
              + "\"formal_semantics_id\":\"sha256:[0-9a-f]{64}\","
              + "\"max_concurrent_leases\":[0-9]+,\"reason_codes\":\\[[^]]+],"
              + "\"region_route\":\"[A-Za-z0-9._:-]+\","
              + "\"round_config_id\":\"sha256:[0-9a-f]{64}\","
              + "\"schema_version\":\"1.0.0\","
              + "\"type_name\":\"ELIGIBILITY_DECISION\","
              + "\"worker_id\":\"[A-Za-z0-9._:-]+\"\\}");

  private final Arena libraryArena;
  private final MethodHandle borrowed;
  private final MethodHandle copied;

  public NativeScheduling(Path nativeLibrary) {
    libraryArena = Arena.ofShared();
    var linker = Linker.nativeLinker();
    var lookup = SymbolLookup.libraryLookup(nativeLibrary.toAbsolutePath(), libraryArena);
    var descriptor = FunctionDescriptor.of(JAVA_INT, ADDRESS, VIEW, ADDRESS);
    borrowed = downcall(
        linker, lookup, "delta_scheduling_capability_evaluate_borrowed", descriptor);
    copied = downcall(linker, lookup, "delta_scheduling_capability_evaluate_copy", descriptor);
  }

  public Decision evaluate(Policy policy, ByteBuffer canonicalProfile, boolean forceCopy) {
    Objects.requireNonNull(policy, "policy");
    Objects.requireNonNull(canonicalProfile, "canonicalProfile");
    require(canonicalProfile.remaining() > 0, "capability profile is empty");
    require(canonicalProfile.remaining() <= MAX_PROFILE_BYTES, "capability profile exceeds bound");
    boolean direct = !forceCopy && canonicalProfile.isDirect();
    try (var arena = Arena.ofConfined()) {
      var nativePolicy = nativePolicy(arena, policy);
      var profile = memory(arena, canonicalProfile, direct);
      var profileView = arena.allocate(VIEW);
      setView(profileView, profile);
      var output = arena.allocate(OUTPUT);
      resetOutput(output);
      var function = direct ? borrowed : copied;
      int first = invoke(function, nativePolicy, profileView, output);
      require(first == BUFFER_TOO_SMALL, "native scheduling decision sizing failed");
      long required = output.get(JAVA_LONG, 16);
      require(
          required > 0 && required <= MAX_DECISION_BYTES && output.get(JAVA_LONG, 24) == 0,
          "native scheduling decision length is outside bounds");
      var destination = arena.allocate(required);
      output.set(ADDRESS, 0, destination);
      output.set(JAVA_LONG, 8, required);
      output.set(JAVA_LONG, 16, 0);
      output.set(JAVA_LONG, 24, 0);
      int second = invoke(function, nativePolicy, profileView, output);
      require(
          second == OK && output.get(JAVA_LONG, 16) == required
              && output.get(JAVA_LONG, 24) == required,
          "native scheduling bounded retry failed");
      var bytes = destination.toArray(JAVA_BYTE);
      var canonical = new String(bytes, StandardCharsets.US_ASCII);
      require(DECISION.matcher(canonical).matches(), "native scheduling decision is not canonical");
      return new Decision(bytes, canonical, direct);
    }
  }

  @Override
  public void close() {
    libraryArena.close();
  }

  public record Policy(
      String arithmeticProfileId,
      String parameterSchemaId,
      String roundConfigId,
      String eligibilityPolicyId,
      String modelMode,
      List<String> allowedDomainIds,
      List<String> allowedRegionIds,
      List<String> allowedSoftwareBuildIds,
      List<String> trustedSignatureIds,
      long decisionTick,
      long identityEpoch,
      long minimumMemoryBytes,
      long minimumSampleCount) {
    public Policy {
      requireContentId(arithmeticProfileId, "arithmetic profile ID");
      requireContentId(parameterSchemaId, "parameter schema ID");
      requireContentId(roundConfigId, "round config ID");
      requireContentId(eligibilityPolicyId, "eligibility policy ID");
      require(modelMode != null && !modelMode.isBlank(), "model mode is empty");
      allowedDomainIds = canonicalLabels(allowedDomainIds, "allowed domains");
      allowedRegionIds = canonicalLabels(allowedRegionIds, "allowed regions");
      allowedSoftwareBuildIds = canonicalIds(allowedSoftwareBuildIds, "software builds");
      trustedSignatureIds = canonicalIds(trustedSignatureIds, "trusted signatures");
      require(
          decisionTick >= 0 && identityEpoch >= 0 && minimumMemoryBytes >= 0
              && minimumSampleCount > 0,
          "eligibility numeric policy is invalid");
    }
  }

  public record Decision(byte[] canonicalBytes, String canonicalJson, boolean borrowedDirect) {
    public Decision {
      canonicalBytes = Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }

    @Override
    public byte[] canonicalBytes() {
      return Arrays.copyOf(canonicalBytes, canonicalBytes.length);
    }
  }

  private static MemorySegment nativePolicy(Arena arena, Policy value) {
    var result = arena.allocate(POLICY_SIZE, 8);
    result.set(JAVA_INT, 0, POLICY_SIZE);
    result.set(JAVA_INT, 4, 0);
    var values = new String[] {
      value.arithmeticProfileId(),
      value.parameterSchemaId(),
      value.roundConfigId(),
      value.eligibilityPolicyId(),
      value.modelMode(),
      String.join(",", value.allowedDomainIds()),
      String.join(",", value.allowedRegionIds()),
      String.join(",", value.allowedSoftwareBuildIds()),
      String.join(",", value.trustedSignatureIds())
    };
    for (int index = 0; index < values.length; ++index) {
      var bytes = values[index].getBytes(StandardCharsets.US_ASCII);
      var segment = arena.allocate(bytes.length, 1);
      segment.copyFrom(MemorySegment.ofArray(bytes));
      long offset = 8L + 16L * index;
      result.set(ADDRESS, offset, segment);
      result.set(JAVA_LONG, offset + 8L, bytes.length);
    }
    result.set(JAVA_LONG, 152, value.decisionTick());
    result.set(JAVA_LONG, 160, value.identityEpoch());
    result.set(JAVA_LONG, 168, value.minimumMemoryBytes());
    result.set(JAVA_LONG, 176, value.minimumSampleCount());
    return result;
  }

  private static MemorySegment memory(Arena arena, ByteBuffer input, boolean direct) {
    var source = input.duplicate();
    if (direct) {
      return MemorySegment.ofBuffer(source);
    }
    var output = arena.allocate(source.remaining(), 1);
    var bytes = new byte[source.remaining()];
    source.get(bytes);
    output.copyFrom(MemorySegment.ofArray(bytes));
    return output;
  }

  private static int invoke(
      MethodHandle function, MemorySegment policy, MemorySegment profile, MemorySegment output) {
    try {
      return (int) function.invoke(policy, profile, output);
    } catch (Throwable error) {
      throw new IllegalStateException("native scheduling invocation failed", error);
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

  private static List<String> canonicalLabels(List<String> values, String label) {
    require(values != null && !values.isEmpty(), label + " is empty");
    var copy = List.copyOf(values);
    require(copy.stream().allMatch(value -> value.matches("[A-Za-z0-9._:-]{1,128}")),
        label + " contains an invalid label");
    require(copy.stream().sorted().toList().equals(copy) && copy.stream().distinct().count() == copy.size(),
        label + " is not canonical");
    return copy;
  }

  private static List<String> canonicalIds(List<String> values, String label) {
    require(values != null && !values.isEmpty(), label + " is empty");
    var copy = List.copyOf(values);
    copy.forEach(value -> requireContentId(value, label));
    require(copy.stream().sorted().toList().equals(copy) && copy.stream().distinct().count() == copy.size(),
        label + " is not canonical");
    return copy;
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
