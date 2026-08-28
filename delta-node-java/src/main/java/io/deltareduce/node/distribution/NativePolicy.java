package io.deltareduce.node.distribution;

import static java.lang.foreign.ValueLayout.ADDRESS;
import static java.lang.foreign.ValueLayout.JAVA_BYTE;
import static java.lang.foreign.ValueLayout.JAVA_INT;
import static java.lang.foreign.ValueLayout.JAVA_LONG;

import io.netty.buffer.ByteBuf;
import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemoryLayout;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.invoke.MethodHandle;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.regex.Pattern;

/** Sole Java entrypoint to the native certification authority. */
@SuppressWarnings("restricted")
public final class NativePolicy implements AutoCloseable {
  private static final int OK = 0;
  private static final int BUFFER_TOO_SMALL = 7;
  private static final int MAX_EFFECT_BYTES = 4_096;
  private static final MemoryLayout VIEW = MemoryLayout.structLayout(ADDRESS, JAVA_LONG);
  private static final MemoryLayout OUTPUT =
      MemoryLayout.structLayout(ADDRESS, JAVA_LONG, JAVA_LONG, JAVA_LONG);
  private static final Pattern EFFECT =
      Pattern.compile(
          "\\{\"certificate_policy_id\":\"([^\"]*)\",\"code\":\"([A-Z0-9_]+)\","
              + "\"formal_action_id\":\"ACT-PUBLISH\",\"manifest_id\":\"([^\"]*)\","
              + "\"status\":\"(ACCEPT|REJECT)\"\\}");

  private final Arena libraryArena;
  private final MethodHandle borrowed;
  private final MethodHandle copied;

  public NativePolicy(Path nativeLibrary) {
    libraryArena = Arena.ofShared();
    var linker = Linker.nativeLinker();
    var lookup = SymbolLookup.libraryLookup(nativeLibrary.toAbsolutePath(), libraryArena);
    var descriptor = FunctionDescriptor.of(JAVA_INT, VIEW, VIEW, JAVA_BYTE, ADDRESS);
    borrowed = downcall(linker, lookup, "delta_distribution_policy_evaluate_borrowed", descriptor);
    copied = downcall(linker, lookup, "delta_distribution_policy_evaluate_copy", descriptor);
  }

  public NativeDecision evaluate(
      ByteBuf canonicalManifest,
      ByteBuf canonicalCertificate,
      boolean requestMakeCurrent,
      boolean forceCopy) {
    DistributionModel.require(
        canonicalManifest.readableBytes() <= DistributionModel.MAX_MANIFEST_BYTES,
        "manifest exceeds Java staging bound");
    DistributionModel.require(
        canonicalCertificate.readableBytes() <= 65_536,
        "certificate exceeds Java staging bound");
    var direct =
        !forceCopy
            && canonicalManifest.isDirect()
            && canonicalManifest.nioBufferCount() == 1
            && canonicalCertificate.isDirect()
            && canonicalCertificate.nioBufferCount() == 1;
    canonicalManifest.retain();
    canonicalCertificate.retain();
    try (var arena = Arena.ofConfined()) {
      var manifest = memory(arena, canonicalManifest, direct);
      var certificate = memory(arena, canonicalCertificate, direct);
      var manifestView = arena.allocate(VIEW);
      var certificateView = arena.allocate(VIEW);
      setView(manifestView, manifest);
      setView(certificateView, certificate);
      var function = direct ? borrowed : copied;
      var output = arena.allocate(OUTPUT);
      resetOutput(output);
      int first;
      try {
        first =
            (int)
                function.invoke(
                    manifestView,
                    certificateView,
                    (byte) (requestMakeCurrent ? 1 : 0),
                    output);
      } catch (Throwable error) {
        throw new IllegalStateException("native certification invocation failed", error);
      }
      DistributionModel.require(first == BUFFER_TOO_SMALL, "native effect sizing failed");
      var required = output.get(JAVA_LONG, 16);
      DistributionModel.require(
          required > 0 && required <= MAX_EFFECT_BYTES && output.get(JAVA_LONG, 24) == 0,
          "native effect length is outside bounds");
      var destination = arena.allocate(required);
      output.set(ADDRESS, 0, destination);
      output.set(JAVA_LONG, 8, required);
      output.set(JAVA_LONG, 16, 0);
      output.set(JAVA_LONG, 24, 0);
      int second;
      try {
        second =
            (int)
                function.invoke(
                    manifestView,
                    certificateView,
                    (byte) (requestMakeCurrent ? 1 : 0),
                    output);
      } catch (Throwable error) {
        throw new IllegalStateException("native certification retry failed", error);
      }
      DistributionModel.require(
          second == OK && output.get(JAVA_LONG, 16) == required &&
              output.get(JAVA_LONG, 24) == required,
          "native certification returned an invalid status/effect");
      var effect = new String(destination.toArray(JAVA_BYTE), StandardCharsets.US_ASCII);
      return NativeDecision.fromNative(effect, direct);
    } finally {
      canonicalCertificate.release();
      canonicalManifest.release();
    }
  }

  @Override
  public void close() {
    libraryArena.close();
  }

  public static final class NativeDecision {
    private final boolean accepted;
    private final String code;
    private final String manifestId;
    private final String policyId;
    private final String canonicalEffect;
    private final boolean borrowedDirect;

    private NativeDecision(
        boolean accepted,
        String code,
        String manifestId,
        String policyId,
        String canonicalEffect,
        boolean borrowedDirect) {
      this.accepted = accepted;
      this.code = code;
      this.manifestId = manifestId;
      this.policyId = policyId;
      this.canonicalEffect = canonicalEffect;
      this.borrowedDirect = borrowedDirect;
    }

    private static NativeDecision fromNative(String effect, boolean direct) {
      var matcher = EFFECT.matcher(effect);
      DistributionModel.require(matcher.matches(), "native effect is not canonical");
      var accepted = matcher.group(4).equals("ACCEPT");
      DistributionModel.require(accepted == matcher.group(2).equals("OK"), "native effect is incoherent");
      if (accepted) {
        DistributionModel.requireContentId(matcher.group(1), "native policy ID");
        DistributionModel.requireContentId(matcher.group(3), "native manifest ID");
      }
      return new NativeDecision(
          accepted, matcher.group(2), matcher.group(3), matcher.group(1), effect, direct);
    }

    public boolean accepted() {
      return accepted;
    }

    public String code() {
      return code;
    }

    public String manifestId() {
      return manifestId;
    }

    public String policyId() {
      return policyId;
    }

    public String canonicalEffect() {
      return canonicalEffect;
    }

    public boolean borrowedDirect() {
      return borrowedDirect;
    }
  }

  private static MemorySegment memory(Arena arena, ByteBuf input, boolean direct) {
    if (direct) {
      return MemorySegment.ofBuffer(
          input.nioBuffer(input.readerIndex(), input.readableBytes()));
    }
    var result = arena.allocate(Math.max(1, input.readableBytes()));
    if (input.isReadable()) {
      var bytes = new byte[input.readableBytes()];
      input.getBytes(input.readerIndex(), bytes);
      result.asSlice(0, bytes.length).copyFrom(MemorySegment.ofArray(bytes));
      return result.asSlice(0, bytes.length);
    }
    return result.asSlice(0, 0);
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
}
