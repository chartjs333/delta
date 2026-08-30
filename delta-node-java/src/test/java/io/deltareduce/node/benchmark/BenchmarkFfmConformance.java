package io.deltareduce.node.benchmark;

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
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;

/** JDK 25/26 measurement harness for the actual embedded benchmark C ABI. */
@SuppressWarnings("restricted")
public final class BenchmarkFfmConformance {
  private static final int OK = 0;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);

  private BenchmarkFfmConformance() {}

  public static void main(String[] arguments) {
    if (arguments.length != 1) {
      throw new IllegalArgumentException("expected native benchmark library");
    }
    BenchmarkContracts.require(
        Runtime.version().feature() == 25 || Runtime.version().feature() == 26,
        "benchmark FFM requires JDK 25 or 26");
    var linker = Linker.nativeLinker();
    try (var libraryArena = Arena.ofConfined()) {
      var lookup =
          SymbolLookup.libraryLookup(Path.of(arguments[0]).toAbsolutePath(), libraryArena);
      var echo =
          linker.downcallHandle(
              lookup
                  .find("delta_benchmark_sidecar_echo")
                  .orElseThrow(() -> new IllegalArgumentException("benchmark echo symbol missing")),
              FunctionDescriptor.of(JAVA_INT, VIEW, JAVA_LONG, ADDRESS));
      var runner = new EmbeddedFfmRunner(input -> echo(echo, input));
      byte[] request = "embedded-native-ffm".getBytes(StandardCharsets.US_ASCII);
      var result = runner.run(new ProcessProfileRunner.Request("embedded-native", request));
      BenchmarkContracts.require(!result.crashContained(), "embedded crash was marked contained");
      BenchmarkContracts.require(result.replayExact(), "embedded native replay changed bytes");
      BenchmarkContracts.require(result.restartMicros() == 0, "embedded path reported restart");
      BenchmarkContracts.require(
          result.requestBytes() == request.length && result.responseBytes() == request.length,
          "embedded byte accounting changed");
      System.out.println(
          "PROCESS_PROFILE EMBEDDED_FFM "
              + result.requestBytes()
              + " "
              + result.responseBytes()
              + " "
              + result.latencyMicros()
              + " "
              + result.replayLatencyMicros()
              + " "
              + result.restartMicros());
    }
  }

  private static byte[] echo(MethodHandle function, byte[] input) {
    try (var arena = Arena.ofConfined()) {
      var inputBytes = arena.allocate(input.length);
      inputBytes.copyFrom(MemorySegment.ofArray(input));
      var view = arena.allocate(VIEW);
      view.set(ADDRESS, 0, inputBytes);
      view.set(JAVA_LONG, 8, input.length);
      var output = arena.allocate(OUTPUT);
      output.set(ADDRESS, 0, MemorySegment.NULL);
      output.set(JAVA_LONG, 8, 0);
      output.set(JAVA_LONG, 16, 0);
      output.set(JAVA_LONG, 24, 0);
      BenchmarkContracts.require(
          (int) function.invoke(view, 8192L, output) == BUFFER_TOO_SMALL,
          "embedded output sizing failed");
      long required = output.get(JAVA_LONG, 16);
      BenchmarkContracts.require(required == input.length, "embedded output size changed");
      var outputBytes = arena.allocate(required);
      output.set(ADDRESS, 0, outputBytes);
      output.set(JAVA_LONG, 8, required);
      output.set(JAVA_LONG, 16, 0);
      output.set(JAVA_LONG, 24, 0);
      BenchmarkContracts.require(
          (int) function.invoke(view, 8192L, output) == OK, "embedded native call failed");
      BenchmarkContracts.require(
          output.get(JAVA_LONG, 24) == required, "embedded written size changed");
      return outputBytes.toArray(java.lang.foreign.ValueLayout.JAVA_BYTE);
    } catch (Throwable error) {
      throw new IllegalStateException("embedded FFM invocation failed", error);
    }
  }
}
