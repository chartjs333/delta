package io.deltareduce.node;

import static java.lang.foreign.ValueLayout.ADDRESS;
import static java.lang.foreign.ValueLayout.JAVA_INT;
import static java.lang.foreign.ValueLayout.JAVA_LONG;
import static java.lang.foreign.ValueLayout.JAVA_SHORT;

import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemoryLayout;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.invoke.MethodHandle;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.regex.Pattern;

/** JDK 25/26 FFM conformance harness for the frozen feature-003 C ABI. */
public final class NativeRuntimeFfmConformance {
  private static final int OK = 0;
  private static final int FORMAL_MISMATCH = 5;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final int DESCRIPTOR_SIZE = 64;
  private static final int OPEN_OPTIONS_SIZE = 128;
  private static final String SCHEMA_VERSION = "1.0.0";
  private static final String PROTOCOL_VERSION = "003.1.0";
  private static final String FORMAL_SEMANTICS_ID =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  private static final String BUILD_ID =
      "sha256:1616161616161616161616161616161616161616161616161616161616161616";
  private static final String SCHEMA_SET_ID =
      "sha256:1717171717171717171717171717171717171717171717171717171717171717";
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);
  private static final MemoryLayout DESCRIPTOR =
      MemoryLayout.structLayout(
          JAVA_INT,
          JAVA_SHORT,
          JAVA_SHORT,
          JAVA_LONG,
          ADDRESS,
          ADDRESS,
          ADDRESS,
          ADDRESS,
          ADDRESS,
          ADDRESS);
  private static final MemoryLayout OPEN_OPTIONS =
      MemoryLayout.structLayout(
          JAVA_INT,
          JAVA_INT,
          VIEW,
          VIEW,
          JAVA_SHORT,
          JAVA_SHORT,
          JAVA_INT,
          VIEW,
          VIEW,
          VIEW,
          VIEW,
          VIEW);

  private NativeRuntimeFfmConformance() {}

  public static void main(String[] arguments) throws Throwable {
    if (arguments.length != 3) {
      throw new IllegalArgumentException("expected library, golden fixture and runtime directory");
    }
    require(DESCRIPTOR.byteSize() == DESCRIPTOR_SIZE, "descriptor layout size mismatch");
    require(OPEN_OPTIONS.byteSize() == OPEN_OPTIONS_SIZE, "open-options layout size mismatch");
    require(OUTPUT.byteSize() == 32, "output-buffer layout size mismatch");

    var fixture = Files.readString(Path.of(arguments[1]), StandardCharsets.US_ASCII);
    var initialState = golden(fixture, 5);
    var command = golden(fixture, 6);
    var runtimeDirectory = Path.of(arguments[2]).toAbsolutePath();
    Files.createDirectories(runtimeDirectory);

    var linker = Linker.nativeLinker();
    try (var arena = Arena.ofConfined()) {
      var lookup = SymbolLookup.libraryLookup(Path.of(arguments[0]).toAbsolutePath(), arena);
      var descriptorFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_descriptor",
              FunctionDescriptor.of(JAVA_INT, JAVA_INT, ADDRESS));
      var openFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_open",
              FunctionDescriptor.of(JAVA_INT, ADDRESS, ADDRESS));
      var borrowedFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_submit_borrowed",
              FunctionDescriptor.of(JAVA_INT, ADDRESS, VIEW, ADDRESS));
      var copyFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_submit_copy",
              FunctionDescriptor.of(JAVA_INT, ADDRESS, VIEW, ADDRESS));
      var snapshotFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_snapshot",
              FunctionDescriptor.of(JAVA_INT, ADDRESS));
      var releaseFunction =
          downcall(
              linker,
              lookup,
              "delta_runtime_release",
              FunctionDescriptor.of(JAVA_INT, ADDRESS));

      verifyDescriptor(arena, descriptorFunction);
      verifyFormalMismatch(arena, openFunction, runtimeDirectory.resolve("mismatch"), initialState);

      var options = options(arena, runtimeDirectory.resolve("valid"), initialState, FORMAL_SEMANTICS_ID);
      var handlePointer = arena.allocate(ADDRESS);
      handlePointer.set(ADDRESS, 0, MemorySegment.NULL);
      require((int) openFunction.invoke(options, handlePointer) == OK, "FFM runtime open failed");
      var handle = handlePointer.get(ADDRESS, 0);
      require(!handle.equals(MemorySegment.NULL), "FFM runtime open returned a null handle");

      byte[] borrowedEffect;
      try (var callArena = Arena.ofConfined()) {
        var directCommand = bytes(callArena, command);
        borrowedEffect = submit(callArena, borrowedFunction, handle, directCommand);
      }
      require((int) snapshotFunction.invoke(handle) == OK, "snapshot after borrowed lifetime failed");
      byte[] copiedEffect;
      try (var callArena = Arena.ofConfined()) {
        var boundedCopy = bytes(callArena, Arrays.copyOf(command, command.length));
        copiedEffect = submit(callArena, copyFunction, handle, boundedCopy);
      }
      require(Arrays.equals(borrowedEffect, copiedEffect), "direct/copy effect bytes differ");
      require((int) snapshotFunction.invoke(handle) == OK, "FFM snapshot failed");
      require((int) releaseFunction.invoke(handlePointer) == OK, "FFM release failed");
      require(handlePointer.get(ADDRESS, 0).equals(MemorySegment.NULL), "release did not clear handle");
      require((int) releaseFunction.invoke(handlePointer) == OK, "repeated FFM release failed");
    }
    System.out.println(
        "native runtime FFM compatible on JDK " + Runtime.version().feature() + ": exact effects");
  }

  private static void verifyDescriptor(Arena arena, MethodHandle function) throws Throwable {
    var output = arena.allocate(DESCRIPTOR);
    require((int) function.invoke(DESCRIPTOR_SIZE, output) == OK, "descriptor call failed");
    require(output.get(JAVA_INT, 0) == DESCRIPTOR_SIZE, "descriptor size mismatch");
    require(output.get(JAVA_SHORT, 4) == 1, "ABI major mismatch");
    require(output.get(JAVA_SHORT, 6) == 0, "ABI minor mismatch");
    require(cString(output.get(ADDRESS, 32)).equals(FORMAL_SEMANTICS_ID), "formal ID mismatch");
    require(cString(output.get(ADDRESS, 40)).equals(BUILD_ID), "build ID mismatch");
    require(cString(output.get(ADDRESS, 48)).equals(SCHEMA_SET_ID), "schema-set ID mismatch");
  }

  private static void verifyFormalMismatch(
      Arena arena, MethodHandle open, Path directory, byte[] initialState) throws Throwable {
    var wrong =
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    var options = options(arena, directory, initialState, wrong);
    var handle = arena.allocate(ADDRESS);
    handle.set(ADDRESS, 0, MemorySegment.NULL);
    require((int) open.invoke(options, handle) == FORMAL_MISMATCH, "formal mismatch was accepted");
    require(handle.get(ADDRESS, 0).equals(MemorySegment.NULL), "mismatch exposed partial handle");
  }

  private static MemorySegment options(
      Arena arena, Path directory, byte[] initialState, String formalId) {
    var result = arena.allocate(OPEN_OPTIONS);
    result.set(JAVA_INT, 0, OPEN_OPTIONS_SIZE);
    result.set(JAVA_INT, 4, 64);
    setView(result, 8, bytes(arena, directory.toString().getBytes(StandardCharsets.UTF_8)));
    setView(result, 24, bytes(arena, initialState));
    result.set(JAVA_SHORT, 40, (short) 1);
    result.set(JAVA_SHORT, 42, (short) 0);
    result.set(JAVA_INT, 44, 0);
    setView(result, 48, bytes(arena, SCHEMA_VERSION.getBytes(StandardCharsets.US_ASCII)));
    setView(result, 64, bytes(arena, PROTOCOL_VERSION.getBytes(StandardCharsets.US_ASCII)));
    setView(result, 80, bytes(arena, formalId.getBytes(StandardCharsets.US_ASCII)));
    setView(result, 96, bytes(arena, BUILD_ID.getBytes(StandardCharsets.US_ASCII)));
    setView(result, 112, bytes(arena, SCHEMA_SET_ID.getBytes(StandardCharsets.US_ASCII)));
    return result;
  }

  private static byte[] submit(
      Arena arena, MethodHandle function, MemorySegment handle, MemorySegment command)
      throws Throwable {
    var commandView = arena.allocate(VIEW);
    setView(commandView, 0, command);
    var output = arena.allocate(OUTPUT);
    output.set(ADDRESS, 0, MemorySegment.NULL);
    output.set(JAVA_LONG, 8, 0);
    output.set(JAVA_LONG, 16, 0);
    output.set(JAVA_LONG, 24, 0);
    require((int) function.invoke(handle, commandView, output) == BUFFER_TOO_SMALL,
        "FFM output sizing did not request retry");
    var required = output.get(JAVA_LONG, 16);
    require(required > 0 && output.get(JAVA_LONG, 24) == 0, "FFM sizing exposed partial bytes");
    var bytes = arena.allocate(required);
    output.set(ADDRESS, 0, bytes);
    output.set(JAVA_LONG, 8, required);
    output.set(JAVA_LONG, 16, 0);
    output.set(JAVA_LONG, 24, 0);
    require((int) function.invoke(handle, commandView, output) == OK, "FFM output retry failed");
    require(output.get(JAVA_LONG, 24) == required, "FFM written length mismatch");
    return bytes.toArray(java.lang.foreign.ValueLayout.JAVA_BYTE);
  }

  private static void setView(MemorySegment target, long offset, MemorySegment value) {
    target.set(ADDRESS, offset, value);
    target.set(JAVA_LONG, offset + 8, value.byteSize());
  }

  private static MemorySegment bytes(Arena arena, byte[] value) {
    var result = arena.allocate(value.length == 0 ? 1 : value.length);
    if (value.length != 0) {
      result.copyFrom(MemorySegment.ofArray(value));
    }
    return value.length == 0 ? result.asSlice(0, 0) : result;
  }

  private static String cString(MemorySegment address) {
    return address.reinterpret(1024).getString(0);
  }

  private static MethodHandle downcall(
      Linker linker, SymbolLookup lookup, String name, FunctionDescriptor descriptor) {
    return linker.downcallHandle(
        lookup.find(name).orElseThrow(() -> new IllegalArgumentException("missing symbol " + name)),
        descriptor);
  }

  private static byte[] golden(String fixture, int typeCode) {
    var pattern =
        Pattern.compile(
            "\\\"envelope_hex\\\":\\\"([0-9a-f]+)\\\","
                + "\\\"envelope_sha256\\\":\\\"[0-9a-f]+\\\","
                + "\\\"type_code\\\":"
                + typeCode);
    var matcher = pattern.matcher(fixture);
    require(matcher.find(), "golden type " + typeCode + " is missing");
    var result = HexFormat.of().parseHex(matcher.group(1));
    require(!matcher.find(), "golden type " + typeCode + " is duplicated");
    return result;
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }
}
