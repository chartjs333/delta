package io.deltareduce.node.qlora;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/** Fetches cached base objects and one opaque native-authorized adapter checkpoint. */
public final class AdapterTransport {
  private final BaseObjectCache baseCache;
  private final Path adapterRoot;
  private final QloraTelemetry telemetry;

  public AdapterTransport(BaseObjectCache baseCache, Path adapterRoot, QloraTelemetry telemetry)
      throws IOException {
    this.baseCache = Objects.requireNonNull(baseCache, "baseCache");
    this.adapterRoot = adapterRoot.toAbsolutePath().normalize();
    this.telemetry = Objects.requireNonNull(telemetry, "telemetry");
    Files.createDirectories(this.adapterRoot);
    QloraContracts.require(!Files.isSymbolicLink(this.adapterRoot), "adapter root is a symlink");
  }

  public FetchResult fetch(
      QloraContracts.CertifiedContext context, ObjectSource source, AdapterEnvelope envelope)
      throws IOException {
    Objects.requireNonNull(context, "context");
    Objects.requireNonNull(source, "source");
    envelope.validate(context);
    long baseTransferred = 0L;
    var requirements =
        List.of(
            new Requirement(BaseObjectCache.Kind.BASE, context.baseModelManifestId()),
            new Requirement(BaseObjectCache.Kind.TOKENIZER, context.tokenizerHash()),
            new Requirement(
                BaseObjectCache.Kind.QUANTIZATION_PROFILE, context.quantizedBaseProfileId()));
    for (var requirement : requirements) {
      if (baseCache.contains(requirement.objectId())) {
        telemetry.add("base.cache_hits", 1);
        continue;
      }
      var artifact = source.fetchBase(requirement.kind(), requirement.objectId());
      QloraContracts.require(
          artifact.kind() == requirement.kind()
              && artifact.objectId().equals(requirement.objectId()),
          "base source returned the wrong object");
      var result = baseCache.put(artifact);
      baseTransferred += result.transferredBytes();
      telemetry.add("base.bytes", result.transferredBytes());
    }

    var adapterBytes = source.fetchAdapter(envelope.adapterCheckpointId());
    QloraContracts.require(
        QloraContracts.rawSha256(adapterBytes).equals(envelope.payloadSha256()),
        "adapter payload hash mismatch");
    var target = adapterPath(envelope.adapterCheckpointId());
    var transferred = 0L;
    if (Files.exists(target)) {
      QloraContracts.require(
          Arrays.equals(Files.readAllBytes(target), adapterBytes), "immutable adapter collision");
    } else {
      var temporary = target.resolveSibling(target.getFileName() + ".native-tmp");
      Files.write(temporary, adapterBytes);
      try {
        Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE);
      } catch (java.nio.file.AtomicMoveNotSupportedException ignored) {
        Files.move(temporary, target);
      }
      transferred = adapterBytes.length;
      telemetry.add("adapter.bytes", transferred);
    }
    telemetry.add("fetch.completed", 1);
    return new FetchResult(target, baseTransferred, transferred, envelope.copy());
  }

  private Path adapterPath(String adapterId) {
    QloraContracts.requireContentId(adapterId, "adapter checkpoint ID");
    var path = adapterRoot.resolve(adapterId.substring(7)).normalize();
    QloraContracts.require(path.startsWith(adapterRoot), "adapter path escaped root");
    return path;
  }

  @FunctionalInterface
  public interface BaseFetcher {
    BaseObjectCache.BaseArtifact fetch(BaseObjectCache.Kind kind, String objectId) throws IOException;
  }

  public interface ObjectSource {
    BaseObjectCache.BaseArtifact fetchBase(BaseObjectCache.Kind kind, String objectId)
        throws IOException;

    byte[] fetchAdapter(String adapterCheckpointId) throws IOException;
  }

  public record AdapterEnvelope(
      String adapterCheckpointId,
      String payloadSha256,
      String applyQcId,
      String parentAdapterId,
      String baseModelManifestId,
      String tokenizerHash,
      String quantizedBaseProfileId,
      String adapterParameterSchemaId,
      String trainingModeId,
      byte[] nativeAuthorization) {
    public AdapterEnvelope {
      QloraContracts.requireContentId(adapterCheckpointId, "adapter checkpoint ID");
      QloraContracts.requireContentId(payloadSha256, "adapter payload hash");
      QloraContracts.requireContentId(applyQcId, "ApplyQC ID");
      QloraContracts.require(nativeAuthorization != null, "native authorization is missing");
      QloraContracts.require(nativeAuthorization.length > 0, "native authorization is empty");
      nativeAuthorization = Arrays.copyOf(nativeAuthorization, nativeAuthorization.length);
    }

    void validate(QloraContracts.CertifiedContext context) {
      QloraContracts.require(parentAdapterId.equals(context.parentAdapterId()), "wrong parent adapter");
      QloraContracts.require(
          baseModelManifestId.equals(context.baseModelManifestId()), "wrong base manifest");
      QloraContracts.require(tokenizerHash.equals(context.tokenizerHash()), "wrong tokenizer");
      QloraContracts.require(
          quantizedBaseProfileId.equals(context.quantizedBaseProfileId()),
          "wrong quantization profile");
      QloraContracts.require(
          adapterParameterSchemaId.equals(context.adapterParameterSchemaId()),
          "wrong adapter schema");
      QloraContracts.require(trainingModeId.equals(context.trainingModeId()), "wrong training mode");
    }

    @Override
    public byte[] nativeAuthorization() {
      return Arrays.copyOf(nativeAuthorization, nativeAuthorization.length);
    }

    AdapterEnvelope copy() {
      return new AdapterEnvelope(
          adapterCheckpointId,
          payloadSha256,
          applyQcId,
          parentAdapterId,
          baseModelManifestId,
          tokenizerHash,
          quantizedBaseProfileId,
          adapterParameterSchemaId,
          trainingModeId,
          nativeAuthorization);
    }
  }

  private record Requirement(BaseObjectCache.Kind kind, String objectId) {}

  public record FetchResult(
      Path adapterPath,
      long baseBytesTransferred,
      long adapterBytesTransferred,
      AdapterEnvelope envelope) {}
}
