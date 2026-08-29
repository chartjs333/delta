package io.deltareduce.node.qlora;

import java.util.Arrays;

/** Exact native-verified base+adapter composition and resume metadata. */
public final class ModelComposition {
  private ModelComposition() {}

  public static Composition compose(
      QloraContracts.CertifiedContext context, AdapterTransport.AdapterEnvelope adapter) {
    adapter.validate(context);
    return new Composition(
        context.baseModelManifestId(),
        context.tokenizerHash(),
        context.quantizedBaseProfileId(),
        context.adapterParameterSchemaId(),
        adapter.adapterCheckpointId(),
        adapter.applyQcId(),
        adapter.nativeAuthorization());
  }

  public static void validateResume(
      Composition current,
      QloraContracts.CertifiedContext requested,
      String requestedParentAdapterId) {
    QloraContracts.requireContentId(requestedParentAdapterId, "resume parent adapter ID");
    QloraContracts.require(
        current.baseModelManifestId().equals(requested.baseModelManifestId())
            && current.tokenizerHash().equals(requested.tokenizerHash())
            && current.quantizedBaseProfileId().equals(requested.quantizedBaseProfileId())
            && current.adapterParameterSchemaId().equals(requested.adapterParameterSchemaId())
            && current.adapterCheckpointId().equals(requestedParentAdapterId),
        "INCOMPATIBLE_QLORA_RESUME");
  }

  public static DerivedExport derivedExport(
      Composition composition,
      String mergedModelId,
      String sourceLicense,
      boolean redistributionAllowed,
      String provenanceId) {
    QloraContracts.requireContentId(mergedModelId, "merged model ID");
    QloraContracts.requireContentId(provenanceId, "derived provenance ID");
    QloraContracts.require(
        sourceLicense != null && !sourceLicense.isBlank(), "source license is missing");
    QloraContracts.require(redistributionAllowed, "DERIVED_EXPORT_REDISTRIBUTION_FORBIDDEN");
    return new DerivedExport(
        mergedModelId,
        composition.baseModelManifestId(),
        composition.adapterCheckpointId(),
        composition.applyQcId(),
        sourceLicense,
        provenanceId);
  }

  public record Composition(
      String baseModelManifestId,
      String tokenizerHash,
      String quantizedBaseProfileId,
      String adapterParameterSchemaId,
      String adapterCheckpointId,
      String applyQcId,
      byte[] nativeAuthorization) {
    public Composition {
      QloraContracts.requireContentId(applyQcId, "composition ApplyQC ID");
      QloraContracts.require(nativeAuthorization.length > 0, "composition authorization is empty");
      nativeAuthorization = Arrays.copyOf(nativeAuthorization, nativeAuthorization.length);
    }

    @Override
    public byte[] nativeAuthorization() {
      return Arrays.copyOf(nativeAuthorization, nativeAuthorization.length);
    }
  }

  public record DerivedExport(
      String mergedModelId,
      String baseModelManifestId,
      String adapterCheckpointId,
      String applyQcId,
      String sourceLicense,
      String provenanceId) {}
}
