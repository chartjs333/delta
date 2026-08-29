package io.deltareduce.node.qlora;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;

/** Offline cache/transport/composition conformance with exact byte accounting. */
public final class QloraConformance {
  private QloraConformance() {}

  public static void main(String[] arguments) throws Exception {
    var root = Files.createTempDirectory("delta-009-java-");
    try {
      testCacheTransportComposition(root);
      System.out.println(
          "QLoRA Java conformance passed on JDK "
              + Runtime.version().feature()
              + ": zero-base-refetch/native-auth/resume/license");
    } finally {
      try (var paths = Files.walk(root)) {
        paths.sorted(Comparator.reverseOrder()).forEach(QloraConformance::delete);
      }
    }
  }

  private static void testCacheTransportComposition(Path root) throws Exception {
    var context = new QloraContracts.CertifiedContext(id('1'), id('2'), id('3'), id('4'), id('5'), id('6'));
    var baseBytes = "certified-base".getBytes(StandardCharsets.US_ASCII);
    var tokenizerBytes = "certified-tokenizer".getBytes(StandardCharsets.US_ASCII);
    var profileBytes = "certified-nf4-profile".getBytes(StandardCharsets.US_ASCII);
    var objects = new HashMap<String, BaseObjectCache.BaseArtifact>();
    objects.put(
        context.baseModelManifestId(),
        artifact(
            BaseObjectCache.Kind.BASE,
            context.baseModelManifestId(),
            QloraContracts.BASE_MEDIA,
            "MIT",
            true,
            baseBytes));
    objects.put(
        context.tokenizerHash(),
        artifact(
            BaseObjectCache.Kind.TOKENIZER,
            context.tokenizerHash(),
            QloraContracts.TOKENIZER_MEDIA,
            "MIT",
            true,
            tokenizerBytes));
    objects.put(
        context.quantizedBaseProfileId(),
        artifact(
            BaseObjectCache.Kind.QUANTIZATION_PROFILE,
            context.quantizedBaseProfileId(),
            QloraContracts.PROFILE_MEDIA,
            "MIT",
            true,
            profileBytes));
    var adapterOne = "adapter-one".getBytes(StandardCharsets.US_ASCII);
    var adapterTwo = "adapter-two".getBytes(StandardCharsets.US_ASCII);
    var adapters = Map.of(id('7'), adapterOne, id('8'), adapterTwo);
    var source = new MapSource(objects, adapters);
    var telemetry = new QloraTelemetry();
    var cache = new BaseObjectCache(root.resolve("base-cache"), 1_000_000);
    var transport = new AdapterTransport(cache, root.resolve("adapters"), telemetry);

    var firstEnvelope = envelope(context, id('7'), id('9'), adapterOne);
    var first = transport.fetch(context, source, firstEnvelope);
    var expectedBaseBytes = baseBytes.length + tokenizerBytes.length + profileBytes.length;
    require(first.baseBytesTransferred() == expectedBaseBytes, "first fetch base byte count differs");
    require(
        first.adapterBytesTransferred() == adapterOne.length, "first adapter byte count differs");
    require(cache.accountedBytes() == expectedBaseBytes, "base cache accounting differs");

    var secondEnvelope = envelope(context, id('8'), id('a'), adapterTwo);
    var second = transport.fetch(context, source, secondEnvelope);
    require(second.baseBytesTransferred() == 0, "second adapter fetch transferred base bytes");
    require(
        second.adapterBytesTransferred() == adapterTwo.length, "second adapter byte count differs");
    require(source.baseFetches == 3, "cached base objects were fetched more than once");
    require(
        telemetry.snapshot().getOrDefault("base.cache_hits", 0L) == 3L,
        "base cache hit telemetry differs");

    var composition = ModelComposition.compose(context, second.envelope());
    ModelComposition.validateResume(composition, context, secondEnvelope.adapterCheckpointId());
    expectFailure(
        "INCOMPATIBLE_QLORA_RESUME",
        () -> ModelComposition.validateResume(composition, context, id('f')));
    var wrongBase =
        new QloraContracts.CertifiedContext(id('1'), id('f'), id('3'), id('4'), id('5'), id('6'));
    expectFailure(
        "INCOMPATIBLE_QLORA_RESUME",
        () ->
            ModelComposition.validateResume(
                composition, wrongBase, secondEnvelope.adapterCheckpointId()));

    var export =
        ModelComposition.derivedExport(composition, id('b'), "MIT", true, id('c'));
    require(
        export.applyQcId().equals(secondEnvelope.applyQcId()),
        "derived export lost ApplyQC provenance");
    expectFailure(
        "DERIVED_EXPORT_REDISTRIBUTION_FORBIDDEN",
        () -> ModelComposition.derivedExport(composition, id('b'), "restricted", false, id('c')));

    var wrongEnvelope = envelope(wrongBase, id('7'), id('9'), adapterOne);
    expectFailure("wrong base manifest", () -> transport.fetch(context, source, wrongEnvelope));
  }

  private static BaseObjectCache.BaseArtifact artifact(
      BaseObjectCache.Kind kind,
      String objectId,
      String media,
      String license,
      boolean redistribution,
      byte[] bytes) {
    return new BaseObjectCache.BaseArtifact(
        kind,
        objectId,
        QloraContracts.rawSha256(bytes),
        media,
        license,
        redistribution,
        bytes);
  }

  private static AdapterTransport.AdapterEnvelope envelope(
      QloraContracts.CertifiedContext context,
      String adapterId,
      String applyQcId,
      byte[] bytes) {
    return new AdapterTransport.AdapterEnvelope(
        adapterId,
        QloraContracts.rawSha256(bytes),
        applyQcId,
        context.parentAdapterId(),
        context.baseModelManifestId(),
        context.tokenizerHash(),
        context.quantizedBaseProfileId(),
        context.adapterParameterSchemaId(),
        context.trainingModeId(),
        new byte[] {1, 2, 3});
  }

  private static String id(char digit) {
    return "sha256:" + String.valueOf(digit).repeat(64);
  }

  private static void require(boolean condition, String message) {
    if (!condition) {
      throw new IllegalStateException(message);
    }
  }

  private static void expectFailure(String expected, CheckedRunnable action) throws Exception {
    try {
      action.run();
    } catch (IllegalArgumentException error) {
      require(error.getMessage().contains(expected), "unexpected rejection: " + error.getMessage());
      return;
    }
    throw new IllegalStateException("expected rejection was not observed: " + expected);
  }

  private static void delete(Path path) {
    try {
      Files.deleteIfExists(path);
    } catch (IOException error) {
      throw new java.io.UncheckedIOException(error);
    }
  }

  @FunctionalInterface
  private interface CheckedRunnable {
    void run() throws Exception;
  }

  private static final class MapSource implements AdapterTransport.ObjectSource {
    private final Map<String, BaseObjectCache.BaseArtifact> bases;
    private final Map<String, byte[]> adapters;
    private int baseFetches;

    private MapSource(
        Map<String, BaseObjectCache.BaseArtifact> bases, Map<String, byte[]> adapters) {
      this.bases = Map.copyOf(bases);
      this.adapters = Map.copyOf(adapters);
    }

    @Override
    public BaseObjectCache.BaseArtifact fetchBase(
        BaseObjectCache.Kind kind, String objectId) {
      baseFetches++;
      var result = bases.get(objectId);
      require(result != null && result.kind() == kind, "base source object is unavailable");
      return result;
    }

    @Override
    public byte[] fetchAdapter(String adapterCheckpointId) {
      var result = adapters.get(adapterCheckpointId);
      require(result != null, "adapter source object is unavailable");
      return result.clone();
    }
  }
}
