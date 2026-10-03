package io.deltareduce.node.sidecar;

import java.lang.invoke.MethodHandle;
import java.lang.reflect.Array;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Child JVM that deliberately co-fails with the test-only native qualification probe. */
public final class EmbeddedCrashProbeChild {
  private static final int MAX_CANONICAL_BYTES = 16 * 1024 * 1024;
  private static final int MAX_DIRECTORY_UTF8_BYTES = 4096;
  private static final String SYMBOL = "delta_sidecar_qualification_crash_v1";

  private EmbeddedCrashProbeChild() {}

  public static void main(String[] arguments) throws Throwable {
    require(
        arguments.length == 5,
        "usage: EmbeddedCrashProbeChild <probe-library> <directory> "
            + "<initial-state-file> <command-file> <crash-point-1..7>");
    require(Runtime.version().feature() >= 22, "embedded qualification child requires JDK 22+");
    var library = regularFile(arguments[0], "probe library");
    var directory = Path.of(arguments[1]).toAbsolutePath().normalize();
    Files.createDirectories(directory);
    var directoryBytes = directory.toString().getBytes(StandardCharsets.UTF_8);
    require(directoryBytes.length > 0 && directoryBytes.length <= MAX_DIRECTORY_UTF8_BYTES,
        "durable-directory UTF-8 is outside the probe bound");
    var initialState = boundedFile(arguments[2], "initial state");
    var command = boundedFile(arguments[3], "canonical command");
    var crashPoint = Integer.parseInt(arguments[4]);
    require(crashPoint >= 1 && crashPoint <= 7, "crash point is outside 1..7");

    var marker = SidecarQualificationRaw.canonicalBytes(
        Map.of(
            "crash_point_code", crashPoint,
            "event", "FFM_DOWNCALL_ENTER",
            "schema_version", "1.0.0",
            "symbol", SYMBOL));
    System.out.write(marker);
    System.out.write('\n');
    System.out.flush();
    invokeProbe(library, directoryBytes, initialState, command, crashPoint);
    throw new IllegalStateException("qualification probe unexpectedly returned");
  }

  private static void invokeProbe(
      Path library, byte[] directory, byte[] initialState, byte[] command, int crashPoint)
      throws Throwable {
    var arenaClass = Class.forName("java.lang.foreign.Arena");
    var memorySegmentClass = Class.forName("java.lang.foreign.MemorySegment");
    var memoryLayoutClass = Class.forName("java.lang.foreign.MemoryLayout");
    var valueLayoutClass = Class.forName("java.lang.foreign.ValueLayout");
    var symbolLookupClass = Class.forName("java.lang.foreign.SymbolLookup");
    var functionDescriptorClass = Class.forName("java.lang.foreign.FunctionDescriptor");
    var linkerClass = Class.forName("java.lang.foreign.Linker");
    var linkerOptionClass = Class.forName("java.lang.foreign.Linker$Option");

    var arena = arenaClass.getMethod("ofConfined").invoke(null);
    try {
      var directorySegment = nativeBytes(arenaClass, memorySegmentClass, arena, directory);
      var initialSegment = nativeBytes(arenaClass, memorySegmentClass, arena, initialState);
      var commandSegment = nativeBytes(arenaClass, memorySegmentClass, arena, command);

      var lookup = symbolLookupClass
          .getMethod("libraryLookup", Path.class, arenaClass)
          .invoke(null, library, arena);
      @SuppressWarnings("unchecked")
      var symbol = (Optional<Object>) symbolLookupClass.getMethod("find", String.class)
          .invoke(lookup, SYMBOL);
      require(symbol.isPresent(), "qualification probe symbol is absent: " + SYMBOL);

      var address = valueLayoutClass.getField("ADDRESS").get(null);
      var javaLong = valueLayoutClass.getField("JAVA_LONG").get(null);
      var javaInt = valueLayoutClass.getField("JAVA_INT").get(null);
      var layouts = Array.newInstance(memoryLayoutClass, 7);
      Array.set(layouts, 0, address);
      Array.set(layouts, 1, javaLong);
      Array.set(layouts, 2, address);
      Array.set(layouts, 3, javaLong);
      Array.set(layouts, 4, address);
      Array.set(layouts, 5, javaLong);
      Array.set(layouts, 6, javaInt);
      var descriptor = functionDescriptorClass
          .getMethod("ofVoid", layouts.getClass())
          .invoke(null, layouts);
      var linker = linkerClass.getMethod("nativeLinker").invoke(null);
      var options = Array.newInstance(linkerOptionClass, 0);
      var handle = (MethodHandle) linkerClass
          .getMethod(
              "downcallHandle",
              memorySegmentClass,
              functionDescriptorClass,
              options.getClass())
          .invoke(linker, symbol.orElseThrow(), descriptor, options);
      handle.invokeWithArguments(
          List.of(
              directorySegment,
              (long) directory.length,
              initialSegment,
              (long) initialState.length,
              commandSegment,
              (long) command.length,
              crashPoint));
    } finally {
      ((AutoCloseable) arena).close();
    }
  }

  private static Object nativeBytes(
      Class<?> arenaClass, Class<?> memorySegmentClass, Object arena, byte[] value)
      throws ReflectiveOperationException {
    var destination = arenaClass.getMethod("allocate", long.class, long.class)
        .invoke(arena, (long) value.length, 1L);
    var source = memorySegmentClass.getMethod("ofArray", byte[].class)
        .invoke(null, (Object) value);
    memorySegmentClass
        .getMethod(
            "copy",
            memorySegmentClass,
            long.class,
            memorySegmentClass,
            long.class,
            long.class)
        .invoke(null, source, 0L, destination, 0L, (long) value.length);
    return destination;
  }

  private static byte[] boundedFile(String value, String label) throws Exception {
    var path = regularFile(value, label);
    var size = Files.size(path);
    require(size > 0 && size <= MAX_CANONICAL_BYTES, label + " is outside the probe bound");
    return Files.readAllBytes(path);
  }

  private static Path regularFile(String value, String label) {
    var path = Path.of(value).toAbsolutePath().normalize();
    require(Files.isRegularFile(path), label + " is not a regular file");
    return path;
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
